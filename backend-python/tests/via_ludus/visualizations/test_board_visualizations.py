import pytest

from via_ludus.board import Cell, SearchBoard, UnionFindBoard
from via_ludus.utils import OptionalDependencyError
from via_ludus.visualizations import plot_board


@pytest.fixture
def same_color(plt):
	from matplotlib.colors import same_color as _same_color

	return _same_color


@pytest.fixture
def drawn_board(plt, patch_colors):
	"""Plot a board without showing it; returns (ax, fig, colors by position)."""
	def _draw(board, **kwargs):
		kwargs.setdefault("show", False)
		ax, fig, _ = plot_board(board, return_fig=True, **kwargs)

		return ax, fig, patch_colors(ax, board)

	return _draw


class TestBoardDrawing:
	def test_one_square_per_cell(self, drawn_board, board_type, board_size):
		board = board_type(size=board_size)

		ax, _, _ = drawn_board(board)

		assert len(ax.patches) == board_size * board_size

	def test_cells_are_drawn_in_their_own_color(self, drawn_board, same_color, board):
		_, _, colors = drawn_board(board)

		for row in range(board.rows):
			for col in range(board.cols):
				assert same_color(colors[(row, col)], board.get(row, col).color), (row, col)

	def test_squares_have_unit_size_and_a_black_border(self, drawn_board, same_color, board):
		ax, _, _ = drawn_board(board)

		for patch in ax.patches:
			assert patch.get_width() == 1
			assert patch.get_height() == 1
			assert same_color(patch.get_edgecolor(), "black")

	def test_row_zero_is_drawn_at_the_top(self, drawn_board, board):
		ax, _, _ = drawn_board(board)

		positions = {patch.get_xy() for patch in ax.patches}

		assert (1, board.rows - 1) in positions
		assert (0, 0) in positions
		assert (board.cols - 1, board.rows - 1) in positions

	def test_the_top_edge_is_red_and_the_left_edge_is_blue(self, drawn_board, same_color, board):
		_, _, colors = drawn_board(board)

		assert same_color(colors[(0, 5)], "red")
		assert same_color(colors[(board.rows - 1, 5)], "red")
		assert same_color(colors[(5, 0)], "blue")
		assert same_color(colors[(5, board.cols - 1)], "blue")
		assert same_color(colors[(0, 0)], "black")

	def test_claimed_cells_are_drawn_in_the_players_color(self, drawn_board, same_color, board_type, red_winning_game):
		board = red_winning_game(board_type)

		_, _, colors = drawn_board(board)

		for row in range(board.rows):
			for col in range(board.cols):
				assert same_color(colors[(row, col)], board.get(row, col).color), (row, col)

	def test_unclaimed_cells_are_white(self, drawn_board, same_color, board):
		_, _, colors = drawn_board(board)

		for row, col in board.available:
			assert same_color(colors[(row, col)], "white")

	def test_the_drawing_follows_later_moves(self, drawn_board, same_color, board):
		board.set(1, 1, Cell.RED)
		board.set(3, 3, Cell.BLUE)

		_, _, colors = drawn_board(board)

		assert same_color(colors[(1, 1)], "red")
		assert same_color(colors[(3, 3)], "blue")

	def test_axes_cover_the_board(self, drawn_board, board_type):
		board = board_type(size=7)

		ax, _, _ = drawn_board(board)

		assert ax.get_xlim() == (0, 7)
		assert ax.get_ylim() == (0, 7)

	def test_axes_are_square_and_hidden(self, drawn_board, board):
		ax, _, _ = drawn_board(board)

		assert ax.get_aspect() == 1.0
		assert not ax.axison

	def test_both_implementations_are_drawn_identically(self, drawn_board, same_color, red_winning_game):
		search_colors = drawn_board(red_winning_game(SearchBoard))[2]
		union_find_colors = drawn_board(red_winning_game(UnionFindBoard))[2]

		assert search_colors.keys() == union_find_colors.keys()
		assert all(same_color(search_colors[key], union_find_colors[key]) for key in search_colors)


class TestFigure:
	@pytest.mark.parametrize(
		"size, side",
		[(3, 2.0), (5, 2.0), (11, 2.2), (21, 4.2), (61, 12.0)],
	)
	def test_the_figure_size_grows_with_the_board(self, drawn_board, size, side):
		_, fig, _ = drawn_board(SearchBoard(size=size))

		assert tuple(fig.get_size_inches()) == pytest.approx((side, side))

	def test_the_figure_is_square(self, drawn_board):
		_, fig, _ = drawn_board(UnionFindBoard(size=15))

		width, height = fig.get_size_inches()

		assert width == height

	def test_an_explicit_figure_size_is_used(self, drawn_board, board):
		_, fig, _ = drawn_board(board, figsize=(6, 4))

		assert tuple(fig.get_size_inches()) == (6.0, 4.0)

	def test_returns_the_axes_the_figure_and_the_axes_again(self, plt, board):
		result = plot_board(board, show=False, return_fig=True)

		assert len(result) == 3
		assert result[0] is result[2]
		assert result[1] is result[2].figure

	def test_returns_the_axes_by_default(self, plt, board):
		ax = plot_board(board, show=False)

		assert ax in ax.figure.axes


