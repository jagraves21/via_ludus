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

	def choose_move(self, board):
		return self.select_move(board, self.color)

	@abstractmethod
	def select_move(self, board, color):
		"""Return the move this player would select for color.

		Assumes it is color's turn; color need not be this player's
		color. This lets a player ask what it would play for its
		opponent, for example to model the opponent during a search.

		color must be a PlayerColor. This is not checked here, because
		the color argument comes from the caller; choose_move always
		passes this player's own color, which is validated when the
		player is created.

		choose_move is the method that plays this player's own move.
		"""

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


class DeterministicMoveSelectionMixin:
	"""Contract for players that guarantee repeatable move selection.

	Implementations promise that choose_move returns the same move for
	equivalent board states, regardless of the history that produced
	the board or previous calls to the player.

	This contract applies to choose_move only; select_move called with
	another color makes no promise.

	This contract is declarative and is not enforced at runtime.
	"""

	@property
	def is_deterministic(self):
		return True
