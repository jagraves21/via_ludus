
from abc import ABC, abstractmethod

import numpy as np


class MoveSelector(ABC):
	def _validate_scores(self, scores):
		scores = {
			move: score
			for move, score in scores.items()
			if np.isfinite(score)
		}

		if not scores:
			raise ValueError("No available moves with finite scores")

		return scores

	def select(self, scores):
		scores = self._validate_scores(scores)
		return self._select(scores)

	def select_with_determinism(self, scores):
		scores = self._validate_scores(scores)
		is_deterministic = self.has_deterministic_selection(scores)

		if not self.is_stochastic and not is_deterministic:
			raise RuntimeError(
				f"{type(self).__name__} violates its contract: "
				"non-stochastic selector reported a "
				"non-deterministic selection"
			)

		move = self._select(scores)
		return move, is_deterministic

	@abstractmethod
	def _select(self, scores):
		pass

	@property
	@abstractmethod
	def is_stochastic(self):
		"""Whether this selector can make random choices."""
		pass

	@abstractmethod
	def has_deterministic_selection(self, scores):
		"""Whether these scores guarantee a single selected move."""
		pass


class BestSelector(MoveSelector):
	@property
	def is_stochastic(self):
		return False

	def has_deterministic_selection(self, scores):
		return True

	def _select(self, scores):
		max_score = max(scores.values())

		best_moves = sorted(
			move
			for move, score in scores.items()
			if score == max_score
		)

		return best_moves[len(best_moves) // 2]


class RandomBestSelector(MoveSelector, ABC):
	def __init__(self, seed=None):
		self._rng = np.random.default_rng(seed)

	@property
	def is_stochastic(self):
		return True

	def has_deterministic_selection(self, scores):
		best_score = self._best_score(scores)

		return sum(
			score == best_score
			for score in scores.values()
		) == 1

	def _select(self, scores):
		best_score = self._best_score(scores)

		best_moves = [
			move
			for move, score in scores.items()
			if score == best_score
		]

		index = self._rng.integers(len(best_moves))
		return best_moves[index]

	@abstractmethod
	def _best_score(self, scores):
		pass


class RandomMaxSelector(RandomBestSelector):
	def _best_score(self, scores):
		return max(scores.values())


class RandomMinSelector(RandomBestSelector):
	def _best_score(self, scores):
		return min(scores.values())


class _SoftSelector(MoveSelector, ABC):
	_direction = 1

	def __init__(self, temperature=1.0, seed=None):
		if not np.isfinite(temperature) or temperature <= 0:
			raise ValueError(
				"Temperature must be finite and greater than 0"
			)

		self._temperature = temperature
		self._rng = np.random.default_rng(seed)

	@property
	def is_stochastic(self):
		return True

	def has_deterministic_selection(self, scores):
		return len(scores) == 1

	def _select(self, scores):
		moves = list(scores)

		values = np.asarray(
			[scores[move] for move in moves],
			dtype=np.longdouble,
		)

		temperature = np.longdouble(self._temperature)

		# normalize before dividing to reduce overflow risk
		values = self._direction * values
		max_value = np.max(values)
		differences = values - max_value

		# clamp extreme differences to avoid numerical overflow
		differences = np.maximum(
			differences,
			-np.longdouble(np.finfo(np.longdouble).max),
		)

		logits = differences / temperature

		# treat negligible probabilities as zero
		logits = np.maximum(logits, -745.0)

		probabilities = np.asarray(np.exp(logits), dtype=float)
		probabilities /= probabilities.sum()

		index = self._rng.choice(
			len(moves),
			p=probabilities,
		)

		return moves[index]


class SoftmaxSelector(_SoftSelector):
	_direction = 1


class SoftminSelector(_SoftSelector):
	_direction = -1

