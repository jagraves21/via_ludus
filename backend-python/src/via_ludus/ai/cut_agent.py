from abc import abstractmethod

from ..board import PlayerColor
from .graphs import (
	board_to_move_graph,
	minimum_endpoint_cut,
)

from .tactical_agent import TacticalAgent


class CutAgent(TacticalAgent):
	def get_cuts(self, board, color):
		my_graph = board_to_move_graph(board, color)
		opponent_graph = board_to_move_graph(board, color.opponent)

		my_cut = minimum_endpoint_cut(my_graph)
		opponent_cut = minimum_endpoint_cut(opponent_graph)

		return my_cut, opponent_cut

	def evaluate_move_options(self, board, color):
		my_cut, opponent_cut = self.get_cuts(board, color)
		return self.evaluate_cuts(my_cut, opponent_cut)

	@abstractmethod
	def evaluate_cuts(self, my_cut, opponent_cut):
		pass


# Delbert Ray Fulkerson
class OffensiveCutAgent(CutAgent):
	name = "Fulkerson"

	def evaluate_cuts(self, my_cut, opponent_cut):
		return {
			move: 0
			for move in opponent_cut
		}


# Lester Randolph Ford Jr.
class DefensiveCutAgent(CutAgent):
	name = "Ford"

	def evaluate_cuts(self, my_cut, opponent_cut):
		return {
			move: 0
			for move in my_cut
		}


# Karl Menger
class OffensiveOverlapCutAgent(CutAgent):
	name = "Menger"
	
	def evaluate_cuts(self, my_cut, opponent_cut):
		return {
			move: int(move in my_cut)
			for move in opponent_cut
		}


# Hassler Whitney
class DefensiveOverlapCutAgent(CutAgent):
	name = "Whitney"
	
	def evaluate_cuts(self, my_cut, opponent_cut):
		return {
			move: int(move in opponent_cut)
			for move in my_cut
		}

