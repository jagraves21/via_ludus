import pytest

from via_ludus.board import (
	Cell,
	is_cell,
	is_playable_cell,
	is_player_cell,
	validate_cell,
	validate_playable_cell,
	validate_player_cell,
)


class TestCell:
	def test_cell_values(self):
		assert {cell.name: cell.value for cell in Cell} == {
			"RED": "red",
			"BLUE": "blue",
			"WHITE": "white",
			"WALL": "wall",
		}

	@pytest.mark.parametrize(
		"cell, symbol",
		[
			(Cell.RED, "🟥"),
			(Cell.BLUE, "🟦"),
			(Cell.WHITE, "⬜"),
			(Cell.WALL, "⬛"),
		],
	)
	def test_cell_symbol(self, cell, symbol):
		assert cell.symbol == symbol

	@pytest.mark.parametrize(
		"cell, color",
		[
			(Cell.RED, "red"),
			(Cell.BLUE, "blue"),
			(Cell.WHITE, "white"),
			(Cell.WALL, "black"),
		],
	)
	def test_cell_color(self, cell, color):
		assert cell.color == color

	def test_cell_str_and_repr(self):
		assert str(Cell.RED) == "red"
		assert repr(Cell.WALL) == "Cell.WALL"


class TestCellPredicates:
	def test_is_cell(self):
		assert all(is_cell(cell) for cell in Cell)
		assert not is_cell("red")
		assert not is_cell(None)

	def test_is_playable_cell_only_accepts_white(self):
		assert is_playable_cell(Cell.WHITE)
		assert not any(
			is_playable_cell(cell)
			for cell in (Cell.RED, Cell.BLUE, Cell.WALL)
		)
		assert not is_playable_cell("white")

	def test_is_player_cell_only_accepts_red_and_blue(self):
		assert is_player_cell(Cell.RED)
		assert is_player_cell(Cell.BLUE)
		assert not is_player_cell(Cell.WHITE)
		assert not is_player_cell(Cell.WALL)
		assert not is_player_cell("red")


class TestCellValidation:
	def test_validate_cell(self):
		for cell in Cell:
			validate_cell(cell)

		with pytest.raises(TypeError, match="Expected a Cell"):
			validate_cell("red")

	def test_validate_playable_cell(self):
		validate_playable_cell(Cell.WHITE)

		for cell in (Cell.RED, Cell.BLUE, Cell.WALL):
			with pytest.raises(ValueError, match="Cell.WHITE"):
				validate_playable_cell(cell)

		with pytest.raises(TypeError):
			validate_playable_cell("white")

	def test_validate_player_cell(self):
		validate_player_cell(Cell.RED)
		validate_player_cell(Cell.BLUE)

		for cell in (Cell.WHITE, Cell.WALL):
			with pytest.raises(ValueError, match="Cell.RED or Cell.BLUE"):
				validate_player_cell(cell)

		with pytest.raises(TypeError):
			validate_player_cell("blue")
