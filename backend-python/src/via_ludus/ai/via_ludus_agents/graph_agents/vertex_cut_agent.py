from abc import abstractmethod
import inspect

from ....player import (
	DeterministicScoringMixin,
	RandomMaxSelectorMixin,
)

from .graph_utils import (
	board_to_move_graph,
	minimum_endpoint_cut,
)

from .graph_agent import GraphAgent


class VertexCutAgent(
	DeterministicScoringMixin,
	RandomMaxSelectorMixin,
	GraphAgent,
):
	def build_graphs(self, board, color):
		my_graph = board_to_move_graph(board, color)
		opponent_graph = board_to_move_graph(
			board,
			color.opponent,
		)

		return my_graph, opponent_graph

	@property
	def graph_builder(self):
		return self.build_graphs

	def graph_scores(self, graph):
		my_graph, opponent_graph = graph

		my_cut = minimum_endpoint_cut(my_graph)
		opponent_cut = minimum_endpoint_cut(opponent_graph)

		return self.score_cuts(my_cut, opponent_cut)

	@abstractmethod
	def score_cuts(self, my_cut, opponent_cut):
		pass


# Delbert Ray Fulkerson
class OffensiveCutAgent(VertexCutAgent):
	name = "Fulkerson"

	def score_cuts(self, my_cut, opponent_cut):
		return {
			move: 0
			for move in opponent_cut
		}


# Lester Randolph Ford Jr.
class DefensiveCutAgent(VertexCutAgent):
	name = "Ford"

	def score_cuts(self, my_cut, opponent_cut):
		return {
			move: 0
			for move in my_cut
		}


# Karl Menger
class OffensiveOverlapCutAgent(VertexCutAgent):
	name = "Menger"

	def score_cuts(self, my_cut, opponent_cut):
		return {
			move: int(move in my_cut)
			for move in opponent_cut
		}


# Hassler Whitney
class DefensiveOverlapCutAgent(VertexCutAgent):
	name = "Whitney"

	def score_cuts(self, my_cut, opponent_cut):
		return {
			move: int(move in opponent_cut)
			for move in my_cut
		}


VERTEX_CUT_AGENTS = {
	agent.get_agent_name(): agent
	for agent in VertexCutAgent.__subclasses__()
	if not inspect.isabstract(agent)
}

