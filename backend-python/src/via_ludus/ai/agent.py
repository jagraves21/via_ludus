from abc import ABC, abstractmethod
import inspect
import warnings

from ..board import validate_player_color
from ..player import Player, ScoringPlayer


class AgentBase(ABC):
	_registry = {}
	_warned_agent_names = set()

	def __init_subclass__(cls, **kwargs):
		super().__init_subclass__(**kwargs)

		if inspect.isabstract(cls):
			return

		name = cls.get_agent_name()

		if name in AgentBase._registry:
			raise ValueError(f"Duplicate agent name: {name}")

		AgentBase._registry[name] = cls

	@classmethod
	def get_agent_name(cls):
		name = cls.__dict__.get("name")

		if name is not None:
			return name

		name = cls.__name__

		if name not in AgentBase._warned_agent_names:
			warnings.warn(
				f"{name} does not define a custom agent name; "
				"using its class name instead.",
				UserWarning,
				stacklevel=2,
			)
			AgentBase._warned_agent_names.add(name)

		return name

	@classmethod
	def get_agents(cls):
		return dict(AgentBase._registry)


class Agent(AgentBase, Player, ABC):
	pass


class ScoringAgent(AgentBase, ScoringPlayer, ABC):
	def score_moves(self, board, color):
		validate_player_color(color)

		scores = self.evaluate_move_options(board, color)
		available = board.available

		return {
			move: score
			for move, score in scores.items()
			if move in available
		}

	@abstractmethod
	def evaluate_move_options(self, board, color):
		pass

