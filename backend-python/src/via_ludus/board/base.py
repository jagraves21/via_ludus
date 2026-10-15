from abc import ABC, abstractmethod
import warnings

import matplotlib.pyplot as plt
import numpy as np

from ..utils import with_ax
from .cells import (
	Cell,
	validate_cell,
)


class Board(ABC):
	def __init__(self, size=11):
		self._validate_size(size)
		self._board = self._generate(size)

	@property
	def shape(self):
		return self._board.shape

	@property
	def rows(self):
		return self._board.shape[0]

	@property
	def cols(self):
		return self._board.shape[1]

	def _positions(self, cell):
		validate_cell(cell)
		rows, cols = np.where(self._board == cell)
		return set(zip(map(int, rows), map(int, cols)))

	@property
	def empty_cells(self):
		return self._positions(Cell.WHITE)

	@property
	def red_cells(self):
		return self._positions(Cell.RED)

	@property
	def blue_cells(self):
		return self._positions(Cell.BLUE)

	@property
	def available(self):
		return self.empty_cells

	@property
	@abstractmethod
	def winner(self):
		pass

	@property
	def is_game_over(self):
		return self.winner is not None

	@staticmethod
	def _validate_size(size):
		if size < 3:
			raise ValueError("Board must have a size of at least 3")

		if size % 2 == 0:
			warnings.warn(
				"Even-sized boards contain redundant white cells along the "
				"second-to-last row and column. Any winning path through these "
				"cells has a shorter alternative."
			)

	def _generate(self, size):
		board = np.full(
			(size, size),
			Cell.WHITE,
			dtype=object,
		)

		# corners
		board[0, 0] = Cell.WALL
		board[0, -1] = Cell.WALL
		board[-1, 0] = Cell.WALL
		board[-1, -1] = Cell.WALL

		# edges
		board[0, 1:-1] = Cell.RED
		board[-1, 1:-1] = Cell.RED
		board[1:-1, 0] = Cell.BLUE
		board[1:-1, -1] = Cell.BLUE

		# interior
		for row in range(1, size - 1):
			for col in range(1, size - 1):
				if (row + col) % 2 == 1:
					board[row, col] = (
						Cell.BLUE if row % 2 else Cell.RED
					)

		return board

	def get(self, row, col):
		return self._board[row, col]

	def set(self, row, col, cell):
		from .cells import (
			validate_player_cell,
			validate_playable_cell,
		)

		validate_player_cell(cell)
		validate_playable_cell(self._board[row, col])
		self._board[row, col] = cell

	def reset(self, row, col):
		from .cells import validate_player_cell

		validate_player_cell(self._board[row, col])
		self._board[row, col] = Cell.WHITE

	def copy(self):
		instance = self.__class__.__new__(self.__class__)
		instance._board = self._board.copy()
		return instance

	@classmethod
	def from_board(cls, board):
		if not isinstance(board, Board):
			raise TypeError(
				f"Expected a Board, got {type(board).__name__}"
			)

		instance = cls.__new__(cls)
		instance._board = board._board.copy()

		return instance

	def _neighbors(self, row, col):
		directions = (
			(-1, 0),
			(1, 0),
			(0, -1),
			(0, 1),
		)

		for row_offset, col_offset in directions:
			new_row = row + row_offset
			new_col = col + col_offset

			if (
				0 <= new_row < self.rows
				and 0 <= new_col < self.cols
			):
				yield new_row, new_col

	@with_ax
	def plot(self, ax):
		for row in range(self.rows):
			for col in range(self.cols):
				cell = self.get(row, col)

				ax.add_patch(
					plt.Rectangle(
						(col, self.rows - row - 1),
						1,
						1,
						facecolor=cell.color,
						edgecolor="black",
					)
				)

		ax.set_xlim(0, self.cols)
		ax.set_ylim(0, self.rows)
		ax.set_aspect("equal")
		ax.axis("off")

	def serialize(self):
		serialization = {
			Cell.RED: "R",
			Cell.BLUE: "B",
			Cell.WHITE: "W",
			Cell.WALL: "X",
		}

		cells = "".join(
			serialization[cell]
			for cell in self._board.flat
		)

		return f"{self.rows},{self.cols},{cells}"

	@classmethod
	def deserialize(cls, serialized):
		try:
			rows, cols, cells = serialized.split(",", 2)
			rows = int(rows)
			cols = int(cols)
		except ValueError as exc:
			raise ValueError("Invalid board serialization") from exc

		if rows < 1 or cols < 1:
			raise ValueError(
				"Board dimensions must be greater than 0"
			)

		expected_size = rows * cols

		if len(cells) != expected_size:
			raise ValueError(
				f"Expected {expected_size} cells, "
				f"got {len(cells)}"
			)

		deserialization = {
			"R": Cell.RED,
			"B": Cell.BLUE,
			"W": Cell.WHITE,
			"X": Cell.WALL,
		}

		try:
			board = np.array(
				[deserialization[cell] for cell in cells],
				dtype=object,
			).reshape((rows, cols))
		except KeyError as exc:
			raise ValueError("Invalid board serialization") from exc

		instance = cls.__new__(cls)
		instance._board = board

		return instance

	def __str__(self):
		return "\n".join(
			"".join(cell.symbol for cell in row)
			for row in self._board
		)

	def __repr__(self):
		return f"{self.__class__.__name__}(shape={self.shape})"


def is_board(board):
	return isinstance(board, Board)


def validate_board(board):
	if not is_board(board):
		raise TypeError(
			f"Expected a Board, got {type(board).__name__}"
		)

