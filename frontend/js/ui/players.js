import { BLUE, RED, state } from "../game/state.js";
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

function createPlayerOption(player) {
	const option = document.createElement("option");

	option.value = player;
	option.textContent = player === "human" ? "Human" : player;

	return option;
}

function hasSameValues(playerElement, players) {
	const current = Array.from(
		playerElement.options,
		(option) => option.value,
	);

	return (
		current.length === players.length &&
		current.every((value, index) => value === players[index])
	);
}

// Replaces the options of one menu without changing what is selected.
// Menus that already list exactly these players are left alone.
function setPlayerOptions(playerElement, players) {
	if (hasSameValues(playerElement, players)) {
		return;
	}

	const selected = playerElement.value;
	const stillAvailable = players.includes(selected);

	// If the selected agent is gone, fall back to Human, unless a game is
	// being played with it: the game must keep its players.
	const keep = stillAvailable || state.gameActive ? selected : "human";
	const options = players.includes(keep) ? players : [...players, keep];

	playerElement.replaceChildren(...options.map(createPlayerOption));
	playerElement.value = keep;
}

// Fetches the agents and fills both player menus, keeping whatever is
// selected. Callers that ask while a request is already running share it.
let pendingLoad = null;

export function loadPlayers(
	redPlayerElement,
	bluePlayerElement,
) {
	if (pendingLoad === null) {
		pendingLoad = getAgents()
			.then((agents) => {
				const players = ["human", ...agents];

				setPlayerOptions(redPlayerElement, players);
				setPlayerOptions(bluePlayerElement, players);
			})
			.finally(() => {
				pendingLoad = null;
			});
	}

	return pendingLoad;
}