class TestGivenAxes:
	def test_draws_on_the_given_axes(self, plt, board):
		fig, ax = plt.subplots()

		result = plot_board(board, ax=ax, show=False)

		assert result is ax
		assert len(ax.patches) == 121

	def test_does_not_create_another_figure(self, plt, board):
		fig, ax = plt.subplots()

		plot_board(board, ax=ax, show=False)

		assert plt.get_fignums() == [fig.number]

	def test_keeps_the_figure_size_of_the_given_axes(self, plt, board):
		fig, ax = plt.subplots(figsize=(4, 4))

		plot_board(board, ax=ax, show=False)

		assert tuple(fig.get_size_inches()) == (4.0, 4.0)

	def test_several_boards_can_share_a_figure(self, plt, board_type):
		fig, axes = plt.subplots(1, 2)

		for ax, size in zip(axes, (3, 5)):
			plot_board(board_type(size=size), ax=ax, show=False)

		assert [len(ax.patches) for ax in axes] == [9, 25]


class TestShowAndClose:
	def test_shows_by_default(self, plt, board, monkeypatch):
		shown = []
		monkeypatch.setattr(plt, "show", lambda *args, **kwargs: shown.append(True))

		plot_board(board)

		assert shown == [True]

	def test_show_can_be_disabled(self, plt, board, monkeypatch):
		shown = []
		monkeypatch.setattr(plt, "show", lambda *args, **kwargs: shown.append(True))

		plot_board(board, show=False)

		assert shown == []

	def test_the_figure_can_be_closed(self, plt, board):
		_, fig, _ = plot_board(board, show=False, close=True, return_fig=True)

		assert not plt.fignum_exists(fig.number)

	def test_the_figure_stays_open_by_default(self, plt, board):
		_, fig, _ = plot_board(board, show=False, return_fig=True)

		assert plt.fignum_exists(fig.number)


class TestInvalidBoards:
	@pytest.mark.parametrize("value", ["board", None, 11, [[0]]])
	def test_non_boards_are_rejected(self, plt, value):
		with pytest.raises(TypeError, match="Expected a Board"):
			plot_board(value, figsize=(2, 2), show=False)

	@pytest.mark.parametrize("value", ["board", None, 11, [[0]]])
	def test_non_boards_are_rejected_without_a_figure_size(self, plt, value):
		with pytest.raises(TypeError, match="Expected a Board"):
			plot_board(value, show=False)

	def test_non_boards_are_rejected_for_a_given_axes(self, plt):
		fig, ax = plt.subplots()

		with pytest.raises(TypeError, match="Expected a Board"):
			plot_board("board", ax=ax, show=False)

	@pytest.mark.parametrize("figsize", [None, (2, 2)])
	def test_no_figure_is_created_for_a_non_board(self, plt, figsize):
		with pytest.raises(TypeError):
			plot_board("board", figsize=figsize, show=False)

		assert plt.get_fignums() == []


class TestBoardPlotMethod:
	def test_draws_the_board(self, plt, board):
		fig, ax = plt.subplots()

		board.plot(ax=ax, show=False)

		assert len(ax.patches) == 121

	def test_returns_nothing(self, plt, board):
		assert board.plot(show=False, close=True) is None

	def test_keyword_arguments_are_forwarded_to_plot_board(self, plt, board):
		before = set(plt.get_fignums())

		board.plot(show=False, close=True)

		assert set(plt.get_fignums()) == before

	def test_shows_by_default(self, plt, board, monkeypatch):
		shown = []
		monkeypatch.setattr(plt, "show", lambda *args, **kwargs: shown.append(True))

		board.plot()

		assert shown == [True]


class TestWithoutMatplotlib:
	"""These tests run whether or not matplotlib is installed."""

	def test_plot_board_explains_the_missing_dependency(self, block_imports, board):
		block_imports("matplotlib")

		with pytest.raises(OptionalDependencyError, match="visualization"):
			plot_board(board, show=False)

	def test_a_non_board_is_still_reported_first(self, block_imports):
		block_imports("matplotlib")

		with pytest.raises(TypeError, match="Expected a Board"):
			plot_board("board", show=False)

	def test_board_plot_explains_the_missing_dependency(self, block_imports, board):
		block_imports("matplotlib")

		with pytest.raises(OptionalDependencyError, match="matplotlib"):
			board.plot(show=False)

	def test_boards_work_without_matplotlib(self, block_imports, board_type):
		block_imports("matplotlib")

		board = board_type(size=5)
		board.set(1, 1, Cell.RED)

		assert board.get(1, 1) is Cell.RED
