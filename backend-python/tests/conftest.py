"""Shared fixtures for the via_ludus test suite.

Design notes
------------
- Every serialized position, move sequence and playout used by the tests is a
*reachable* game state: Red moves first, players alternate, only white cells
are claimed and the game stops at the first winning move.
- Positions are written out literally instead of being derived from the code
under test, so a regression in ``serialize`` or in the initial board
generation cannot silently change the expected data.
- ``reference`` is a small, independent re-implementation of the rules (initial
layout and path search on plain lists). Tests use it as an oracle when
comparing the two ``Board`` implementations.
"""

import importlib.abc
import random
import sys
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from via_ludus.board import (
	Cell,
	PlayerColor,
	SearchBoard,
	UnionFindBoard,
)
from via_ludus.player import (
	DeterministicMoveSelectionMixin,
	DeterministicScoringMixin,
	Player,
	RandomMaxSelectorMixin,
	ScoringPlayer,
)
from via_ludus.tournament import TournamentResults


BOARD_TYPES = (SearchBoard, UnionFindBoard)

PLAYOUT_SIZES = (3, 5, 7, 11)
PLAYOUT_SEEDS = tuple(range(10))


# ---------------------------------------------------------------------
# Independent reference implementation of the rules (test oracle)
# ---------------------------------------------------------------------

_CELL_CHARS = {
	Cell.RED: "R",
	Cell.BLUE: "B",
	Cell.WHITE: "W",
	Cell.WALL: "X",
}

_PLAYER_CHARS = {
	PlayerColor.RED: "R",
	PlayerColor.BLUE: "B",
}


def _reference_initial_grid(size):
	grid = [["W"] * size for _ in range(size)]

	for index in range(1, size - 1):
		grid[0][index] = "R"
		grid[size - 1][index] = "R"
		grid[index][0] = "B"
		grid[index][size - 1] = "B"

	for row in (0, size - 1):
		for col in (0, size - 1):
			grid[row][col] = "X"

	for row in range(1, size - 1):
		for col in range(1, size - 1):
			if row % 2 == 1 and col % 2 == 0:
				grid[row][col] = "B"
			elif row % 2 == 0 and col % 2 == 1:
				grid[row][col] = "R"

	return grid


def _reference_grid_of(board):
	return [
		[_CELL_CHARS[board.get(row, col)] for col in range(board.cols)]
		for row in range(board.rows)
	]


def _reference_has_path(grid, char):
	rows = len(grid)
	cols = len(grid[0])

	if char == "R":
		starts = [(0, col) for col in range(cols) if grid[0][col] == "R"]

		def reached(row, col):
			return row == rows - 1
	else:
		starts = [(row, 0) for row in range(rows) if grid[row][0] == "B"]

		def reached(row, col):
			return col == cols - 1

	stack = list(starts)
	visited = set(starts)

	while stack:
		row, col = stack.pop()

		if reached(row, col):
			return True

		for row_offset, col_offset in ((1, 0), (-1, 0), (0, 1), (0, -1)):
			new_row = row + row_offset
			new_col = col + col_offset

			if not (0 <= new_row < rows and 0 <= new_col < cols):
				continue

			if (new_row, new_col) in visited:
				continue

			if grid[new_row][new_col] != char:
				continue

			visited.add((new_row, new_col))
			stack.append((new_row, new_col))

	return False


def _reference_winners(grid):
	winners = set()

	if _reference_has_path(grid, "R"):
		winners.add(PlayerColor.RED)

	if _reference_has_path(grid, "B"):
		winners.add(PlayerColor.BLUE)

	return frozenset(winners)


def _reference_random_playout(size, seed):
	"""One random, legal game: alternating moves, stopping at the first win."""
	rng = random.Random(seed)
	grid = _reference_initial_grid(size)

	whites = [
		(row, col)
		for row in range(size)
		for col in range(size)
		if grid[row][col] == "W"
	]
	rng.shuffle(whites)

	moves = []
	player = PlayerColor.RED

	for row, col in whites:
		char = _PLAYER_CHARS[player]
		grid[row][col] = char
		moves.append(((row, col), player))

		if _reference_has_path(grid, char):
			break

		player = player.opponent

	return tuple(moves)


