from abc import ABC, abstractmethod
import inspect

from ....player import (
	DeterministicScoringMixin,
	RandomMaxSelectorMixin,
)

from .graph_utils import minimum_endpoint_cut
from .graph_builder_mixins import (
	UndirectedOpponentMoveGraphMixin,
	UndirectedMoveGraphMixin,
	UndirectedMoveGraphPairMixin,
	UndirectedOpponentMoveGraphPairMixin,
)
from .graph_agent import GraphAgent


class VertexCutAgent(
	#DeterministicScoringMixin, # verify the cut code first
	RandomMaxSelectorMixin,
	GraphAgent,
	ABC,
):
	@abstractmethod
	def _get_cut(self, graph):
		pass

	@abstractmethod
	def _score_cut(self, cut):
		pass

	def graph_scores(self, graph):
		cut = self._get_cut(graph)
		return self._score_cut(cut)


class SingleCutAgent(VertexCutAgent):
	def _get_cut(self, graph):
		return minimum_endpoint_cut(graph)

	def _score_cut(self, cut):
		return {
			move: 0
			for move in cut
		}


# Delbert Ray Fulkerson
class OffensiveCutAgent(
	UndirectedOpponentMoveGraphMixin,
	SingleCutAgent,
):
	name = "Fulkerson"


# Lester Randolph Ford Jr.
class DefensiveCutAgent(
	UndirectedMoveGraphMixin,
	SingleCutAgent,
):
	name = "Ford"


class DoubleCutAgent(VertexCutAgent):
	def _get_cut(self, graphs):
		return tuple(
			minimum_endpoint_cut(graph)
			for graph in graphs
		)

	def _score_cut(self, cut):
		candidate_cut, reference_cut = cut
		return {
			move: int(move in reference_cut)
			for move in candidate_cut
		}


# Karl Menger
class OffensiveOverlapCutAgent(
	UndirectedOpponentMoveGraphPairMixin,
	DoubleCutAgent,
):
	name = "Menger"


# Hassler Whitney
class DefensiveOverlapCutAgent(
	UndirectedMoveGraphPairMixin,
	DoubleCutAgent,
):
	name = "Whitney"


VERTEX_CUT_AGENTS = {
	agent.get_agent_name(): agent
	for agent in VertexCutAgent.__subclasses__()
	if not inspect.isabstract(agent)
}

