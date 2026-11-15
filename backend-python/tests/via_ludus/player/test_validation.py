import pytest

from via_ludus.board import PlayerColor
from via_ludus.player import (
	Player,
	ScoringPlayer,
	is_player,
	is_player_class,
	is_scoring_player,
	is_scoring_player_class,
	validate_player,
	validate_player_class,
	validate_scoring_player,
	validate_scoring_player_class,
)


NOT_PLAYERS = ["red", None, 1, PlayerColor.RED, object(), (), {}]


class TestPlayerInstances:
	def test_player_instance(self, first_move_player_class):
		player = first_move_player_class(PlayerColor.RED)

		assert is_player(player) is True
		validate_player(player)

	def test_scoring_player_is_also_a_player(self, index_scoring_player_class):
		player = index_scoring_player_class(PlayerColor.RED)

		assert is_player(player) is True
		validate_player(player)

	@pytest.mark.parametrize("value", NOT_PLAYERS)
	def test_non_players(self, value):
		assert is_player(value) is False

		with pytest.raises(TypeError, match="Expected a Player, got"):
			validate_player(value)

	def test_player_classes_are_not_player_instances(self, first_move_player_class):
		assert is_player(first_move_player_class) is False
		assert is_player(Player) is False

	def test_error_message_names_the_offending_type(self):
		with pytest.raises(TypeError, match="got str"):
			validate_player("red")


class TestScoringPlayerInstances:
	def test_scoring_player_instance(self, index_scoring_player_class):
		player = index_scoring_player_class(PlayerColor.BLUE)

		assert is_scoring_player(player) is True
		validate_scoring_player(player)

	def test_plain_player_is_not_a_scoring_player(self, first_move_player_class):
		player = first_move_player_class(PlayerColor.RED)

		assert is_scoring_player(player) is False

		with pytest.raises(TypeError, match="Expected a ScoringPlayer, got FirstMovePlayer"):
			validate_scoring_player(player)

	@pytest.mark.parametrize("value", NOT_PLAYERS)
	def test_non_players(self, value):
		assert is_scoring_player(value) is False

		with pytest.raises(TypeError, match="Expected a ScoringPlayer, got"):
			validate_scoring_player(value)

	def test_scoring_player_classes_are_not_instances(self, index_scoring_player_class):
		assert is_scoring_player(index_scoring_player_class) is False
		assert is_scoring_player(ScoringPlayer) is False


class TestPlayerClasses:
	def test_player_base_class(self):
		assert is_player_class(Player) is True
		validate_player_class(Player)

	def test_player_subclasses(self, first_move_player_class, index_scoring_player_class):
		for player_class in (first_move_player_class, index_scoring_player_class, ScoringPlayer):
			assert is_player_class(player_class) is True
			validate_player_class(player_class)

	@pytest.mark.parametrize("value", [int, str, object, "Player", None, 1])
	def test_non_player_classes(self, value):
		assert is_player_class(value) is False

		with pytest.raises(TypeError, match="Expected a Player subclass"):
			validate_player_class(value)

	def test_instances_are_not_classes(self, first_move_player_class):
		player = first_move_player_class(PlayerColor.RED)

		assert is_player_class(player) is False

		with pytest.raises(TypeError):
			validate_player_class(player)


class TestScoringPlayerClasses:
	def test_scoring_player_subclasses(self, index_scoring_player_class, tied_scoring_player_class):
		for player_class in (ScoringPlayer, index_scoring_player_class, tied_scoring_player_class):
			assert is_scoring_player_class(player_class) is True
			validate_scoring_player_class(player_class)

	def test_plain_player_classes_are_not_scoring_player_classes(self, first_move_player_class):
		for player_class in (Player, first_move_player_class):
			assert is_scoring_player_class(player_class) is False

			with pytest.raises(TypeError, match="Expected a ScoringPlayer subclass"):
				validate_scoring_player_class(player_class)

	@pytest.mark.parametrize("value", [int, object, "ScoringPlayer", None])
	def test_non_player_classes(self, value):
		assert is_scoring_player_class(value) is False

		with pytest.raises(TypeError, match="Expected a ScoringPlayer subclass"):
			validate_scoring_player_class(value)

	def test_instances_are_not_classes(self, index_scoring_player_class):
		player = index_scoring_player_class(PlayerColor.RED)

		assert is_scoring_player_class(player) is False
