import math

import pytest

from via_ludus.player import (
	BestSelector,
	MaxSelector,
	MinSelector,
	MoveSelector,
	RandomBestSelector,
	RandomMaxSelector,
	RandomMinSelector,
	SoftmaxSelector,
	SoftminSelector,
)


DETERMINISTIC_SELECTORS = [BestSelector, MaxSelector, MinSelector]
RANDOM_SELECTORS = [RandomBestSelector, RandomMaxSelector, RandomMinSelector]
SOFT_SELECTORS = [SoftmaxSelector, SoftminSelector]
ALL_SELECTORS = DETERMINISTIC_SELECTORS + RANDOM_SELECTORS + SOFT_SELECTORS


@pytest.fixture(params=ALL_SELECTORS, ids=lambda cls: cls.__name__)
def selector_class(request):
	return request.param


class TestMoveSelectorInterface:
	def test_move_selector_is_abstract(self):
		with pytest.raises(TypeError):
			MoveSelector()

	def test_all_selectors_are_move_selectors(self, selector_class):
		assert issubclass(selector_class, MoveSelector)
		assert isinstance(selector_class(), MoveSelector)

	@pytest.mark.parametrize("selector_class", DETERMINISTIC_SELECTORS)
	def test_best_selectors_are_not_stochastic(self, selector_class):
		assert selector_class().is_stochastic is False

	@pytest.mark.parametrize("selector_class", RANDOM_SELECTORS + SOFT_SELECTORS)
	def test_random_and_soft_selectors_are_stochastic(self, selector_class):
		assert selector_class().is_stochastic is True


class TestScoreValidation:
	def test_rejects_empty_scores(self, selector_class):
		with pytest.raises(ValueError, match="No available moves"):
			selector_class().select({})

	@pytest.mark.parametrize("bad_score", [math.nan, math.inf, -math.inf])
	def test_rejects_scores_that_are_all_non_finite(self, selector_class, bad_score):
		with pytest.raises(ValueError, match="No available moves"):
			selector_class().select({(1, 1): bad_score, (1, 3): bad_score})

	@pytest.mark.parametrize("bad_score", [math.nan, math.inf, -math.inf])
	def test_ignores_non_finite_scores(self, selector_class, bad_score):
		scores = {(1, 1): bad_score, (1, 3): 2.0, (3, 1): bad_score}

		assert selector_class().select(scores) == (1, 3)

	def test_non_finite_scores_never_win_even_when_they_look_best(self):
		scores = {(1, 1): math.inf, (1, 3): 1.0, (3, 1): 2.0}

		assert MaxSelector().select(scores) == (3, 1)
		assert MinSelector().select(scores) == (1, 3)

	def test_select_does_not_modify_the_scores(self, selector_class, move_scores):
		before = dict(move_scores)

		selector_class().select(move_scores)

		assert move_scores == before

	def test_integer_and_numpy_scores_are_accepted(self, selector_class):
		import numpy as np

		scores = {(1, 1): 1, (1, 3): np.int64(2), (3, 1): np.float32(0.5)}

		assert selector_class().select(scores) in scores


class TestBestSelectors:
	def test_max_selector_picks_the_highest_score(self, move_scores):
		assert MaxSelector().select(move_scores) == (1, 3)

	def test_min_selector_picks_the_lowest_score(self, move_scores):
		assert MinSelector().select(move_scores) == (3, 3)

	def test_best_selector_behaves_like_the_max_selector(self, move_scores, tied_move_scores):
		assert BestSelector().select(move_scores) == MaxSelector().select(move_scores)
		assert BestSelector().select(tied_move_scores) == MaxSelector().select(tied_move_scores)

	def test_single_move_is_selected(self, selector_class):
		assert selector_class().select({(5, 5): 0.0}) == (5, 5)

	def test_negative_scores(self):
		scores = {(1, 1): -10.0, (1, 3): -2.0, (3, 1): -7.0}

		assert MaxSelector().select(scores) == (1, 3)
		assert MinSelector().select(scores) == (1, 1)

	def test_ties_select_the_upper_median_of_the_tied_moves(self):
		odd = {(1, 1): 1.0, (1, 3): 1.0, (3, 1): 1.0, (3, 3): 0.0}
		even = {(1, 1): 1.0, (1, 3): 1.0, (3, 3): 0.0}

		assert MaxSelector().select(odd) == (1, 3)
		assert MaxSelector().select(even) == (1, 3)

	def test_ties_for_the_lowest_score(self, tied_move_scores):
		assert MinSelector().select(tied_move_scores) == (1, 3)

	def test_ties_for_the_highest_score(self, tied_move_scores):
		assert MaxSelector().select(tied_move_scores) == (3, 3)

	@pytest.mark.parametrize("selector_class", [MaxSelector, MinSelector])
	def test_tie_breaking_ignores_insertion_order(self, selector_class, tied_move_scores):
		reversed_scores = dict(reversed(list(tied_move_scores.items())))

		assert (
			selector_class().select(tied_move_scores)
			== selector_class().select(reversed_scores)
		)

	@pytest.mark.parametrize("selector_class", DETERMINISTIC_SELECTORS)
	def test_repeated_selection_is_identical(self, selector_class, tied_move_scores):
		selector = selector_class()

		assert len({selector.select(tied_move_scores) for _ in range(20)}) == 1

	@pytest.mark.parametrize("selector_class", DETERMINISTIC_SELECTORS)
	def test_always_reports_a_unique_best_move(self, selector_class, move_scores, tied_move_scores):
		selector = selector_class()

		assert selector.has_unique_best_move(move_scores) is True
		assert selector.has_unique_best_move(tied_move_scores) is True