@pytest.fixture
def reference():
	return SimpleNamespace(
		initial_grid=_reference_initial_grid,
		grid_of=_reference_grid_of,
		has_path=_reference_has_path,
		winners=_reference_winners,
		board_winners=lambda board: _reference_winners(
			_reference_grid_of(board)
		),
		random_playout=_reference_random_playout,
	)


def _replay_game(board_type, moves, size=11):
	board = board_type(size=size)

	for position, player in moves:
		row, col = position
		board.set(row, col, player.cell)

	return board


# ---------------------------------------------------------------------
# Board factories and parametrized fixtures
# ---------------------------------------------------------------------

@pytest.fixture(params=BOARD_TYPES, ids=lambda board_type: board_type.__name__)
def board_type(request):
	return request.param


@pytest.fixture
def board(board_type):
	return board_type(size=11)


@pytest.fixture
def board_types():
	return list(BOARD_TYPES)


@pytest.fixture
def search_board():
	return SearchBoard(size=11)


@pytest.fixture
def union_find_board():
	return UnionFindBoard(size=11)


@pytest.fixture(params=[3, 5, 7, 11], ids=lambda size: f"size{size}")
def board_size(request):
	return request.param


@pytest.fixture
def make_board():
	def _make_board(board_type=SearchBoard, size=11):
		return board_type(size=size)

	return _make_board


@pytest.fixture
def make_board_from_serialization():
	def _make_board(serialized, board_type=SearchBoard):
		return board_type.deserialize(serialized)

	return _make_board


@pytest.fixture
def make_board_from_moves():
	"""Replay a move sequence on a fresh board of the given type and size."""
	def _make_board(moves, board_type=SearchBoard, size=11):
		return _replay_game(board_type, moves, size=size)

	return _make_board


# ---------------------------------------------------------------------
# Random (but reproducible and legal) playouts
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class Playout:
	size: int
	seed: int
	moves: tuple


@pytest.fixture
def make_random_playout(reference):
	def _make_random_playout(size, seed):
		return Playout(
			size=size,
			seed=seed,
			moves=reference.random_playout(size, seed),
		)

	return _make_random_playout


@pytest.fixture(
	params=[
		(size, seed)
		for size in PLAYOUT_SIZES
		for seed in PLAYOUT_SEEDS
	],
	ids=lambda case: f"size{case[0]}-seed{case[1]}",
)
def playout(request, make_random_playout):
	size, seed = request.param
	return make_random_playout(size, seed)


# ---------------------------------------------------------------------
# Standard board positions
# ---------------------------------------------------------------------

@pytest.fixture
def empty_board(board_type):
	return board_type(size=11)


@pytest.fixture
def initial_board_serialization():
	return (
		"11,11,"
		"XRRRRRRRRRX"
		"BWBWBWBWBWB"
		"BRWRWRWRWRB"
		"BWBWBWBWBWB"
		"BRWRWRWRWRB"
		"BWBWBWBWBWB"
		"BRWRWRWRWRB"
		"BWBWBWBWBWB"
		"BRWRWRWRWRB"
		"BWBWBWBWBWB"
		"XRRRRRRRRRX"
	)


@pytest.fixture
def initial_board_text():
	return "\n".join((
		"⬛🟥🟥🟥🟥🟥🟥🟥🟥🟥⬛",
		"🟦⬜🟦⬜🟦⬜🟦⬜🟦⬜🟦",
		"🟦🟥⬜🟥⬜🟥⬜🟥⬜🟥🟦",
		"🟦⬜🟦⬜🟦⬜🟦⬜🟦⬜🟦",
		"🟦🟥⬜🟥⬜🟥⬜🟥⬜🟥🟦",
		"🟦⬜🟦⬜🟦⬜🟦⬜🟦⬜🟦",
		"🟦🟥⬜🟥⬜🟥⬜🟥⬜🟥🟦",
		"🟦⬜🟦⬜🟦⬜🟦⬜🟦⬜🟦",
		"🟦🟥⬜🟥⬜🟥⬜🟥⬜🟥🟦",
		"🟦⬜🟦⬜🟦⬜🟦⬜🟦⬜🟦",
		"⬛🟥🟥🟥🟥🟥🟥🟥🟥🟥⬛",
	))


