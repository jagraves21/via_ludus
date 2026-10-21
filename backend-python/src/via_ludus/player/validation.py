from .base import Player
from .scoring import ScoringPlayer


def is_player(player):
	return isinstance(player, Player)


def validate_player(player):
	if not is_player(player):
		raise TypeError(
			f"Expected a Player, got {type(player).__name__}"
		)


def is_scoring_player(player):
	return isinstance(player, ScoringPlayer)


def validate_scoring_player(player):
	if not is_scoring_player(player):
		raise TypeError(
			f"Expected a ScoringPlayer, got {type(player).__name__}"
		)


def is_player_class(player_class):
	return (
		isinstance(player_class, type)
		and issubclass(player_class, Player)
	)


def validate_player_class(player_class):
	if not is_player_class(player_class):
		raise TypeError("Expected a Player subclass")


def is_scoring_player_class(player_class):
	return (
		isinstance(player_class, type)
		and issubclass(player_class, ScoringPlayer)
	)


def validate_scoring_player_class(player_class):
	if not is_scoring_player_class(player_class):
		raise TypeError("Expected a ScoringPlayer subclass")

