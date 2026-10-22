from .cells import (
	Cell,
	is_cell,
	is_playable_cell,
	is_player_cell,
	validate_cell,
	validate_playable_cell,
	validate_player_cell,
)
from .colors import (
	PlayerColor,
	is_player_color,
	validate_player_color,
	resolve_starting_player_color,
)
from .base import (
	Board,
	is_board,
	validate_board,
)
from .search import SearchBoard
from .union_find import UnionFindBoard


def resolve_board(board, default=None):
	if board is None:
		board = UnionFindBoard() if default is None else default

	validate_board(board)
	return board


__all__ = [
	"Cell",
	"is_cell",
	"is_playable_cell",
	"is_player_cell",
	"validate_cell",
	"validate_playable_cell",
	"validate_player_cell",
	
	"PlayerColor",
	"is_player_color",
	"validate_player_color",
	"resolve_starting_player_color",

	"Board",
	"is_board",
	"validate_board",
	"resolve_board",

	"SearchBoard",

	"UnionFindBoard",
]