class TestRandomBestSelectors:
	def test_random_max_selector_only_picks_among_the_highest_scores(self, tied_move_scores):
		selector = RandomMaxSelector(seed=0)

		picks = {selector.select(tied_move_scores) for _ in range(100)}

		assert picks == {(3, 1), (3, 3)}

	def test_random_min_selector_only_picks_among_the_lowest_scores(self, tied_move_scores):
		selector = RandomMinSelector(seed=0)

		picks = {selector.select(tied_move_scores) for _ in range(100)}

		assert picks == {(1, 1), (1, 3)}

	def test_random_best_selector_behaves_like_random_max(self, tied_move_scores):
		selector = RandomBestSelector(seed=0)

		picks = {selector.select(tied_move_scores) for _ in range(100)}

		assert picks == {(3, 1), (3, 3)}

	def test_unique_best_move_is_always_selected(self, move_scores):
		assert {
			RandomMaxSelector(seed=seed).select(move_scores)
			for seed in range(10)
		} == {(1, 3)}
		assert {
			RandomMinSelector(seed=seed).select(move_scores)
			for seed in range(10)
		} == {(3, 3)}

	@pytest.mark.parametrize("selector_class", RANDOM_SELECTORS)
	def test_same_seed_gives_the_same_sequence(self, selector_class, tied_move_scores):
		first = selector_class(seed=123)
		second = selector_class(seed=123)

		assert (
			[first.select(tied_move_scores) for _ in range(30)]
			== [second.select(tied_move_scores) for _ in range(30)]
		)

	@pytest.mark.parametrize("selector_class", RANDOM_SELECTORS)
	def test_different_seeds_can_give_different_sequences(self, selector_class, tied_move_scores):
		sequences = {
			tuple(
				selector_class(seed=seed).select(tied_move_scores)
				for _ in range(30)
			)
			for seed in range(5)
		}

		assert len(sequences) > 1

	@pytest.mark.parametrize("selector_class", RANDOM_SELECTORS)
	def test_selection_varies_over_time(self, selector_class, tied_move_scores):
		selector = selector_class(seed=7)

		assert len({selector.select(tied_move_scores) for _ in range(50)}) == 2

	def test_has_unique_best_move_for_random_max(self, move_scores, tied_move_scores):
		selector = RandomMaxSelector()

		assert selector.has_unique_best_move(move_scores) is True
		assert selector.has_unique_best_move(tied_move_scores) is False

	def test_has_unique_best_move_for_random_min(self, move_scores, tied_move_scores):
		selector = RandomMinSelector()

		assert selector.has_unique_best_move(move_scores) is True
		assert selector.has_unique_best_move(tied_move_scores) is False


