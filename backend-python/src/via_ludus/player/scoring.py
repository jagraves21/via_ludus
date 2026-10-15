from abc import abstractmethod

from .base import Player
from .move_selector import RandomBestSelector


class ScoringPlayer(Player):
	def __init__(self, color, selector=None):
		super().__init__(color)

		self._selector = (
			RandomBestSelector()
			if selector is None
			else selector 
		)

	def choose_move(self, board):
		scores = self.score_moves(board, self.color)
		return self._selector.select(scores)

	@abstractmethod
	def score_moves(self, board, color):
		pass

