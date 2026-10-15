import { RED, state } from "./state.js";
import { createBoard } from "./board.js";

export function initializeGame(size) {
	createBoard(size);
	state.currentTurn = RED;
	state.gameActive = false;
	state.winningPath = [];
	state.winningColor = null;

	return state;
}

export function startGame(size) {
	createBoard(size);
	state.currentTurn = RED;
	state.gameActive = true;
	state.winningPath = [];
	state.winningColor = null;

	return state;
}

export function endGame() {
	state.gameActive = false;
	state.winningPath = [];
	state.winningColor = null;

	return state;
}

