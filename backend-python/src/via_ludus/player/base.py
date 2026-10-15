from abc import ABC, abstractmethod

from ..board import PlayerColor


class Player(ABC):
	def __init__(self, color):
		if not isinstance(color, PlayerColor):
			raise ValueError(f"Invalid player color: {color}")

		self._color = color

	@property
	def color(self):
		return self._color

	@property
	def opponent_color(self):
		return self.color.opponent

	@property
	def cell(self):
		return self.color.cell

	@abstractmethod
	def choose_move(self, board):
		pass

	def make_move(self, board):
		row, col = self.choose_move(board)
		board.set(row, col, self.cell)
		return row, col

	def is_winner(self, board):
		return board.winner == self.color

	def __repr__(self):
		return f"{self.__class__.__name__}(color={self.color!r})"

	def __str__(self):
		return f"{self.color} Player"

