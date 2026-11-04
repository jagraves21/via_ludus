import math

import numpy as np
import pytest

from via_ludus.board import Cell, PlayerColor
from via_ludus.utils import OptionalDependencyError
from via_ludus.visualizations import plot_agent_scores


R = PlayerColor.RED
B = PlayerColor.BLUE

# On an empty 11 x 11 board the index-scoring player scores the white cells
# 12 (row 1, column 1) up to 108 (row 9, column 9).
LOWEST_SCORE = 12
HIGHEST_SCORE = 108


@pytest.fixture
def same_color(plt):
	from matplotlib.colors import same_color as _same_color

	return _same_color


@pytest.fixture
def colormap(plt):
	def _colormap(name="YlOrRd_r"):
		import matplotlib

		return matplotlib.colormaps[name]

	return _colormap


@pytest.fixture
def agent(index_scoring_player_class):
	return index_scoring_player_class(R)


@pytest.fixture
def drawn_scores(plt, patch_colors):
	"""Plot agent scores without showing them; returns (ax, fig, colors)."""
	def _draw(board, agent, color=R, **kwargs):
		kwargs.setdefault("show", False)
		_, fig, ax = plot_agent_scores(board, agent, color, return_fig=True, **kwargs)

		return ax, fig, patch_colors(ax, board)

	return _draw


def _scores_to_colors(board, colormap, low, high):
	return {
		(row, col): colormap((row * board.cols + col - low) / (high - low))
		for row, col in board.available
	}


class TestScoreColors:
	def test_cells_are_colored_by_their_score(self, drawn_scores, same_color, colormap, board, agent):
		_, _, colors = drawn_scores(board, agent)

		expected = _scores_to_colors(board, colormap(), LOWEST_SCORE, HIGHEST_SCORE)

		for position, color in expected.items():
			assert same_color(colors[position], color), position

	def test_the_lowest_and_highest_scores_get_the_ends_of_the_color_map(self, drawn_scores, same_color, colormap, board, agent):
		_, _, colors = drawn_scores(board, agent)

		assert same_color(colors[(1, 1)], colormap()(0.0))
		assert same_color(colors[(9, 9)], colormap()(1.0))

	def test_a_custom_color_map(self, drawn_scores, same_color, colormap, board, agent):
		_, _, colors = drawn_scores(board, agent, cmap="viridis")

		assert same_color(colors[(1, 1)], colormap("viridis")(0.0))
		assert same_color(colors[(9, 9)], colormap("viridis")(1.0))

	def test_the_default_color_map_is_reversed_yellow_orange_red(self, drawn_scores, same_color, colormap, board, agent):
		_, _, default_colors = drawn_scores(board, agent)
		_, _, explicit_colors = drawn_scores(board, agent, cmap="YlOrRd_r")

		assert all(same_color(default_colors[key], explicit_colors[key]) for key in default_colors)

	def test_unknown_color_maps_are_rejected(self, plt, board, agent):
		with pytest.raises(KeyError):
			plot_agent_scores(board, agent, R, cmap="no_such_colormap", show=False)

	def test_all_scores_equal_use_the_middle_of_the_color_map(self, drawn_scores, same_color, colormap, board, tied_scoring_player_class):
		_, _, colors = drawn_scores(board, tied_scoring_player_class(R))

		assert all(same_color(colors[position], colormap()(0.5)) for position in board.available)

	def test_scores_may_be_integers_or_numpy_numbers(self, drawn_scores, same_color, colormap, board, agent):
		class IntegerScorer(type(agent)):
			def score_moves(self, board, color):
				scores = super().score_moves(board, color)

				return {
					position: (int(score) if index % 2 else np.float32(score))
					for index, (position, score) in enumerate(scores.items())
				}

		_, _, colors = drawn_scores(board, IntegerScorer(R))

		assert same_color(colors[(1, 1)], colormap()(0.0))
		assert same_color(colors[(9, 9)], colormap()(1.0))

	def test_scores_for_cells_that_are_not_available_are_ignored(self, drawn_scores, same_color, colormap, board, agent):
		board.set(1, 1, Cell.RED)

		class ExtraScores(type(agent)):
			def score_moves(self, board, color):
				scores = super().score_moves(board, color)
				scores[(1, 1)] = 10_000.0
				scores[(0, 1)] = -10_000.0

				return scores

		_, fig, colors = drawn_scores(board, ExtraScores(R))

		# the color scale only covers the available cells: 14 (1, 3) to 108 (9, 9)
		assert same_color(colors[(1, 3)], colormap()(0.0))
		assert same_color(colors[(9, 9)], colormap()(1.0))
		assert fig.axes[1].get_ylim() == pytest.approx((14.0, 108.0))

	@pytest.mark.parametrize("bad_score", [math.nan, math.inf, -math.inf])
	def test_cells_without_a_finite_score_stay_white(self, drawn_scores, same_color, colormap, board, agent, bad_score):
		class PartlyUnscored(type(agent)):
			def score_moves(self, board, color):
				scores = super().score_moves(board, color)
				scores[(1, 1)] = bad_score
				scores[(1, 3)] = bad_score

				return scores

		_, fig, colors = drawn_scores(board, PartlyUnscored(R))

		assert same_color(colors[(1, 1)], "white")
		assert same_color(colors[(1, 3)], "white")
		# the color scale only covers the finite scores: 16 (row 1, column 5) to 108
		assert same_color(colors[(1, 5)], colormap()(0.0))
		assert same_color(colors[(9, 9)], colormap()(1.0))
		assert fig.axes[1].get_ylim() == pytest.approx((16.0, 108.0))

	def test_the_player_is_asked_to_score_for_the_requested_color(self, drawn_scores, board, agent):
		drawn_scores(board, agent, B)

		assert agent.scored_colors == [B]


