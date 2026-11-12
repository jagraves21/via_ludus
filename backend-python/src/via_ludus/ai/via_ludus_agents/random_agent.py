"""
This module demonstrates how to implement an agent that selects a single move.

An agent must inherit from the Agent class (`from ..agent import Agent`) and
implement the `get_move` method. This method must return the row and column
of the desired move as standard Python integers.

The `board.available` property returns a set of open positions representing
the possible moves. These positions may contain NumPy integers, so they must
be cast to standard Python integers before being returned.
"""

from random import choice

from ..agent import Agent


class RandomAgent(Agent):
	name = "Random"

	def get_move(self, board):
		row, col = choice(list(board.available))
		return int(row), int(col)

