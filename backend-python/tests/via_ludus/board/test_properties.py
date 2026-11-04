"""Property tests: invariants that must hold for every legal game.

The games come from reproducible random playouts (see ``playout`` in
``conftest.py``): Red moves first, players alternate, only white cells are
claimed and play stops at the first win. Every property is checked for both
board implementations.
"""

import pytest

from via_ludus.board import Cell, PlayerColor


def _replay(board_type, playout):
	"""Yield (board, move_index, position, player) after each move."""
	board = board_type(size=playout.size)

	for index, ((row, col), player) in enumerate(playout.moves):
		board.set(row, col, player.cell)

		yield board, index, (row, col), player


class TestRulesOfPlay:
	def test_playouts_are_legal_games(self, playout):
		players = [player for _, player in playout.moves]
		positions = [position for position, _ in playout.moves]

		assert players[0] is PlayerColor.RED
		assert all(
			current is previous.opponent
			for previous, current in zip(players, players[1:])
		)
		assert len(set(positions)) == len(positions)

	def test_each_move_claims_exactly_one_white_cell(self, board_type, playout):
		board = board_type(size=playout.size)

		for (row, col), player in playout.moves:
			before = board.serialize()
			white_before = len(board.available)

			board.set(row, col, player.cell)

			assert board.get(row, col) is player.cell
			assert len(board.available) == white_before - 1
			changed = [
				index
				for index, (old, new) in enumerate(zip(before.split(",", 2)[2], board.serialize().split(",", 2)[2]))
				if old != new
			]
			assert changed == [row * board.cols + col]

	def test_walls_edges_and_prefilled_cells_never_change(self, board_type, playout, reference):
		initial = reference.initial_grid(playout.size)

		for board, _, _, _ in _replay(board_type, playout):
			grid = reference.grid_of(board)

			for row in range(playout.size):
				for col in range(playout.size):
					if initial[row][col] != "W":
						assert grid[row][col] == initial[row][col]

	def test_players_hold_balanced_numbers_of_claimed_cells(self, board_type, playout):
		initial = board_type(size=playout.size)

		for board, index, _, _ in _replay(board_type, playout):
			red_claimed = len(board.red_cells) - len(initial.red_cells)
			blue_claimed = len(board.blue_cells) - len(initial.blue_cells)

			assert red_claimed - blue_claimed in (0, 1)
			assert red_claimed + blue_claimed == index + 1

	def test_corners_remain_walls(self, board_type, playout):
		last = playout.size - 1

		for board, _, _, _ in _replay(board_type, playout):
			assert board.positions_of(Cell.WALL) == {
				(0, 0),
				(0, last),
				(last, 0),
				(last, last),
			}

	def test_exactly_the_claimed_cells_can_be_reset(self, board_type, playout):
		board = board_type(size=playout.size)
		claimed = set()

		for (row, col), player in playout.moves:
			board.set(row, col, player.cell)
			claimed.add((row, col))

		for row in range(board.rows):
			for col in range(board.cols):
				clone = board.copy()

				if board.get(row, col) not in (Cell.RED, Cell.BLUE):
					continue

				if (row, col) in claimed:
					clone.reset(row, col)

					assert clone.get(row, col) is Cell.WHITE
				else:
					with pytest.raises(ValueError, match="starting position"):
						clone.reset(row, col)


class TestWinning:
	def test_the_game_is_won_exactly_on_the_final_move(self, board_type, playout):
		last_index = len(playout.moves) - 1

		for board, index, _, player in _replay(board_type, playout):
			if index < last_index:
				assert board.winner is None
				assert not board.is_game_over
			else:
				assert board.winner is player
				assert board.is_game_over

	def test_only_the_player_who_just_moved_can_win(self, board_type, playout):
		for board, _, _, player in _replay(board_type, playout):
			assert board.winner in (None, player)

	def test_both_players_never_win_at_the_same_time(self, board_type, playout, reference):
		for board, _, _, _ in _replay(board_type, playout):
			assert len(reference.board_winners(board)) <= 1

	def test_winner_matches_the_reference_implementation(self, board_type, playout, reference):
		for board, _, _, _ in _replay(board_type, playout):
			expected = reference.board_winners(board)

			assert expected == (set() if board.winner is None else {board.winner})

	def test_there_are_no_draws(self, board_type, playout, reference):
		board = None

		for board, _, _, _ in _replay(board_type, playout):
			pass

		# The playout only ends when somebody has won, even if every white cell
		# has been claimed.
		assert board.winner is not None
		assert len(reference.board_winners(board)) == 1

	def test_a_full_board_always_has_a_red_winner(self, board_type, playout):
		board = None

		for board, _, _, _ in _replay(board_type, playout):
			pass

		if not board.available:
			# Odd-sized boards have an odd number of white cells, so Red makes
			# the last possible move.
			assert board.winner is PlayerColor.RED

	def test_some_playouts_fill_the_whole_board(self, make_random_playout):
		filled = [
			seed
			for seed in range(30)
			if len(make_random_playout(5, seed).moves) == 5
		]

		assert filled


class TestSerializationAndCopying:
	def test_serialization_round_trips_at_every_step(self, board_type, playout):
		for board, _, _, _ in _replay(board_type, playout):
			restored = board_type.deserialize(board.serialize())

			assert restored.serialize() == board.serialize()
			assert restored.winner is board.winner
			assert restored.available == board.available

	def test_copies_are_equal_and_independent_at_every_step(self, board_type, playout):
		for board, _, _, _ in _replay(board_type, playout):
			clone = board.copy()

			assert clone.serialize() == board.serialize()
			assert clone.winner is board.winner

			if board.available:
				row, col = sorted(board.available)[0]
				clone.set(row, col, Cell.BLUE)

				assert board.get(row, col) is Cell.WHITE


_MIRRORS = {
	"horizontal": lambda size, row, col: (row, size - 1 - col),
	"vertical": lambda size, row, col: (size - 1 - row, col),
	"rotation": lambda size, row, col: (size - 1 - row, size - 1 - col),
}


@pytest.fixture(params=sorted(_MIRRORS))
def mirror(request):
	return _MIRRORS[request.param]


class TestSymmetry:
	"""On odd-sized boards the starting position is unchanged by flipping the
	board left-to-right or top-to-bottom, and both flips keep Red's and Blue's
	goals. Mirroring every move of a legal game therefore gives another legal
	game with exactly the same winner at every step."""

	def test_starting_position_is_unchanged_by_mirroring(self, board_type, board_size, mirror):
		board = board_type(size=board_size)

		for row in range(board_size):
			for col in range(board_size):
				mirrored_row, mirrored_col = mirror(board_size, row, col)

				assert board.get(row, col) is board.get(mirrored_row, mirrored_col)

	def test_mirrored_games_have_the_same_winner_at_every_step(self, board_type, playout, mirror):
		original = board_type(size=playout.size)
		mirrored = board_type(size=playout.size)

		for (row, col), player in playout.moves:
			mirrored_row, mirrored_col = mirror(playout.size, row, col)

			original.set(row, col, player.cell)
			mirrored.set(mirrored_row, mirrored_col, player.cell)

			assert original.winner is mirrored.winner
			assert len(original.available) == len(mirrored.available)