# ---------------------------------------------------------------------
# Red winning position
# ---------------------------------------------------------------------

@pytest.fixture
def red_winning_serialization():
	return (
		"11,11,"
		"XRRRRRRRRRX"
		"BWBRBWBRBRB"
		"BRWRBRRRBRB"
		"BWBBBRBRBBB"
		"BRBRRRRRBRB"
		"BRBBBBBRBRB"
		"BRBRRRRRBRB"
		"BWBBBRBBBWB"
		"BRBRRRBRBRB"
		"BWBRBRBWBBB"
		"XRRRRRRRRRX"
	)


@pytest.fixture
def red_winning_moves():
	return (
		((2, 6), PlayerColor.RED),
		((6, 2), PlayerColor.BLUE),
		((5, 9), PlayerColor.RED),
		((8, 6), PlayerColor.BLUE),
		((1, 9), PlayerColor.RED),
		((8, 8), PlayerColor.BLUE),
		((4, 4), PlayerColor.RED),
		((4, 2), PlayerColor.BLUE),
		((1, 3), PlayerColor.RED),
		((4, 8), PlayerColor.BLUE),
		((6, 4), PlayerColor.RED),
		((2, 8), PlayerColor.BLUE),
		((9, 3), PlayerColor.RED),
		((3, 3), PlayerColor.BLUE),
		((7, 5), PlayerColor.RED),
		((6, 8), PlayerColor.BLUE),
		((1, 7), PlayerColor.RED),
		((7, 3), PlayerColor.BLUE),
		((3, 5), PlayerColor.RED),
		((9, 9), PlayerColor.BLUE),
		((4, 6), PlayerColor.RED),
		((5, 5), PlayerColor.BLUE),
		((5, 7), PlayerColor.RED),
		((2, 4), PlayerColor.BLUE),
		((8, 4), PlayerColor.RED),
		((7, 7), PlayerColor.BLUE),
		((9, 5), PlayerColor.RED),
		((5, 3), PlayerColor.BLUE),
		((3, 7), PlayerColor.RED),
		((3, 9), PlayerColor.BLUE),
		((5, 1), PlayerColor.RED),
		((8, 2), PlayerColor.BLUE),
		((6, 6), PlayerColor.RED),
	)


@pytest.fixture
def red_winning_board(red_winning_serialization):
	def _make_board(board_type=SearchBoard):
		return board_type.deserialize(red_winning_serialization)

	return _make_board


@pytest.fixture
def red_winning_game(
	red_winning_moves,
	red_winning_serialization,
):
	def _make_game(board_type=SearchBoard):
		board = _replay_game(board_type, red_winning_moves)

		assert board.serialize() == red_winning_serialization
		assert board.winner is PlayerColor.RED

		return board

	return _make_game


# Red wins with a path that changes direction (down, right, down, right, down).
# Reached by legal alternating play on a 7 x 7 board.

@pytest.fixture
def red_turning_winning_serialization():
	return (
		"7,7,"
		"XRRRRRX"
		"BRBBBWB"
		"BRRRWRB"
		"BWBRBBB"
		"BRBRRRB"
		"BBBWBRB"
		"XRRRRRX"
	)


@pytest.fixture
def red_turning_winning_moves():
	return (
		((1, 1), PlayerColor.RED),
		((1, 3), PlayerColor.BLUE),
		((2, 2), PlayerColor.RED),
		((3, 5), PlayerColor.BLUE),
		((3, 3), PlayerColor.RED),
		((4, 2), PlayerColor.BLUE),
		((4, 4), PlayerColor.RED),
		((5, 1), PlayerColor.BLUE),
		((5, 5), PlayerColor.RED),
	)


@pytest.fixture
def red_turning_winning_board(red_turning_winning_serialization):
	def _make_board(board_type=SearchBoard):
		return board_type.deserialize(red_turning_winning_serialization)

	return _make_board


@pytest.fixture
def red_turning_winning_game(
	red_turning_winning_moves,
	red_turning_winning_serialization,
):
	def _make_game(board_type=SearchBoard):
		board = _replay_game(board_type, red_turning_winning_moves, size=7)

		assert board.serialize() == red_turning_winning_serialization
		assert board.winner is PlayerColor.RED

		return board

	return _make_game


