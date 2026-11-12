import pytest

from via_ludus import AI_AGENTS, PlayerColor, SearchBoard
from web_service.exceptions import AgentComputationError
from web_service.services import agents as services_agents
from web_service.services import get_agents, get_move


# Initial 7 x 7 board.
CELLS_7 = "XRRRRRXBWBWBWBBRWRWRBBWBWBWBBRWRWRBBWBWBWBXRRRRRX"

# Initial 5 x 5 board.
CELLS_5 = "XRRRXBWBWBBRWRBBWBWBXRRRX"

# 5 x 5 position after Red claims (2, 2) and Blue claims (1, 1); Red to move.
# The only white cells left are (1, 3), (3, 1) and (3, 3).
MIDGAME_CELLS_5 = (
	"XRRRX"
	"BBBWB"
	"BRRRB"
	"BWBWB"
	"XRRRX"
)
MIDGAME_MOVES_5 = {(1, 3), (3, 1), (3, 3)}

# 5 x 6 board (rows x cols).
CELLS_5X6 = (
	"XRRRRX"
	"BWWWWB"
	"BWWWWB"
	"BWWWWB"
	"XRRRRX"
)


def make_agent_class(move=(3, 3), error=None):
	"""Build a stand-in agent class that records how the service uses it."""
	class FakeAgent:
		instances = []

		def __init__(self, color):
			self.color = color
			self.boards = []
			type(self).instances.append(self)

		def choose_move(self, board):
			self.boards.append(board)

			if error is not None:
				raise error

			return move

	return FakeAgent


@pytest.fixture
def registry(monkeypatch):
	"""Replace the real agent registry with two recording fake agents."""
	agents = {
		"Alpha": make_agent_class(move=(1, 1)),
		"Beta": make_agent_class(move=(5, 5)),
	}

	monkeypatch.setattr(services_agents, "AI_AGENTS", agents)

	return agents


class TestGetAgents:
	def test_returns_the_registered_names_in_order(self, registry):
		assert get_agents() == ["Alpha", "Beta"]

	def test_returns_a_list(self, registry):
		assert isinstance(get_agents(), list)

	def test_returns_a_new_list_on_every_call(self, registry):
		names = get_agents()
		names.append("Mutated")

		assert get_agents() == ["Alpha", "Beta"]
		assert list(registry) == ["Alpha", "Beta"]

	def test_empty_registry_gives_an_empty_list(self, monkeypatch):
		monkeypatch.setattr(services_agents, "AI_AGENTS", {})

		assert get_agents() == []

	def test_real_registry_is_exposed(self):
		names = get_agents()

		assert names == list(AI_AGENTS)
		assert "Random" in names
		assert len(names) == len(set(names))
		assert all(isinstance(name, str) and name for name in names)


class TestGetMove:
	def test_returns_the_move_chosen_by_the_agent(self, registry):
		assert get_move("Alpha", 7, 7, CELLS_7, "red") == (1, 1)

	def test_returns_the_move_object_unchanged(self, monkeypatch):
		move = (3, 3)

		monkeypatch.setattr(
			services_agents,
			"AI_AGENTS",
			{"Alpha": make_agent_class(move=move)},
		)

		assert get_move("Alpha", 7, 7, CELLS_7, "red") is move

	def test_uses_the_agent_with_the_requested_name(self, registry):
		assert get_move("Beta", 7, 7, CELLS_7, "red") == (5, 5)

		assert len(registry["Beta"].instances) == 1
		assert registry["Alpha"].instances == []

	@pytest.mark.parametrize(
		"color, expected",
		[
			("red", PlayerColor.RED),
			("blue", PlayerColor.BLUE),
			(PlayerColor.RED, PlayerColor.RED),
			(PlayerColor.BLUE, PlayerColor.BLUE),
		],
		ids=["red", "blue", "red-enum", "blue-enum"],
	)
	def test_creates_the_agent_for_the_requested_color(
		self,
		registry,
		color,
		expected,
	):
		get_move("Alpha", 7, 7, CELLS_7, color)

		(agent,) = registry["Alpha"].instances

		assert agent.color is expected

	def test_asks_the_agent_for_exactly_one_move(self, registry):
		get_move("Alpha", 7, 7, CELLS_7, "red")

		(agent,) = registry["Alpha"].instances

		assert len(agent.boards) == 1

	def test_gives_the_agent_the_deserialized_board(self, registry):
		get_move("Alpha", 7, 7, CELLS_7, "red")

		(board,) = registry["Alpha"].instances[0].boards

		assert isinstance(board, SearchBoard)
		assert board.shape == (7, 7)
		assert board.serialize() == f"7,7,{CELLS_7}"

	def test_supports_non_square_boards(self, registry):
		get_move("Alpha", 5, 6, CELLS_5X6, "blue")

		(board,) = registry["Alpha"].instances[0].boards

		assert board.shape == (5, 6)
		assert board.serialize() == f"5,6,{CELLS_5X6}"


