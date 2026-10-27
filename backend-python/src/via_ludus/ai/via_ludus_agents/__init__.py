import warnings

from ...utils.optional_dependencies import OptionalDependencyError

from .random_agent import RandomAgent
from .shortest_path_agent import ShortestPathAgent


VIA_LUDUS_AGENTS = {
	RandomAgent.get_agent_name(): RandomAgent,
	ShortestPathAgent.get_agent_name(): ShortestPathAgent,
}

__all__ = [
	"RandomAgent",
	"ShortestPathAgent",
	"VIA_LUDUS_AGENTS",
]


try:
	from . import graph_agents
	from .graph_agents import (
		OffensiveDistanceAgent,
		DefensiveDistanceAgent,
		CombinedDistanceAgent,
		OffensivePathsAgent,
		DefensivePathsAgent,
		CombinedPathsAgent,
		OffensiveCutAgent,
		DefensiveCutAgent,
		OffensiveOverlapCutAgent,
		DefensiveOverlapCutAgent,
		DegreeCentralityAgent,
		BetweennessCentralityAgent,
		BetweennessCentralitySubsetAgent,
		ClosenessCentralityAgent,
		EigenvectorCentralityAgent,
		EigenvectorNumpyCentralityAgent,
		KatzCentralityAgent,
		KatzNumpyCentralityAgent,
		LoadCentralityAgent,
		CurrentFlowBetweennessCentralityAgent,
		ApproximateCurrentFlowBetweennessCentralityAgent,
		CurrentFlowBetweennessCentralitySubsetAgent,
		CurrentFlowClosenessCentralityAgent,
		InformationCentralityAgent,
		CommunicabilityBetweennessCentralityAgent,
		SubgraphCentralityAgent,
		SubgraphCentralityExpAgent,
		HarmonicCentralityAgent,
		PercolationCentralityAgent,
		SecondOrderCentralityAgent,
		LaplacianCentralityAgent,
		EdgeBetweennessCentralityAgent,
		EdgeBetweennessCentralitySubsetAgent,
		EdgeCurrentFlowBetweennessCentralityAgent,
		EdgeCurrentFlowBetweennessCentralitySubsetAgent,
		EdgeLoadCentralityAgent,
		GRAPH_AGENTS,
		DISTANCE_AGENTS,
		PATH_AGENTS,
		VERTEX_CUT_AGENTS,
		VERTEX_CENTRALITY_AGENTS,
		EDGE_CENTRALITY_AGENTS,
	)

except OptionalDependencyError as exc:
	warnings.warn(
		f"{exc} Graph agents will not be registered.",
		UserWarning,
		stacklevel=2,
	)

else:
	VIA_LUDUS_AGENTS.update(GRAPH_AGENTS)

	__all__ += [
		"OffensiveDistanceAgent",
		"DefensiveDistanceAgent",
		"CombinedDistanceAgent",
		"OffensivePathsAgent",
		"DefensivePathsAgent",
		"CombinedPathsAgent",
		"OffensiveCutAgent",
		"DefensiveCutAgent",
		"OffensiveOverlapCutAgent",
		"DefensiveOverlapCutAgent",
		"DegreeCentralityAgent",
		"BetweennessCentralityAgent",
		"BetweennessCentralitySubsetAgent",
		"ClosenessCentralityAgent",
		"EigenvectorCentralityAgent",
		"EigenvectorNumpyCentralityAgent",
		"KatzCentralityAgent",
		"KatzNumpyCentralityAgent",
		"LoadCentralityAgent",
		"CurrentFlowBetweennessCentralityAgent",
		"ApproximateCurrentFlowBetweennessCentralityAgent",
		"CurrentFlowBetweennessCentralitySubsetAgent",
		"CurrentFlowClosenessCentralityAgent",
		"InformationCentralityAgent",
		"CommunicabilityBetweennessCentralityAgent",
		"SubgraphCentralityAgent",
		"SubgraphCentralityExpAgent",
		"HarmonicCentralityAgent",
		"PercolationCentralityAgent",
		"SecondOrderCentralityAgent",
		"LaplacianCentralityAgent",
		"EdgeBetweennessCentralityAgent",
		"EdgeBetweennessCentralitySubsetAgent",
		"EdgeCurrentFlowBetweennessCentralityAgent",
		"EdgeCurrentFlowBetweennessCentralitySubsetAgent",
		"EdgeLoadCentralityAgent",
		"GRAPH_AGENTS",
		"DISTANCE_AGENTS",
		"PATH_AGENTS",
		"VERTEX_CUT_AGENTS",
		"VERTEX_CENTRALITY_AGENTS",
		"EDGE_CENTRALITY_AGENTS",
	]

