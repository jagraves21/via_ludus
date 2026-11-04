import numpy as np
import pytest

import via_ludus.board as board_package
import via_ludus.player as player_package
import via_ludus.validation as validation


BOARD_NAMES = [
	"is_board",
	"is_board_serialization",
	"is_cell",
	"is_playable_cell",
	"is_player_cell",
	"is_player_color",
	"validate_board",
	"validate_board_serialization",
	"validate_cell",
	"validate_playable_cell",
	"validate_player_cell",
	"validate_player_color",
	"resolve_board",
	"resolve_starting_player_color",
]

PLAYER_NAMES = [
	"is_player",
	"is_player_class",
	"is_scoring_player",
	"is_scoring_player_class",
	"validate_player",
	"validate_player_class",
	"validate_scoring_player",
	"validate_scoring_player_class",
]


class TestReExports:
	@pytest.mark.parametrize("name", BOARD_NAMES)
	def test_board_helpers_are_the_board_package_functions(self, name):
		assert getattr(validation, name) is getattr(board_package, name)

	@pytest.mark.parametrize("name", PLAYER_NAMES)
	def test_player_helpers_are_the_player_package_functions(self, name):
		assert getattr(validation, name) is getattr(player_package, name)

	@pytest.mark.parametrize("name", BOARD_NAMES + PLAYER_NAMES)
	def test_every_helper_is_callable(self, name):
		assert callable(getattr(validation, name))

	def test_there_are_no_duplicate_names(self):
		assert len(set(BOARD_NAMES + PLAYER_NAMES)) == len(BOARD_NAMES + PLAYER_NAMES)

	def test_star_import_exposes_the_helpers(self):
		namespace = {}

		exec("from via_ludus.validation import *", namespace)

		assert set(BOARD_NAMES + PLAYER_NAMES) <= set(namespace)

	def test_validation_is_available_from_the_top_level_package(self):
		import via_ludus

		assert via_ludus.validation is validation


VALID_POSITIVE_INTEGERS = [1, 2, 10**9, np.int64(3), np.int32(1), np.uint8(7)]
INVALID_POSITIVE_INTEGERS = [
	0,
	-1,
	-3,
	1.5,
	2.0,
	np.float64(2.0),
	"2",
	None,
	True,
	False,
	[1],
	(1,),
]


class TestPositiveInteger:
	@pytest.mark.parametrize("value", VALID_POSITIVE_INTEGERS)
	def test_valid_values(self, value):
		assert validation.is_positive_integer(value) is True
		assert validation.validate_positive_integer(value) is None

	@pytest.mark.parametrize("value", INVALID_POSITIVE_INTEGERS)
	def test_invalid_values(self, value):
		assert validation.is_positive_integer(value) is False

		with pytest.raises(ValueError, match="value must be a positive integer"):
			validation.validate_positive_integer(value)

	def test_the_error_names_the_argument(self):
		with pytest.raises(ValueError, match="num_games must be a positive integer"):
			validation.validate_positive_integer(0, "num_games")

	def test_booleans_are_not_integers_here(self):
		assert validation.is_positive_integer(True) is False

	def test_the_boundary_is_one(self):
		assert validation.is_positive_integer(1) is True
		assert validation.is_positive_integer(0) is False


class TestString:
	@pytest.mark.parametrize("value", ["", "text", "multi\nline", str("x")])
	def test_strings(self, value):
		assert validation.is_string(value) is True
		assert validation.validate_string(value) is None

	@pytest.mark.parametrize("value", [None, 1, 1.5, b"bytes", ["text"], ("text",), {"text"}])
	def test_non_strings(self, value):
		assert validation.is_string(value) is False

		with pytest.raises(TypeError, match="value must be a string, got"):
			validation.validate_string(value)

	def test_the_error_names_the_argument_and_the_type(self):
		with pytest.raises(TypeError, match="name must be a string, got int"):
			validation.validate_string(123, "name")

	def test_string_subclasses_are_strings(self):
		from via_ludus.board import PlayerColor

		assert validation.is_string(PlayerColor.RED) is True

