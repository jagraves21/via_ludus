import pytest

from via_ludus.board import (
	Cell,
	PlayerColor,
	is_player_color,
	resolve_starting_player_color,
	validate_player_color,
)


class TestPlayerColor:
	def test_opponent(self, player_color):
		assert player_color.opponent is not player_color
		assert player_color.opponent.opponent is player_color

	def test_opponents_are_red_and_blue(self):
		assert PlayerColor.RED.opponent is PlayerColor.BLUE
		assert PlayerColor.BLUE.opponent is PlayerColor.RED

	def test_cell_of_player_color(self):
		assert PlayerColor.RED.cell is Cell.RED
		assert PlayerColor.BLUE.cell is Cell.BLUE

	def test_str_and_repr(self, player_color):
		assert str(player_color) == player_color.name.title()
		assert repr(player_color) == f"PlayerColor.{player_color.name}"


class TestPlayerColorValidation:
	def test_is_player_color(self):
		assert is_player_color(PlayerColor.RED)
		assert not is_player_color(Cell.RED)
		assert not is_player_color(None)

	def test_is_player_color_rejects_plain_strings(self):
		# PlayerColor is a StrEnum, so "red" == PlayerColor.RED, but a plain
		# string is still not a PlayerColor.
		assert not is_player_color("red")

	def test_validate_player_color(self):
		validate_player_color(PlayerColor.BLUE)

		with pytest.raises(TypeError, match="PlayerColor"):
			validate_player_color("blue")


class TestResolveStartingPlayerColor:
	def test_resolve_starting_player_color_defaults_to_red(self):
		assert resolve_starting_player_color(None) is PlayerColor.RED

	def test_resolve_starting_player_color_custom_default(self):
		assert (
			resolve_starting_player_color(None, default=PlayerColor.BLUE)
			is PlayerColor.BLUE
		)

	def test_resolve_starting_player_color_keeps_explicit_color(self, player_color):
		assert resolve_starting_player_color(player_color) is player_color

	def test_resolve_starting_player_color_rejects_invalid_color(self):
		with pytest.raises(TypeError):
			resolve_starting_player_color("red")
