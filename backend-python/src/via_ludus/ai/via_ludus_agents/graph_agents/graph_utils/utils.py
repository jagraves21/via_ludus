from .....board import (
	Cell,
	PlayerColor,
)

from .constants import Endpoint


def neighbors(board, row, col):
	directions = (
		(-1, 0),
		(1, 0),
		(0, -1),
		(0, 1),
	)

	for row_offset, col_offset in directions:
		neighbor_row = row + row_offset
		neighbor_col = col + col_offset

		if is_on_board(board, neighbor_row, neighbor_col):
			yield neighbor_row, neighbor_col


def is_on_board(board, row, col):
	return (
		0 <= row < board.rows
		and 0 <= col < board.cols
	)


def edge_cells(board, color, endpoint):
	if not isinstance(color, PlayerColor):
		raise ValueError(f"Invalid player color: {color}")

	try:
		endpoint = Endpoint(endpoint)
	except (TypeError, ValueError):
		raise ValueError(f"Invalid endpoint: {endpoint}") from None

	if color == PlayerColor.RED:
		row = (
			0
			if endpoint == Endpoint.SOURCE
			else board.rows - 1
		)

		for col in range(board.cols):
			yield row, col

	elif color == PlayerColor.BLUE:
		col = (
			0
			if endpoint == Endpoint.SOURCE
			else board.cols - 1
		)

		for row in range(board.rows):
			yield row, col

