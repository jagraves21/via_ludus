from abc import ABC, abstractmethod

import networkx as nx

from ....player import (
	MaxSelectorMixin,
	MinSelectorMixin,
)
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
	MaxSelectorMixin,
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
	MaxSelectorMixin,
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
	MaxSelectorMixin,
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
	MaxSelectorMixin,
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
	MaxSelectorMixin,
	EdgeCentralityAgent,
):
	name = "Kwang-Il"

	def edge_centrality(self, graph):
		return nx.edge_load_centrality(graph)

