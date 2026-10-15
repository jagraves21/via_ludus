import { BLUE, RED, WALL, WHITE, state } from "./state.js";

export function createBoard(size) {
	state.board = Array.from({ length: size }, (_, row) =>
		Array.from({ length: size }, (_, col) => {
			const isTopEdge = row === 0;
			const isBottomEdge = row === size - 1;
			const isLeftEdge = col === 0;
			const isRightEdge = col === size - 1;
			const isCorner =
				(isTopEdge || isBottomEdge) && (isLeftEdge || isRightEdge);

			if (isCorner) {
				return WALL;
			}

			if (isTopEdge || isBottomEdge) {
				return RED;
			}

			if (isLeftEdge || isRightEdge) {
				return BLUE;
			}

			if ((row + col) % 2 === 1) {
				return row % 2 === 1 ? BLUE : RED;
			}

			return WHITE;
		}),
	);

	return state.board;
}

export function getNeighbors(row, col) {
	const neighbors = [
		[row - 1, col],
		[row + 1, col],
		[row, col - 1],
		[row, col + 1],
	];

	return neighbors.filter(
		([neighborRow, neighborCol]) =>
			neighborRow >= 0 &&
			neighborRow < state.board.length &&
			neighborCol >= 0 &&
			neighborCol < state.board[neighborRow].length,
	);
}

