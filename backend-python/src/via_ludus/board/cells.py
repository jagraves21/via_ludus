from enum import Enum


class Cell(Enum):
	RED = "red"
	BLUE = "blue"
	WHITE = "white"
	WALL = "wall"

	def __str__(self):
		return self.value

	def __repr__(self):
		return f"Cell.{self.name}"

	@property
	def symbol(self):
		match self:
			case Cell.RED:
				return "🟥"
			case Cell.BLUE:
				return "🟦"
			case Cell.WHITE:
				return "⬜"
			case Cell.WALL:
				return "⬛"

	@property
	def color(self):
		match self:
			case Cell.RED:
				return "red"
			case Cell.BLUE:
				return "blue"
			case Cell.WHITE:
				return "white"
			case Cell.WALL:
				return "black"


def is_cell(cell):
	return isinstance(cell, Cell)


def validate_cell(cell):
	if not is_cell(cell):
		raise TypeError(f"Expected a Cell, got {type(cell).__name__}")


def is_playable_cell(cell):
	return is_cell(cell) and cell == Cell.WHITE


def validate_playable_cell(cell):
	validate_cell(cell)
	if cell != Cell.WHITE:
		raise ValueError(f"Expected Cell.WHITE, got {cell!r}")


def is_player_cell(cell):
	return is_cell(cell) and cell in (Cell.RED, Cell.BLUE)


def validate_player_cell(cell):
	validate_cell(cell)
	if cell not in (Cell.RED, Cell.BLUE):
		raise ValueError(f"Expected Cell.RED or Cell.BLUE, got {cell!r}")