class TestSoftSelectors:
	@pytest.mark.parametrize("selector_class", SOFT_SELECTORS)
	@pytest.mark.parametrize("temperature", [0, -1.0, math.nan, math.inf, -math.inf])
	def test_rejects_invalid_temperatures(self, selector_class, temperature):
		with pytest.raises(ValueError, match="Temperature"):
			selector_class(temperature=temperature)

	@pytest.mark.parametrize("selector_class", SOFT_SELECTORS)
	@pytest.mark.parametrize("temperature", [1e-6, 0.5, 1, 100.0])
	def test_accepts_valid_temperatures(self, selector_class, temperature):
		selector_class(temperature=temperature)

	def test_low_temperature_softmax_picks_the_highest_score(self, move_scores):
		selector = SoftmaxSelector(temperature=0.01, seed=0)

		assert {selector.select(move_scores) for _ in range(50)} == {(1, 3)}

	def test_low_temperature_softmin_picks_the_lowest_score(self, move_scores):
		selector = SoftminSelector(temperature=0.01, seed=0)

		assert {selector.select(move_scores) for _ in range(50)} == {(3, 3)}

	def test_high_temperature_explores_all_moves(self, move_scores):
		selector = SoftmaxSelector(temperature=1000.0, seed=0)

		assert {selector.select(move_scores) for _ in range(300)} == set(move_scores)

	@pytest.mark.parametrize("selector_class", SOFT_SELECTORS)
	def test_equal_scores_are_chosen_with_similar_frequency(self, selector_class):
		selector = selector_class(seed=0)
		scores = {(1, 1): 1.0, (1, 3): 1.0}

		picks = [selector.select(scores) for _ in range(1000)]

		assert 350 < picks.count((1, 1)) < 650

	def test_better_moves_are_chosen_more_often_by_softmax(self):
		selector = SoftmaxSelector(temperature=1.0, seed=0)
		scores = {(1, 1): 0.0, (1, 3): 1.0}

		picks = [selector.select(scores) for _ in range(2000)]

		# exp(1) / (1 + exp(1)) is about 0.73
		assert 0.65 < picks.count((1, 3)) / len(picks) < 0.80

	def test_better_moves_are_chosen_more_often_by_softmin(self):
		selector = SoftminSelector(temperature=1.0, seed=0)
		scores = {(1, 1): 0.0, (1, 3): 1.0}

		picks = [selector.select(scores) for _ in range(2000)]

		assert 0.65 < picks.count((1, 1)) / len(picks) < 0.80

	def test_extreme_score_differences_do_not_break_selection(self):
		scores = {(1, 1): 1e308, (1, 3): -1e308, (3, 1): 0.0}

		assert SoftmaxSelector(seed=0).select(scores) == (1, 1)
		assert SoftminSelector(seed=0).select(scores) == (1, 3)

	@pytest.mark.parametrize("selector_class", SOFT_SELECTORS)
	def test_single_move_is_always_selected(self, selector_class):
		assert selector_class(seed=0).select({(5, 5): 123.0}) == (5, 5)

	@pytest.mark.parametrize("selector_class", SOFT_SELECTORS)
	def test_same_seed_gives_the_same_sequence(self, selector_class, move_scores):
		first = selector_class(temperature=5.0, seed=99)
		second = selector_class(temperature=5.0, seed=99)

		assert (
			[first.select(move_scores) for _ in range(30)]
			== [second.select(move_scores) for _ in range(30)]
		)

	@pytest.mark.parametrize("selector_class", SOFT_SELECTORS)
	def test_has_unique_best_move_only_with_a_single_move(self, selector_class, move_scores):
		selector = selector_class()

		assert selector.has_unique_best_move({(1, 1): 1.0}) is True
		assert selector.has_unique_best_move(move_scores) is False


class TestSelectWithDeterminism:
	@pytest.mark.parametrize("selector_class", DETERMINISTIC_SELECTORS)
	def test_best_selectors_are_always_deterministic(self, selector_class, tied_move_scores):
		move, is_deterministic = selector_class().select_with_determinism(tied_move_scores)

		assert move in tied_move_scores
		assert is_deterministic is True

	@pytest.mark.parametrize("selector_class", DETERMINISTIC_SELECTORS)
	def test_selected_move_matches_select(self, selector_class, tied_move_scores):
		selector = selector_class()

		move, _ = selector.select_with_determinism(tied_move_scores)

		assert move == selector.select(tied_move_scores)

	@pytest.mark.parametrize("selector_class", [RandomMaxSelector, RandomMinSelector])
	def test_random_selectors_are_deterministic_with_a_unique_best_move(self, selector_class, move_scores):
		_, is_deterministic = selector_class(seed=0).select_with_determinism(move_scores)

		assert is_deterministic is True

	@pytest.mark.parametrize("selector_class", [RandomMaxSelector, RandomMinSelector])
	def test_random_selectors_are_not_deterministic_with_ties(self, selector_class, tied_move_scores):
		move, is_deterministic = selector_class(seed=0).select_with_determinism(tied_move_scores)

		assert move in tied_move_scores
		assert is_deterministic is False

	@pytest.mark.parametrize("selector_class", SOFT_SELECTORS)
	def test_soft_selectors_are_deterministic_only_with_a_single_move(self, selector_class, move_scores):
		selector = selector_class(seed=0)

		assert selector.select_with_determinism({(1, 1): 1.0}) == ((1, 1), True)
		assert selector.select_with_determinism(move_scores)[1] is False

	def test_determinism_is_judged_after_dropping_non_finite_scores(self):
		scores = {(1, 1): 1.0, (1, 3): math.nan}

		move, is_deterministic = SoftmaxSelector(seed=0).select_with_determinism(scores)

		assert (move, is_deterministic) == ((1, 1), True)

	@pytest.mark.parametrize("selector_class", ALL_SELECTORS)
	def test_rejects_scores_without_a_finite_value(self, selector_class):
		with pytest.raises(ValueError, match="No available moves"):
			selector_class().select_with_determinism({(1, 1): math.nan})

	def test_non_stochastic_selector_that_reports_ambiguity_violates_its_contract(self, move_scores):
		class BrokenSelector(MaxSelector):
			def has_unique_best_move(self, scores):
				return False

		with pytest.raises(RuntimeError, match="violates its contract"):
			BrokenSelector().select_with_determinism(move_scores)

	def test_stochastic_selector_may_report_ambiguity(self, tied_move_scores):
		class AmbiguousSelector(RandomMaxSelector):
			def has_unique_best_move(self, scores):
				return False

		move, is_deterministic = AmbiguousSelector(seed=0).select_with_determinism(tied_move_scores)

		assert move in tied_move_scores
		assert is_deterministic is False
