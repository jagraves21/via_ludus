import {
	BLUE,
	RED,
	WALL,
	WHITE,
	state,
} from "./game/state.js";

import {
	createBoardElement,
} from "./ui/board.js";

const startingBoard = [
	[WALL, RED, RED, RED, RED, RED, RED, RED, RED, RED, WALL],
	[BLUE, WHITE, BLUE, WHITE, BLUE, WHITE, BLUE, WHITE, BLUE, WHITE, BLUE],
	[BLUE, RED, WHITE, RED, WHITE, RED, WHITE, RED, WHITE, RED, BLUE],
	[BLUE, WHITE, BLUE, WHITE, BLUE, WHITE, BLUE, WHITE, BLUE, WHITE, BLUE],
	[BLUE, RED, WHITE, RED, WHITE, RED, WHITE, RED, WHITE, RED, BLUE],
	[BLUE, WHITE, BLUE, WHITE, BLUE, WHITE, BLUE, WHITE, BLUE, WHITE, BLUE],
	[BLUE, RED, WHITE, RED, WHITE, RED, WHITE, RED, WHITE, RED, BLUE],
	[BLUE, WHITE, BLUE, WHITE, BLUE, WHITE, BLUE, WHITE, BLUE, WHITE, BLUE],
	[BLUE, RED, WHITE, RED, WHITE, RED, WHITE, RED, WHITE, RED, BLUE],
	[BLUE, WHITE, BLUE, WHITE, BLUE, WHITE, BLUE, WHITE, BLUE, WHITE, BLUE],
	[WALL, RED, RED, RED, RED, RED, RED, RED, RED, RED, WALL],
];

const redWinningBoard = [
	[WALL, RED, RED, RED, RED, RED, WALL],
	[BLUE, WHITE, BLUE, RED, BLUE, BLUE, BLUE],
	[BLUE, RED, WHITE, RED, RED, RED, BLUE],
	[BLUE, BLUE, BLUE, RED, BLUE, BLUE, BLUE],
	[BLUE, RED, RED, RED, WHITE, RED, BLUE],
	[BLUE, RED, BLUE, BLUE, BLUE, WHITE, BLUE],
	[WALL, RED, RED, RED, RED, RED, WALL],
];

const redWinningPath = [
	[0, 3],
	[1, 3],
	[2, 3],
	[2, 3],
	[3, 3],
	[4, 3],
	[4, 2],
	[4, 1],
	[5, 1],
	[6, 1],
];

const blueWinningBoard = [
	[WALL, RED, RED, RED, RED, RED, WALL],
	[BLUE, WHITE, BLUE, RED, BLUE, WHITE, BLUE],
	[BLUE, RED, WHITE, RED, RED, RED, BLUE],
	[BLUE, BLUE, BLUE, WHITE, BLUE, RED, BLUE],
	[BLUE, RED, BLUE, RED, WHITE, RED, BLUE],
	[BLUE, RED, BLUE, BLUE, BLUE, BLUE, BLUE],
	[WALL, RED, RED, RED, RED, RED, WALL],
];

const blueWinningPath = [
	[3, 0],
	[3, 1],
	[3, 2],
	[4, 2],
	[5, 2],
	[5, 3],
	[5, 4],
	[5, 5],
	[5, 6],
];

document
	.getElementById("starting-board-example")
	.replaceChildren(
		createBoardElement(startingBoard),
	);

state.winningPath = redWinningPath;

document
	.getElementById("red-winning-example")
	.replaceChildren(
		createBoardElement(redWinningBoard),
	);

state.winningPath = blueWinningPath;

document
	.getElementById("blue-winning-example")
	.replaceChildren(
		createBoardElement(blueWinningBoard),
	);

