import warnings

import pytest

from via_ludus.board import (
	Board,
	Cell,
	PlayerColor,
	SearchBoard,
	UnionFindBoard,
	is_board,
	is_board_serialization,
	resolve_board,
	validate_board,
	validate_board_serialization,
)


class TestBoardConstruction:
	def test_board_is_abstract(self):
		with pytest.raises(TypeError):
			Board()

	def test_default_size_is_11(self, board_type):
		board = board_type()

		assert board.shape == (11, 11)

	def test_shape_rows_and_cols(self, board_type, board_size):
		board = board_type(size=board_size)

		assert board.shape == (board_size, board_size)
		assert board.rows == board_size
		assert board.cols == board_size

	@pytest.mark.parametrize("size", [-1, 0, 1, 2])
	def test_size_below_three_is_rejected(self, board_type, size):
		with pytest.raises(ValueError, match="at least 3"):
			board_type(size=size)

	def test_smallest_board_is_allowed(self, board_type):
		board = board_type(size=3)

		assert board.serialize() == "3,3,XRXBWBXRX"

	@pytest.mark.parametrize("size", [4, 6, 10])
	def test_even_size_warns(self, board_type, size):
		with pytest.warns(UserWarning, match="Even-sized"):
			board = board_type(size=size)

		assert board.shape == (size, size)

	@pytest.mark.parametrize("size", [3, 5, 11])
	def test_odd_size_does_not_warn(self, board_type, size):
		with warnings.catch_warnings():
			warnings.simplefilter("error")
			board_type(size=size)


class TestStartingPosition:
	def test_initial_serialization(self, board_type, initial_board_serialization):
		assert board_type(size=11).serialize() == initial_board_serialization

	def test_initial_board_matches_reference_layout(self, board_type, board_size, reference):
		board = board_type(size=board_size)

		assert reference.grid_of(board) == reference.initial_grid(board_size)

	def test_initial_board_matches_reference_layout_for_even_sizes(self, board_type, reference):
		for size in (4, 6):
			with pytest.warns(UserWarning):
				board = board_type(size=size)

			assert reference.grid_of(board) == reference.initial_grid(size)

	def test_corners_are_walls(self, board_type, board_size):
		board = board_type(size=board_size)
		last = board_size - 1

		for row, col in ((0, 0), (0, last), (last, 0), (last, last)):
			assert board.get(row, col) is Cell.WALL

	def test_edges_belong_to_the_expected_player(self, board_type, board_size):
		board = board_type(size=board_size)
		last = board_size - 1

		for index in range(1, last):
			assert board.get(0, index) is Cell.RED
			assert board.get(last, index) is Cell.RED
			assert board.get(index, 0) is Cell.BLUE
			assert board.get(index, last) is Cell.BLUE

	def test_there_are_exactly_four_walls(self, board_type, board_size):
		board = board_type(size=board_size)

		assert len(board.positions_of(Cell.WALL)) == 4

	def test_initial_white_cells(self, board_type, board_size):
		board = board_type(size=board_size)
		interior = board_size - 2

		assert len(board.empty_cells) == (interior * interior + 1) // 2
		assert all(
			0 < row < board_size - 1
			and 0 < col < board_size - 1
			and (row + col) % 2 == 0
			for row, col in board.empty_cells
		)

	def test_initial_board_has_no_winner(self, board):
		assert board.winner is None
		assert not board.is_game_over


class TestBoardRepresentation:
	def test_initial_text(self, board, initial_board_text):
		assert str(board) == initial_board_text

	def test_repr(self, board_type):
		assert repr(board_type(size=5)) == f"{board_type.__name__}(shape=(5, 5))"