class TestOccupiedCells:
	def test_stones_are_drawn_in_dark_red_and_dark_blue(self, drawn_scores, same_color, board, agent):
		board.set(1, 1, Cell.RED)
		board.set(3, 3, Cell.BLUE)

		_, _, colors = drawn_scores(board, agent)

		assert same_color(colors[(1, 1)], "#400000")
		assert same_color(colors[(3, 3)], "#000040")

	def test_prefilled_cells_and_edges_use_the_same_dark_colors(self, drawn_scores, same_color, board, agent):
		_, _, colors = drawn_scores(board, agent)

		assert same_color(colors[(0, 5)], "#400000")
		assert same_color(colors[(2, 1)], "#400000")
		assert same_color(colors[(5, 0)], "#000040")
		assert same_color(colors[(1, 2)], "#000040")

	def test_walls_are_black(self, drawn_scores, same_color, board, agent):
		_, _, colors = drawn_scores(board, agent)

		for position in ((0, 0), (0, 10), (10, 0), (10, 10)):
			assert same_color(colors[position], "black")

	def test_every_cell_is_drawn(self, drawn_scores, board_type, board_size, index_scoring_player_class):
		board = board_type(size=board_size)

		ax, _, _ = drawn_scores(board, index_scoring_player_class(R))

		assert len(ax.patches) == board_size * board_size

	def test_a_finished_game_has_no_scored_cells(self, drawn_scores, same_color, board_type, full_winning_game, agent):
		board = full_winning_game(board_type)

		ax, fig, colors = drawn_scores(board, agent)

		assert len(fig.axes) == 1
		assert all(
			same_color(colors[(row, col)], "#400000" if board.get(row, col) is Cell.RED else "#000040")
			for row in range(1, board.rows - 1)
			for col in range(1, board.cols - 1)
		)


