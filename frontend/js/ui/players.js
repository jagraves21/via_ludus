import { BLUE, RED } from "../game/state.js";
import { getAgents } from "../api/agents.js";

export function getCurrentPlayerElement(
	redPlayerElement,
	bluePlayerElement,
	currentTurn,
) {
	if (currentTurn === RED) {
		return redPlayerElement;
	}

	if (currentTurn === BLUE) {
		return bluePlayerElement;
	}

	return null;
}

export async function loadPlayers(
	redPlayerElement,
	bluePlayerElement,
) {
	const agents = await getAgents();

	redPlayerElement.innerHTML = "";
	bluePlayerElement.innerHTML = "";

	const players = ["human", ...agents];

	for (const player of players) {
		const redOption = document.createElement("option");
		redOption.value = player;
		redOption.textContent =
			player === "human" ? "Human" : player;

		const blueOption = document.createElement("option");
		blueOption.value = player;
		blueOption.textContent =
			player === "human" ? "Human" : player;

		redPlayerElement.appendChild(redOption);
		bluePlayerElement.appendChild(blueOption);
	}
}

