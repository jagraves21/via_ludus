from abc import ABC, abstractmethod

from .graphs import board_to_player_graph
from .tactical_agent import TacticalAgent


class GraphAgent(TacticalAgent, ABC):
	@property
	def graph_builder(self):
		return board_to_player_graph

	@abstractmethod
	def graph_scores(self, graph):
		pass

	def move_scores_from_graph_scores(self, graph, scores):
		return scores

	def evaluate_move_options(self, board, color):
		graph = self.graph_builder(board, color)
		scores = self.graph_scores(graph)

		return self.move_scores_from_graph_scores(
			graph,
			scores,
		)