# ---------------------------------------------------------------------
# Blue winning position
# ---------------------------------------------------------------------

@pytest.fixture
def blue_winning_serialization():
	return (
		"11,11,"
		"XRRRRRRRRRX"
		"BWBBBRBBBRB"
		"BRBRBRRRRRB"
		"BBBWBBBBBRB"
		"BRRRRRBRBRB"
		"BRBRBBBRBRB"
		"BRWRRRRRBRB"
		"BBBBBRBRBBB"
		"BRRRBRWRWRB"
		"BBBRBBBRBBB"
		"XRRRRRRRRRX"
	)


@pytest.fixture
def blue_winning_moves():
	return (
		((1, 9), PlayerColor.RED),
		((7, 3), PlayerColor.BLUE),
		((9, 7), PlayerColor.RED),
		((9, 5), PlayerColor.BLUE),
		((8, 2), PlayerColor.RED),
		((4, 8), PlayerColor.BLUE),
		((7, 5), PlayerColor.RED),
		((6, 8), PlayerColor.BLUE),
		((6, 4), PlayerColor.RED),
		((9, 9), PlayerColor.BLUE),
		((5, 7), PlayerColor.RED),
		((9, 1), PlayerColor.BLUE),
		((5, 3), PlayerColor.RED),
		((3, 5), PlayerColor.BLUE),
		((5, 1), PlayerColor.RED),
		((7, 1), PlayerColor.BLUE),
		((2, 6), PlayerColor.RED),
		((3, 1), PlayerColor.BLUE),
		((2, 8), PlayerColor.RED),
		((5, 5), PlayerColor.BLUE),
		((4, 2), PlayerColor.RED),
		((2, 2), PlayerColor.BLUE),
		((9, 3), PlayerColor.RED),
		((8, 4), PlayerColor.BLUE),
		((3, 9), PlayerColor.RED),
		((7, 9), PlayerColor.BLUE),
		((6, 6), PlayerColor.RED),
		((1, 7), PlayerColor.BLUE),
		((1, 5), PlayerColor.RED),
		((4, 6), PlayerColor.BLUE),
		((7, 7), PlayerColor.RED),
		((1, 3), PlayerColor.BLUE),
		((5, 9), PlayerColor.RED),
		((2, 4), PlayerColor.BLUE),
		((4, 4), PlayerColor.RED),
		((3, 7), PlayerColor.BLUE),
	)


@pytest.fixture
def blue_winning_board(blue_winning_serialization):
	def _make_board(board_type=SearchBoard):
		return board_type.deserialize(blue_winning_serialization)

	return _make_board


@pytest.fixture
def blue_winning_game(
	blue_winning_moves,
	blue_winning_serialization,
):
	def _make_game(board_type=SearchBoard):
		board = _replay_game(board_type, blue_winning_moves)

		assert board.serialize() == blue_winning_serialization
		assert board.winner is PlayerColor.BLUE

		return board

	return _make_game


# Blue wins with a path that changes direction (right, down, right, down, right).
# Reached by legal alternating play on a 7 x 7 board.

@pytest.fixture
def blue_turning_winning_serialization():
	return (
		"7,7,"
		"XRRRRRX"
		"BBBRBWB"
		"BRBRRRB"
		"BRBBBRB"
		"BRWRBRB"
		"BWBRBBB"
		"XRRRRRX"
	)


@pytest.fixture
def blue_turning_winning_moves():
	return (
		((1, 3), PlayerColor.RED),
		((1, 1), PlayerColor.BLUE),
		((3, 1), PlayerColor.RED),
		((2, 2), PlayerColor.BLUE),
		((2, 4), PlayerColor.RED),
		((3, 3), PlayerColor.BLUE),
		((5, 3), PlayerColor.RED),
		((4, 4), PlayerColor.BLUE),
		((3, 5), PlayerColor.RED),
		((5, 5), PlayerColor.BLUE),
	)


@pytest.fixture
def blue_turning_winning_board(blue_turning_winning_serialization):
	def _make_board(board_type=SearchBoard):
		return board_type.deserialize(blue_turning_winning_serialization)

	return _make_board


