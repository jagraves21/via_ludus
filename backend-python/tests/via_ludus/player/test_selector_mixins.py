import pytest

from via_ludus.board import PlayerColor
from via_ludus.player import (
	MaxSelector,
	MaxSelectorMixin,
	MinSelector,
	MinSelectorMixin,
	RandomMaxSelector,
	RandomMaxSelectorMixin,
	RandomMinSelector,
	RandomMinSelectorMixin,
	SoftmaxSelector,
	SoftmaxSelectorMixin,
	SoftminSelector,
	SoftminSelectorMixin,
)


MIXINS = [
	(MaxSelectorMixin, MaxSelector),
	(MinSelectorMixin, MinSelector),
	(RandomMaxSelectorMixin, RandomMaxSelector),
	(RandomMinSelectorMixin, RandomMinSelector),
	(SoftmaxSelectorMixin, SoftmaxSelector),
	(SoftminSelectorMixin, SoftminSelector),
]


@pytest.fixture(params=MIXINS, ids=lambda case: case[0].__name__)
def mixin_case(request):
	return request.param


class TestCreateSelector:
	def test_creates_the_matching_selector(self, mixin_case):
		mixin, selector_class = mixin_case

		assert type(mixin().create_selector()) is selector_class

	def test_creates_a_new_selector_on_every_call(self, mixin_case):
		mixin, _ = mixin_case
		instance = mixin()

		assert instance.create_selector() is not instance.create_selector()


class TestMixinsWithScoringPlayers:
	def test_mixin_selects_the_scoring_players_selector(self, mixin_case, index_scoring_player_class):
		mixin, selector_class = mixin_case

		class Player(mixin, index_scoring_player_class):
			pass

		player = Player(PlayerColor.RED)

		assert player.is_stochastic is selector_class().is_stochastic

	def test_max_mixin_makes_the_player_choose_the_highest_scoring_move(self, board, index_scoring_player_class):
		class Player(MaxSelectorMixin, index_scoring_player_class):
			pass

		assert Player(PlayerColor.RED).choose_move(board) == max(board.available)

	def test_min_mixin_makes_the_player_choose_the_lowest_scoring_move(self, board, index_scoring_player_class):
		class Player(MinSelectorMixin, index_scoring_player_class):
			pass

		assert Player(PlayerColor.RED).choose_move(board) == min(board.available)

	@pytest.mark.parametrize(
		"mixin, extreme",
		[
			(RandomMaxSelectorMixin, max),
			(RandomMinSelectorMixin, min),
		],
		ids=["random-max", "random-min"],
	)
	def test_random_mixins_choose_the_unique_best_move(self, mixin, extreme, board, index_scoring_player_class):
		class Player(mixin, index_scoring_player_class):
			pass

		assert Player(PlayerColor.RED).choose_move(board) == extreme(board.available)

	@pytest.mark.parametrize("mixin", [SoftmaxSelectorMixin, SoftminSelectorMixin])
	def test_soft_mixins_choose_an_available_move(self, mixin, board, index_scoring_player_class):
		class Player(mixin, index_scoring_player_class):
			pass

		assert Player(PlayerColor.RED).choose_move(board) in board.available

	def test_explicit_selector_overrides_the_mixin(self, board, index_scoring_player_class):
		class Player(MaxSelectorMixin, index_scoring_player_class):
			pass

		player = Player(PlayerColor.RED, selector=MinSelector())

		assert player.choose_move(board) == min(board.available)
