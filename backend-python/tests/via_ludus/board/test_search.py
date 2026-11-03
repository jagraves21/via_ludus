import pytest

from via_ludus.board import (
	Cell,
	PlayerColor,
	SearchBoard,
)


@pytest.fixture
def board():
	return SearchBoard(size=11)


class TestWinnerDetection:
	def test_winner_is_recomputed_from_the_cells(self, board, red_winning_moves):
		for (row, col), player in red_winning_moves:
			board.set(row, col, player.cell)

		assert board.winner is PlayerColor.RED

		# SearchBoard keeps no cached state: changing a cell changes the result.
		(row, col), _ = red_winning_moves[-1]
		board.reset(row, col)

		assert board.winner is None

	def test_straight_red_path_on_the_smallest_board(self):
		board = SearchBoard(size=3)

		assert board.winner is None

		board.set(1, 1, Cell.RED)

		assert board.winner is PlayerColor.RED

	def test_blue_claiming_the_only_white_cell_wins_on_the_smallest_board(self):
		board = SearchBoard(size=3)

		board.set(1, 1, Cell.BLUE)

		assert board.winner is PlayerColor.BLUE

	def test_red_group_touching_only_one_edge_does_not_win(self):
		board = SearchBoard(size=5)

		# (1, 1) joins the top edge to the prefilled Red cell at (2, 1),
		# but nothing reaches the bottom edge yet.
		board.set(1, 1, Cell.RED)

		assert board.winner is None

	def test_red_needs_every_missing_link_on_a_straight_column(self):
		board = SearchBoard(size=7)

		board.set(1, 1, Cell.RED)
		board.set(3, 1, Cell.RED)

		assert board.winner is None

		board.set(5, 1, Cell.RED)

		assert board.winner is PlayerColor.RED

	def test_blue_stone_on_a_red_column_blocks_it(self):
		board = SearchBoard(size=7)

		board.set(1, 1, Cell.RED)
		board.set(3, 1, Cell.BLUE)
		board.set(5, 1, Cell.RED)

		assert board.winner is None


class TestHasPath:
	def test_has_path_requires_a_player_color(self, board):
		with pytest.raises(TypeError):
			board._has_path("red")

		with pytest.raises(TypeError):
			board._has_path(Cell.RED)

	def test_has_path_checks_each_player_independently(self, board, red_winning_game):
		won = red_winning_game(SearchBoard)

		assert board._has_path(PlayerColor.RED) is False
		assert board._has_path(PlayerColor.BLUE) is False
		assert won._has_path(PlayerColor.RED) is True
		assert won._has_path(PlayerColor.BLUE) is False
