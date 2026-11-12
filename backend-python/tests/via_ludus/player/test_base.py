import pytest

from via_ludus.board import Cell, PlayerColor
from via_ludus.player import DeterministicMoveSelectionMixin, Player


class TestPlayerConstruction:
	def test_player_is_abstract(self):
		with pytest.raises(TypeError):
			Player(PlayerColor.RED)

	def test_subclass_must_implement_choose_move(self):
		class Incomplete(Player):
			pass

		with pytest.raises(TypeError):
			Incomplete(PlayerColor.RED)

	def test_accepts_a_player_color(self, first_move_player_class, player_color):
		player = first_move_player_class(player_color)

		assert player.color is player_color

	@pytest.mark.parametrize("color", ["red", Cell.RED, None, 1])
	def test_rejects_invalid_colors(self, first_move_player_class, color):
		with pytest.raises(TypeError, match="Invalid player color"):
			first_move_player_class(color)


class TestPlayerProperties:
	def test_opponent_color(self, first_move_player_class, player_color):
		player = first_move_player_class(player_color)

		assert player.opponent_color is player_color.opponent

	def test_cell(self, first_move_player_class, player_color):
		player = first_move_player_class(player_color)

		assert player.cell is player_color.cell

	def test_is_not_deterministic_by_default(self, first_move_player_class, player_color):
		assert first_move_player_class(player_color).is_deterministic is False

	def test_deterministic_mixin_makes_the_player_deterministic(self, first_move_player_class, player_color):
		class DeterministicPlayer(DeterministicMoveSelectionMixin, first_move_player_class):
			pass

		assert DeterministicPlayer(player_color).is_deterministic is True

	def test_repr(self, first_move_player_class):
		player = first_move_player_class(PlayerColor.BLUE)

		assert repr(player) == "FirstMovePlayer(color=PlayerColor.BLUE)"

	def test_str(self, first_move_player_class):
		assert str(first_move_player_class(PlayerColor.RED)) == "Red Player"
		assert str(first_move_player_class(PlayerColor.BLUE)) == "Blue Player"


class TestMakeMove:
	def test_claims_the_chosen_cell_for_the_player(self, first_move_player_class, board, player_color):
		player = first_move_player_class(player_color)
		expected = min(board.available)

		move = player.make_move(board)

		assert move == expected
		assert board.get(*move) is player_color.cell

	def test_returns_the_chosen_move(self, first_move_player_class, board):
		player = first_move_player_class(PlayerColor.RED)

		expected = player.choose_move(board)

		assert player.make_move(board) == expected

	def test_removes_the_move_from_the_available_cells(self, first_move_player_class, board):
		player = first_move_player_class(PlayerColor.RED)
		available = board.available

		move = player.make_move(board)

		assert board.available == available - {move}

	def test_successive_moves_claim_different_cells(self, first_move_player_class, board):
		red = first_move_player_class(PlayerColor.RED)
		blue = first_move_player_class(PlayerColor.BLUE)

		first = red.make_move(board)
		second = blue.make_move(board)

		assert first != second
		assert board.get(*first) is Cell.RED
		assert board.get(*second) is Cell.BLUE

	def test_illegal_move_is_rejected_and_the_board_is_unchanged(self, first_move_player_class, board):
		class EdgePlayer(first_move_player_class):
			def choose_move(self, board):
				return (0, 1)

		before = board.serialize()

		with pytest.raises(ValueError):
			EdgePlayer(PlayerColor.RED).make_move(board)

		assert board.serialize() == before

	def test_out_of_range_move_is_rejected(self, first_move_player_class, board):
		class OffBoardPlayer(first_move_player_class):
			def choose_move(self, board):
				return (board.rows, 0)

		with pytest.raises(IndexError):
			OffBoardPlayer(PlayerColor.RED).make_move(board)


class TestIsWinner:
	def test_nobody_wins_on_the_initial_board(self, first_move_player_class, board, player_color):
		assert first_move_player_class(player_color).is_winner(board) is False

	def test_red_winning_position(self, first_move_player_class, board_type, red_winning_game):
		board = red_winning_game(board_type)

		assert first_move_player_class(PlayerColor.RED).is_winner(board) is True
		assert first_move_player_class(PlayerColor.BLUE).is_winner(board) is False

	def test_blue_winning_position(self, first_move_player_class, board_type, blue_winning_game):
		board = blue_winning_game(board_type)

		assert first_move_player_class(PlayerColor.BLUE).is_winner(board) is True
		assert first_move_player_class(PlayerColor.RED).is_winner(board) is False
