from abc import ABC, abstractmethod

from .graph_agent import GraphAgent


class CentralityAgent(GraphAgent, ABC):
	@abstractmethod
	def centrality(self, graph):
		pass

	def graph_scores(self, graph):
		return self.centrality(graph)

	def move_scores_from_graph_scores(self, graph, scores):
		return self.move_scores_from_centrality(graph, scores)

	def move_scores_from_centrality(self, graph, centrality):
		return centrality

