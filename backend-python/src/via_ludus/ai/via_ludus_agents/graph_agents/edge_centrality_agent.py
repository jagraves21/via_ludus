from abc import ABC, abstractmethod

import networkx as nx

from ....player import (
	RandomMaxSelectorMixin,
	RandomMinSelectorMixin,
)

from ..utils import get_concrete_subclasses

from .graph_agent import GraphAgent
from .graph_builder_mixins import (
	UndirectedMoveGraphMixin,
	DirectedMoveGraphMixin,
)
from .graph_utils import Endpoint


class EdgeCentralityAgent(GraphAgent, ABC):
	def graph_scores(self, graph):
		return self.edge_centrality(graph)

	def move_scores_from_graph_scores(self, graph, centrality):
		def edge_score(u, v):
			return centrality.get(
				(u, v),
				centrality.get((v, u), 0),
			)

		return {
			node: sum(
				edge_score(node, neighbor)
				for neighbor in graph.neighbors(node)
			)
			for node in graph
			if isinstance(node, tuple)
		}

	@abstractmethod
	def edge_centrality(self, graph):
		pass


# Michelle Girvan
class EdgeBetweennessCentralityAgent(
	UndirectedMoveGraphMixin,
	RandomMaxSelectorMixin,
	EdgeCentralityAgent,
):
	name = "Girvan"

	def edge_centrality(self, graph):
		return nx.edge_betweenness_centrality(
			graph,
			weight="traversal_cost",
		)


# Ulrik Brandes
class EdgeBetweennessCentralitySubsetAgent(
	UndirectedMoveGraphMixin,
	RandomMaxSelectorMixin,
	EdgeCentralityAgent,
):
	name = "Ulrik"

	def edge_centrality(self, graph):
		return nx.edge_betweenness_centrality_subset(
			graph,
			sources=[Endpoint.SOURCE],
			targets=[Endpoint.TARGET],
			weight="traversal_cost",
		)


# Daniel Fleischer
class EdgeCurrentFlowBetweennessCentralityAgent(
	UndirectedMoveGraphMixin,
	RandomMaxSelectorMixin,
	EdgeCentralityAgent,
):
	name = "Daniel"

	def edge_centrality(self, graph):
		if not nx.is_connected(graph):
			return {}

		return nx.edge_current_flow_betweenness_centrality(
			graph,
			weight="connection_strength",
		)


# Mark E. J. Newman
class EdgeCurrentFlowBetweennessCentralitySubsetAgent(
	UndirectedMoveGraphMixin,
	RandomMaxSelectorMixin,
	EdgeCentralityAgent,
):
	name = "Mark"

	def edge_centrality(self, graph):
		if not nx.is_connected(graph):
			return {}

		return nx.edge_current_flow_betweenness_centrality_subset(
			graph,
			sources=[Endpoint.SOURCE],
			targets=[Endpoint.TARGET],
			weight="connection_strength",
		)


# Kwang-Il Goh
class EdgeLoadCentralityAgent(
	UndirectedMoveGraphMixin,
	RandomMaxSelectorMixin,
	EdgeCentralityAgent,
):
	name = "Kwang-Il"

	def edge_centrality(self, graph):
		return nx.edge_load_centrality(graph)


EDGE_CENTRALITY_AGENTS = get_concrete_subclasses(EdgeCentralityAgent)

