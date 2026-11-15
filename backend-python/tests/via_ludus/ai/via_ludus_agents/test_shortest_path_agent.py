import heapq

import pytest

from via_ludus.ai import AgentBase, ScoringAgent
from via_ludus.ai.via_ludus_agents import ShortestPathAgent
from via_ludus.board import Cell, PlayerColor, SearchBoard


R = PlayerColor.RED
B = PlayerColor.BLUE

# 5 x 5 board whose middle row is walls: Red cannot get from top to bottom,
# but Blue can go along the row above or below it.
BLOCKED_BOARD = (
	"XRRRX"
	"BWBWB"
	"BXXXB"
	"BWBWB"
	"XRRRX"
)

# 7 x 7 board with a long Red corridor that is missing one cell, (4, 3), and a
# much shorter direct column of five empty cells down the left side. The
# corridor needs only one more cell, so that is the route to score.
DETOUR_BOARD = (
	"XRRRRRX"
	"BWBBBRB"
	"BWBRRRB"
	"BWBRBBB"
	"BWBWRRB"
	"BWBBBRB"
	"XRRRRRX"
)


def cells_needed(board, color):
	"""The fewest white cells `color` must claim to connect its two sides.

	An independent Dijkstra search (cost 1 for a white cell, 0 for the
	player's own cells), or None if the sides cannot be connected.
	"""
	rows, cols = board.shape
	own = color.cell

	if color is R:
		starts = [(0, col) for col in range(cols)]
		is_goal = lambda row, col: row == rows - 1
	else:
		starts = [(row, 0) for row in range(rows)]
		is_goal = lambda row, col: col == cols - 1

	best = {}
	heap = []

	for row, col in starts:
		cell = board.get(row, col)

		if cell in (Cell.WHITE, own):
			cost = int(cell == Cell.WHITE)
			best[(row, col)] = cost
			heapq.heappush(heap, (cost, row, col))

	while heap:
		cost, row, col = heapq.heappop(heap)

		if cost > best[(row, col)]:
			continue

		if is_goal(row, col):
			return cost

		for next_row, next_col in board.neighbors(row, col):
			cell = board.get(next_row, next_col)

			if cell not in (Cell.WHITE, own):
				continue

			next_cost = cost + int(cell == Cell.WHITE)

			if next_cost < best.get((next_row, next_col), float("inf")):
				best[(next_row, next_col)] = next_cost
				heapq.heappush(heap, (next_cost, next_row, next_col))

	return None


def claim(board, moves, color):
	trial = board.copy()

	for row, col in moves:
		trial.set(row, col, color.cell)

	return trial


class TestShortestPathAgent:
	def test_has_the_name_dijkstra(self):
		assert ShortestPathAgent.get_agent_name() == "Dijkstra"

	def test_is_registered_under_its_name(self):
		assert AgentBase.get_agents()["Dijkstra"] is ShortestPathAgent

	def test_is_a_scoring_agent(self):
		assert issubclass(ShortestPathAgent, ScoringAgent)

	def test_declares_deterministic_scoring(self, player_color):
		assert ShortestPathAgent(player_color).has_deterministic_scoring is True

	def test_is_not_fully_deterministic_because_it_breaks_ties_randomly(self, player_color):
		assert ShortestPathAgent(player_color).is_deterministic is False


