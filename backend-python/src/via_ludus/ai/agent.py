from abc import ABC, abstractmethod
import warnings

from ..board import (
	PlayerColor,
	validate_player_color,
)
from ..player import ScoringPlayer


class Agent(ScoringPlayer, ABC):
	_warned_agent_names = set()

	@classmethod
	def get_agent_name(cls):
		name = cls.__dict__.get("name")

		if name is not None:
			return name
			#return cls.__name__

		name = cls.__name__

		if name not in Agent._warned_agent_names:
			warnings.warn(
				f"{name} does not define a custom agent name; "
				f"using its class name instead.",
				UserWarning,
				stacklevel=2,
			)
			Agent._warned_agent_names.add(name)

		return name

	@property
	def higher_is_better(self):
		return True

	def score_moves(self, board, color):
		validate_player_color(color)

		scores = self.evaluate_move_options(board, color)
		score_sign = 1 if self.higher_is_better else -1
		available = board.available

		return {
			move: score_sign * score
			for move, score in scores.items()
			if move in available
		}

	@abstractmethod
	def evaluate_move_options(self, board, color):
		pass

