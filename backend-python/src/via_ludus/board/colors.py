from enum import StrEnum

from .cells import Cell


class PlayerColor(StrEnum):
	RED = "red"
	BLUE = "blue"

	def __str__(self):
		return self.name.title()

	def __repr__(self):
		return f"PlayerColor.{self.name}"

	@property
	def opponent(self):
		if self == PlayerColor.RED:
			return PlayerColor.BLUE

		return PlayerColor.RED

	@property
	def cell(self):
		match self:
			case PlayerColor.RED:
				return Cell.RED
			case PlayerColor.BLUE:
				return Cell.BLUE


def is_player_color(color):
	return isinstance(color, PlayerColor)


def validate_player_color(color):
	if not is_player_color(color):
		raise TypeError(
			f"color must be a PlayerColor, got {type(color).__name__}"
		)


def resolve_starting_player_color(color, default=PlayerColor.RED):
	if color is None:
		color = default

	validate_player_color(color)
	return color
