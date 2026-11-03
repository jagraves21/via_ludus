import pytest

from via_ludus.board import (
	Cell,
	PlayerColor,
	SearchBoard,
	UnionFindBoard,
)


@pytest.fixture
def board():
	return UnionFindBoard(size=11)


def _assert_structures_match_a_fresh_build(board):
	"""The incrementally maintained structures equal a from-scratch build."""
	rebuilt = UnionFindBoard.deserialize(board.serialize())

	assert board._red_union_find.equivalent(rebuilt._red_union_find)
	assert board._blue_union_find.equivalent(rebuilt._blue_union_find)


class TestInitialStructure:
	def test_sources_and_targets_are_distinct_markers(self, board):
		markers = {
			board._red_source,
			board._red_target,
			board._blue_source,
			board._blue_target,
		}

		assert len(markers) == 4
		assert markers.isdisjoint(board.positions_of(Cell.WHITE))
		assert markers.isdisjoint(board.positions_of(Cell.RED))

	def test_nobody_is_connected_initially(self, board):
		assert not board._red_union_find.connected(board._red_source, board._red_target)
		assert not board._blue_union_find.connected(board._blue_source, board._blue_target)

	@pytest.mark.parametrize("size", [3, 5, 7, 11])
	def test_edge_cells_are_connected_to_their_source_and_target(self, size):
		board = UnionFindBoard(size=size)
		last = size - 1

		for index in range(1, last):
			assert board._red_union_find.connected(board._red_source, (0, index))
			assert board._red_union_find.connected(board._red_target, (last, index))
			assert board._blue_union_find.connected(board._blue_source, (index, 0))
			assert board._blue_union_find.connected(board._blue_target, (index, last))

	def test_opposite_edges_are_not_connected_initially(self, board):
		assert not board._red_union_find.connected((0, 1), (10, 1))
		assert not board._blue_union_find.connected((1, 0), (1, 10))

	def test_only_red_cells_are_tracked_for_red_and_blue_for_blue(self, board):
		red_elements = set(board._red_union_find._parent)
		blue_elements = set(board._blue_union_find._parent)

		assert red_elements == board.red_cells | {board._red_source, board._red_target}
		assert blue_elements == board.blue_cells | {board._blue_source, board._blue_target}

	def test_interior_prefilled_cells_start_isolated(self, board):
		# e.g. (2, 1) is a prefilled Red cell with white / Blue neighbours only.
		interior_red = {
			(row, col)
			for row, col in board.red_cells
			if 0 < row < 10
		}

		assert interior_red
		for position in interior_red:
			assert not board._red_union_find.connected(position, board._red_source)
			assert not board._red_union_find.connected(position, board._red_target)


class TestIncrementalUpdates:
	def test_set_adds_the_cell_to_the_matching_structure_only(self, board):
		board.set(1, 1, Cell.RED)
		board.set(3, 3, Cell.BLUE)

		assert (1, 1) in board._red_union_find
		assert (1, 1) not in board._blue_union_find
		assert (3, 3) in board._blue_union_find
		assert (3, 3) not in board._red_union_find

	def test_set_connects_the_new_cell_to_adjacent_cells_of_its_color(self, board):
		board.set(1, 1, Cell.RED)

		assert board._red_union_find.connected((1, 1), (0, 1))
		assert board._red_union_find.connected((1, 1), (2, 1))
		assert board._red_union_find.connected((1, 1), board._red_source)

	def test_set_does_not_track_neighbours_of_the_other_color(self, board):
		board.set(1, 1, Cell.RED)

		# (1, 2) is a prefilled Blue cell next to the new Red cell.
		assert (1, 2) not in board._red_union_find

	def test_set_joins_previously_separate_groups(self, board):
		board.set(1, 1, Cell.RED)
		board.set(3, 3, Cell.RED)

		assert not board._red_union_find.connected((1, 1), (3, 3))

		board.set(2, 2, Cell.RED)

		# (2, 2) bridges the prefilled cells (2, 1) and (2, 3), which touch
		# (1, 1) and (3, 3) respectively.
		assert board._red_union_find.connected((1, 1), (3, 3))

	def test_failed_set_does_not_modify_the_structures(self, board):
		before_red = board._red_union_find.copy()
		before_blue = board._blue_union_find.copy()

		with pytest.raises(ValueError):
			board.set(0, 1, Cell.RED)

		assert board._red_union_find.equivalent(before_red)
		assert board._blue_union_find.equivalent(before_blue)

	def test_winner_appears_exactly_when_source_and_target_connect(self, red_winning_moves):
		board = UnionFindBoard(size=11)

		for index, ((row, col), player) in enumerate(red_winning_moves):
			board.set(row, col, player.cell)

			connected = board._red_union_find.connected(
				board._red_source,
				board._red_target,
			)

			assert connected == (index == len(red_winning_moves) - 1)

	def test_blue_winner_appears_exactly_when_source_and_target_connect(self, blue_winning_moves):
		board = UnionFindBoard(size=11)

		for index, ((row, col), player) in enumerate(blue_winning_moves):
			board.set(row, col, player.cell)

			connected = board._blue_union_find.connected(
				board._blue_source,
				board._blue_target,
			)

			assert connected == (index == len(blue_winning_moves) - 1)

	@pytest.mark.parametrize(
		"moves_fixture",
		["red_winning_moves", "blue_winning_moves", "full_board_moves"],
	)
	def test_incremental_structures_match_a_fresh_build_after_every_move(self, moves_fixture, request):
		moves = request.getfixturevalue(moves_fixture)
		board = UnionFindBoard(size=11)

		for (row, col), player in moves:
			board.set(row, col, player.cell)
			_assert_structures_match_a_fresh_build(board)


