import networkx as nx

from .graphs import (
	Endpoint,
	board_to_player_graph,
)
from .tactical_agent import TacticalAgent
from ..board import Cell, PlayerColor


class Undergrad(TacticalAgent):
	name = "Undergrad"

	@property
	def higher_is_better(self):
		return False

	def _calculate_scores(self, graph):
		source_distances = nx.single_source_dijkstra_path_length(
			graph,
			Endpoint.SOURCE,
			weight="cost",
		)
		target_distances = nx.single_source_dijkstra_path_length(
			graph,
			Endpoint.TARGET,
			weight="cost",
		)

		return {
			node: source_distances[node] + target_distances[node]
			for node, data in graph.nodes(data=True)
			if (
				isinstance(node, tuple)
				and data["cell"] == Cell.WHITE
				and node in source_distances
				and node in target_distances
			)
		}

	def evaluate_move_options(self, board, color):
		my_graph = board_to_player_graph(board, color)
		opponent_graph = board_to_player_graph(board, color.opponent)

		my_scores = self._calculate_scores(my_graph)
		opponent_scores = self._calculate_scores(opponent_graph)
		
		#return my_scores
		return opponent_scores

		return {
			cell: my_score#- opponent_scores.get(cell, 0)
			for cell, my_score in my_scores.items()
		}

