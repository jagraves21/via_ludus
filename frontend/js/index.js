import { AI_MOVE_DELAY } from "./config.js";
import { state } from "./game/state.js";
import { makeMove } from "./game/moves.js";
import {
	endGame as endGameState,
	initializeGame,
	startGame as startGameState,
} from "./game/game.js";
import { getPlayerName } from "./game/players.js";
import {
	renderBoard,
	setBoardInteractive,
} from "./ui/board.js";
import {
	showThinking,
	updateGameStatus,
} from "./ui/status.js";
import { setGameActive } from "./ui/controls.js";
import { loadPlayers } from "./ui/players.js";
import { getAgentMove } from "./api/moves.js";

const boardContainerElement =
	document.getElementById("game-board-container");

let boardElement = null;

const boardSizeElement = document.getElementById("board-size");
const redPlayerElement = document.getElementById("red-player");
const bluePlayerElement = document.getElementById("blue-player");
const gameActionElement = document.getElementById("game-action");
const gameStatusElement = document.getElementById("game-status");
const gameStatusTitleElement =
	document.getElementById("game-status-title");
const turnIndicatorElement =
	document.getElementById("turn-indicator");

function createGameBoard() {
	const element = document.createElement("div");

	element.id = "game-board";
	element.className = "game-board";
	element.setAttribute(
		"aria-label",
		"Game board",
	);

	return element;
}

function showGameBoard() {
	boardElement = createGameBoard();

	boardContainerElement.replaceChildren(
		boardElement,
	);

	boardElement.addEventListener(
		"click",
		handleBoardClick,
	);
}

function updateControls() {
	setGameActive(
		boardSizeElement,
		redPlayerElement,
		bluePlayerElement,
		gameActionElement,
	);
}

function getCurrentPlayerElement() {
	if (state.currentTurn === "red") {
		return redPlayerElement;
	}

	return bluePlayerElement;
}

function getCurrentPlayerName() {
	return getCurrentPlayerElement().value;
}

function isCurrentPlayerHuman() {
	return getCurrentPlayerName() === "human";
}

function serializeBoard() {
	const serialization = {
		red: "R",
		blue: "B",
		white: "W",
		wall: "X",
	};

	return state.board
		.flat()
		.map((cell) => serialization[cell])
		.join("");
}

function renderGame() {
	renderBoard(boardElement);
	updateControls();

	setBoardInteractive(
		boardElement,
		state.gameActive && isCurrentPlayerHuman(),
	);
}

function updateTurnStatus() {
	updateGameStatus(
		boardElement,
		gameStatusElement,
		gameStatusTitleElement,
		turnIndicatorElement,
		"Game In Progress",
		`${getPlayerName(state.currentTurn)} player's turn.`,
	);
}

function handleGameOver() {
	const playerName = getPlayerName(
		state.winningColor,
	);

	updateGameStatus(
		boardElement,
		gameStatusElement,
		gameStatusTitleElement,
		turnIndicatorElement,
		"Game Over",
		`${playerName} player wins!`,
		"game-status--win",
	);
}

async function playAgentTurn() {
	if (!state.gameActive || isCurrentPlayerHuman()) {
		return;
	}

	const agentName = getCurrentPlayerName();
	const color = state.currentTurn;

	setBoardInteractive(
		boardElement,
		false,
	);

	updateGameStatus(
		boardElement,
		gameStatusElement,
		gameStatusTitleElement,
		turnIndicatorElement,
		"Game In Progress",
		"",
	);

	showThinking(
		turnIndicatorElement,
		getPlayerName(state.currentTurn),
	);

	try {
		const rows = state.board.length;
		const cols = state.board[0].length;

		const startTime = performance.now();

		const move = await getAgentMove(
			agentName,
			rows,
			cols,
			serializeBoard(),
			color,
		);

		const elapsedTime =
			performance.now() - startTime;

		const remainingTime =
			AI_MOVE_DELAY - elapsedTime;

		if (remainingTime > 0) {
			await new Promise((resolve) => {
				setTimeout(resolve, remainingTime);
			});
		}

		const moveMade = makeMove(
			move.row,
			move.col,
		);

		if (!moveMade) {
			console.error(
				"Agent returned an invalid move:",
				move,
			);
			return;
		}

		renderGame();

		if (state.winningColor) {
			handleGameOver();
			return;
		}

		updateTurnStatus();

		if (!isCurrentPlayerHuman()) {
			await playAgentTurn();
		}
	} catch (error) {
		console.error(
			"Failed to get agent move:",
			error,
		);

		setBoardInteractive(
			boardElement,
			state.gameActive &&
				isCurrentPlayerHuman(),
		);

		updateGameStatus(
			boardElement,
			gameStatusElement,
			gameStatusTitleElement,
			turnIndicatorElement,
			"Game Error",
			"Failed to get a move from the selected player.",
		);
	}
}

async function handleBoardClick(event) {
	const cell = event.target.closest(".board-cell");

	if (
		!cell ||
		!state.gameActive ||
		!isCurrentPlayerHuman()
	) {
		return;
	}

	const row = Number.parseInt(
		cell.dataset.row,
		10,
	);

	const col = Number.parseInt(
		cell.dataset.col,
		10,
	);

	const moveMade = makeMove(row, col);

	if (!moveMade) {
		return;
	}

	renderGame();

	if (state.winningColor) {
		handleGameOver();
		return;
	}

	updateTurnStatus();

	await playAgentTurn();
}

async function startGame() {
	const size = Number.parseInt(
		boardSizeElement.value,
		10,
	);

	startGameState(size);

	updateGameStatus(
		boardElement,
		gameStatusElement,
		gameStatusTitleElement,
		turnIndicatorElement,
		"Game In Progress",
		"Red player's turn.",
	);

	renderGame();

	await playAgentTurn();
}

function endGame() {
	endGameState();

	updateGameStatus(
		boardElement,
		gameStatusElement,
		gameStatusTitleElement,
		turnIndicatorElement,
		"Game Cancelled",
		"Start a new game to begin playing.",
	);

	renderGame();
}

async function initializeBoard() {
	const size = Number.parseInt(
		boardSizeElement.value,
		10,
	);

	initializeGame(size);

	showGameBoard();

	updateGameStatus(
		boardElement,
		gameStatusElement,
		gameStatusTitleElement,
		turnIndicatorElement,
		"Game Not Started",
		"Start a new game to begin playing.",
	);

	renderGame();

	try {
		await loadPlayers(
			redPlayerElement,
			bluePlayerElement,
		);
	} catch (error) {
		console.error(
			"Failed to load players:",
			error,
		);
	}
}

gameActionElement.addEventListener(
	"click",
	() => {
		if (state.gameActive) {
			endGame();
			return;
		}

		startGame();
	},
);

document.addEventListener(
	"DOMContentLoaded",
	initializeBoard,
);