class TestReset:
	def test_reset_rebuilds_the_structure_of_the_reset_color(self, board):
		board.set(1, 1, Cell.RED)
		board.reset(1, 1)

		assert (1, 1) not in board._red_union_find
		assert not board._red_union_find.connected((0, 1), (2, 1))
		_assert_structures_match_a_fresh_build(board)

	def test_reset_of_one_color_leaves_the_other_color_intact(self, board):
		board.set(3, 3, Cell.BLUE)
		board.set(1, 1, Cell.RED)

		board.reset(1, 1)

		assert (3, 3) in board._blue_union_find
		_assert_structures_match_a_fresh_build(board)

	def test_reset_of_the_winning_move_clears_the_connection(self, red_winning_game, red_winning_moves):
		board = red_winning_game(UnionFindBoard)
		(row, col), _ = red_winning_moves[-1]

		board.reset(row, col)

		assert not board._red_union_find.connected(board._red_source, board._red_target)
		assert board.winner is None

	def test_failed_reset_keeps_the_structures(self, board):
		board.set(1, 1, Cell.RED)

		with pytest.raises(ValueError):
			board.reset(3, 3)

		assert (1, 1) in board._red_union_find
		_assert_structures_match_a_fresh_build(board)

	@pytest.mark.parametrize("position", [(0, 5), (5, 0), (2, 1), (1, 2)])
	def test_rejected_reset_of_a_starting_cell_keeps_the_structures(self, board, position):
		board.set(1, 1, Cell.RED)
		board.set(3, 3, Cell.BLUE)

		with pytest.raises(ValueError, match="starting position"):
			board.reset(*position)

		_assert_structures_match_a_fresh_build(board)

	def test_rejected_reset_keeps_the_winner(self, red_winning_game):
		board = red_winning_game(UnionFindBoard)

		with pytest.raises(ValueError, match="starting position"):
			board.reset(0, 5)

		assert board.winner is PlayerColor.RED
		_assert_structures_match_a_fresh_build(board)


class TestConstructionFromOtherBoards:
	def test_deserialize_builds_the_structures(self, terminal_position):
		board = UnionFindBoard.deserialize(terminal_position.serialization)

		assert board.winner is terminal_position.winner
		_assert_structures_match_a_fresh_build(board)

	def test_deserialized_board_accepts_further_moves(self):
		board = UnionFindBoard.deserialize("3,3,XRXBWBXRX")

		board.set(1, 1, Cell.BLUE)

		assert board.winner is PlayerColor.BLUE

	def test_from_board_builds_the_structures(self, red_winning_game):
		source = red_winning_game(SearchBoard)
		board = UnionFindBoard.from_board(source)

		assert board.winner is PlayerColor.RED
		_assert_structures_match_a_fresh_build(board)

	def test_from_board_structures_are_independent_of_the_source(self, red_winning_game, red_winning_moves):
		source = red_winning_game(UnionFindBoard)
		board = UnionFindBoard.from_board(source)
		(row, col), _ = red_winning_moves[-1]

		board.reset(row, col)

		assert source.winner is PlayerColor.RED
		assert board.winner is None


class TestCopy:
	def test_copy_duplicates_the_structures(self, board):
		board.set(1, 1, Cell.RED)
		clone = board.copy()

		assert clone._red_union_find is not board._red_union_find
		assert clone._blue_union_find is not board._blue_union_find
		assert clone._red_union_find.equivalent(board._red_union_find)
		assert clone._blue_union_find.equivalent(board._blue_union_find)

	def test_moves_on_a_copy_do_not_affect_the_original(self, red_winning_moves):
		board = UnionFindBoard(size=11)

		for (row, col), player in red_winning_moves[:-1]:
			board.set(row, col, player.cell)

		clone = board.copy()
		(row, col), player = red_winning_moves[-1]
		clone.set(row, col, player.cell)

		assert clone.winner is PlayerColor.RED
		assert board.winner is None
		assert (row, col) not in board._red_union_find
		_assert_structures_match_a_fresh_build(board)
		_assert_structures_match_a_fresh_build(clone)

	def test_moves_on_the_original_do_not_affect_a_copy(self, board):
		clone = board.copy()

		board.set(1, 1, Cell.RED)

		assert (1, 1) not in clone._red_union_find
		assert clone.get(1, 1) is Cell.WHITE

	def test_copy_of_a_deserialized_board_keeps_working(self, full_board):
		board = full_board(UnionFindBoard)
		clone = board.copy()

		assert clone.winner is PlayerColor.RED
		_assert_structures_match_a_fresh_build(clone)