@pytest.fixture
def blue_turning_winning_game(
	blue_turning_winning_moves,
	blue_turning_winning_serialization,
):
	def _make_game(board_type=SearchBoard):
		board = _replay_game(board_type, blue_turning_winning_moves, size=7)

		assert board.serialize() == blue_turning_winning_serialization
		assert board.winner is PlayerColor.BLUE

		return board

	return _make_game


# ---------------------------------------------------------------------
# Full board (Red winning position)
#
# On an odd-sized board the number of white cells is odd, so Red always
# makes the last possible move. A full board that is reached by legal play
# is therefore always a Red win.
# ---------------------------------------------------------------------

@pytest.fixture
def full_board_serialization():
	return (
		"11,11,"
		"XRRRRRRRRRX"
		"BBBBBBBBBRB"
		"BRRRRRRRRRB"
		"BRBBBBBBBBB"
		"BRBRRRRRRRB"
		"BRBRBRBBBBB"
		"BRRRRRRRBRB"
		"BBBRBBBBBRB"
		"BRBRRRBRBRB"
		"BBBRBRBRBBB"
		"XRRRRRRRRRX"
	)


@pytest.fixture
def full_board_moves():
	return (
		((9, 7), PlayerColor.RED),
		((9, 1), PlayerColor.BLUE),
		((9, 5), PlayerColor.RED),
		((7, 7), PlayerColor.BLUE),
		((5, 5), PlayerColor.RED),
		((7, 1), PlayerColor.BLUE),
		((5, 3), PlayerColor.RED),
		((6, 8), PlayerColor.BLUE),
		((7, 3), PlayerColor.RED),
		((5, 7), PlayerColor.BLUE),
		((4, 4), PlayerColor.RED),
		((3, 3), PlayerColor.BLUE),
		((9, 3), PlayerColor.RED),
		((8, 6), PlayerColor.BLUE),
		((6, 2), PlayerColor.RED),
		((8, 8), PlayerColor.BLUE),
		((2, 8), PlayerColor.RED),
		((1, 7), PlayerColor.BLUE),
		((7, 9), PlayerColor.RED),
		((8, 2), PlayerColor.BLUE),
		((3, 1), PlayerColor.RED),
		((3, 9), PlayerColor.BLUE),
		((4, 6), PlayerColor.RED),
		((3, 7), PlayerColor.BLUE),
		((5, 1), PlayerColor.RED),
		((1, 3), PlayerColor.BLUE),
		((1, 9), PlayerColor.RED),
		((7, 5), PlayerColor.BLUE),
		((8, 4), PlayerColor.RED),
		((1, 5), PlayerColor.BLUE),
		((6, 6), PlayerColor.RED),
		((9, 9), PlayerColor.BLUE),
		((6, 4), PlayerColor.RED),
		((3, 5), PlayerColor.BLUE),
		((2, 2), PlayerColor.RED),
		((5, 9), PlayerColor.BLUE),
		((2, 4), PlayerColor.RED),
		((4, 2), PlayerColor.BLUE),
		((4, 8), PlayerColor.RED),
		((1, 1), PlayerColor.BLUE),
		((2, 6), PlayerColor.RED),
	)


@pytest.fixture
def full_board(full_board_serialization):
	def _make_board(board_type=SearchBoard):
		return board_type.deserialize(full_board_serialization)

	return _make_board


@pytest.fixture
def full_winning_game(
	full_board_moves,
	full_board_serialization,
):
	def _make_game(board_type=SearchBoard):
		board = _replay_game(board_type, full_board_moves)

		assert board.serialize() == full_board_serialization
		assert not board.available
		assert board.winner is PlayerColor.RED

		return board

	return _make_game


# ---------------------------------------------------------------------
# All terminal positions, for tests that should hold for every one of them
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TerminalPosition:
	name: str
	size: int
	serialization: str
	moves: tuple
	winner: PlayerColor


_TERMINAL_POSITIONS = (
	("red_winning", 11, PlayerColor.RED),
	("blue_winning", 11, PlayerColor.BLUE),
	("full_board", 11, PlayerColor.RED),
	("red_turning_winning", 7, PlayerColor.RED),
	("blue_turning_winning", 7, PlayerColor.BLUE),
)


