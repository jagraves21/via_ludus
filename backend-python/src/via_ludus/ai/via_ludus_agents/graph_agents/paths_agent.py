from abc import ABC, abstractmethod
from collections import Counter
import inspect

import networkx as nx

from ....board import Cell
from ....player import (
	DeterministicScoringMixin,
	RandomMaxSelectorMixin,
)

from .graph_utils import Endpoint
from .graph_builder_mixins import (
	DirectedOpponentPlayerGraphMixin,
	DirectedPlayerGraphMixin,
	DirectedPlayerGraphPairMixin,
)
from .graph_agent import GraphAgent


class PathsAgent(
	DeterministicScoringMixin,
	RandomMaxSelectorMixin,
	GraphAgent,
	ABC,
):
	@abstractmethod
	def _get_paths(self, graph):
		pass

	@abstractmethod
	def _score_paths(self, paths):
		pass

	def graph_scores(self, graph):
		paths = self._get_paths(graph)
		return self._score_paths(paths)

	@staticmethod
	def _get_shortest_paths(graph):
		return [
			[
				node
				for node in path
				if graph.nodes[node]["cell"] == Cell.WHITE
			]
			for path in nx.all_shortest_paths(
				graph,
				source=Endpoint.SOURCE,
				target=Endpoint.TARGET,
				weight="traversal_cost",
				method="dijkstra",
			)
		]

	@staticmethod
	def _count_path_nodes(
		paths,
		normalize=False,
		weight_by_path_length=False,
	):
		scores = Counter()
		num_paths = 0
		path_length = None

		for path in paths:
			num_paths += 1
			current_path_length = len(path)

			if path_length is None:
				path_length = current_path_length
			elif current_path_length != path_length:
				raise ValueError(
					f"Paths have different lengths: "
					f"{path_length} and {current_path_length}."
				)

			scores.update(path)

		if not num_paths:
			return {}

		scalar = 1

		if normalize:
			scalar /= num_paths

		if weight_by_path_length and path_length:
			scalar /= path_length

		return {
			node: score * scalar
			for node, score in scores.items()
		}


class SinglePathsAgent(PathsAgent):
	def _get_paths(self, graph):
		return self._get_shortest_paths(graph)

	def _score_paths(self, paths):
		return self._count_path_nodes(paths)


class MyPathsAgent(
	DirectedPlayerGraphMixin,
	SinglePathsAgent,
):
	name = "Bellman"


class OpponentPathsAgent(
	DirectedOpponentPlayerGraphMixin,
	SinglePathsAgent,
):
	name = "Moore"


class DoublePathsAgent(PathsAgent):
	def _get_paths(self, graphs):
		return tuple(
			self._get_shortest_paths(graph)
			for graph in graphs
		)

	def _score_paths(self, paths):
		candidate_paths, reference_paths = paths

		candidate_scores = self._count_path_nodes(
			candidate_paths,
			normalize=True,
			weight_by_path_length=True,
		)
		reference_scores = self._count_path_nodes(
			reference_paths,
			normalize=True,
			weight_by_path_length=True,
		)

		return {
			cell: candidate_scores.get(cell, 0)
			+ reference_scores.get(cell, 0)
			for cell in candidate_scores.keys() | reference_scores.keys()
		}


class CombinedPathsAgent(
	DirectedPlayerGraphPairMixin,
	DoublePathsAgent,
):
	name = "Bellman-Moore"


PATH_AGENTS = {
	agent.get_agent_name(): agent
	for agent in PathsAgent.__subclasses__()
	if not inspect.isabstract(agent)
}

