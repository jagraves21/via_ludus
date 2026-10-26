from ..data_structures import UnionFind

from .base import Board
from .cells import (
	Cell,
	validate_cell,
	validate_player_cell,
)
from .colors import PlayerColor


class UnionFindBoard(Board):
	def __init__(self, size=11):
		super().__init__(size)
		self._initialize_union_find()

	def _initialize_union_find(self):
		self._red_source = ("RED_SOURCE",)
		self._red_target = ("RED_TARGET",)
		self._blue_source = ("BLUE_SOURCE",)
		self._blue_target = ("BLUE_TARGET",)

		self._initialize_red_union_find()
		self._initialize_blue_union_find()

	def _initialize_red_union_find(self):
		self._red_union_find = self._build_union_find(
			Cell.RED,
			self._red_source,
			self._red_target,
		)

	def _initialize_blue_union_find(self):
		self._blue_union_find = self._build_union_find(
			Cell.BLUE,
			self._blue_source,
			self._blue_target,
		)

	def _build_union_find(self, cell, source, target):
		validate_cell(cell)

		positions = list(self.positions_of(cell))
		union_find = UnionFind(
			[source, target] + positions
		)

		for row, col in positions:
			current = (row, col)

			if cell == Cell.RED:
				if row == 0:
					union_find.union(current, source)
				if row == self.rows - 1:
					union_find.union(current, target)
			else:
				if col == 0:
					union_find.union(current, source)
				if col == self.cols - 1:
					union_find.union(current, target)

			for neighbor_row, neighbor_col in self.neighbors(row, col):
				neighbor = (neighbor_row, neighbor_col)

				if self.get(neighbor_row, neighbor_col) == cell:
					union_find.union(current, neighbor)

		return union_find

	@property
	def winner(self):
		if self._red_union_find.connected(
			self._red_source,
			self._red_target,
		):
			return PlayerColor.RED

		if self._blue_union_find.connected(
			self._blue_source,
			self._blue_target,
		):
			return PlayerColor.BLUE

		return None

	def set(self, row, col, cell):
		super().set(row, col, cell)
		self._add_cell(row, col, cell)

	def reset(self, row, col):
		cell = self.get(row, col)
		super().reset(row, col)

		if cell == Cell.RED:
			self._initialize_red_union_find()
		elif cell == Cell.BLUE:
			self._initialize_blue_union_find()

	def _add_cell(self, row, col, cell):
		validate_player_cell(cell)

		if cell == Cell.RED:
			union_find = self._red_union_find
		else:
			union_find = self._blue_union_find

		current = (row, col)
		union_find.add(current)

		for neighbor_row, neighbor_col in self.neighbors(row, col):
			if self.get(neighbor_row, neighbor_col) == cell:
				neighbor = (neighbor_row, neighbor_col)
				union_find.union(current, neighbor)

	def copy(self):
		board = super().copy()
		board._red_source = self._red_source
		board._red_target = self._red_target
		board._blue_source = self._blue_source
		board._blue_target = self._blue_target
		board._red_union_find = self._red_union_find.copy()
		board._blue_union_find = self._blue_union_find.copy()
		return board

	@classmethod
	def from_board(cls, board):
		instance = super().from_board(board)
		instance._initialize_union_find()
		return instance

	@classmethod
	def deserialize(cls, serialized):
		board = super().deserialize(serialized)
		board._initialize_union_find()
		return board