class TestGetMoveUnknownAgent:
	def test_raises_a_key_error_naming_the_agent_and_the_alternatives(
		self,
		registry,
	):
		with pytest.raises(KeyError) as excinfo:
			get_move("Gamma", 7, 7, CELLS_7, "red")

		# KeyError.__str__ adds quotes around its message, so read the
		# message from args instead.
		assert excinfo.value.args[0] == (
			"Agent 'Gamma' not found. Available agents: Alpha, Beta."
		)

	def test_chains_the_registry_lookup_error(self, registry):
		with pytest.raises(KeyError) as excinfo:
			get_move("Gamma", 7, 7, CELLS_7, "red")

		assert isinstance(excinfo.value.__cause__, KeyError)

	@pytest.mark.parametrize("name", ["alpha", "ALPHA", "", " Alpha"])
	def test_agent_names_are_matched_exactly(self, registry, name):
		with pytest.raises(KeyError):
			get_move(name, 7, 7, CELLS_7, "red")

	def test_does_not_instantiate_any_agent(self, registry):
		with pytest.raises(KeyError):
			get_move("Gamma", 7, 7, CELLS_7, "red")

		assert registry["Alpha"].instances == []
		assert registry["Beta"].instances == []


class TestGetMoveInvalidBoard:
	@pytest.mark.parametrize(
		"rows, cols, board, message",
		[
			(7, 7, CELLS_7[:-1], "Expected 49 cells, got 48"),
			(7, 7, CELLS_7 + "W", "Expected 49 cells, got 50"),
			(7, 6, CELLS_7, "Expected 42 cells, got 49"),
			(7, 7, "", "Expected 49 cells, got 0"),
			(0, 0, "", "Board dimensions must be greater than 0"),
			(7, 7, "Z" + CELLS_7[1:], "Invalid board serialization"),
			(7, 7, CELLS_7.lower(), "Invalid board serialization"),
		],
		ids=[
			"too-short",
			"too-long",
			"wrong-dimensions",
			"empty",
			"zero-dimensions",
			"unknown-cell",
			"lowercase-cells",
		],
	)
	def test_raises_a_value_error(
		self,
		registry,
		rows,
		cols,
		board,
		message,
	):
		with pytest.raises(ValueError) as excinfo:
			get_move("Alpha", rows, cols, board, "red")

		assert str(excinfo.value) == f"Invalid board: {message}"

	def test_chains_the_board_error(self, registry):
		with pytest.raises(ValueError) as excinfo:
			get_move("Alpha", 7, 7, CELLS_7[:-1], "red")

		assert isinstance(excinfo.value.__cause__, ValueError)

	def test_does_not_instantiate_the_agent(self, registry):
		with pytest.raises(ValueError):
			get_move("Alpha", 7, 7, CELLS_7[:-1], "red")

		assert registry["Alpha"].instances == []


