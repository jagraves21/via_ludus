from via_ludus import (
	PlayerColor,
	SearchBoard as ViaLudusBoard,
	AI_AGENTS,
)

from ..exceptions import AgentComputationError


def get_agents() -> list[str]:
	return list(AI_AGENTS)


def get_move(
	agent_name,
	rows,
	cols,
	board,
	color,
):
	serialized = f"{rows},{cols},{board}"

	try:
		board = ViaLudusBoard.deserialize(serialized)
	except ValueError as exc:
		raise ValueError(
			f"Invalid board: {exc}"
		) from exc

	try:
		agent_class = AI_AGENTS[agent_name]
	except KeyError as exc:
		available_agents = ", ".join(AI_AGENTS)
		raise KeyError(
			f"Agent '{agent_name}' not found. "
			f"Available agents: {available_agents}."
		) from exc

	try:
		player_color = PlayerColor(color)
	except ValueError as exc:
		raise ValueError(
			f"Invalid player color '{color}'. "
			f"Valid colors: {', '.join(c.value for c in PlayerColor)}."
		) from exc

	agent = agent_class(player_color)

	try:
		return agent.choose_move(board)
	except Exception as exc:
		raise AgentComputationError(
			f"Agent '{agent_name}' failed to compute a move: {exc}"
		) from exc

