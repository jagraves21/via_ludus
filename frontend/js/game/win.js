import { BLUE, RED, state } from "./state.js";
import { getNeighbors } from "./board.js";

export function findPath(color) {
	const queue = [];
	const visited = new Set();
	const parent = new Map();

	if (color === RED) {
		for (let col = 0; col < state.board[0].length; col++) {
			if (state.board[0][col] === RED) {
				queue.push([0, col]);
				visited.add(`0,${col}`);
			}
		}
	} else if (color === BLUE) {
		for (let row = 0; row < state.board.length; row++) {
			if (state.board[row][0] === BLUE) {
				queue.push([row, 0]);
				visited.add(`${row},0`);
			}
		}
	}

	while (queue.length > 0) {
		const [row, col] = queue.shift();

		if (
			(color === RED && row === state.board.length - 1) ||
			(color === BLUE && col === state.board[row].length - 1)
		) {
			const path = [];
			let current = [row, col];

			while (current) {
				path.unshift(current);
				current = parent.get(`${current[0]},${current[1]}`);
			}

			return path;
		}

		for (const [neighborRow, neighborCol] of getNeighbors(row, col)) {
			if (state.board[neighborRow][neighborCol] !== color) {
				continue;
			}

			const key = `${neighborRow},${neighborCol}`;

			if (visited.has(key)) {
				continue;
			}

			visited.add(key);
			parent.set(key, [row, col]);
			queue.push([neighborRow, neighborCol]);
		}
	}

	return null;
}

export function checkWinner() {
	const redPath = findPath(RED);

	if (redPath) {
		return {
			color: RED,
			path: redPath,
		};
	}

	const bluePath = findPath(BLUE);

	if (bluePath) {
		return {
			color: BLUE,
			path: bluePath,
		};
	}

	return null;
}

