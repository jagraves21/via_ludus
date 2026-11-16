import pytest

import via_ludus.board as board_package
from via_ludus.board import (
	SearchBoard,
	UnionFindBoard,
	base,
	cells,
	colors,
	resolve_board,
	search,
	union_find,
)


EXPORTS = [
	("Cell", cells, "Cell"),
	("is_cell", cells, "is_cell"),
	("is_playable_cell", cells, "is_playable_cell"),
	("is_player_cell", cells, "is_player_cell"),
	("validate_cell", cells, "validate_cell"),
	("validate_playable_cell", cells, "validate_playable_cell"),
	("validate_player_cell", cells, "validate_player_cell"),
	("PlayerColor", colors, "PlayerColor"),
	("is_player_color", colors, "is_player_color"),
	("validate_player_color", colors, "validate_player_color"),
	("resolve_starting_player_color", colors, "resolve_starting_player_color"),
	("Board", base, "Board"),
	("is_board", base, "is_board"),
	("is_board_serialization", base, "is_board_serialization"),
	("validate_board", base, "validate_board"),
	("validate_board_serialization", base, "validate_board_serialization"),
	("SearchBoard", search, "SearchBoard"),
	("UnionFindBoard", union_find, "UnionFindBoard"),
	("resolve_board", board_package, "resolve_board"),
]


class TestPackageExports:
	def test_all_lists_only_existing_names(self):
		assert all(hasattr(board_package, name) for name in board_package.__all__)

	def test_all_has_no_duplicates(self):
		assert len(board_package.__all__) == len(set(board_package.__all__))

	@pytest.mark.parametrize(
		"name, module, attribute",
		EXPORTS,
		ids=[name for name, _, _ in EXPORTS],
	)
	def test_public_api_is_exported(self, name, module, attribute):
		assert name in board_package.__all__
		assert getattr(board_package, name) is getattr(module, attribute)

	def test_all_matches_the_expected_api(self):
		assert set(board_package.__all__) == {name for name, _, _ in EXPORTS}

	def test_star_import_exposes_the_public_api(self):
		namespace = {}

		exec("from via_ludus.board import *", namespace)

		assert set(board_package.__all__) <= set(namespace)

	def test_resolve_board_is_defined_in_the_package(self):
		assert resolve_board.__module__ == "via_ludus.board"


class TestResolveBoard:
	def test_defaults_to_a_union_find_board(self):
		assert type(resolve_board(None)) is UnionFindBoard

	def test_creates_a_new_default_board_each_time(self):
		assert resolve_board(None) is not resolve_board(None)

	def test_uses_the_given_default_when_there_is_no_board(self):
		default = SearchBoard(size=5)

		assert resolve_board(None, default=default) is default

	def test_returns_the_given_board(self):
		board = SearchBoard(size=5)

		assert resolve_board(board) is board

	def test_the_given_board_wins_over_the_default(self):
		board = SearchBoard(size=5)
		default = UnionFindBoard(size=5)

		assert resolve_board(board, default=default) is board

	def test_rejects_a_board_that_is_not_a_board(self):
		with pytest.raises(TypeError, match="Expected a Board, got str"):
			resolve_board("board")

	def test_rejects_a_default_that_is_not_a_board(self):
		with pytest.raises(TypeError, match="Expected a Board, got str"):
			resolve_board(None, default="board")
