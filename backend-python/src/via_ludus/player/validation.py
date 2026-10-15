from .base import Player


def is_player(player):
	return isinstance(player, Player)


def validate_player(player):
	if not is_player(player):
		raise TypeError(
			f"Expected a Player, got {type(player).__name__}"
		)


def is_player_class(player_class):
	return (
		isinstance(player_class, type)
		and issubclass(player_class, Player)
	)


def validate_player_class(player_class):
	if not is_player_class(player_class):
		raise TypeError("Expected a Player subclass")

