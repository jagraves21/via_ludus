
from abc import ABC, abstractmethod

import numpy as np


class MoveSelector(ABC):
	def select(self, scores):
		scores = {
			move: score
			for move, score in scores.items()
			if np.isfinite(score)
		}

		if not scores:
			raise ValueError("No available moves with finite scores")

		return self._select(scores)

	@abstractmethod
	def _select(self, scores):
		pass


class BestSelector(MoveSelector):
	def _select(self, scores):
		max_score = max(scores.values())

		best_moves = sorted(
			move
			for move, score in scores.items()
			if score == max_score
		)

		return best_moves[len(best_moves) // 2]


class RandomBestSelector(MoveSelector):
	def __init__(self, seed=None):
		self._rng = np.random.default_rng(seed)

	def _select(self, scores):
		max_score = max(scores.values())

		best_moves = [
			move
			for move, score in scores.items()
			if score == max_score
		]

		index = self._rng.integers(len(best_moves))
		return best_moves[index]


class _SoftSelector(MoveSelector):
	_direction = 1

	def __init__(self, temperature=1.0, seed=None):
		if not np.isfinite(temperature) or temperature <= 0:
			raise ValueError(
				"Temperature must be finite and greater than 0"
			)

		self._temperature = temperature
		self._rng = np.random.default_rng(seed)

	def _select(self, scores):
		moves = list(scores)

		values = np.asarray(
			[scores[move] for move in moves],
			dtype=np.longdouble,
		)

		temperature = np.longdouble(self._temperature)

		# normalize before dividing to avoid overflow with extreme scores
		values = self._direction * values
		max_value = np.max(values)
		differences = values - max_value

		# clamp differences to avoid overflow during subtraction and
		# underflow during exponentiation for extreme finite scores
		differences = np.maximum(
			differences,
			-np.longdouble(np.finfo(np.longdouble).max),
		)

		logits = differences / temperature

		# probabilities too small to matter are treated as zero
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

