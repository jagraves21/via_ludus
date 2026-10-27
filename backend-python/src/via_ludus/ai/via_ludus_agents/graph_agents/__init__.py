from importlib import import_module

from ....utils.optional_dependencies import OptionalDependencyError


try:
	import_module("networkx")
except ModuleNotFoundError as exc:
	if exc.name != "networkx":
		raise

	raise OptionalDependencyError(
		"The graph_agents package requires NetworkX. "
		'Install it with `pip install -e ".[graph-agents]"` '
		"from the repository root."
	) from exc


from .graph_builder_mixins import (
	UndirectedPlayerGraphMixin,
	UndirectedPlayerGraphFilteredMixin,
	UndirectedOpponentPlayerGraphMixin,
	UndirectedOpponentPlayerGraphFilteredMixin,
	UndirectedMoveGraphMixin,
	UndirectedOpponentMoveGraphMixin,
	DirectedPlayerGraphMixin,
	DirectedPlayerGraphFilteredMixin,
	DirectedOpponentPlayerGraphMixin,
	DirectedOpponentPlayerGraphFilteredMixin,
	DirectedMoveGraphMixin,
	DirectedOpponentMoveGraphMixin,
	UndirectedPlayerGraphPairMixin,
	UndirectedPlayerGraphFilteredPairMixin,
	UndirectedMoveGraphPairMixin,
	DirectedPlayerGraphPairMixin,
	DirectedPlayerGraphFilteredPairMixin,
	DirectedMoveGraphPairMixin,
	UndirectedOpponentPlayerGraphPairMixin,
	UndirectedOpponentPlayerGraphFilteredPairMixin,
	UndirectedOpponentMoveGraphPairMixin,
	DirectedOpponentPlayerGraphPairMixin,
	DirectedOpponentPlayerGraphFilteredPairMixin,
	DirectedOpponentMoveGraphPairMixin,
)

from .graph_agent import GraphAgent

from .distance_agent import (
	OffensiveDistanceAgent,
	DefensiveDistanceAgent,
	CombinedDistanceAgent,
	DISTANCE_AGENTS,
)

from .paths_agent import (
	OffensivePathsAgent,
	DefensivePathsAgent,
	CombinedPathsAgent,
	PATH_AGENTS,
)

from .vertex_cut_agent import (
	OffensiveCutAgent,
	DefensiveCutAgent,
	OffensiveOverlapCutAgent,
	DefensiveOverlapCutAgent,
	VERTEX_CUT_AGENTS,
)

from .vertex_centrality_agent import (
	VertexCentralityAgent,
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
	VERTEX_CENTRALITY_AGENTS,
)

from .edge_centrality_agent import (
	EdgeCentralityAgent,
	EdgeBetweennessCentralityAgent,
	EdgeBetweennessCentralitySubsetAgent,
	EdgeCurrentFlowBetweennessCentralityAgent,
	EdgeCurrentFlowBetweennessCentralitySubsetAgent,
	EdgeLoadCentralityAgent,
	EDGE_CENTRALITY_AGENTS,
)

GRAPH_AGENTS = {
	**DISTANCE_AGENTS,
	**PATH_AGENTS,
	**VERTEX_CUT_AGENTS,
	**VERTEX_CENTRALITY_AGENTS,
	**EDGE_CENTRALITY_AGENTS,
}


__all__ = [
	"UndirectedPlayerGraphMixin",
	"UndirectedPlayerGraphFilteredMixin",
	"UndirectedOpponentPlayerGraphMixin",
	"UndirectedOpponentPlayerGraphFilteredMixin",
	"UndirectedMoveGraphMixin",
	"UndirectedOpponentMoveGraphMixin",
	"DirectedPlayerGraphMixin",
	"DirectedPlayerGraphFilteredMixin",
	"DirectedOpponentPlayerGraphMixin",
	"DirectedOpponentPlayerGraphFilteredMixin",
	"DirectedMoveGraphMixin",
	"DirectedOpponentMoveGraphMixin",
	"UndirectedPlayerGraphPairMixin",
	"UndirectedPlayerGraphFilteredPairMixin",
	"UndirectedMoveGraphPairMixin",
	"DirectedPlayerGraphPairMixin",
	"DirectedPlayerGraphFilteredPairMixin",
	"DirectedMoveGraphPairMixin",
	"UndirectedOpponentPlayerGraphPairMixin",
	"UndirectedOpponentPlayerGraphFilteredPairMixin",
	"UndirectedOpponentMoveGraphPairMixin",
	"DirectedOpponentPlayerGraphPairMixin",
	"DirectedOpponentPlayerGraphFilteredPairMixin",
	"DirectedOpponentMoveGraphPairMixin",

	"GraphAgent",
	
	"OffensiveDistanceAgent",
	"DefensiveDistanceAgent",
	"CombinedDistanceAgent",
	"DISTANCE_AGENTS",
	
	"OffensivePathsAgent",
	"DefensivePathsAgent",
	"CombinedPathsAgent",

	"OffensiveCutAgent",
	"DefensiveCutAgent",
	"OffensiveOverlapCutAgent",
	"DefensiveOverlapCutAgent",

	"VertexCentralityAgent",
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

	"EdgeCentralityAgent",
	"EdgeBetweennessCentralityAgent",
	"EdgeBetweennessCentralitySubsetAgent",
	"EdgeCurrentFlowBetweennessCentralityAgent",
	"EdgeCurrentFlowBetweennessCentralitySubsetAgent",
	"EdgeLoadCentralityAgent",
	
	"GRAPH_AGENTS",
	"PATH_AGENTS",
	"VERTEX_CUT_AGENTS",
	"VERTEX_CENTRALITY_AGENTS",
	"EDGE_CENTRALITY_AGENTS",
]

