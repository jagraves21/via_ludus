from abc import ABC, abstractmethod
import inspect

import networkx as nx

from ....board import Cell
from ....player import (
	DeterministicScoringMixin,
	RandomMinSelectorMixin,
)

from .graph_utils import (
	Endpoint,
	is_endpoint,
)
from .graph_builder_mixins import (
	DirectedOpponentPlayerGraphMixin,
	DirectedPlayerGraphMixin,
	DirectedPlayerGraphPairMixin,
)
from .graph_agent import GraphAgent


class DistanceAgent(
	DeterministicScoringMixin,
	RandomMinSelectorMixin,
	GraphAgent,
	ABC,
):
	@abstractmethod
	def _get_distances(self, graph):
		pass

	@abstractmethod
	def _score_distances(self, distances):
		pass

	def graph_scores(self, graph):
		distances = self._get_distances(graph)
		return self._score_distances(distances)

	@staticmethod
	def _calculate_distances(graph):
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
				not is_endpoint(node)
				and data["cell"] == Cell.WHITE
				and node in source_distances
				and node in target_distances
			)
		}

class SingleDistanceAgent(DistanceAgent):
	def _get_distances(self, graph):
		return self._calculate_distances(graph)

	def _score_distances(self, distances):
		return distances


# Robert W. Floyd
class OffensiveDistanceAgent(
	DirectedPlayerGraphMixin,
	SingleDistanceAgent,
):
	name = "Floyd"


# Stephen Warshall
class DefensiveDistanceAgent(
	DirectedOpponentPlayerGraphMixin,
	SingleDistanceAgent,
):
	name = "Warshall"


class DoubleDistanceAgent(DistanceAgent):
	def _get_distances(self, graphs):
		return tuple(
			self._calculate_distances(graph)
			for graph in graphs
		)

	def _score_distances(self, distances):
		candidate_distances, reference_distances = distances

		return {
			cell: candidate_distances.get(cell, 0)
			+ reference_distances.get(cell, 0)
			for cell in (
				candidate_distances.keys()
				| reference_distances.keys()
			)
		}


# Bernard Roy
class CombinedDistanceAgent(
	DirectedPlayerGraphPairMixin,
	DoubleDistanceAgent,
):
	name = "Roy"


DISTANCE_AGENTS = {
	agent.get_agent_name(): agent
	for agent in DistanceAgent.__subclasses__()
	if not inspect.isabstract(agent)
}

