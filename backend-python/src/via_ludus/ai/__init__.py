from . import graphs

from .random_agent import RandomAgent

from .undergrad import Undergrad

from .cut_agent import (
	OffensiveCutAgent,
	DefensiveCutAgent,
	OffensiveOverlapCutAgent,
	DefensiveOverlapCutAgent,
)

from .monte_carlo_agent import (
	MonteCarloAgent,
	FastMonteCarloAgent,
)

from .node_centrality_agent import (
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
)

from .edge_centrality_agent import (
	EdgeBetweennessCentralityAgent,
	EdgeBetweennessCentralitySubsetAgent,
	EdgeCurrentFlowBetweennessCentralityAgent,
	EdgeCurrentFlowBetweennessCentralitySubsetAgent,
	EdgeLoadCentralityAgent,
)


all_agents = {
	agent.get_agent_name(): agent
	for agent in (
		RandomAgent,

		Undergrad,

		OffensiveCutAgent,
		DefensiveCutAgent,
		OffensiveOverlapCutAgent,
		DefensiveOverlapCutAgent,

		MonteCarloAgent,
		#FastMonteCarloAgent,

		DegreeCentralityAgent,
		BetweennessCentralityAgent,
		BetweennessCentralitySubsetAgent,
		ClosenessCentralityAgent,
		#EigenvectorCentralityAgent,
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
	)
}

ordered_agents = {
	agent.get_agent_name(): agent
	for agent in (
		RandomAgent,
		SubgraphCentralityAgent,
		SubgraphCentralityExpAgent,
		EigenvectorNumpyCentralityAgent,
		EdgeBetweennessCentralitySubsetAgent,
		EdgeBetweennessCentralityAgent,
		LaplacianCentralityAgent,
		KatzCentralityAgent,
		DegreeCentralityAgent,
		KatzNumpyCentralityAgent,
		HarmonicCentralityAgent,
		ClosenessCentralityAgent,
		InformationCentralityAgent,
		SecondOrderCentralityAgent,
		CurrentFlowClosenessCentralityAgent,
		CommunicabilityBetweennessCentralityAgent,
		PercolationCentralityAgent,
		LoadCentralityAgent,
		BetweennessCentralityAgent,
		ApproximateCurrentFlowBetweennessCentralityAgent,
		EdgeLoadCentralityAgent,
		CurrentFlowBetweennessCentralityAgent,
		OffensiveCutAgent,
		EdgeCurrentFlowBetweennessCentralityAgent,
		DefensiveCutAgent,
		Undergrad,
		DefensiveOverlapCutAgent,
		OffensiveOverlapCutAgent,
		EdgeCurrentFlowBetweennessCentralitySubsetAgent,
	)
}

agents = ordered_agents


__all__ = [
	"graphs",

	"RandomAgent",
	"CutAgent",

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

	"agents",
]

