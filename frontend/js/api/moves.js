import { post } from "./client.js";

export async function getAgentMove(
	agentName,
	rows,
	cols,
	board,
	color,
) {
	return post(
		`/agents/${encodeURIComponent(agentName)}/move`,
		{
			rows,
			cols,
			board,
			color,
		},
	);
}
