"""
This module demonstrates how to implement an agent that selects a single move.

An agent must inherit from the Agent class (`from ..agent import Agent`) and
implement the `select_move(self, board, color)` method. This method returns
the row and column of the move that `color` should play, as standard Python
integers. It may assume that it is `color`'s turn. During a game an agent is
always asked for its own color, so this example does not need to use it.

The `board.available` property returns the set of open positions, which are
the possible moves.

Always cast the row and column to standard Python integers before returning
them. The positions in `board.available` are already plain integers, but moves
that are computed with NumPy (array indexing, argmax, and so on) are NumPy
integers, which are a different type.
"""

from random import choice

from ..agent import Agent


class RandomAgent(Agent):
	name = "Random"

	def select_move(self, board, color):
		row, col = choice(list(board.available))
		return int(row), int(col)

