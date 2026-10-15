import networkx as nx

from .graphs import (
	Endpoint,
	board_to_move_graph,
)

from .centrality_agent import CentralityAgent


class NodeCentralityAgent(CentralityAgent):
	@property
	def graph_builder(self):
		return board_to_move_graph


# Marvin E. Shaw
class DegreeCentralityAgent(NodeCentralityAgent):
	name = "Shaw"

	def centrality(self, graph):
		return nx.degree_centrality(graph)


# Jan L. Anthonisse
class BetweennessCentralityAgent(NodeCentralityAgent):
	name = "Anthonisse"

	def centrality(self, graph):
		return nx.betweenness_centrality(
			graph,
			weight="cost",
		)


# Ulrik Brandes
class BetweennessCentralitySubsetAgent(NodeCentralityAgent):
	name = "Brandes"

	def centrality(self, graph):
		return nx.betweenness_centrality_subset(
			graph,
			sources=[Endpoint.SOURCE],
			targets=[Endpoint.TARGET],
			weight="cost",
		)


# Alex Bavelas
class ClosenessCentralityAgent(NodeCentralityAgent):
	name = "Bavelas"

	def centrality(self, graph):
		return nx.closeness_centrality(
			graph,
			distance="cost",
		)


# Edmund Landau
class EigenvectorCentralityAgent(NodeCentralityAgent):
	name = "Landau"

	def centrality(self, graph):
		return nx.eigenvector_centrality(
			graph,
			weight="strength",
		)


# Phillip Bonacich
class EigenvectorNumpyCentralityAgent(NodeCentralityAgent):
	name = "Bonacich"

	def centrality(self, graph):
		return nx.eigenvector_centrality_numpy(
			graph,
			weight="strength",
		)


# Leo Katz
class KatzCentralityAgent(NodeCentralityAgent):
	name = "Katz"

	def centrality(self, graph):
		return nx.katz_centrality(
			graph,
			weight="strength",
		)


# Leo Katz
class KatzNumpyCentralityAgent(NodeCentralityAgent):
	name = "Leo"

	def centrality(self, graph):
		return nx.katz_centrality_numpy(
			graph,
			weight="strength",
		)


# Kwang-Il Goh
class LoadCentralityAgent(NodeCentralityAgent):
	name = "Goh"

	def centrality(self, graph):
		return nx.load_centrality(
			graph,
			weight="cost",
		)


# Mark E. J. Newman
class CurrentFlowBetweennessCentralityAgent(NodeCentralityAgent):
	name = "Newman"

	def centrality(self, graph):
		return nx.current_flow_betweenness_centrality(
			graph,
			weight="cost",
		)


# Enrico Bozzo
class ApproximateCurrentFlowBetweennessCentralityAgent(
	NodeCentralityAgent
):
	name = "Bozzo"

	def centrality(self, graph):
		return nx.approximate_current_flow_betweenness_centrality(
			graph,
		)


# Daniel Fleischer
class CurrentFlowBetweennessCentralitySubsetAgent(
	NodeCentralityAgent
):
	name = "Fleischer"

	def centrality(self, graph):
		return nx.current_flow_betweenness_centrality_subset(
			graph,
			sources=[Endpoint.SOURCE],
			targets=[Endpoint.TARGET],
			weight="cost",
		)


# Milan Zelen
class CurrentFlowClosenessCentralityAgent(NodeCentralityAgent):
	name = "Zelen"

	def centrality(self, graph):
		return nx.current_flow_closeness_centrality(
			graph,
			weight="cost",
		)


# Karen Stephenson
class InformationCentralityAgent(NodeCentralityAgent):
	name = "Stephenson"

	def centrality(self, graph):
		return nx.information_centrality(
			graph,
			weight="cost",
		)


# Desmond J. Higham
class CommunicabilityBetweennessCentralityAgent(
	NodeCentralityAgent
):
	name = "Higham"

	def centrality(self, graph):
		return nx.communicability_betweenness_centrality(
			graph,
		)


# Ernesto Estrada
class SubgraphCentralityAgent(NodeCentralityAgent):
	name = "Estrada"

	def centrality(self, graph):
		return nx.subgraph_centrality(graph)


# Juan A. Rodriguez-Velazquez
class SubgraphCentralityExpAgent(NodeCentralityAgent):
	name = "Rodriguez-Velazquez"

	def centrality(self, graph):
		return nx.subgraph_centrality_exp(graph)


# Massimo Marchiori
class HarmonicCentralityAgent(NodeCentralityAgent):
	name = "Marchiori"

	def centrality(self, graph):
		return nx.harmonic_centrality(
			graph,
			distance="cost",
		)


# Mahendra Piraveenan
class PercolationCentralityAgent(NodeCentralityAgent):
	name = "Piraveenan"

	def centrality(self, graph):
		return nx.percolation_centrality(graph)


# Anne-Marie Kermarrec
class SecondOrderCentralityAgent(NodeCentralityAgent):
	name = "Kermarrec"

	@property
	def higher_is_better(self):
		return False

	def centrality(self, graph):
		return nx.second_order_centrality(
			graph,
			weight="cost",
		)


# Xingqin Qi
class LaplacianCentralityAgent(NodeCentralityAgent):
	name = "Qi"

	def centrality(self, graph):
		return nx.laplacian_centrality(
			graph,
			normalized=True,
		)

