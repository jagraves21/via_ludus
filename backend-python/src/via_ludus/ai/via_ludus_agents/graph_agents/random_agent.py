from ...player import RandomMaxSelectorMixin

from ..agent import ScoringAgent


class RandomAgent(RandomMaxSelectorMixin, ScoringAgent):
	name = "Random"

	def evaluate_move_options(self, board, color):
		return {
			move: 0
			for move in board.available
		}
