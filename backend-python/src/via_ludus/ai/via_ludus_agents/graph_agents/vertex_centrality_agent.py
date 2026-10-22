from abc import ABC, abstractmethod
import inspect

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
	UndirectedPlayerGraphMixin,
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
	UndirectedPlayerGraphMixin,
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
	UndirectedPlayerGraphMixin,
	VertexCentralityAgent,
):
	name = "Landau"

	def vertex_centrality(self, graph):
		return nx.eigenvector_centrality(
			graph,
			weight="connection_strength",
		)


# Phillip Bonacich
class EigenvectorNumpyCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	VertexCentralityAgent,
):
	name = "Bonacich"

	def vertex_centrality(self, graph):
		return nx.eigenvector_centrality_numpy(
			graph,
			weight="connection_strength",
		)


# Phillip Bonacich
class KatzCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	VertexCentralityAgent,
):
	name = "Katz"

	def vertex_centrality(self, graph):
		return nx.katz_centrality(
			graph,
			weight="connection_strength",
		)


# Leo Katz
class KatzNumpyCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	VertexCentralityAgent,
):
	name = "Leo"

	def vertex_centrality(self, graph):
		return nx.katz_centrality_numpy(
			graph,
			weight="connection_strength",
		)


# Kwang-Il Goh
class LoadCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
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
	UndirectedPlayerGraphMixin,
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
	UndirectedPlayerGraphMixin,
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
	UndirectedPlayerGraphMixin,
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
	UndirectedPlayerGraphMixin,
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
	UndirectedPlayerGraphMixin,
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
	UndirectedPlayerGraphMixin,
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
	UndirectedPlayerGraphMixin,
	VertexCentralityAgent,
):
	name = "Estrada"

	def vertex_centrality(self, graph):
		return nx.subgraph_centrality(graph)


# Juan A. Rodriguez-Velazquez
class SubgraphCentralityExpAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	VertexCentralityAgent,
):
	name = "Rodriguez-Velazquez"

	def vertex_centrality(self, graph):
		return nx.subgraph_centrality_exp(graph)


# Massimo Marchiori
class HarmonicCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
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
	UndirectedPlayerGraphMixin,
	VertexCentralityAgent,
):
	name = "Kermarrec"

	@property
	def higher_is_better(self):
		return False

	def vertex_centrality(self, graph):
		return nx.second_order_centrality(
			graph,
			weight="connection_strength",
		)


# Xingqin Qi
class LaplacianCentralityAgent(
	RandomMaxSelectorMixin,
	UndirectedPlayerGraphMixin,
	VertexCentralityAgent,
):
	name = "Qi"

	def vertex_centrality(self, graph):
		return nx.laplacian_centrality(
			graph,
			normalized=True,
		)


VERTEX_CENTRALITY_AGENTS = {
	agent.get_agent_name(): agent
	for agent in VertexCentralityAgent.__subclasses__()
	if not inspect.isabstract(agent)
}
