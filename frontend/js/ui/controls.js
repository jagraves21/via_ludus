import { state } from "../game/state.js";

export function setGameActive(
	boardSizeElement,
	redPlayerElement,
	bluePlayerElement,
	gameActionElement,
) {
	boardSizeElement.disabled = state.gameActive;
	redPlayerElement.disabled = state.gameActive;
	bluePlayerElement.disabled = state.gameActive;

	gameActionElement.textContent =
		state.gameActive ? "End Game" : "Start Game";

	gameActionElement.classList.remove(
		"game-action--start",
		"game-action--end",
	);

	gameActionElement.classList.add(
		state.gameActive
			? "game-action--end"
			: "game-action--start",
	);
}