class TestCellCollections:
	def test_available_is_the_set_of_empty_cells(self, board):
		assert board.available == board.empty_cells
		assert board.available == board.positions_of(Cell.WHITE)

	def test_cell_collections_partition_the_board(self, board_type, board_size):
		board = board_type(size=board_size)

		groups = (
			board.red_cells,
			board.blue_cells,
			board.empty_cells,
			board.positions_of(Cell.WALL),
		)

		assert sum(len(group) for group in groups) == board_size * board_size
		assert set().union(*groups) == {
			(row, col)
			for row in range(board_size)
			for col in range(board_size)
		}

	def test_positions_of_returns_plain_int_tuples(self, board):
		positions = board.positions_of(Cell.WALL)

		assert positions == {(0, 0), (0, 10), (10, 0), (10, 10)}
		assert all(
			type(row) is int and type(col) is int
			for row, col in positions
		)

	def test_positions_of_rejects_non_cells(self, board):
		with pytest.raises(TypeError):
			board.positions_of("white")


class TestGet:
	def test_get_returns_cells(self, board):
		assert board.get(0, 0) is Cell.WALL
		assert board.get(0, 1) is Cell.RED
		assert board.get(1, 0) is Cell.BLUE
		assert board.get(1, 1) is Cell.WHITE

	@pytest.mark.parametrize("row, col", [(-1, 0), (0, -1), (11, 0), (0, 11), (99, 99)])
	def test_get_out_of_range(self, board, row, col):
		with pytest.raises(IndexError):
			board.get(row, col)

	@pytest.mark.parametrize(
		"row, col",
		[(1.0, 1), (1, 1.0), ("1", 1), (1, None), (True, 1), (1, False)],
	)
	def test_get_rejects_non_integer_positions(self, board, row, col):
		with pytest.raises(TypeError):
			board.get(row, col)

	def test_get_accepts_numpy_integers(self, board):
		import numpy as np

		assert board.get(np.int64(1), np.int32(1)) is Cell.WHITE


class TestSet:
	def test_set_claims_a_white_cell(self, board, player_cell):
		board.set(1, 1, player_cell)

		assert board.get(1, 1) is player_cell
		assert (1, 1) not in board.available

	def test_set_red_and_blue_cell_collections(self, board):
		red_before = board.red_cells
		blue_before = board.blue_cells

		board.set(1, 1, Cell.RED)
		board.set(3, 3, Cell.BLUE)

		assert board.red_cells == red_before | {(1, 1)}
		assert board.blue_cells == blue_before | {(3, 3)}

	@pytest.mark.parametrize(
		"position",
		[
			(0, 0),
			(0, 1),
			(1, 0),
			(1, 2),
			(2, 1),
		],
		ids=["corner-wall", "red-edge", "blue-edge", "prefilled-blue", "prefilled-red"],
	)
	def test_set_rejects_cells_that_are_not_white(self, board, position, player_cell):
		before = board.serialize()

		with pytest.raises(ValueError):
			board.set(*position, player_cell)

		assert board.serialize() == before

	def test_set_cannot_overwrite_a_claimed_cell(self, board):
		board.set(1, 1, Cell.RED)

		with pytest.raises(ValueError):
			board.set(1, 1, Cell.BLUE)

		assert board.get(1, 1) is Cell.RED

	@pytest.mark.parametrize("cell", [Cell.WHITE, Cell.WALL])
	def test_set_rejects_non_player_cells(self, board, cell):
		with pytest.raises(ValueError):
			board.set(1, 1, cell)

		assert board.get(1, 1) is Cell.WHITE

	@pytest.mark.parametrize("cell", ["red", PlayerColor.RED, None])
	def test_set_rejects_non_cell_values(self, board, cell):
		with pytest.raises(TypeError):
			board.set(1, 1, cell)

	def test_set_out_of_range(self, board):
		with pytest.raises(IndexError):
			board.set(11, 1, Cell.RED)

	def test_set_rejects_non_integer_position(self, board):
		with pytest.raises(TypeError):
			board.set(1.5, 1, Cell.RED)


