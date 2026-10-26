from tqdm.auto import tqdm

import numpy as np

from ..board import (
	PlayerColor,
	UnionFindBoard as ViaLudusBoard
)
from ..player import Player
from ..tournament import play_matchup
from ..validation import validate_player_class

from .agent import Agent
#from .cut_agent import (
#	OffensiveOverlapCutAgent as RedPlayer,
#	OffensiveOverlapCutAgent as BluePlayer,
#)

from .random_agent import (
	RandomAgent as RedPlayer,
	RandomAgent as BluePlayer,
)


class NullProgress:
	def set_postfix(self, **kwargs):
		pass

	def update(self, n=1):
		pass


class MonteCarloAgent(Agent):
	name = "MonteCarloAgent"

	def __init__(
		self,
		color,
		num_simulations=2,
		selector=None,
		red_player=None,
		blue_player=None,
	):
		super().__init__(
			color=color,
			selector=selector,
		)

		if num_simulations <= 0:
			raise ValueError(
				"num_simulations must be greater than 0"
			)

		red_player = RedPlayer if red_player is None else red_player
		blue_player = BluePlayer if red_player is None else red_player
		
		validate_player_class(red_player)
		validate_player_class(blue_player)

		self._simulations = num_simulations
		self._red_player = red_player
		self._blue_player = blue_player

	@property
	def num_simulations(self):
		return self._simulations

	@property
	def red_player(self):
		return self._red_player
	
	@property
	def blue_player(self):
		return self._blue_player

	def evaluate_move_options(self, board, color):
		scores = {}

		tmp_board = ViaLudusBoard.from_board(board)

		with tqdm(
			total=len(board.available)*self.num_simulations,
			desc=f"MonteCarloAgent {len(board.available)} x {self.num_simulations}",
			unit="game",
		) as move_progress:
			for move in board.available:
				tmp_board.set(*move, color.cell)

				results = play_matchup(
					red_player=self.red_player,
					blue_player=self.blue_player,
					num_games=self.num_simulations,
					board=tmp_board,
					starting_color=color.opponent,
					progress=move_progress, #NullProgress(),
					red_name="mc_red",
					blue_name="mc_blue",
				)

				matchup_results = results.get_matchup_results(
					"mc_red", "mc_blue"
				)

				scores[move] = sum(
					result == color
					for result in matchup_results
				) / self.num_simulations


				tmp_board.reset(*move)

		return scores


class FastMonteCarloAgent(Agent):
	name = "FastMonteCarloAgent"

	def __init__(
		self,
		color,
		selector=None,
		num_simulations=100,
		seed=None,
	):
		super().__init__(
			color=color,
			selector=selector,
		)

		if num_simulations <= 0:
			raise ValueError(
				"num_simulations must be greater than 0"
			)

		self._simulations = num_simulations
		self._rng = np.random.default_rng(seed)

	@property
	def num_simulations(self):
		return self._simulations

	def evaluate_move_options(self, board, color):
		scores = {
			move: 0
			for move in board.available
		}

		tmp_board = board.copy()

		available = board.available
		for move in available:
			moves = list(available - {move})

			for _ in range(self.num_simulations):
				tmp_board._board[...] = board._board
				tmp_board.set(*move, color.cell)

				self._rng.shuffle(moves)

				current_color = color.opponent

				for tmp_move in moves:
					tmp_board.set(
						*tmp_move,
						current_color.cell,
					)

					if tmp_board.is_game_over:
						break

					current_color = current_color.opponent

				if tmp_board.winner == color:
					scores[move] += 1

		for move in scores:
			scores[move] /= self.num_simulations

		return scores


class FastMonteCarloAgent(Agent):
	name = "FastMonteCarloAgent"

	def __init__(
		self,
		color,
		num_simulations=100,
		selector=None,
		seed=None,
	):
		super().__init__(
			color=color,
			selector=selector,
		)

		if num_simulations <= 0:
			raise ValueError(
				"num_simulations must be greater than 0"
			)

		self._simulations = num_simulations
		self._rng = np.random.default_rng(seed)

	@property
	def num_simulations(self):
		return self._simulations

	def evaluate_move_options(self, board, color):
		scores = {
			move: 0
			for move in board.available
		}

		tmp_board = board.copy()

		available = board.available
		for move in available:
			moves = list(available - {move})

			for _ in range(self.num_simulations):
				tmp_board._board[...] = board._board
				tmp_board.set(*move, color.cell)

				self._rng.shuffle(moves)

				current_color = color.opponent

				for tmp_move in moves:
					tmp_board.set(
						*tmp_move,
						current_color.cell,
					)

					if tmp_board.is_game_over:
						break

					current_color = current_color.opponent

				if tmp_board.winner == color:
					scores[move] += 1

		for move in scores:
			scores[move] /= self.num_simulations

		return scores