class TestTitleAndColorbar:
	def test_title_without_a_name(self, drawn_scores, board, agent):
		ax, _, _ = drawn_scores(board, agent, R)

		assert ax.get_title() == "Player: RED | Evaluating: RED"

	def test_title_with_a_name(self, drawn_scores, board, agent):
		ax, _, _ = drawn_scores(board, agent, R, name="Index Scoring")

		assert ax.get_title() == "Index Scoring\nPlayer: RED | Evaluating: RED"

	def test_title_names_the_color_being_evaluated(self, drawn_scores, board, index_scoring_player_class):
		ax, _, _ = drawn_scores(board, index_scoring_player_class(B), R)

		assert ax.get_title() == "Player: BLUE | Evaluating: RED"

	def test_the_name_goes_on_its_own_first_line(self, drawn_scores, board, agent):
		ax, _, _ = drawn_scores(board, agent, B, name="My Heuristic")

		assert ax.get_title().split("\n") == [
			"My Heuristic",
			"Player: RED | Evaluating: BLUE",
		]

	def test_an_empty_name_is_the_same_as_no_name(self, drawn_scores, board, agent):
		ax, _, _ = drawn_scores(board, agent, R, name="")

		assert ax.get_title() == "Player: RED | Evaluating: RED"

	def test_the_name_does_not_change_anything_else(self, drawn_scores, same_color, board, agent):
		_, fig_plain, colors_plain = drawn_scores(board, agent)
		_, fig_named, colors_named = drawn_scores(board, agent, name="Named")

		assert all(same_color(colors_plain[key], colors_named[key]) for key in colors_plain)
		assert len(fig_plain.axes) == len(fig_named.axes) == 2

	def test_the_name_is_used_when_drawing_on_a_given_axes(self, plt, board, agent):
		fig, ax = plt.subplots()

		plot_agent_scores(board, agent, R, ax=ax, name="Given Axes", show=False)

		assert ax.get_title() == "Given Axes\nPlayer: RED | Evaluating: RED"

	def test_colorbar_is_added_next_to_the_board(self, drawn_scores, board, agent):
		ax, fig, _ = drawn_scores(board, agent)

		assert len(fig.axes) == 2
		assert fig.axes[0] is ax

	def test_colorbar_label_names_the_evaluated_color(self, drawn_scores, board, agent):
		_, fig, _ = drawn_scores(board, agent, B)

		assert fig.axes[1].get_ylabel() == "Move Score (BLUE)"

	def test_colorbar_covers_the_score_range(self, drawn_scores, board, agent):
		_, fig, _ = drawn_scores(board, agent)

		assert fig.axes[1].get_ylim() == pytest.approx((LOWEST_SCORE, HIGHEST_SCORE))

	def test_colorbar_range_is_widened_when_all_scores_are_equal(self, drawn_scores, board, tied_scoring_player_class):
		_, fig, _ = drawn_scores(board, tied_scoring_player_class(R))

		assert fig.axes[1].get_ylim() == pytest.approx((-0.5, 0.5))

	def test_no_colorbar_without_finite_scores(self, drawn_scores, same_color, board, agent):
		class Unscored(type(agent)):
			def score_moves(self, board, color):
				return {position: math.nan for position in board.available}

		ax, fig, colors = drawn_scores(board, Unscored(R))

		assert len(fig.axes) == 1
		assert ax.get_title() == "Player: RED | Evaluating: RED"
		assert all(same_color(colors[position], "white") for position in board.available)


