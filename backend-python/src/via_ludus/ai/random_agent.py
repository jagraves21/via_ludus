from .tactical_agent import TacticalAgent


class RandomAgent(TacticalAgent):
	name = "Random"

	def evaluate_move_options(self, board, color):
		available = board.available

		return {
			move: 0
			for move in available
		}

