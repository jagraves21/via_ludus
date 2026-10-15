import { BLUE, RED, WALL, WHITE, state } from "../game/state.js";

function isWinningCell(row, col) {
	return state.winningPath.some(
		([pathRow, pathCol]) => pathRow === row && pathCol === col,
	);
}

function createCell(row, col) {
	const cell = document.createElement("button");

	cell.type = "button";
	cell.className = "board-cell";
	cell.dataset.row = row;
	cell.dataset.col = col;

	const value = state.board[row][col];

	if (value === RED) {
		cell.classList.add("board-cell--red");
		cell.disabled = true;
	} else if (value === BLUE) {
		cell.classList.add("board-cell--blue");
		cell.disabled = true;
	} else if (value === WALL) {
		cell.classList.add("board-cell--wall");
		cell.disabled = true;
	} else if (value === WHITE && !state.gameActive) {
		cell.disabled = true;
	}

	if (isWinningCell(row, col)) {
		cell.classList.add("board-cell--winning");
	}

	return cell;
}

export function renderBoard(boardElement) {
	boardElement.innerHTML = "";
	boardElement.style.setProperty(
		"--board-size",
		state.board.length,
	);

	state.board.forEach((row, rowIndex) => {
		row.forEach((_, colIndex) => {
			boardElement.appendChild(
				createCell(rowIndex, colIndex),
			);
		});
	});
}

export function setBoardInteractive(boardElement, interactive) {
	const cells = boardElement.querySelectorAll(
		".board-cell",
	);

	for (const cell of cells) {
		if (
			cell.classList.contains("board-cell--red") ||
			cell.classList.contains("board-cell--blue") ||
			cell.classList.contains("board-cell--wall")
		) {
			continue;
		}

		cell.disabled = !interactive;
	}
}

export function createBoardElement(board) {
	const boardElement = document.createElement("div");

	boardElement.className = "game-board";
	boardElement.style.setProperty(
		"--board-size",
		board.length,
	);

	const previousBoard = state.board;
	state.board = board;

	board.forEach((row, rowIndex) => {
		row.forEach((_, colIndex) => {
			boardElement.appendChild(
				createCell(rowIndex, colIndex),
			);
		});
	});

	state.board = previousBoard;

	return boardElement;
}

