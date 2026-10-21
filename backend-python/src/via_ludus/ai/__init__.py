from .agent import (
	AgentBase,
	Agent,
	ScoringAgent,
)

from .via_ludus_agents import (
	RandomAgent,
	Undergrad,
	DegreeCentralityAgent,
)

agents = AgentBase.get_agents()


__all__ = [
	"AgentBase",
	"Agent",
	"ScoringAgent",

	"RandomAgent",
	"Undergrad",
	"DegreeCentralityAgent",

	"agents",
]

