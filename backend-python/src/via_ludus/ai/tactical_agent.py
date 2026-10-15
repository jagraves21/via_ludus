from abc import abstractmethod

from ..board import validate_player_color
from .graphs import (
	board_to_move_graph,
	minimum_endpoint_cut,
)
from .agent import Agent


class TacticalAgent(Agent):
	def score_moves(self, board, color, tactics=False):
		validate_player_color(color)
		
		if tactics:
			# take an immediate winning move
			graph = board_to_move_graph(board, color)
			cut = minimum_endpoint_cut(graph)

			if len(cut) == 1:
				return {next(iter(cut)): 0}

			# block an immediate losing move
			graph = board_to_move_graph(board, color.opponent)
			cut = minimum_endpoint_cut(graph)

			if len(cut) == 1:
				return {next(iter(cut)): 0}

		# let the derived agent decide
		return super().score_moves(board, color)

