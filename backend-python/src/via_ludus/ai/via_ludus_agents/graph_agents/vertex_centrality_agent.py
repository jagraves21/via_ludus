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
	UndirectedMoveGraphMixin,
	UndirectedOpponentMoveGraphMixin,
	DirectedOpponentMoveGraphMixin,
	DirectedOpponentPlayerGraphMixin,
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
	DirectedOpponentMoveGraphMixin,
	RandomMaxSelectorMixin,
	VertexCentralityAgent,
):
	name = "Shaw"

	def vertex_centrality(self, graph):
		return nx.degree_centrality(graph)


# Jan L. Anthonisse
class BetweennessCentralityAgent(
	UndirectedMoveGraphMixin,
	RandomMaxSelectorMixin,
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
	UndirectedOpponentMoveGraphMixin,
	RandomMaxSelectorMixin,
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
	DirectedOpponentPlayerGraphMixin,
	RandomMaxSelectorMixin,
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
	DirectedOpponentMoveGraphMixin,
	RandomMaxSelectorMixin,
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
	DirectedOpponentMoveGraphMixin,
	RandomMaxSelectorMixin,
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

	# sometimes this does not converge and raise an exception
	# make abstract so it does not get registered
	@abstractmethod
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
	UndirectedMoveGraphMixin,
	RandomMaxSelectorMixin,
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
	UndirectedOpponentMoveGraphMixin,
	RandomMaxSelectorMixin,
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
	UndirectedOpponentMoveGraphMixin,
	RandomMaxSelectorMixin,
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
	UndirectedOpponentMoveGraphMixin,
	RandomMaxSelectorMixin,
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
	UndirectedOpponentMoveGraphMixin,
	RandomMaxSelectorMixin,
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
	UndirectedOpponentMoveGraphMixin,
	RandomMaxSelectorMixin,
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
	UndirectedOpponentMoveGraphMixin,
	RandomMaxSelectorMixin,
	VertexCentralityAgent,
):
	name = "Higham"

	def vertex_centrality(self, graph):
		return nx.communicability_betweenness_centrality(
			graph,
		)


# Ernesto Estrada
class SubgraphCentralityAgent(
	UndirectedOpponentMoveGraphMixin,
	RandomMaxSelectorMixin,
	VertexCentralityAgent,
):
	name = "Estrada"

	def vertex_centrality(self, graph):
		return nx.subgraph_centrality(graph)


# Juan A. Rodriguez-Velazquez
class SubgraphCentralityExpAgent(
	UndirectedOpponentMoveGraphMixin,
	RandomMaxSelectorMixin,
	VertexCentralityAgent,
):
	name = "Rodriguez-Velazquez"

	def vertex_centrality(self, graph):
		return nx.subgraph_centrality_exp(graph)


# Massimo Marchiori
class HarmonicCentralityAgent(
	DirectedOpponentPlayerGraphMixin,
	RandomMaxSelectorMixin,
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
	UndirectedOpponentMoveGraphMixin,
	RandomMaxSelectorMixin,
	VertexCentralityAgent,
):
	name = "Piraveenan"

	def vertex_centrality(self, graph):
		return nx.percolation_centrality(graph)


# Anne-Marie Kermarrec
class SecondOrderCentralityAgent(
	UndirectedOpponentMoveGraphMixin,
	RandomMinSelectorMixin,
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
	UndirectedOpponentMoveGraphMixin,
	RandomMaxSelectorMixin,
	VertexCentralityAgent,
):
	name = "Qi"

	def vertex_centrality(self, graph):
		return nx.laplacian_centrality(
			graph,
			normalized=True,
		)


VERTEX_CENTRALITY_AGENTS = get_concrete_subclasses(VertexCentralityAgent)