@pytest.fixture(
	params=_TERMINAL_POSITIONS,
	ids=lambda case: case[0],
)
def terminal_position(request):
	name, size, winner = request.param

	return TerminalPosition(
		name=name,
		size=size,
		serialization=request.getfixturevalue(f"{name}_serialization"),
		moves=request.getfixturevalue(f"{name}_moves"),
		winner=winner,
	)


# ---------------------------------------------------------------------
# Common player and cell fixtures
# ---------------------------------------------------------------------

@pytest.fixture(params=[PlayerColor.RED, PlayerColor.BLUE], ids=lambda color: color.name)
def player_color(request):
	return request.param


@pytest.fixture(params=[Cell.RED, Cell.BLUE], ids=lambda cell: cell.name)
def player_cell(request):
	return request.param


# ---------------------------------------------------------------------
# Players and move scores
# ---------------------------------------------------------------------

class FirstMovePlayer(Player):
	"""Chooses the first available move in row-major order."""

	def select_move(self, board, color):
		return min(board.available)


class IndexScoringPlayer(ScoringPlayer):
	"""Scores every available move by its row-major index (all distinct)."""

	def __init__(self, color, selector=None):
		super().__init__(color, selector=selector)
		self.scored_colors = []

	def score_moves(self, board, color):
		self.scored_colors.append(color)

		return {
			(row, col): float(row * board.cols + col)
			for row, col in board.available
		}


class TiedScoringPlayer(ScoringPlayer):
	"""Gives every available move the same score."""

	def score_moves(self, board, color):
		return {move: 0.0 for move in board.available}


@pytest.fixture
def first_move_player_class():
	return FirstMovePlayer


@pytest.fixture
def index_scoring_player_class():
	return IndexScoringPlayer


@pytest.fixture
def tied_scoring_player_class():
	return TiedScoringPlayer


@pytest.fixture
def move_scores():
	"""Scores with a single best and a single worst move."""
	return {
		(1, 1): 1.0,
		(1, 3): 5.0,
		(3, 1): 3.0,
		(3, 3): -2.0,
	}


@pytest.fixture
def tied_move_scores():
	"""Scores with two moves tied for best and two tied for worst."""
	return {
		(1, 1): 1.0,
		(1, 3): 1.0,
		(3, 1): 5.0,
		(3, 3): 5.0,
		(5, 5): 3.0,
	}


class DeterministicFirstMovePlayer(DeterministicMoveSelectionMixin, FirstMovePlayer):
	"""Always plays the first available move (a deterministic policy)."""


class DeterministicLastMovePlayer(DeterministicMoveSelectionMixin, Player):
	"""Always plays the last available move (a deterministic policy)."""

	def select_move(self, board, color):
		return max(board.available)


class RandomMovePlayer(Player):
	"""Plays a uniformly random available move (not deterministic)."""

	def __init__(self, color):
		super().__init__(color)
		self._random = random.Random()

	def select_move(self, board, color):
		return self._random.choice(sorted(board.available))


class DeterministicIndexScoringPlayer(DeterministicScoringMixin, IndexScoringPlayer):
	"""Deterministic scores and a deterministic (best-move) selector."""


class UniqueBestRandomScoringPlayer(
	DeterministicScoringMixin,
	RandomMaxSelectorMixin,
	IndexScoringPlayer,
):
	"""Deterministic scores with a random selector.

	The scores never tie, so every individual move is deterministic even
	though the player as a whole is not.
	"""


@pytest.fixture
def deterministic_first_move_player_class():
	return DeterministicFirstMovePlayer


@pytest.fixture
def deterministic_last_move_player_class():
	return DeterministicLastMovePlayer


@pytest.fixture
def random_move_player_class():
	return RandomMovePlayer


@pytest.fixture
def deterministic_scoring_player_class():
	return DeterministicIndexScoringPlayer


@pytest.fixture
def unique_best_random_scoring_player_class():
	return UniqueBestRandomScoringPlayer


# ---------------------------------------------------------------------
# Progress bars
# ---------------------------------------------------------------------

class RecordingProgress:
	"""Stand-in for a tqdm progress bar that records how it is used."""

	def __init__(self, *args, **kwargs):
		self.init_kwargs = kwargs
		self.updates = 0
		self.postfixes = []
		self.closed = False
		self.entered = False

	def update(self, amount=1):
		self.updates += amount

	def set_postfix(self, *args, **kwargs):
		self.postfixes.append(kwargs)

	def close(self):
		self.closed = True

	def __enter__(self):
		self.entered = True

		return self

	def __exit__(self, *exc_info):
		self.close()

		return False