class TestReset:
	def test_reset_restores_a_claimed_cell(self, board, player_cell):
		initial = board.serialize()

		board.set(1, 1, player_cell)
		board.reset(1, 1)

		assert board.get(1, 1) is Cell.WHITE
		assert board.serialize() == initial

	def test_reset_allows_the_cell_to_be_claimed_again(self, board):
		board.set(3, 3, Cell.RED)
		board.reset(3, 3)
		board.set(3, 3, Cell.BLUE)

		assert board.get(3, 3) is Cell.BLUE

	def test_reset_rejects_white_and_wall_cells(self, board):
		with pytest.raises(ValueError):
			board.reset(1, 1)

		with pytest.raises(ValueError):
			board.reset(0, 0)

	def test_reset_validates_position(self, board):
		with pytest.raises(IndexError):
			board.reset(-1, 0)

		with pytest.raises(TypeError):
			board.reset("1", 1)

	def test_reset_in_reverse_order_undoes_a_game(self, board_type, red_winning_moves, red_winning_game):
		board = red_winning_game(board_type)

		for (row, col), _ in reversed(red_winning_moves):
			board.reset(row, col)

		assert board.serialize() == board_type(size=11).serialize()
		assert board.winner is None

	@pytest.mark.parametrize(
		"position",
		[(0, 5), (10, 5), (5, 0), (5, 10), (2, 1), (1, 2)],
		ids=["top-edge", "bottom-edge", "left-edge", "right-edge", "prefilled-red", "prefilled-blue"],
	)
	def test_reset_rejects_cells_of_the_starting_position(self, board, position):
		before = board.serialize()

		with pytest.raises(ValueError, match="starting position"):
			board.reset(*position)

		assert board.serialize() == before

	def test_reset_rejects_every_prefilled_cell(self, board_type, board_size):
		board = board_type(size=board_size)
		before = board.serialize()
		prefilled = board.red_cells | board.blue_cells

		assert prefilled
		for row, col in prefilled:
			with pytest.raises(ValueError, match="starting position"):
				board.reset(row, col)

		assert board.serialize() == before

	def test_reset_accepts_every_cell_that_can_be_claimed(self, board_type, board_size, player_cell):
		board = board_type(size=board_size)
		initial = board.serialize()

		for row, col in sorted(board.available):
			board.set(row, col, player_cell)
			board.reset(row, col)

			assert board.get(row, col) is Cell.WHITE

		assert board.serialize() == initial

	@pytest.mark.parametrize("size", [4, 6])
	def test_reset_follows_the_same_rule_on_even_sized_boards(self, board_type, size, reference):
		with pytest.warns(UserWarning):
			board = board_type(size=size)

		initial = reference.initial_grid(size)

		for row in range(size):
			for col in range(size):
				if initial[row][col] == "W":
					board.set(row, col, Cell.RED)
					board.reset(row, col)
				elif initial[row][col] in "RB":
					with pytest.raises(ValueError, match="starting position"):
						board.reset(row, col)

	def test_reset_only_accepts_cells_claimed_in_a_known_position(self, board_type, terminal_position, reference):
		board = board_type.deserialize(terminal_position.serialization)
		initial = reference.initial_grid(terminal_position.size)

		for row in range(board.rows):
			for col in range(board.cols):
				if initial[row][col] == "W" and board.get(row, col) in (Cell.RED, Cell.BLUE):
					board.reset(row, col)

					assert board.get(row, col) is Cell.WHITE
				elif initial[row][col] in "RB":
					with pytest.raises(ValueError, match="starting position"):
						board.reset(row, col)

	def test_rejected_reset_does_not_affect_a_won_game(self, board_type, red_winning_game):
		board = red_winning_game(board_type)
		before = board.serialize()

		with pytest.raises(ValueError, match="starting position"):
			board.reset(0, 5)

		assert board.serialize() == before
		assert board.winner is PlayerColor.RED