class TestFigureAndAxes:
	@pytest.mark.parametrize(
		"size, side",
		[(3, 2.0), (5, 3.0), (11, 6.6), (21, 12.0)],
	)
	def test_the_figure_size_grows_with_the_board(self, drawn_scores, board_type, index_scoring_player_class, size, side):
		_, fig, _ = drawn_scores(board_type(size=size), index_scoring_player_class(R))

		assert tuple(fig.get_size_inches()) == pytest.approx((side, side))

	def test_an_explicit_figure_size_is_used(self, drawn_scores, board, agent):
		_, fig, _ = drawn_scores(board, agent, figsize=(6, 4))

		assert tuple(fig.get_size_inches()) == (6.0, 4.0)

	def test_return_fig_returns_nothing_figure_and_axes(self, plt, board, agent):
		result, fig, ax = plot_agent_scores(board, agent, R, show=False, return_fig=True)

		assert result is None
		assert ax.figure is fig

	def test_returns_nothing_by_default(self, plt, board, agent):
		assert plot_agent_scores(board, agent, R, show=False) is None

	def test_draws_on_a_given_axes(self, plt, board, agent):
		fig, ax = plt.subplots()

		plot_agent_scores(board, agent, R, ax=ax, show=False)

		assert len(ax.patches) == 121
		assert ax.get_title() == "Player: RED | Evaluating: RED"
		assert len(fig.axes) == 2

	def test_does_not_create_another_figure_for_a_given_axes(self, plt, board, agent):
		fig, ax = plt.subplots()

		plot_agent_scores(board, agent, R, ax=ax, show=False)

		assert plt.get_fignums() == [fig.number]

	def test_the_board_is_not_modified(self, plt, board, agent):
		before = board.serialize()

		plot_agent_scores(board, agent, R, show=False, close=True)

		assert board.serialize() == before

	def test_shows_by_default(self, plt, board, agent, monkeypatch):
		shown = []
		monkeypatch.setattr(plt, "show", lambda *args, **kwargs: shown.append(True))

		plot_agent_scores(board, agent, R)

		assert shown == [True]

	def test_the_figure_can_be_closed(self, plt, board, agent):
		_, fig, _ = plot_agent_scores(board, agent, R, show=False, close=True, return_fig=True)

		assert not plt.fignum_exists(fig.number)

	def test_the_player_is_scored_once(self, plt, board, agent):
		plot_agent_scores(board, agent, R, show=False)

		assert len(agent.scored_colors) == 1


class TestRealAgents:
	def test_the_random_agent_is_plotted_with_a_flat_color_scale(self, drawn_scores, same_color, colormap, board):
		from via_ludus.ai.via_ludus_agents import RandomAgent

		ax, fig, colors = drawn_scores(board, RandomAgent(R), name="Random")

		assert ax.get_title() == "Random\nPlayer: RED | Evaluating: RED"
		assert all(same_color(colors[position], colormap()(0.5)) for position in board.available)
		assert fig.axes[1].get_ylim() == pytest.approx((-0.5, 0.5))

	def test_agents_can_evaluate_the_other_player(self, drawn_scores, board):
		from via_ludus.ai.via_ludus_agents import RandomAgent

		ax, fig, _ = drawn_scores(board, RandomAgent(R), B)

		assert ax.get_title() == "Player: RED | Evaluating: BLUE"
		assert fig.axes[1].get_ylabel() == "Move Score (BLUE)"


class TestOptionalTitle:
	"""``_plot_agent_scores`` only adds a title when it is given one."""

	def _plot(self, board, agent, **kwargs):
		from via_ludus.visualizations.score_visualizations import _plot_agent_scores

		_, _, ax = _plot_agent_scores(
			board,
			agent,
			R,
			cmap="YlOrRd_r",
			show=False,
			return_fig=True,
			**kwargs,
		)

		return ax

	def test_no_title_is_added_when_it_is_none(self, plt, board, agent):
		ax = self._plot(board, agent, title=None)

		assert ax.get_title() == ""

	def test_the_given_title_is_used_unchanged(self, plt, board, agent):
		ax = self._plot(board, agent, title="Custom title\nsecond line")

		assert ax.get_title() == "Custom title\nsecond line"

	def test_the_scores_are_drawn_without_a_title(self, plt, same_color, colormap, board, agent):
		ax = self._plot(board, agent, title=None)

		assert len(ax.patches) == 121
		assert len(ax.figure.axes) == 2


