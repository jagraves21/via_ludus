from .agent import (
	AgentBase,
	Agent,
	ScoringAgent,
)

from . import via_ludus_agents
from .via_ludus_agents import (
	VIA_LUDUS_AGENTS,
	GRAPH_AGENTS,
	VERTEX_CUT_AGENTS,
	VERTEX_CENTRALITY_AGENTS,
	EDGE_CENTRALITY_AGENTS,
)

AI_AGENTS = AgentBase.get_agents()


__all__ = [
	"AgentBase",
	"Agent",
	"ScoringAgent",

	"AI_AGENTS",
	"VIA_LUDUS_AGENTS",
	"GRAPH_AGENTS",
	"VERTEX_CUT_AGENTS",
	"VERTEX_CENTRALITY_AGENTS",
	"EDGE_CENTRALITY_AGENTS",
]

