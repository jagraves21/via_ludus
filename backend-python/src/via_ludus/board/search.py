from collections import deque

from .base import Board
from .colors import PlayerColor, validate_player_color


class SearchBoard(Board):
	@property
	def winner(self):
		if self._has_path(PlayerColor.RED):
			return PlayerColor.RED

		if self._has_path(PlayerColor.BLUE):
			return PlayerColor.BLUE

		return None

	def _has_path(self, player):
		validate_player_color(player)
		cell = player.cell

		visited = set()
		queue = deque()

		if player == PlayerColor.RED:
			starts = [
				(0, col)
				for col in range(1, self.cols - 1)
				if self._board[0, col] == cell
			]
		else:
			starts = [
				(row, 0)
				for row in range(1, self.rows - 1)
				if self._board[row, 0] == cell
			]

		for position in starts:
			queue.append(position)
			visited.add(position)

		while queue:
			row, col = queue.popleft()

			if player == PlayerColor.RED and row == self.rows - 1:
				return True

			if player == PlayerColor.BLUE and col == self.cols - 1:
				return True

			for neighbor in self._neighbors(row, col):
				if neighbor in visited:
					continue

				n_row, n_col = neighbor

				if self._board[n_row, n_col] != cell:
					continue

				visited.add(neighbor)
				queue.append(neighbor)

		return False

