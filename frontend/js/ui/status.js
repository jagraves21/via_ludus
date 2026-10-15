import { state } from "../game/state.js";
import { getPlayerName } from "../game/players.js";

const stateClasses = [
	"red-turn",
	"blue-turn",
	"red-win",
	"blue-win",
];

function getGameStateClass() {
	if (!state.gameActive && state.winningColor) {
		return `${state.winningColor}-win`;
	}

	if (!state.gameActive) {
		return null;
	}

	return `${state.currentTurn}-turn`;
}

export function updateStateClasses(
	boardElement,
	gameStatusElement,
	turnIndicatorElement,
) {
	const gameStateClass = getGameStateClass();

	boardElement.classList.remove(...stateClasses);
	gameStatusElement.classList.remove(...stateClasses);
	turnIndicatorElement.classList.remove(...stateClasses);

	if (gameStateClass) {
		boardElement.classList.add(gameStateClass);
		gameStatusElement.classList.add(gameStateClass);
		turnIndicatorElement.classList.add(gameStateClass);
	}
}

export function updateGameStatus(
	boardElement,
	gameStatusElement,
	gameStatusTitleElement,
	turnIndicatorElement,
	title,
	message,
	statusClass = null,
) {
	gameStatusElement.classList.remove(
		"game-status--active",
		"game-status--win",
	);

	if (statusClass) {
		gameStatusElement.classList.add(statusClass);
	}

	gameStatusTitleElement.textContent = title;
	turnIndicatorElement.textContent = message;

	updateStateClasses(
		boardElement,
		gameStatusElement,
		turnIndicatorElement,
	);
}

export function updateTurnIndicator(turnIndicatorElement) {
	turnIndicatorElement.textContent =
		`${getPlayerName(state.currentTurn)} player's turn.`;
}

export function showThinking(turnIndicatorElement, playerName) {
	turnIndicatorElement.innerHTML = `
		<span class="loading loading--inline" aria-live="polite">
			<span class="loading__spinner" aria-hidden="true"></span>
			<span>${playerName} is thinking...</span>
		</span>
	`;
}