class TestNeighbors:
	def test_neighbors_of_an_interior_cell(self, board):
		assert set(board.neighbors(5, 5)) == {(4, 5), (6, 5), (5, 4), (5, 6)}

	def test_neighbors_are_orthogonal_only(self, board):
		for row, col in set(board.neighbors(5, 5)):
			assert abs(row - 5) + abs(col - 5) == 1

	@pytest.mark.parametrize(
		"position, expected",
		[
			((0, 0), {(1, 0), (0, 1)}),
			((0, 10), {(1, 10), (0, 9)}),
			((10, 0), {(9, 0), (10, 1)}),
			((10, 10), {(9, 10), (10, 9)}),
			((0, 5), {(1, 5), (0, 4), (0, 6)}),
			((5, 0), {(4, 0), (6, 0), (5, 1)}),
		],
	)
	def test_neighbors_stay_on_the_board(self, board, position, expected):
		assert set(board.neighbors(*position)) == expected

	def test_neighbors_have_no_duplicates(self, board):
		neighbors = list(board.neighbors(5, 5))

		assert len(neighbors) == len(set(neighbors))


class TestSerialization:
	def test_serialize_format(self, board_type):
		assert board_type(size=3).serialize() == "3,3,XRXBWBXRX"

	def test_deserialize_returns_the_calling_class(self, board_type, initial_board_serialization):
		board = board_type.deserialize(initial_board_serialization)

		assert type(board) is board_type
		assert board.serialize() == initial_board_serialization

	def test_serialization_round_trip(self, terminal_position, board_type):
		board = board_type.deserialize(terminal_position.serialization)

		assert board.serialize() == terminal_position.serialization

	def test_deserialized_board_is_playable(self, board_type):
		board = board_type.deserialize("3,3,XRXBWBXRX")

		board.set(1, 1, Cell.RED)

		assert board.winner is PlayerColor.RED

	@pytest.mark.parametrize(
		"serialized",
		[
			"",
			"3",
			"3,3",
			"a,b,XRXBWBXRX",
			"3,x,XRXBWBXRX",
			"0,3,",
			"3,0,",
			"-1,3,XRX",
			"3,3,XRXBWBXR",
			"3,3,XRXBWBXRXX",
			"3,3,XRXBWBXR?",
			"3,3,xrxbwbxrx",
		],
	)
	def test_deserialize_rejects_invalid_input(self, board_type, serialized):
		with pytest.raises(ValueError):
			board_type.deserialize(serialized)


class TestCopyAndFromBoard:
	def test_copy_has_the_same_class_and_contents(self, board_type, red_winning_game):
		board = red_winning_game(board_type)
		clone = board.copy()

		assert type(clone) is board_type
		assert clone is not board
		assert clone.serialize() == board.serialize()
		assert clone.winner is board.winner

	def test_copy_is_independent_of_the_original(self, board):
		clone = board.copy()
		clone.set(1, 1, Cell.RED)

		assert board.get(1, 1) is Cell.WHITE

		board.set(3, 3, Cell.BLUE)

		assert clone.get(3, 3) is Cell.WHITE

	def test_from_board_rejects_non_boards(self, board_type):
		with pytest.raises(TypeError, match="Expected a Board"):
			board_type.from_board("not a board")

	@pytest.mark.parametrize("source_type", [SearchBoard, UnionFindBoard], ids=lambda t: t.__name__)
	def test_from_board_converts_between_implementations(self, board_type, source_type, red_winning_game):
		source = red_winning_game(source_type)
		converted = board_type.from_board(source)

		assert type(converted) is board_type
		assert converted.serialize() == source.serialize()
		assert converted.winner is PlayerColor.RED

	def test_from_board_is_independent_of_the_source(self, board_type, board):
		converted = board_type.from_board(board)
		converted.set(1, 1, Cell.RED)

		assert board.get(1, 1) is Cell.WHITE