class TestScores:
	def test_every_scored_move_is_available_and_scores_one(self, board, player_color):
		scores = ShortestPathAgent(player_color).score_moves(board, player_color)

		assert scores
		assert set(scores) <= board.available
		assert set(scores.values()) == {1}

	def test_scores_exactly_the_cells_a_shortest_path_still_needs(self, board, player_color):
		scores = ShortestPathAgent(player_color).score_moves(board, player_color)

		assert len(scores) == cells_needed(board, player_color)

	def test_positions_are_plain_python_integers(self, board, player_color):
		scores = ShortestPathAgent(player_color).score_moves(board, player_color)

		for row, col in scores:
			assert type(row) is int
			assert type(col) is int

	def test_claiming_the_scored_cells_connects_the_sides(self, board, player_color):
		scores = ShortestPathAgent(player_color).score_moves(board, player_color)

		trial = claim(board, scores, player_color)

		assert trial.winner is player_color

	def test_can_score_for_the_opponent(self, board, player_color):
		opponent = player_color.opponent

		scores = ShortestPathAgent(player_color).score_moves(board, opponent)

		assert len(scores) == cells_needed(board, opponent)
		assert claim(board, scores, opponent).winner is opponent

	def test_claiming_a_scored_cell_shortens_the_path_by_one(self, board, player_color):
		agent = ShortestPathAgent(player_color)
		scores = agent.score_moves(board, player_color)

		trial = claim(board, [min(scores)], player_color)

		assert len(agent.score_moves(trial, player_color)) == len(scores) - 1

	def test_the_path_goes_around_cells_the_opponent_has_taken(self, board, player_color):
		agent = ShortestPathAgent(player_color)
		scores = agent.score_moves(board, player_color)
		blocked = claim(board, [min(scores)], player_color.opponent)

		new_scores = agent.score_moves(blocked, player_color)

		assert min(scores) not in new_scores
		assert len(new_scores) == cells_needed(blocked, player_color)

	def test_prefers_a_longer_route_through_its_own_cells_to_a_shorter_empty_one(self):
		board = SearchBoard.deserialize(f"7,7,{DETOUR_BOARD}")

		assert cells_needed(board, R) == 1
		assert ShortestPathAgent(R).score_moves(board, R) == {(4, 3): 1}

	def test_no_scores_once_the_sides_are_connected(self, board, player_color):
		agent = ShortestPathAgent(player_color)
		scores = agent.score_moves(board, player_color)
		connected = claim(board, scores, player_color)

		assert agent.score_moves(connected, player_color) == {}

	def test_no_scores_when_the_sides_cannot_be_connected(self):
		board = SearchBoard.deserialize(f"5,5,{BLOCKED_BOARD}")

		assert cells_needed(board, R) is None
		assert ShortestPathAgent(R).score_moves(board, R) == {}

	def test_scores_the_player_that_can_still_connect_on_a_blocked_board(self):
		board = SearchBoard.deserialize(f"5,5,{BLOCKED_BOARD}")

		scores = ShortestPathAgent(B).score_moves(board, B)

		assert set(scores) == {(3, 1), (3, 3)}

	def test_does_not_modify_the_board(self, board, player_color):
		before = board.serialize()

		ShortestPathAgent(player_color).score_moves(board, player_color)

		assert board.serialize() == before

	def test_scores_do_not_change_for_the_same_position(self, board, player_color):
		agent = ShortestPathAgent(player_color)

		first = agent.score_moves(board, player_color)

		assert agent.score_moves(board, player_color) == first


class TestChooseMove:
	def test_plays_a_cell_on_a_shortest_path(self, board, player_color):
		agent = ShortestPathAgent(player_color)
		scored = set(agent.score_moves(board, player_color))

		moves = {agent.choose_move(board) for _ in range(100)}

		assert moves <= scored

	def test_varies_among_equally_good_cells(self, board, player_color):
		agent = ShortestPathAgent(player_color)

		assert len(agent.score_moves(board, player_color)) > 1

		assert len({agent.choose_move(board) for _ in range(200)}) > 1

	def test_returns_plain_python_integers(self, board, player_color):
		row, col = ShortestPathAgent(player_color).choose_move(board)

		assert type(row) is int
		assert type(col) is int

	def test_fails_when_there_is_nothing_to_score(self):
		board = SearchBoard.deserialize(f"5,5,{BLOCKED_BOARD}")

		with pytest.raises(ValueError, match="No available moves with finite scores"):
			ShortestPathAgent(R).choose_move(board)

	def test_can_play_a_whole_game_against_itself(self):
		from via_ludus.tournament import Game

		assert Game(ShortestPathAgent, ShortestPathAgent).play() in (R, B)
