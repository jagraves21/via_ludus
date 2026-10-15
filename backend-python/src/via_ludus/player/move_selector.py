from abc import ABC, abstractmethod

import numpy as np


class MoveSelector(ABC):
	def select(self, scores):
		scores = {
			move: score
			for move, score in scores.items()
			if not np.isinf(score)
		}

		if not scores:
			raise ValueError("No available moves")

		return self._select(scores)

	@abstractmethod
	def _select(self, scores):
		pass


class BestSelector(MoveSelector):
	def _select(self, scores):
		return max(scores, key=scores.get)


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


class SoftmaxSelector(MoveSelector):
	def __init__(self, temperature=1.0, seed=None):
		if temperature <= 0:
			raise ValueError("Temperature must be greater than 0")

		self._temperature = temperature
		self._rng = np.random.default_rng(seed)

	def _select(self, scores):
		moves = list(scores)
		values = np.array(
			[scores[move] for move in moves],
			dtype=float,
		)

		logits = -values / self._temperature
		logits -= np.max(logits)

		probabilities = np.exp(logits)
		probabilities /= probabilities.sum()
		
		index = self._rng.choice(
			len(moves),
			p=probabilities,
		)

		return moves[index]

