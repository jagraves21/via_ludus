import numpy as np
import pytest

from via_ludus.ai import Agent, AgentBase, ScoringAgent
from via_ludus.ai.via_ludus_agents import RandomAgent
from via_ludus.board import PlayerColor


class FakeBoard:
	"""A board that only has the positions an agent may choose from."""

	def __init__(self, available):
		self.available = available


class TestRandomAgent:
	def test_has_the_name_random(self):
		assert RandomAgent.get_agent_name() == "Random"

	def test_is_registered_under_its_name(self):
		assert AgentBase.get_agents()["Random"] is RandomAgent

	def test_is_a_plain_agent_not_a_scoring_agent(self):
		assert issubclass(RandomAgent, Agent)
		assert not issubclass(RandomAgent, ScoringAgent)

	def test_is_not_deterministic(self, player_color):
		assert RandomAgent(player_color).is_deterministic is False


class TestSelectMove:
	def test_returns_an_available_move(self, board, player_color):
		move = RandomAgent(player_color).select_move(board, player_color)

		assert move in board.available

	def test_can_be_asked_about_the_opponent(self, board, player_color):
		move = RandomAgent(player_color).select_move(board, player_color.opponent)

		assert move in board.available

	def test_returns_plain_python_integers(self, board, player_color):
		row, col = RandomAgent(player_color).select_move(board, player_color)

		assert type(row) is int
		assert type(col) is int

	def test_converts_numpy_integers_to_python_integers(self):
		board = FakeBoard({(np.int32(1), np.int64(3))})

		row, col = RandomAgent(PlayerColor.RED).select_move(board, PlayerColor.RED)

		assert (row, col) == (1, 3)
		assert type(row) is int
		assert type(col) is int

	def test_returns_the_only_available_move(self, player_color):
		board = FakeBoard({(2, 2)})

		assert RandomAgent(player_color).select_move(board, player_color) == (2, 2)

	def test_does_not_modify_the_board(self, board, player_color):
		before = board.serialize()

		RandomAgent(player_color).select_move(board, player_color)

		assert board.serialize() == before

	def test_varies_its_moves(self, board, player_color):
		agent = RandomAgent(player_color)

		moves = {agent.select_move(board, player_color) for _ in range(200)}

		assert len(moves) > 1
		assert moves <= board.available

	def test_can_choose_every_available_move(self, board_type, player_color):
		board = board_type(size=5)
		agent = RandomAgent(player_color)

		moves = {agent.select_move(board, player_color) for _ in range(500)}

		assert moves == board.available


class TestChooseMove:
	def test_plays_an_available_move(self, board, player_color):
		move = RandomAgent(player_color).choose_move(board)

		assert move in board.available

	def test_can_play_a_whole_game(self):
		from via_ludus.tournament import Game

		assert Game(RandomAgent, RandomAgent).play() in (PlayerColor.RED, PlayerColor.BLUE)
