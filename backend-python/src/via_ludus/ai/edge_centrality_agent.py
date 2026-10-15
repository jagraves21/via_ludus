import networkx as nx

from .graphs import (
	Endpoint,
	board_to_move_graph,
)
from .centrality_agent import CentralityAgent


class EdgeCentralityAgent(CentralityAgent):
	@property
	def graph_builder(self):
		return board_to_move_graph

	def move_scores_from_centrality(self, graph, centrality):
		return {
			node: sum(
				centrality.get(edge, 0)
				for edge in graph.edges(node)
			)
			for node in graph
		}


# Michelle Girvan
class EdgeBetweennessCentralityAgent(EdgeCentralityAgent):
	name = "Girvan"

	def centrality(self, graph):
		return nx.edge_betweenness_centrality(
			graph,
			weight="weight",
		)


# Ulrik Brandes
class EdgeBetweennessCentralitySubsetAgent(
	EdgeCentralityAgent
):
	name = "Brandes"

	def centrality(self, graph):
		return nx.edge_betweenness_centrality_subset(
			graph,
			sources=[Endpoint.SOURCE],
			targets=[Endpoint.TARGET],
			weight="weight",
		)


# Daniel Fleischer
class EdgeCurrentFlowBetweennessCentralityAgent(
	EdgeCentralityAgent
):
	name = "Fleischer"

	def centrality(self, graph):
		return nx.edge_current_flow_betweenness_centrality(
			graph,
		)


# Mark E. J. Newman
class EdgeCurrentFlowBetweennessCentralitySubsetAgent(
	EdgeCentralityAgent
):
	name = "Mark"

	def centrality(self, graph):
		nodes = list(graph)

		return nx.edge_current_flow_betweenness_centrality_subset(
			graph,
			sources=[Endpoint.SOURCE],
			targets=[Endpoint.TARGET],
		)


# Kwang-Il Goh
class EdgeLoadCentralityAgent(EdgeCentralityAgent):
	name = "Kwang-Il"

	def centrality(self, graph):
		return nx.edge_load_centrality(graph)

