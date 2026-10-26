from via_ludus import (
	PlayerColor,
	SearchBoard as ViaLudusBoard,
	AI_AGENTS,
)


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
	board = ViaLudusBoard.deserialize(serialized)

	agent = AI_AGENTS[agent_name](
		PlayerColor(color),
	)

	return agent.choose_move(board)

