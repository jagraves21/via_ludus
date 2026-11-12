"""
This module demonstrates how to implement an agent that returns multiple
possible moves, allowing the selection mixins to determine which move is
ultimately chosen based on their selection strategy.

The agent must inherit from the ScoringAgent class and implement the
evaluate_move_options method. This method returns a dictionary mapping
possible moves (row, column) to their respective scores.

A score does not need to be provided for every possible move. Moves omitted
from the dictionary are simply excluded from consideration. However, the
dictionary must contain at least one valid move with a finite score.

The agent is responsible for evaluating the board and assigning scores to
the moves it considers viable. The scoring and selection mixins then use
those scores to determine which move the agent will return.

This example uses Dijkstra's shortest-path algorithm to find the lowest-cost
path toward the opposite side of the board. Empty cells along the path are
assigned a score of 1, while cells already occupied by the agent are treated
as having no additional cost.
"""

from collections import deque

import numpy as np

from ...board import Cell, PlayerColor
from ...player import (
	DeterministicScoringMixin,
	RandomMaxSelectorMixin,
)
from ..agent import ScoringAgent


# Edsger W. Dijkstra
class ShortestPathAgent(
	DeterministicScoringMixin,
	RandomMaxSelectorMixin,
	ScoringAgent,
):
	name = "Dijkstra"

	def evaluate_move_options(self, board, color):
		rows, cols = board.shape
		own_cell = color.cell
		infinity = np.iinfo(np.int32).max

		distances = np.full((rows, cols), infinity, dtype=np.int32)
		parents = np.full((rows, cols, 2), -1, dtype=np.int32)
		queue = deque()

		if color == PlayerColor.RED:
			starts = [(0, col) for col in range(cols)]
			is_target = lambda row, col: row == rows - 1
		else:
			starts = [(row, 0) for row in range(rows)]
			is_target = lambda row, col: col == cols - 1

		for row, col in starts:
			value = board.get(row, col)

			if value not in (Cell.WHITE, own_cell):
				continue

			cost = int(value == Cell.WHITE)
			distances[row, col] = cost

			if cost == 0:
				queue.appendleft((row, col))
			else:
				queue.append((row, col))

		end = None

		while queue:
			row, col = queue.popleft()

			if is_target(row, col):
				end = (row, col)
				break

			for nr, nc in board.neighbors(row, col):
				value = board.get(nr, nc)

				if value not in (Cell.WHITE, own_cell):
					continue

				cost = int(value == Cell.WHITE)
				new_distance = distances[row, col] + cost

				if new_distance >= distances[nr, nc]:
					continue

				distances[nr, nc] = new_distance
				parents[nr, nc] = (row, col)

				if cost == 0:
					queue.appendleft((nr, nc))
				else:
					queue.append((nr, nc))

		if end is None:
			return {}

		scores = {}
		row, col = end

		while row != -1:
			if board.get(row, col) == Cell.WHITE:
				scores[
					(int(row), int(col))
				] = 1

			row, col = parents[row, col]

		return scores

