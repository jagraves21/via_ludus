import numbers

from .board import (
	is_board,
	is_board_serialization,
	is_cell,
	is_playable_cell,
	is_player_cell,
	is_player_color,
	validate_board,
	validate_board_serialization,
	validate_cell,
	validate_playable_cell,
	validate_player_cell,
	validate_player_color,
	resolve_board,
	resolve_starting_player_color,
)

from .player import (
	is_player,
	is_player_class,
	is_scoring_player,
	is_scoring_player_class,
	validate_player,
	validate_player_class,
	validate_scoring_player,
	validate_scoring_player_class,
)


def is_positive_integer(value):
	if not isinstance(value, numbers.Integral) or isinstance(value, bool):
		return False

	return bool(value >= 1)


def validate_positive_integer(value, name="value"):
	if not is_positive_integer(value):
		raise ValueError(f"{name} must be a positive integer")


def is_string(value):
	return isinstance(value, str)


def validate_string(value, name="value"):
	if not is_string(value):
		raise TypeError(
			f"{name} must be a string, got {type(value).__name__}"
		)
