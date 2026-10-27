
from .agent import (
	AgentBase,
	Agent,
	ScoringAgent,
)

from . import via_ludus_agents
from .via_ludus_agents import VIA_LUDUS_AGENTS


__all__ = [
	"AgentBase",
	"Agent",
	"ScoringAgent",
	
	"AI_AGENTS",
	
	"VIA_LUDUS_AGENTS",
]


_GRAPH_REGISTRIES = (
	"GRAPH_AGENTS",
	"DISTANCE_AGENTS",
	"PATH_AGENTS",
	"VERTEX_CUT_AGENTS",
	"VERTEX_CENTRALITY_AGENTS",
	"EDGE_CENTRALITY_AGENTS",
)

for name in _GRAPH_REGISTRIES:
	if hasattr(via_ludus_agents, name):
		globals()[name] = getattr(via_ludus_agents, name)
		__all__.append(name)

AI_AGENTS = AgentBase.get_agents()
__all__.append("AI_AGENTS")

