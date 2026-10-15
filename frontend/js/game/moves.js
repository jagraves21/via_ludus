import { WHITE, RED, BLUE, state } from "./state.js";
import { checkWinner } from "./win.js";

export function makeMove(row, col) {
	if (!state.gameActive) {
		return false;
	}

	if (
		row < 0 ||
		row >= state.board.length ||
		col < 0 ||
		col >= state.board[row].length
	) {
		return false;
	}

	if (state.board[row][col] !== WHITE) {
		return false;
	}

	state.board[row][col] = state.currentTurn;

	const winner = checkWinner();

	if (winner) {
		state.winningPath = winner.path;
		state.winningColor = winner.color;
		state.gameActive = false;

		return true;
	}

	switchTurn();

	return true;
}

export function switchTurn() {
	state.currentTurn = state.currentTurn === RED ? BLUE : RED;
}

