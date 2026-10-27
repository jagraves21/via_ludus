from abc import ABC, abstractmethod

import networkx as nx

from ....player import (
	RandomMaxSelectorMixin,
	RandomMinSelectorMixin,
)

from ..utils import get_concrete_subclasses

from .graph_builder_mixins import (
	UndirectedPlayerGraphMixin,
	UndirectedPlayerGraphFilteredMixin,
	DirectedPlayerGraphMixin,
	DirectedPlayerGraphFilteredMixin,
	UndirectedMoveGraphMixin,
	DirectedMoveGraphMixin,
)

from .graph_utils import Endpoint
from .graph_agent import GraphAgent

# For these agents to qualify as deterministic scorers,
# any convergence-based algorithm must use a fixed,
# deterministic initialization.
#
# For example, eigenvector centrality implementations that
# depend on iterative convergence may not be deterministic.
class VertexCentralityAgent(GraphAgent, ABC):
	def graph_scores(self, graph):
		return self.vertex_centrality(graph)

	@abstractmethod
	def vertex_centrality(self, graph):
		pass


# Marvin E. Shaw
class DegreeCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedMoveGraphMixin,
	VertexCentralityAgent,
):
	name = "Shaw"

	def vertex_centrality(self, graph):
		return nx.degree_centrality(graph)


# Jan L. Anthonisse
class BetweennessCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedMoveGraphMixin,
	VertexCentralityAgent,
):
	name = "Anthonisse"

	def vertex_centrality(self, graph):
		return nx.betweenness_centrality(
			graph,
			weight="resistance",
		)


# Ulrik Brandes
class BetweennessCentralitySubsetAgent(
	RandomMaxSelectorMixin,
	UndirectedMoveGraphMixin,
	VertexCentralityAgent,
):
	name = "Brandes"

	def vertex_centrality(self, graph):
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
	VertexCentralityAgent,
):
	name = "Bavelas"

	def vertex_centrality(self, graph):
		return nx.closeness_centrality(
			graph,
			distance="resistance",
		)


# Edmund Landau
class EigenvectorCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedMoveGraphMixin,
	VertexCentralityAgent,
	ABC,
):
	name = "Landau"

	# this often does not converge and raise an exception
	# make abstract so it does not get registered
	@abstractmethod
	def vertex_centrality(self, graph):
		return nx.eigenvector_centrality(
			graph,
			weight="connection_strength",
		)


# Phillip Bonacich
class EigenvectorNumpyCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedMoveGraphMixin,
	VertexCentralityAgent,
):
	name = "Bonacich"

	def vertex_centrality(self, graph):
		return nx.eigenvector_centrality_numpy(
			graph,
			weight="connection_strength",
		)


# Leo Katz
class KatzCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedMoveGraphMixin,
	VertexCentralityAgent,
	ABC, 
):
	name = "Leo"

	def vertex_centrality(self, graph):
		return nx.katz_centrality(
			graph,
			weight="connection_strength",
		)


# Leo Katz
class KatzNumpyCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedMoveGraphMixin,
	VertexCentralityAgent,
):
	name = "Katz"

	def vertex_centrality(self, graph):
		return nx.katz_centrality_numpy(
			graph,
			weight="connection_strength",
		)


# Kwang-Il Goh
class LoadCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedMoveGraphMixin,
	VertexCentralityAgent,
):
	name = "Goh"

	def vertex_centrality(self, graph):
		return nx.load_centrality(
			graph,
			weight="resistance",
		)


# Mark E. J. Newman
class CurrentFlowBetweennessCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphFilteredMixin,
	VertexCentralityAgent,
):
	name = "Newman"

	def vertex_centrality(self, graph):
		return nx.current_flow_betweenness_centrality(
			graph,
			weight="connection_strength",
		)


# Enrico Bozzo
class ApproximateCurrentFlowBetweennessCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphFilteredMixin,
	VertexCentralityAgent,
):
	name = "Bozzo"

	def vertex_centrality(self, graph):
		return nx.approximate_current_flow_betweenness_centrality(
			graph,
			weight="connection_strength",
		)


# Daniel Fleischer
class CurrentFlowBetweennessCentralitySubsetAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphFilteredMixin,
	VertexCentralityAgent,
):
	name = "Fleischer"

	def vertex_centrality(self, graph):
		return nx.current_flow_betweenness_centrality_subset(
			graph,
			sources=[Endpoint.SOURCE],
			targets=[Endpoint.TARGET],
			weight="connection_strength",
		)


# Milan Zelen
class CurrentFlowClosenessCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedMoveGraphMixin,
	VertexCentralityAgent,
):
	name = "Zelen"

	def vertex_centrality(self, graph):
		return nx.current_flow_closeness_centrality(
			graph,
			weight="connection_strength",
		)


# Karen Stephenson
class InformationCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedMoveGraphMixin,
	VertexCentralityAgent,
):
	name = "Stephenson"

	def vertex_centrality(self, graph):
		return nx.information_centrality(
			graph,
			weight="connection_strength",
		)


# Desmond J. Higham
class CommunicabilityBetweennessCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedMoveGraphMixin,
	VertexCentralityAgent,
):
	name = "Higham"

	def vertex_centrality(self, graph):
		return nx.communicability_betweenness_centrality(
			graph,
		)


# Ernesto Estrada
class SubgraphCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedMoveGraphMixin,
	VertexCentralityAgent,
):
	name = "Estrada"

	def vertex_centrality(self, graph):
		return nx.subgraph_centrality(graph)


# Juan A. Rodriguez-Velazquez
class SubgraphCentralityExpAgent(
	RandomMaxSelectorMixin,
	UndirectedMoveGraphMixin,
	VertexCentralityAgent,
):
	name = "Rodriguez-Velazquez"

	def vertex_centrality(self, graph):
		return nx.subgraph_centrality_exp(graph)


# Massimo Marchiori
class HarmonicCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedMoveGraphMixin,
	VertexCentralityAgent,
):
	name = "Marchiori"

	def vertex_centrality(self, graph):
		return nx.harmonic_centrality(
			graph,
			distance="resistance",
		)


# Mahendra Piraveenan
class PercolationCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	VertexCentralityAgent,
):
	name = "Piraveenan"

	def vertex_centrality(self, graph):
		return nx.percolation_centrality(graph)


# Anne-Marie Kermarrec
class SecondOrderCentralityAgent(
	RandomMinSelectorMixin,
	UndirectedMoveGraphMixin,
	VertexCentralityAgent,
):
	name = "Kermarrec"

	@property
	def higher_is_better(self):
		return False

	def vertex_centrality(self, graph):
		return nx.second_order_centrality(
			graph,
			weight="traversal_cost",
		)


# Xingqin Qi
class LaplacianCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedMoveGraphMixin,
	VertexCentralityAgent,
):
	name = "Qi"

	def vertex_centrality(self, graph):
		return nx.laplacian_centrality(
			graph,
			normalized=True,
		)


VERTEX_CENTRALITY_AGENTS = get_concrete_subclasses(VertexCentralityAgent)