@pytest.fixture
def recording_progress():
	return RecordingProgress()


@pytest.fixture
def patched_tqdm(monkeypatch):
	"""Replace tqdm in the tournament modules; returns the bars created."""
	created = []

	def factory(*args, **kwargs):
		progress = RecordingProgress(*args, **kwargs)
		created.append(progress)

		return progress

	monkeypatch.setattr("via_ludus.tournament.matchup.tqdm", factory)
	monkeypatch.setattr("via_ludus.tournament.tournament.tqdm", factory)

	return created


# ---------------------------------------------------------------------
# Tournament results
# ---------------------------------------------------------------------

R = PlayerColor.RED
B = PlayerColor.BLUE


@pytest.fixture
def sample_results():
	"""Three players and four matchups with hand-computed statistics.

	alpha (red) vs beta (blue):  4 games
	beta (red) vs alpha (blue):  3 games
	alpha (red) vs gamma (blue): 2 games
	gamma (red) vs beta (blue):  1 game
	"""
	results = TournamentResults(["alpha", "beta", "gamma"])

	results.add_matchup_data("alpha", "beta", [R, R, B, R], [10, 12, 9, 14], [True, True, False, False])
	results.add_matchup_data("beta", "alpha", [B, R, B], [11, 13, 15], [False, False, True])
	results.add_matchup_data("alpha", "gamma", [B, B], [20, 22], [True, True])
	results.add_matchup_data("gamma", "beta", [R], [8], [True])

	return results


@pytest.fixture
def full_results():
	"""Two players with three games in every ordered pairing."""
	results = TournamentResults(["a", "b"])

	results.add_matchup_data("a", "a", [R, R, B], [5, 7, 6], [True, True, True])
	results.add_matchup_data("a", "b", [R, B, B], [9, 8, 10], [True, False, False])
	results.add_matchup_data("b", "a", [B, B, R], [11, 12, 13], [False, False, True])
	results.add_matchup_data("b", "b", [B, R, R], [4, 6, 5], [True, True, True])

	return results


# ---------------------------------------------------------------------
# Simulating missing packages inside the test process
# ---------------------------------------------------------------------

class _ImportBlocker(importlib.abc.MetaPathFinder):
	"""Makes ``import <name>`` fail exactly as if the package were missing."""

	def __init__(self, names):
		self.names = tuple(names)

	def find_spec(self, fullname, path=None, target=None):
		for name in self.names:
			if fullname == name or fullname.startswith(name + "."):
				raise ModuleNotFoundError(
					f"No module named {fullname!r}",
					name=fullname,
				)

		return None


@pytest.fixture
def block_imports(monkeypatch):
	"""Block imports of the given packages (and their submodules).

	Everything is undone automatically at the end of the test. Modules that
	are already imported are hidden for the duration of the test, so code
	that is imported *afterwards* sees the packages as missing.
	"""
	def _block_imports(*names):
		for loaded in list(sys.modules):
			if any(loaded == name or loaded.startswith(name + ".") for name in names):
				monkeypatch.delitem(sys.modules, loaded)

		monkeypatch.setattr(
			sys,
			"meta_path",
			[_ImportBlocker(names), *sys.meta_path],
		)

	return _block_imports


# ---------------------------------------------------------------------
# matplotlib (optional dependency)
# ---------------------------------------------------------------------

@pytest.fixture
def plt():
	"""pyplot with a non-interactive backend; skips when matplotlib is missing."""
	matplotlib = pytest.importorskip("matplotlib")
	matplotlib.use("Agg", force=True)

	import matplotlib.pyplot as pyplot

	yield pyplot

	pyplot.close("all")


@pytest.fixture
def patch_colors():
	"""Map each board position to the face color of its drawn rectangle."""
	def _patch_colors(ax, board):
		colors = {}

		for patch in ax.patches:
			x, y = patch.get_xy()
			colors[(board.rows - int(y) - 1, int(x))] = patch.get_facecolor()

		return colors

	return _patch_colors
