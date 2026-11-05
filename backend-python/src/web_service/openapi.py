API_VERSION = "0.1.0"

API_DESCRIPTION = """
Via Ludus is a strategy game in which two players compete to connect
opposite sides of a board.

The API provides access to the game's AI agents.

## Available functionality

- Discover the AI agents available in the current installation.
- Request a move from a selected AI agent.

## Agent discovery

Use `GET /api/agents` to retrieve the names of the available agents.

The available agents are determined by the backend installation and
may vary between deployments.

## Move selection

Use `POST /api/agents/{agent_name}/move` to request a move from an
available agent.

The request includes the board dimensions, board contents, and the
agent's player color.
"""

OPENAPI_TAGS = [
	{
		"name": "Agents",
		"description": (
			"Discover available AI agents and request moves "
			"from a selected agent."
		),
	},
]

