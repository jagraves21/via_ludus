import math

import pytest

from via_ludus.board import PlayerColor
from via_ludus.player import (
	BestSelector,
	DeterministicScoringMixin,
	MaxSelector,
	MinSelector,
	Player,
	RandomMaxSelector,
	ScoringPlayer,
	SoftmaxSelector,
)


class TestScoringPlayerConstruction:
	def test_scoring_player_is_a_player(self):
		assert issubclass(ScoringPlayer, Player)

	def test_scoring_player_is_abstract(self):
		with pytest.raises(TypeError):
			ScoringPlayer(PlayerColor.RED)

	def test_subclass_must_implement_score_moves(self):
		class Incomplete(ScoringPlayer):
			pass

		with pytest.raises(TypeError):
			Incomplete(PlayerColor.RED)

	def test_rejects_invalid_colors(self, index_scoring_player_class):
		with pytest.raises(TypeError, match="Invalid player color"):
			index_scoring_player_class("red")

	def test_color_and_cell(self, index_scoring_player_class, player_color):
		player = index_scoring_player_class(player_color)

		assert player.color is player_color
		assert player.cell is player_color.cell

	def test_default_selector_is_created_by_create_selector(self, index_scoring_player_class):
		player = index_scoring_player_class(PlayerColor.RED)

		assert type(player.create_selector()) is BestSelector

	def test_create_selector_is_used_when_no_selector_is_given(self, index_scoring_player_class, board):
		class MinPlayer(index_scoring_player_class):
			def create_selector(self):
				return MinSelector()

		assert MinPlayer(PlayerColor.RED).choose_move(board) == min(board.available)

	def test_explicit_selector_is_used(self, index_scoring_player_class, board):
		player = index_scoring_player_class(PlayerColor.RED, selector=MinSelector())

		assert player.choose_move(board) == min(board.available)

	def test_create_selector_is_not_called_when_a_selector_is_given(self, index_scoring_player_class):
		class StrictPlayer(index_scoring_player_class):
			def create_selector(self):
				raise AssertionError("create_selector must not be called")

		StrictPlayer(PlayerColor.RED, selector=MaxSelector())


class TestScoringPlayerDeterminism:
	def test_scoring_is_not_deterministic_by_default(self, index_scoring_player_class):
		assert index_scoring_player_class(PlayerColor.RED).has_deterministic_scoring is False

	def test_deterministic_scoring_mixin(self, index_scoring_player_class):
		class DeterministicPlayer(DeterministicScoringMixin, index_scoring_player_class):
			pass

		assert DeterministicPlayer(PlayerColor.RED).has_deterministic_scoring is True

	@pytest.mark.parametrize(
		"selector, expected",
		[
			(MaxSelector(), False),
			(MinSelector(), False),
			(RandomMaxSelector(seed=0), True),
			(SoftmaxSelector(seed=0), True),
		],
		ids=["max", "min", "random-max", "softmax"],
	)
	def test_is_stochastic_follows_the_selector(self, index_scoring_player_class, selector, expected):
		player = index_scoring_player_class(PlayerColor.RED, selector=selector)

		assert player.is_stochastic is expected

	@pytest.mark.parametrize(
		"deterministic_scoring, stochastic_selector, expected",
		[
			(True, False, True),
			(True, True, False),
			(False, False, False),
			(False, True, False),
		],
		ids=[
			"deterministic-scoring-and-selector",
			"deterministic-scoring-random-selector",
			"non-deterministic-scoring",
			"non-deterministic-scoring-random-selector",
		],
	)
	def test_player_is_deterministic_only_with_deterministic_scoring_and_selector(
		self,
		index_scoring_player_class,
		deterministic_scoring,
		stochastic_selector,
		expected,
	):
		base = (
			(DeterministicScoringMixin, index_scoring_player_class)
			if deterministic_scoring
			else (index_scoring_player_class,)
		)

		class ConfiguredPlayer(*base):
			pass

		selector = RandomMaxSelector(seed=0) if stochastic_selector else MaxSelector()
		player = ConfiguredPlayer(PlayerColor.RED, selector=selector)

		assert player.is_deterministic is expected


class TestChooseMove:
	def test_scores_moves_with_the_players_own_color(self, index_scoring_player_class, board, player_color):
		player = index_scoring_player_class(player_color)

		player.choose_move(board)

		assert player.scored_colors == [player_color]

	def test_default_selector_chooses_the_highest_scoring_move(self, index_scoring_player_class, board, player_color):
		player = index_scoring_player_class(player_color)

		assert player.choose_move(board) == max(board.available)

	def test_does_not_modify_the_board(self, index_scoring_player_class, board_type, red_winning_moves, make_board_from_moves):
		board = make_board_from_moves(red_winning_moves[:10], board_type=board_type)
		before = board.serialize()

		index_scoring_player_class(PlayerColor.BLUE).choose_move(board)

		assert board.serialize() == before

	def test_chooses_an_available_move_in_the_middle_of_a_game(self, index_scoring_player_class, board_type, playout, make_board_from_moves):
		board = make_board_from_moves(
			playout.moves[:-1],
			board_type=board_type,
			size=playout.size,
		)
		player = index_scoring_player_class(PlayerColor.RED)

		assert player.choose_move(board) in board.available

	def test_choose_move_consults_the_scores_every_time(self, index_scoring_player_class, board):
		player = index_scoring_player_class(PlayerColor.RED)

		player.choose_move(board)
		board.set(*max(board.available), PlayerColor.RED.cell)
		move = player.choose_move(board)

		assert len(player.scored_colors) == 2
		assert move == max(board.available)

	def test_fails_when_no_moves_are_available(self, index_scoring_player_class, board_type, full_winning_game):
		board = full_winning_game(board_type)

		with pytest.raises(ValueError, match="No available moves"):
			index_scoring_player_class(PlayerColor.RED).choose_move(board)

	def test_fails_when_no_score_is_finite(self, index_scoring_player_class, board):
		class NanPlayer(index_scoring_player_class):
			def score_moves(self, board, color):
				return {move: math.nan for move in board.available}

		with pytest.raises(ValueError, match="No available moves"):
			NanPlayer(PlayerColor.RED).choose_move(board)

	def test_moves_with_non_finite_scores_are_never_chosen(self, index_scoring_player_class, board):
		best = max(board.available)

		class MaskedPlayer(index_scoring_player_class):
			def score_moves(self, board, color):
				scores = super().score_moves(board, color)
				scores[best] = math.nan
				return scores

		move = MaskedPlayer(PlayerColor.RED).choose_move(board)

		assert move != best
		assert move in board.available


