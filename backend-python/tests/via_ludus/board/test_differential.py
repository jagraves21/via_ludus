"""Differential tests: SearchBoard and UnionFindBoard must always agree.

Both implementations are also compared against the independent reference
implementation from ``conftest.py``.
"""

import pytest

from via_ludus.board import (
	Cell,
	PlayerColor,
	SearchBoard,
	UnionFindBoard,
)


def _expected_winner(reference, board):
	winners = reference.board_winners(board)

	assert len(winners) <= 1

	return next(iter(winners), None)


def _assert_boards_agree(search, union_find, reference):
	assert search.serialize() == union_find.serialize()
	assert search.available == union_find.available
	assert search.red_cells == union_find.red_cells
	assert search.blue_cells == union_find.blue_cells
	assert search.winner is union_find.winner
	assert search.winner is _expected_winner(reference, search)
	assert search.is_game_over == union_find.is_game_over


class TestKnownPositions:
	def test_known_positions_agree_when_replayed_move_by_move(self, terminal_position, reference):
		search = SearchBoard(size=terminal_position.size)
		union_find = UnionFindBoard(size=terminal_position.size)

		for (row, col), player in terminal_position.moves:
			search.set(row, col, player.cell)
			union_find.set(row, col, player.cell)

			_assert_boards_agree(search, union_find, reference)

		assert search.winner is terminal_position.winner

	def test_known_positions_agree_when_deserialized(self, terminal_position, reference):
		search = SearchBoard.deserialize(terminal_position.serialization)
		union_find = UnionFindBoard.deserialize(terminal_position.serialization)

		_assert_boards_agree(search, union_find, reference)
		assert search.winner is terminal_position.winner

	def test_incremental_and_deserialized_union_find_boards_agree(self, terminal_position, make_board_from_moves):
		incremental = make_board_from_moves(
			terminal_position.moves,
			board_type=UnionFindBoard,
			size=terminal_position.size,
		)
		rebuilt = UnionFindBoard.deserialize(incremental.serialize())

		assert rebuilt.winner is incremental.winner
		assert rebuilt._red_union_find.equivalent(incremental._red_union_find)
		assert rebuilt._blue_union_find.equivalent(incremental._blue_union_find)


class TestRandomPlayouts:
	def test_playouts_agree_after_every_move(self, playout, reference):
		search = SearchBoard(size=playout.size)
		union_find = UnionFindBoard(size=playout.size)

		for (row, col), player in playout.moves:
			search.set(row, col, player.cell)
			union_find.set(row, col, player.cell)

			_assert_boards_agree(search, union_find, reference)

		assert search.winner is playout.moves[-1][1]

	def test_playouts_agree_after_conversion_between_implementations(self, playout):
		search = SearchBoard(size=playout.size)

		for (row, col), player in playout.moves[:-1]:
			search.set(row, col, player.cell)

		converted = UnionFindBoard.from_board(search)
		(row, col), player = playout.moves[-1]

		search.set(row, col, player.cell)
		converted.set(row, col, player.cell)

		assert converted.winner is search.winner is player

	def test_playouts_agree_after_copying_midway(self, playout):
		search = SearchBoard(size=playout.size)
		union_find = UnionFindBoard(size=playout.size)
		midpoint = len(playout.moves) // 2

		for (row, col), player in playout.moves[:midpoint]:
			search.set(row, col, player.cell)
			union_find.set(row, col, player.cell)

		search_copy = search.copy()
		union_find_copy = union_find.copy()

		for (row, col), player in playout.moves[midpoint:]:
			search_copy.set(row, col, player.cell)
			union_find_copy.set(row, col, player.cell)

		assert search_copy.serialize() == union_find_copy.serialize()
		assert search_copy.winner is union_find_copy.winner is playout.moves[-1][1]
		# the originals were not touched by moves on their copies
		assert search.serialize() == union_find.serialize()
		assert len(search.available) == len(search_copy.available) + (
			len(playout.moves) - midpoint
		)

	def test_playouts_agree_when_moves_are_undone_in_reverse_order(self, playout, reference):
		search = SearchBoard(size=playout.size)
		union_find = UnionFindBoard(size=playout.size)

		for (row, col), player in playout.moves:
			search.set(row, col, player.cell)
			union_find.set(row, col, player.cell)

		for (row, col), _ in reversed(playout.moves):
			search.reset(row, col)
			union_find.reset(row, col)

			_assert_boards_agree(search, union_find, reference)

		assert search.serialize() == SearchBoard(size=playout.size).serialize()


def _explore_all_legal_games(size):
	"""Yield (search, union_find) for every position reachable by legal play.

	Red moves first, players alternate and a position in which somebody has
	already won is terminal.
	"""
	start = (SearchBoard(size=size), UnionFindBoard(size=size))
	seen = {start[0].serialize()}
	stack = [(start, PlayerColor.RED)]

	while stack:
		(search, union_find), player = stack.pop()

		yield search, union_find

		if search.winner is not None:
			continue

		for row, col in sorted(search.available):
			next_search = search.copy()
			next_union_find = union_find.copy()

			next_search.set(row, col, player.cell)
			next_union_find.set(row, col, player.cell)

			key = next_search.serialize()

			if key in seen:
				continue

			seen.add(key)
			stack.append(((next_search, next_union_find), player.opponent))


class TestExhaustive5x5:
	def test_every_reachable_5x5_position_agrees(self, reference):
		positions = list(_explore_all_legal_games(5))
		winners = [search.winner for search, _ in positions]

		for search, union_find in positions:
			_assert_boards_agree(search, union_find, reference)

			rebuilt = UnionFindBoard.deserialize(search.serialize())

			assert rebuilt.winner is search.winner

		# the exploration must be non-trivial and must reach both kinds of win
		assert len(positions) > 50
		assert PlayerColor.RED in winners
		assert PlayerColor.BLUE in winners
		assert None in winners

	def test_every_full_5x5_position_has_exactly_one_winner(self, reference):
		full_positions = [
			search
			for search, _ in _explore_all_legal_games(5)
			if not search.available
		]

		assert full_positions

		for search in full_positions:
			assert reference.board_winners(search) == {PlayerColor.RED}
			assert search.winner is PlayerColor.RED
