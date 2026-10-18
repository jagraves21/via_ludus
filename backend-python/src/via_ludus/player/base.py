from abc import ABC, abstractmethod

from ..board import PlayerColor


class Player(ABC):
	def __init__(self, color):
		if not isinstance(color, PlayerColor):
			raise TypeError(f"Invalid player color: {color}")

		self._color = color

	@property
	def is_deterministic(self):
		return False

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


class DeterministicPlayer(Player):
	"""A player that guarantees repeatable move selection.

	Subclasses promise that choose_move returns the same move for
	equivalent board states, regardless of the history that produced
	the board or previous calls to the player.

	The guarantee assumes the player's configuration remains unchanged.
	This contract is declarative and is not enforced at runtime.
	"""
	pass

	@property
	def is_deterministic(self):
		return True

