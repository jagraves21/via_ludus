from abc import abstractmethod

from .base import Player
from .move_selector import BestSelector


class ScoringPlayer(Player):
	def __init__(self, color, selector=None):
		super().__init__(color)

		self._selector = (
			self.create_selector()
			if selector is None
			else selector
		)

	def create_selector(self):
		return BestSelector()

	@property
	def is_stochastic(self):
		return self._selector.is_stochastic

	def choose_move(self, board):
		scores = self.score_moves(board, self.color)
		return self._selector.select(scores)

	def choose_move_with_determinism(self, board):
		scores = self.score_moves(board, self.color)
		return self._selector.select_with_determinism(scores)

	@property
	def has_deterministic_scoring(self):
		return False

	@abstractmethod
	def score_moves(self, board, color):
		pass


class DeterministicScoringPlayer(ScoringPlayer):
	"""A scoring player that guarantees deterministic scoring.

	Subclasses promise that score_moves returns the same scores for
	equivalent board states and colors, regardless of the history
	that produced the board or previous calls to the player.

	This contract applies only to score_moves. The configured move
	selector may be stochastic, so choose_move is not necessarily
	deterministic.

	This contract is declarative and is not enforced at runtime.
	"""

	@property
	def has_deterministic_scoring(self):
		return True

