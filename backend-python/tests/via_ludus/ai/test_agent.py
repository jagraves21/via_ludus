import pytest

from via_ludus.ai import Agent, AgentBase, ScoringAgent
from via_ludus.board import Cell, PlayerColor
from via_ludus.player import scoring


# Agents register themselves by name when the class is defined, so every
# class below has a unique name and is defined once, at module level.

class FirstCellAgent(Agent):
	name = "TestAgent.FirstCell"

	def select_move(self, board, color):
		return min(board.available)


class SelectRecordingAgent(Agent):
	"""Plays the first available move and remembers the color it was asked for."""

	name = "TestAgent.SelectRecording"

	def select_move(self, board, color):
		self.selected_for = color

		return min(board.available)


class RecordingScoringAgent(ScoringAgent):
	"""Scores each available move by its index, plus one unavailable move."""

	name = "TestAgent.RecordingScoring"

	def __init__(self, color, selector=None):
		super().__init__(color, selector=selector)
		self.evaluated_colors = []

	def evaluate_move_options(self, board, color):
		self.evaluated_colors.append(color)

		scores = {
			(row, col): float(row * board.cols + col)
			for row, col in board.available
		}
		scores[(0, 1)] = 1000.0  # a prefilled edge cell, never available

		return scores


class TestAgent:
	def test_subclass_must_implement_select_move(self):
		class Incomplete(Agent):
			name = "TestAgent.Incomplete"

		with pytest.raises(TypeError, match="select_move"):
			Incomplete(PlayerColor.RED)

	def test_is_registered_under_its_name(self):
		assert AgentBase.get_agents()["TestAgent.FirstCell"] is FirstCellAgent

	def test_choose_move_selects_a_move_for_the_agents_own_color(self, board, player_color):
		agent = SelectRecordingAgent(player_color)

		assert agent.choose_move(board) == min(board.available)
		assert agent.selected_for is player_color

	def test_select_move_can_be_asked_for_the_opponent(self, board, player_color):
		agent = FirstCellAgent(player_color)

		assert agent.select_move(board, player_color.opponent) == min(board.available)


class TestScoringAgent:
	def test_subclass_must_implement_evaluate_move_options(self):
		class Incomplete(ScoringAgent):
			name = "TestAgent.IncompleteScoring"

		with pytest.raises(TypeError, match="evaluate_move_options"):
			Incomplete(PlayerColor.RED)

	def test_is_registered_under_its_name(self):
		agents = AgentBase.get_agents()

		assert agents["TestAgent.RecordingScoring"] is RecordingScoringAgent


class TestScoreMoves:
	def test_drops_moves_that_are_not_available(self, board, player_color):
		agent = RecordingScoringAgent(player_color)

		scores = agent.score_moves(board, player_color)

		assert (0, 1) not in scores
		assert set(scores) == board.available

	def test_keeps_the_scores_of_available_moves(self, board, player_color):
		agent = RecordingScoringAgent(player_color)

		scores = agent.score_moves(board, player_color)

		assert scores[max(board.available)] == float(
			max(board.available)[0] * board.cols + max(board.available)[1]
		)

	def test_passes_the_color_to_evaluate_move_options(self, board, player_color):
		agent = RecordingScoringAgent(player_color)

		agent.score_moves(board, player_color.opponent)

		assert agent.evaluated_colors == [player_color.opponent]


class TestSelectMove:
	def test_never_selects_an_unavailable_move(self, board, player_color):
		agent = RecordingScoringAgent(player_color)

		assert agent.select_move(board, player_color) == max(board.available)

	def test_evaluates_for_the_given_color(self, board, player_color):
		agent = RecordingScoringAgent(player_color)

		agent.select_move(board, player_color.opponent)

		assert agent.evaluated_colors == [player_color.opponent]

	@pytest.mark.parametrize("color", ["red", Cell.RED, None, 1], ids=["str", "cell", "none", "int"])
	def test_rejects_a_color_that_is_not_a_player_color(self, board, color):
		agent = RecordingScoringAgent(PlayerColor.RED)

		with pytest.raises(TypeError, match="color must be a PlayerColor"):
			agent.select_move(board, color)

		assert agent.evaluated_colors == []


class TestChooseMove:
	def test_evaluates_for_the_agents_own_color(self, board, player_color):
		agent = RecordingScoringAgent(player_color)

		agent.choose_move(board)

		assert agent.evaluated_colors == [player_color]

	def test_the_color_is_validated_only_once_per_move_from_outside(self, board, player_color, monkeypatch):
		validated = []
		validate = scoring.validate_player_color

		def spy(color):
			validated.append(color)
			validate(color)

		monkeypatch.setattr(scoring, "validate_player_color", spy)
		agent = RecordingScoringAgent(player_color)

		agent.choose_move(board)
		agent.select_move(board, player_color.opponent)

		assert validated == [player_color.opponent]