class TestValidation:
	@pytest.mark.parametrize("make_value", [
		lambda cls: None,
		lambda cls: "agent",
		lambda cls: cls,
	], ids=["none", "string", "class-not-instance"])
	def test_agents_must_be_scoring_player_instances(self, plt, board, index_scoring_player_class, make_value):
		with pytest.raises(TypeError, match="Expected a ScoringPlayer"):
			plot_agent_scores(board, make_value(index_scoring_player_class), R, show=False)

	@pytest.mark.parametrize("value", ["board", None, 11, [[0]]])
	def test_boards_must_be_boards(self, plt, agent, value):
		with pytest.raises(TypeError, match="Expected a Board"):
			plot_agent_scores(value, agent, R, show=False)

	@pytest.mark.parametrize("figsize", [None, (2, 2)])
	def test_an_invalid_board_is_rejected_before_a_figure_is_created(self, plt, agent, figsize):
		with pytest.raises(TypeError):
			plot_agent_scores("board", agent, R, figsize=figsize, show=False)

		assert plt.get_fignums() == []

	def test_the_player_is_not_asked_to_score_an_invalid_board(self, plt, agent):
		with pytest.raises(TypeError):
			plot_agent_scores("board", agent, R, show=False)

		assert agent.scored_colors == []

	def test_plain_players_are_rejected(self, plt, board, first_move_player_class):
		with pytest.raises(TypeError, match="Expected a ScoringPlayer"):
			plot_agent_scores(board, first_move_player_class(R), R, show=False)

	def test_invalid_agents_are_rejected_before_a_figure_is_created(self, plt, board):
		with pytest.raises(TypeError):
			plot_agent_scores(board, "agent", R, show=False)

		assert plt.get_fignums() == []

	@pytest.mark.parametrize("color", ["red", None, Cell.RED, 1])
	def test_the_evaluated_color_must_be_a_player_color(self, plt, board, agent, color):
		with pytest.raises(TypeError):
			plot_agent_scores(board, agent, color, show=False)

	def test_an_invalid_color_is_rejected_before_a_figure_is_created(self, plt, board, agent):
		with pytest.raises(TypeError):
			plot_agent_scores(board, agent, "red", show=False)

		assert plt.get_fignums() == []

	@pytest.mark.parametrize("name", [123, 1.5, ["name"], b"bytes"])
	def test_the_name_must_be_a_string(self, plt, board, agent, name):
		with pytest.raises(TypeError, match="name must be a string, got"):
			plot_agent_scores(board, agent, R, name=name, show=False)

	def test_an_invalid_name_is_rejected_before_a_figure_is_created(self, plt, board, agent):
		with pytest.raises(TypeError):
			plot_agent_scores(board, agent, R, name=123, show=False)

		assert plt.get_fignums() == []

	def test_an_invalid_name_does_not_ask_the_player_for_scores(self, plt, board, agent):
		with pytest.raises(TypeError):
			plot_agent_scores(board, agent, R, name=123, show=False)

		assert agent.scored_colors == []

	def test_the_player_is_not_asked_to_score_for_an_invalid_color(self, plt, board, agent):
		with pytest.raises(TypeError):
			plot_agent_scores(board, agent, "red", show=False)

		assert agent.scored_colors == []


class TestWithoutMatplotlib:
	"""These tests run whether or not matplotlib is installed."""

	def test_plotting_explains_the_missing_dependency(self, block_imports, board, agent):
		block_imports("matplotlib")

		with pytest.raises(OptionalDependencyError, match="visualization"):
			plot_agent_scores(board, agent, R, show=False)

	def test_an_invalid_board_is_still_reported_first(self, block_imports, agent):
		block_imports("matplotlib")

		with pytest.raises(TypeError, match="Expected a Board"):
			plot_agent_scores("board", agent, R, show=False)

	def test_invalid_agents_are_still_reported_first(self, block_imports, board):
		block_imports("matplotlib")

		with pytest.raises(TypeError, match="Expected a ScoringPlayer"):
			plot_agent_scores(board, "agent", R, show=False)

	def test_the_player_is_not_asked_for_scores(self, block_imports, board, agent):
		block_imports("matplotlib")

		with pytest.raises(OptionalDependencyError):
			plot_agent_scores(board, agent, R, show=False)

		assert agent.scored_colors == []