class TestKnownPositions:
	def test_winner_of_known_position_from_serialization(self, board_type, terminal_position):
		board = board_type.deserialize(terminal_position.serialization)

		assert board.winner is terminal_position.winner
		assert board.is_game_over

	def test_winner_of_known_position_by_replaying_moves(self, board_type, terminal_position, make_board_from_moves):
		board = make_board_from_moves(
			terminal_position.moves,
			board_type=board_type,
			size=terminal_position.size,
		)

		assert board.serialize() == terminal_position.serialization
		assert board.winner is terminal_position.winner

	def test_winner_appears_only_on_the_final_move(self, board_type, terminal_position):
		board = board_type(size=terminal_position.size)

		for index, ((row, col), player) in enumerate(terminal_position.moves):
			assert board.winner is None, f"game already over before move {index}"
			board.set(row, col, player.cell)

		assert board.winner is terminal_position.winner

	def test_known_move_sequences_are_legal_games(self, terminal_position):
		players = [player for _, player in terminal_position.moves]
		positions = [position for position, _ in terminal_position.moves]

		assert players[0] is PlayerColor.RED
		assert all(
			current is previous.opponent
			for previous, current in zip(players, players[1:])
		)
		assert len(set(positions)) == len(positions)
		assert players[-1] is terminal_position.winner

	def test_full_board_has_no_white_cells_and_one_winner(self, board_type, full_winning_game, reference):
		board = full_winning_game(board_type)

		assert board.available == set()
		assert reference.board_winners(board) == {PlayerColor.RED}

	def test_unfinished_game_has_no_winner(self, board_type, red_winning_moves, make_board_from_moves):
		board = make_board_from_moves(
			red_winning_moves[:-1],
			board_type=board_type,
		)

		assert board.winner is None
		assert not board.is_game_over

	def test_undoing_the_winning_move_removes_the_winner(self, board_type, red_winning_game, red_winning_moves):
		board = red_winning_game(board_type)
		(row, col), _ = red_winning_moves[-1]

		board.reset(row, col)

		assert board.winner is None

		board.set(row, col, Cell.RED)

		assert board.winner is PlayerColor.RED

	def test_blocking_cell_does_not_win_for_the_wrong_player(self, board_type, red_winning_moves, make_board_from_moves):
		# Blue claiming the cell that Red needs prevents Red's win.
		board = make_board_from_moves(
			red_winning_moves[:-1],
			board_type=board_type,
		)
		(row, col), _ = red_winning_moves[-1]

		board.set(row, col, Cell.BLUE)

		assert board.winner is not PlayerColor.RED

class TestBoardSerializationValidation:
	@pytest.mark.parametrize("value", ["", "3,3,XRXBWBXRX", "garbage"])
	def test_strings_are_accepted_as_serializations(self, value):
		assert is_board_serialization(value) is True
		assert validate_board_serialization(value) is None

	@pytest.mark.parametrize("value", [None, 123, 1.5, b"3,3,XRXBWBXRX", ["3,3,XRXBWBXRX"], ("3",)])
	def test_other_types_are_rejected(self, value):
		assert is_board_serialization(value) is False

		with pytest.raises(TypeError, match="Expected a serialized board string"):
			validate_board_serialization(value)

	def test_the_error_names_the_offending_type(self):
		with pytest.raises(TypeError, match="got int"):
			validate_board_serialization(123)

	@pytest.mark.parametrize("value", [None, 123, 1.5, b"3,3,XRXBWBXRX", ["3,3,XRXBWBXRX"]])
	def test_deserialize_rejects_non_strings_with_a_type_error(self, board_type, value):
		with pytest.raises(TypeError, match="Expected a serialized board string"):
			board_type.deserialize(value)


class TestBoardHelpers:
	def test_is_board(self, board):
		assert is_board(board)
		assert not is_board("board")
		assert not is_board(None)

	def test_validate_board(self, board):
		validate_board(board)

		with pytest.raises(TypeError, match="Expected a Board"):
			validate_board(object())

	def test_resolve_board_defaults_to_union_find_board(self):
		assert type(resolve_board(None)) is UnionFindBoard

	def test_resolve_board_uses_the_given_default(self):
		default = SearchBoard(size=5)

		assert resolve_board(None, default=default) is default

	def test_resolve_board_returns_the_given_board(self, board):
		assert resolve_board(board) is board

	def test_resolve_board_rejects_non_boards(self):
		with pytest.raises(TypeError):
			resolve_board("board")

		with pytest.raises(TypeError):
			resolve_board(None, default="board")