class TestGetMoveInvalidColor:
	@pytest.mark.parametrize(
		"color",
		["green", "RED", "Red", "BLUE", "", " red"],
	)
	def test_raises_a_value_error_listing_the_valid_colors(
		self,
		registry,
		color,
	):
		with pytest.raises(ValueError) as excinfo:
			get_move("Alpha", 7, 7, CELLS_7, color)

		assert str(excinfo.value) == (
			f"Invalid player color '{color}'. Valid colors: red, blue."
		)

	def test_chains_the_color_error(self, registry):
		with pytest.raises(ValueError) as excinfo:
			get_move("Alpha", 7, 7, CELLS_7, "green")

		assert isinstance(excinfo.value.__cause__, ValueError)

	def test_does_not_instantiate_the_agent(self, registry):
		with pytest.raises(ValueError):
			get_move("Alpha", 7, 7, CELLS_7, "green")

		assert registry["Alpha"].instances == []


class TestGetMoveAgentFailure:
	@pytest.mark.parametrize(
		"error",
		[
			RuntimeError("boom"),
			ValueError("bad value"),
			KeyError("missing"),
			ZeroDivisionError("division by zero"),
		],
		ids=lambda error: type(error).__name__,
	)
	def test_wraps_any_agent_error(self, registry, error):
		registry["Alpha"] = make_agent_class(error=error)

		with pytest.raises(AgentComputationError) as excinfo:
			get_move("Alpha", 7, 7, CELLS_7, "red")

		assert str(excinfo.value) == (
			f"Agent 'Alpha' failed to compute a move: {error}"
		)
		assert excinfo.value.__cause__ is error

	@pytest.mark.parametrize("error", [ValueError("x"), KeyError("x")])
	def test_agent_errors_never_masquerade_as_client_errors(
		self,
		registry,
		error,
	):
		# The endpoint turns KeyError into 404 and ValueError into 422;
		# a failing agent must not be reported as a client mistake.
		registry["Alpha"] = make_agent_class(error=error)

		with pytest.raises(AgentComputationError) as excinfo:
			get_move("Alpha", 7, 7, CELLS_7, "red")

		assert not isinstance(excinfo.value, (KeyError, ValueError))


class TestGetMoveWithRealAgents:
	@pytest.mark.parametrize("color", ["red", "blue"])
	@pytest.mark.parametrize("agent_name", sorted(AI_AGENTS))
	def test_every_registered_agent_plays_a_legal_move_on_an_initial_board(
		self,
		agent_name,
		color,
	):
		board = SearchBoard.deserialize(f"5,5,{CELLS_5}")

		row, col = get_move(agent_name, 5, 5, CELLS_5, color)

		assert (int(row), int(col)) in board.available

	@pytest.mark.parametrize("color", ["red", "blue"])
	@pytest.mark.parametrize("agent_name", sorted(AI_AGENTS))
	def test_every_registered_agent_returns_python_ints(
		self,
		agent_name,
		color,
	):
		# numpy integers (e.g. np.int32) are not ints, even though they
		# compare equal to them and serialize through pydantic.
		row, col = get_move(agent_name, 5, 5, CELLS_5, color)

		assert type(row) is int, f"row is {type(row).__name__}"
		assert type(col) is int, f"col is {type(col).__name__}"

	@pytest.mark.parametrize("agent_name", sorted(AI_AGENTS))
	def test_every_registered_agent_returns_python_ints_mid_game(
		self,
		agent_name,
	):
		row, col = get_move(agent_name, 5, 5, MIDGAME_CELLS_5, "red")

		assert type(row) is int, f"row is {type(row).__name__}"
		assert type(col) is int, f"col is {type(col).__name__}"

	@pytest.mark.parametrize("agent_name", sorted(AI_AGENTS))
	def test_every_registered_agent_plays_a_legal_move_mid_game(
		self,
		agent_name,
	):
		row, col = get_move(agent_name, 5, 5, MIDGAME_CELLS_5, "red")

		assert (int(row), int(col)) in MIDGAME_MOVES_5
