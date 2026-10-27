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

agent_order = [
	"Mark", "Menger", "Whitney", "Bellman-Moore", "Fleischer",
	"Newman", "Moore", "Piraveenan", "Ford", "Bozzo", "Brandes",
	"Bellman", "Ulrik", "Dijkstra", "Roy", "Fulkerson", "Daniel",
	"Floyd", "Anthonisse", "Goh", "Kwang-Il", "Girvan", "Kermarrec",
	"Zelen", "Stephenson", "Higham", "Marchiori", "Shaw", "Qi",
	"Warshall", "Katz", "Rodriguez-Velazquez", "Estrada",
	"Bonacich", "Bavelas", "Random",
]

AI_AGENTS = {
	name: AI_AGENTS[name]
	for name in agent_order
	if name in AI_AGENTS
}