class TestChooseMoveWithDeterminism:
	def test_non_deterministic_scoring_is_never_reported_as_deterministic(self, index_scoring_player_class, board):
		player = index_scoring_player_class(PlayerColor.RED, selector=MaxSelector())

		move, is_deterministic = player.choose_move_with_determinism(board)

		assert move == max(board.available)
		assert is_deterministic is False

	def test_deterministic_scoring_with_a_best_selector(self, index_scoring_player_class, board):
		class DeterministicPlayer(DeterministicScoringMixin, index_scoring_player_class):
			pass

		move, is_deterministic = DeterministicPlayer(
			PlayerColor.RED,
			selector=MaxSelector(),
		).choose_move_with_determinism(board)

		assert move == max(board.available)
		assert is_deterministic is True

	def test_deterministic_scoring_with_a_random_selector_and_a_unique_best_move(self, index_scoring_player_class, board):
		class DeterministicPlayer(DeterministicScoringMixin, index_scoring_player_class):
			pass

		move, is_deterministic = DeterministicPlayer(
			PlayerColor.RED,
			selector=RandomMaxSelector(seed=0),
		).choose_move_with_determinism(board)

		assert move == max(board.available)
		assert is_deterministic is True

	def test_deterministic_scoring_with_a_random_selector_and_tied_scores(self, tied_scoring_player_class, board):
		class DeterministicPlayer(DeterministicScoringMixin, tied_scoring_player_class):
			pass

		move, is_deterministic = DeterministicPlayer(
			PlayerColor.RED,
			selector=RandomMaxSelector(seed=0),
		).choose_move_with_determinism(board)

		assert move in board.available
		assert is_deterministic is False

	def test_deterministic_scoring_with_a_best_selector_and_tied_scores(self, tied_scoring_player_class, board):
		class DeterministicPlayer(DeterministicScoringMixin, tied_scoring_player_class):
			pass

		move, is_deterministic = DeterministicPlayer(
			PlayerColor.RED,
			selector=MaxSelector(),
		).choose_move_with_determinism(board)

		assert move in board.available
		assert is_deterministic is True

	def test_non_deterministic_scoring_still_reports_the_selected_move(self, tied_scoring_player_class, board):
		player = tied_scoring_player_class(
			PlayerColor.RED,
			selector=RandomMaxSelector(seed=0),
		)

		move, is_deterministic = player.choose_move_with_determinism(board)

		assert move in board.available
		assert is_deterministic is False

	def test_fails_when_no_moves_are_available(self, index_scoring_player_class, board_type, full_winning_game):
		class DeterministicPlayer(DeterministicScoringMixin, index_scoring_player_class):
			pass

		board = full_winning_game(board_type)

		with pytest.raises(ValueError, match="No available moves"):
			DeterministicPlayer(PlayerColor.RED).choose_move_with_determinism(board)


class TestScoringPlayerGames:
	def test_make_move_claims_the_chosen_cell(self, index_scoring_player_class, board, player_color):
		player = index_scoring_player_class(player_color)
		expected = max(board.available)

		move = player.make_move(board)

		assert move == expected
		assert board.get(*move) is player_color.cell

	@pytest.mark.parametrize("size", [3, 5, 7, 11])
	def test_two_scoring_players_play_a_complete_legal_game(self, index_scoring_player_class, board_type, size):
		board = board_type(size=size)
		players = {
			PlayerColor.RED: index_scoring_player_class(PlayerColor.RED),
			PlayerColor.BLUE: index_scoring_player_class(PlayerColor.BLUE),
		}
		color = PlayerColor.RED
		moves = 0

		while board.winner is None:
			available_before = board.available

			move = players[color].make_move(board)

			assert move in available_before
			assert board.available == available_before - {move}

			moves += 1
			color = color.opponent

		assert board.winner is color.opponent
		assert players[board.winner].is_winner(board)
		assert not players[board.winner.opponent].is_winner(board)
		assert moves <= (size - 2) ** 2

	def test_a_game_between_deterministic_players_is_repeatable(self, index_scoring_player_class, board_type):
		def play():
			board = board_type(size=7)
			players = [
				index_scoring_player_class(PlayerColor.RED),
				index_scoring_player_class(PlayerColor.BLUE),
			]
			history = []

			while board.winner is None:
				history.append(players[len(history) % 2].make_move(board))

			return history

		assert play() == play()
