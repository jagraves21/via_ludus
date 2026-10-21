from abc import ABC, abstractmethod

import networkx as nx

from ....player import (
	RandomMaxSelectorMixin,
	RandomMinSelectorMixin,
)

from .graph_builder_mixins import (
	UndirectedPlayerGraphMixin,
	UndirectedMoveGraphMixin,
)

from .graph_utils import Endpoint
from .graph_agent import GraphAgent


class NodeCentralityAgent(GraphAgent, ABC):
	def graph_scores(self, graph):
		return self.node_centrality(graph)

	@abstractmethod
	def node_centrality(self, graph):
		pass


# Marvin E. Shaw
class DegreeCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedMoveGraphMixin,
	NodeCentralityAgent,
):
	name = "Shaw"

	def node_centrality(self, graph):
		return nx.degree_centrality(graph)


# Jan L. Anthonisse
class BetweennessCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	NodeCentralityAgent,
):
	name = "Anthonisse"

	def node_centrality(self, graph):
		return nx.betweenness_centrality(
			graph,
			weight="resistance",
		)


# Ulrik Brandes
class BetweennessCentralitySubsetAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	NodeCentralityAgent,
):
	name = "Brandes"

	def node_centrality(self, graph):
		return nx.betweenness_centrality_subset(
			graph,
			sources=[Endpoint.SOURCE],
			targets=[Endpoint.TARGET],
			weight="resistance",
		)


# Alex Bavelas
class ClosenessCentralityAgent(
	RandomMinSelectorMixin,
	UndirectedPlayerGraphMixin,
	NodeCentralityAgent,
):
	name = "Bavelas"

	def node_centrality(self, graph):
		return nx.closeness_centrality(
			graph,
			distance="resistance",
		)


# Edmund Landau
class EigenvectorCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	NodeCentralityAgent,
):
	name = "Landau"

	def node_centrality(self, graph):
		return nx.eigenvector_centrality(
			graph,
			weight="connection_strength",
		)


# Phillip Bonacich
class EigenvectorNumpyCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	NodeCentralityAgent,
):
	name = "Bonacich"

	def node_centrality(self, graph):
		return nx.eigenvector_centrality_numpy(
			graph,
			weight="connection_strength",
		)


# Phillip Bonacich
class KatzCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	NodeCentralityAgent,
):
	name = "Katz"

	def node_centrality(self, graph):
		return nx.katz_centrality(
			graph,
			weight="connection_strength",
		)


# Leo Katz
class KatzNumpyCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	NodeCentralityAgent,
):
	name = "Leo"

	def node_centrality(self, graph):
		return nx.katz_centrality_numpy(
			graph,
			weight="connection_strength",
		)


# Kwang-Il Goh
class LoadCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	NodeCentralityAgent,
):
	name = "Goh"

	def node_centrality(self, graph):
		return nx.load_centrality(
			graph,
			weight="resistance",
		)


# Mark E. J. Newman
class CurrentFlowBetweennessCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	NodeCentralityAgent,
):
	name = "Newman"

	def node_centrality(self, graph):
		return nx.current_flow_betweenness_centrality(
			graph,
			weight="connection_strength",
		)


# Enrico Bozzo
class ApproximateCurrentFlowBetweennessCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	NodeCentralityAgent,
):
	name = "Bozzo"

	def node_centrality(self, graph):
		return nx.approximate_current_flow_betweenness_centrality(
			graph,
			weight="connection_strength",
		)


# Daniel Fleischer
class CurrentFlowBetweennessCentralitySubsetAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	NodeCentralityAgent,
):
	name = "Fleischer"

	def node_centrality(self, graph):
		return nx.current_flow_betweenness_centrality_subset(
			graph,
			sources=[Endpoint.SOURCE],
			targets=[Endpoint.TARGET],
			weight="connection_strength",
		)


# Milan Zelen
class CurrentFlowClosenessCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	NodeCentralityAgent,
):
	name = "Zelen"

	def node_centrality(self, graph):
		return nx.current_flow_closeness_centrality(
			graph,
			weight="connection_strength",
		)


# Karen Stephenson
class InformationCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	NodeCentralityAgent,
):
	name = "Stephenson"

	def node_centrality(self, graph):
		return nx.information_centrality(
			graph,
			weight="connection_strength",
		)


# Desmond J. Higham
class CommunicabilityBetweennessCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	NodeCentralityAgent,
):
	name = "Higham"

	def node_centrality(self, graph):
		return nx.communicability_betweenness_centrality(
			graph,
		)


# Ernesto Estrada
class SubgraphCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	NodeCentralityAgent,
):
	name = "Estrada"

	def node_centrality(self, graph):
		return nx.subgraph_centrality(graph)


# Juan A. Rodriguez-Velazquez
class SubgraphCentralityExpAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	NodeCentralityAgent,
):
	name = "Rodriguez-Velazquez"

	def node_centrality(self, graph):
		return nx.subgraph_centrality_exp(graph)


# Massimo Marchiori
class HarmonicCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	NodeCentralityAgent,
):
	name = "Marchiori"

	def node_centrality(self, graph):
		return nx.harmonic_centrality(
			graph,
			distance="resistance",
		)


# Mahendra Piraveenan
class PercolationCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	NodeCentralityAgent,
):
	name = "Piraveenan"

	def node_centrality(self, graph):
		return nx.percolation_centrality(graph)


# Anne-Marie Kermarrec
class SecondOrderCentralityAgent(
	RandomMinSelectorMixin,
	UndirectedPlayerGraphMixin,
	NodeCentralityAgent,
):
	name = "Kermarrec"

	@property
	def higher_is_better(self):
		return False

	def node_centrality(self, graph):
		return nx.second_order_centrality(
			graph,
			weight="connection_strength",
		)


# Xingqin Qi
class LaplacianCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	NodeCentralityAgent,
):
	name = "Qi"

	def node_centrality(self, graph):
		return nx.laplacian_centrality(
			graph,
			normalized=True,
		)

