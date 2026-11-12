import logging
from urllib.parse import quote

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from via_ludus import AI_AGENTS, PlayerColor
from web_service.api import agents
from web_service.exceptions import AgentComputationError


# Initial 7 x 7 board.
BOARD_7 = "XRRRRRXBWBWBWBBRWRWRBBWBWBWBBRWRWRBBWBWBWBXRRRRRX"

# 5 x 8 board (rows x cols).
BOARD_5X8 = (
	"XRRRRRRX"
	"BWWWWWWB"
	"BWWWWWWB"
	"BWWWWWWB"
	"XRRRRRRX"
)

UNEXPECTED_ERROR_DETAIL = "An unexpected error occurred while computing the move."
INVALID_COORDINATES_DETAIL = (
	"Agent returned a move outside the valid interior board positions."
)


@pytest.fixture
def client():
	app = FastAPI()
	app.include_router(agents.router, prefix="/api")

	return TestClient(app)


@pytest.fixture
def move_payload():
	return {
		"rows": 7,
		"cols": 7,
		"board": BOARD_7,
		"color": "red",
	}


@pytest.fixture
def stub_get_agents(monkeypatch):
	def _stub(names):
		monkeypatch.setattr(agents, "get_agents", lambda: names)

	return _stub


@pytest.fixture
def stub_get_move(monkeypatch):
	"""Replace the service call; returns the list of calls it receives."""
	def _stub(result=None, error=None):
		calls = []

		def fake_get_move(*args):
			calls.append(args)

			if error is not None:
				raise error

			return result

		monkeypatch.setattr(agents, "get_move", fake_get_move)

		return calls

	return _stub


def move_url(agent_name="Alpha"):
	return f"/api/agents/{quote(agent_name, safe='')}/move"


class TestRouter:
	def test_routes_are_mounted_under_the_agents_prefix(self):
		assert agents.router.prefix == "/agents"

		paths = {route.path for route in agents.router.routes}

		assert paths == {"/agents", "/agents/{agent_name}/move"}

	def test_routes_are_tagged_agents(self):
		assert agents.router.tags == ["Agents"]


class TestGetAgentsEndpoint:
	def test_returns_the_agent_names(self, client, stub_get_agents):
		stub_get_agents(["Alpha", "Beta"])

		response = client.get("/api/agents")

		assert response.status_code == 200
		assert response.json() == {"agents": ["Alpha", "Beta"]}

	def test_preserves_the_order_of_the_names(self, client, stub_get_agents):
		stub_get_agents(["Zeta", "Alpha", "Mu"])

		response = client.get("/api/agents")

		assert response.json()["agents"] == ["Zeta", "Alpha", "Mu"]

	def test_returns_an_empty_list_when_there_are_no_agents(
		self,
		client,
		stub_get_agents,
	):
		stub_get_agents([])

		response = client.get("/api/agents")

		assert response.status_code == 200
		assert response.json() == {"agents": []}

	def test_responds_with_json(self, client, stub_get_agents):
		stub_get_agents(["Alpha"])

		response = client.get("/api/agents")

		assert response.headers["content-type"] == "application/json"

	def test_only_allows_get(self, client, stub_get_agents):
		stub_get_agents(["Alpha"])

		response = client.post("/api/agents")

		assert response.status_code == 405
		assert response.headers["allow"] == "GET"


class TestGetMoveEndpoint:
	def test_returns_the_selected_move(
		self,
		client,
		move_payload,
		stub_get_move,
	):
		stub_get_move(result=(2, 4))

		response = client.post(move_url(), json=move_payload)

		assert response.status_code == 200
		assert response.json() == {"row": 2, "col": 4}

	def test_response_contains_only_the_coordinates(
		self,
		client,
		move_payload,
		stub_get_move,
	):
		stub_get_move(result=(2, 4))

		response = client.post(move_url(), json=move_payload)

		assert set(response.json()) == {"row", "col"}
		assert all(isinstance(value, int) for value in response.json().values())

	def test_passes_the_request_to_the_service_in_order(
		self,
		client,
		move_payload,
		stub_get_move,
	):
		calls = stub_get_move(result=(2, 4))

		client.post(move_url("Alpha"), json=move_payload)

		assert calls == [("Alpha", 7, 7, BOARD_7, PlayerColor.RED)]

	@pytest.mark.parametrize(
		"color, expected",
		[("red", PlayerColor.RED), ("blue", PlayerColor.BLUE)],
	)
	def test_passes_the_color_as_a_player_color(
		self,
		client,
		move_payload,
		stub_get_move,
		color,
		expected,
	):
		calls = stub_get_move(result=(2, 4))
		move_payload["color"] = color

		client.post(move_url(), json=move_payload)

		assert calls[0][4] is expected

	def test_supports_non_square_boards(
		self,
		client,
		move_payload,
		stub_get_move,
	):
		calls = stub_get_move(result=(3, 6))
		move_payload.update(rows=5, cols=8, board=BOARD_5X8)

		response = client.post(move_url(), json=move_payload)

		assert response.status_code == 200
		assert response.json() == {"row": 3, "col": 6}
		assert calls == [("Alpha", 5, 8, BOARD_5X8, PlayerColor.RED)]

	@pytest.mark.parametrize(
		"agent_name",
		["Kwang-Il", "Bellman-Moore", "My Agent"],
	)
	def test_agent_name_comes_from_the_path(
		self,
		client,
		move_payload,
		stub_get_move,
		agent_name,
	):
		calls = stub_get_move(result=(2, 4))

		client.post(move_url(agent_name), json=move_payload)

		assert calls[0][0] == agent_name

	@pytest.mark.parametrize(
		"move",
		[(1, 1), (1, 5), (5, 1), (5, 5)],
		ids=["top-left", "top-right", "bottom-left", "bottom-right"],
	)
	def test_accepts_every_corner_of_the_interior(
		self,
		client,
		move_payload,
		stub_get_move,
		move,
	):
		stub_get_move(result=move)

		response = client.post(move_url(), json=move_payload)

		assert response.status_code == 200
		assert response.json() == {"row": move[0], "col": move[1]}

	def test_only_allows_post(self, client, stub_get_move):
		stub_get_move(result=(2, 4))

		response = client.get(move_url())

		assert response.status_code == 405
		assert response.headers["allow"] == "POST"

	def test_unknown_paths_are_not_found(self, client):
		assert client.get("/api/unknown").status_code == 404


class TestGetMoveEndpointRequestValidation:
	@pytest.mark.parametrize(
		"changes",
		[
			{"rows": None},
			{"cols": None},
			{"board": None},
			{"color": None},
			{"rows": 4},
			{"cols": 4},
			{"rows": "abc"},
			{"board": BOARD_7[:-1] + "z"},
			{"board": BOARD_7[:-1]},
			{"board": BOARD_7 + "W"},
			{"board": ""},
			{"color": "green"},
			{"color": "RED"},
		],
		ids=[
			"missing-rows",
			"missing-cols",
			"missing-board",
			"missing-color",
			"rows-too-small",
			"cols-too-small",
			"rows-not-a-number",
			"unknown-cell",
			"board-too-short",
			"board-too-long",
			"empty-board",
			"unknown-color",
			"wrong-case-color",
		],
	)
	def test_invalid_requests_are_rejected_before_the_service_runs(
		self,
		client,
		move_payload,
		stub_get_move,
		changes,
	):
		calls = stub_get_move(result=(2, 4))

		for field, value in changes.items():
			if value is None:
				del move_payload[field]
			else:
				move_payload[field] = value

		response = client.post(move_url(), json=move_payload)

		assert response.status_code == 422
		assert calls == []

	def test_reports_a_board_length_mismatch(
		self,
		client,
		move_payload,
		stub_get_move,
	):
		stub_get_move(result=(2, 4))
		move_payload["board"] = BOARD_7[:-1]

		response = client.post(move_url(), json=move_payload)

		assert "Board length must equal rows * cols." in response.text

	def test_rejects_an_empty_json_object(self, client, stub_get_move):
		calls = stub_get_move(result=(2, 4))

		response = client.post(move_url(), json={})

		assert response.status_code == 422
		assert calls == []

	def test_rejects_a_missing_body(self, client, stub_get_move):
		calls = stub_get_move(result=(2, 4))

		response = client.post(move_url())

		assert response.status_code == 422
		assert calls == []

	def test_rejects_a_body_that_is_not_json(self, client, stub_get_move):
		calls = stub_get_move(result=(2, 4))

		response = client.post(
			move_url(),
			content="not json",
			headers={"Content-Type": "application/json"},
		)

		assert response.status_code == 422
		assert calls == []

	def test_ignores_unknown_fields(
		self,
		client,
		move_payload,
		stub_get_move,
	):
		stub_get_move(result=(2, 4))
		move_payload["unexpected"] = "value"

		response = client.post(move_url(), json=move_payload)

		assert response.status_code == 200


class TestGetMoveEndpointErrors:
	def test_unknown_agent_is_a_404(
		self,
		client,
		move_payload,
		stub_get_move,
	):
		stub_get_move(
			error=KeyError("Agent 'ghost' not found. Available agents: Alpha."),
		)

		response = client.post(move_url("ghost"), json=move_payload)

		assert response.status_code == 404
		assert "Agent 'ghost' not found." in response.json()["detail"]

	def test_unknown_agent_detail_is_the_documented_message(
		self,
		client,
		move_payload,
		stub_get_move,
	):
		message = "Agent 'unknown-agent' not found. Available agents: Alpha, Beta."
		stub_get_move(error=KeyError(message))

		response = client.post(move_url("unknown-agent"), json=move_payload)

		assert response.json() == {"detail": message}

	def test_invalid_input_is_a_422_with_the_service_message(
		self,
		client,
		move_payload,
		stub_get_move,
	):
		message = "Invalid board: Expected 49 cells, got 48"
		stub_get_move(error=ValueError(message))

		response = client.post(move_url(), json=move_payload)

		assert response.status_code == 422
		assert response.json() == {"detail": message}

	def test_agent_failure_is_a_500_with_the_service_message(
		self,
		client,
		move_payload,
		stub_get_move,
	):
		message = "Agent 'Alpha' failed to compute a move: did not converge"
		stub_get_move(error=AgentComputationError(message))

		response = client.post(move_url(), json=move_payload)

		assert response.status_code == 500
		assert response.json() == {"detail": message}

	@pytest.mark.parametrize(
		"error",
		[
			RuntimeError("secret internal detail"),
			TypeError("secret internal detail"),
			ZeroDivisionError("secret internal detail"),
			OSError("secret internal detail"),
		],
		ids=lambda error: type(error).__name__,
	)
	def test_unexpected_errors_are_a_generic_500(
		self,
		client,
		move_payload,
		stub_get_move,
		error,
	):
		stub_get_move(error=error)

		response = client.post(move_url(), json=move_payload)

		assert response.status_code == 500
		assert response.json() == {"detail": UNEXPECTED_ERROR_DETAIL}
		assert "secret" not in response.text

	@pytest.mark.parametrize("result", [None, 5], ids=["none", "int"])
	def test_a_result_that_is_not_a_pair_is_a_generic_500(
		self,
		client,
		move_payload,
		stub_get_move,
		result,
	):
		stub_get_move(result=result)

		response = client.post(move_url(), json=move_payload)

		assert response.status_code == 500

	@pytest.mark.parametrize("result", [(1,), (1, 2, 3)], ids=["one", "three"])
	def test_a_tuple_of_the_wrong_length_is_a_server_error(
		self,
		client,
		move_payload,
		stub_get_move,
		result,
	):
		stub_get_move(result=result)

		response = client.post(move_url(), json=move_payload)

		assert response.status_code == 500

	@pytest.mark.parametrize(
		"move",
		[
			(0, 3),
			(3, 0),
			(6, 3),
			(3, 6),
			(7, 3),
			(3, 7),
			(-1, 3),
			(3, -1),
			(100, 100),
		],
		ids=[
			"first-row",
			"first-col",
			"last-row",
			"last-col",
			"row-past-end",
			"col-past-end",
			"negative-row",
			"negative-col",
			"far-away",
		],
	)
	def test_a_move_outside_the_interior_is_a_500(
		self,
		client,
		move_payload,
		stub_get_move,
		move,
	):
		stub_get_move(result=move)

		response = client.post(move_url(), json=move_payload)

		assert response.status_code == 500
		assert response.json() == {"detail": INVALID_COORDINATES_DETAIL}

	@pytest.mark.parametrize(
		"move, status",
		[
			((3, 6), 200),
			((3, 7), 500),
			((4, 3), 500),
			((1, 1), 200),
		],
		ids=["last-interior-col", "last-col", "last-row", "first-interior"],
	)
	def test_bounds_use_rows_for_rows_and_cols_for_cols(
		self,
		client,
		move_payload,
		stub_get_move,
		move,
		status,
	):
		stub_get_move(result=move)
		move_payload.update(rows=5, cols=8, board=BOARD_5X8)

		response = client.post(move_url(), json=move_payload)

		assert response.status_code == status


class TestGetMoveEndpointLogging:
	LOGGER = agents.logger.name

	def records(self, caplog):
		return [
			record for record in caplog.records
			if record.name == self.LOGGER
		]

	@pytest.mark.parametrize(
		"error, level, has_traceback, text",
		[
			(KeyError("ghost"), logging.WARNING, False, "Unknown agent"),
			(ValueError("bad"), logging.WARNING, False, "Invalid move request"),
			(
				AgentComputationError("fail"),
				logging.ERROR,
				True,
				"Agent computation failed",
			),
			(
				RuntimeError("oops"),
				logging.ERROR,
				True,
				"Unexpected error computing move",
			),
		],
		ids=["unknown-agent", "invalid-input", "agent-failure", "unexpected"],
	)
	def test_failures_are_logged_once_with_the_request_details(
		self,
		client,
		move_payload,
		stub_get_move,
		caplog,
		error,
		level,
		has_traceback,
		text,
	):
		stub_get_move(error=error)

		with caplog.at_level(logging.DEBUG, logger=self.LOGGER):
			client.post(move_url(), json=move_payload)

		(record,) = self.records(caplog)
		message = record.getMessage()

		assert record.levelno == level
		assert bool(record.exc_info) is has_traceback
		assert text in message
		assert "agent=Alpha" in message
		assert "rows=7" in message
		assert "cols=7" in message
		assert BOARD_7 in message

	def test_invalid_coordinates_are_logged_as_an_error(
		self,
		client,
		move_payload,
		stub_get_move,
		caplog,
	):
		stub_get_move(result=(0, 3))

		with caplog.at_level(logging.DEBUG, logger=self.LOGGER):
			client.post(move_url(), json=move_payload)

		(record,) = self.records(caplog)
		message = record.getMessage()

		assert record.levelno == logging.ERROR
		assert "Agent returned invalid coordinates" in message
		assert "agent=Alpha" in message
		assert "row=0" in message
		assert "col=3" in message

	def test_successful_requests_are_not_logged(
		self,
		client,
		move_payload,
		stub_get_move,
		caplog,
	):
		stub_get_move(result=(2, 4))

		with caplog.at_level(logging.DEBUG, logger=self.LOGGER):
			client.post(move_url(), json=move_payload)

		assert self.records(caplog) == []

	def test_listing_agents_is_not_logged(
		self,
		client,
		stub_get_agents,
		caplog,
	):
		stub_get_agents(["Alpha"])

		with caplog.at_level(logging.DEBUG, logger=self.LOGGER):
			client.get("/api/agents")

		assert self.records(caplog) == []


class TestOpenApiSchema:
	@pytest.fixture
	def schema(self, client):
		return client.get("/openapi.json").json()

	def test_operation_ids(self, schema):
		paths = schema["paths"]

		assert paths["/api/agents"]["get"]["operationId"] == "get_agents"
		assert (
			paths["/api/agents/{agent_name}/move"]["post"]["operationId"]
			== "get_agent_move"
		)

	def test_operations_are_tagged_agents(self, schema):
		paths = schema["paths"]

		assert paths["/api/agents"]["get"]["tags"] == ["Agents"]
		assert paths["/api/agents/{agent_name}/move"]["post"]["tags"] == ["Agents"]

	def test_move_documents_every_error_response(self, schema):
		responses = schema["paths"]["/api/agents/{agent_name}/move"]["post"]["responses"]

		assert {"200", "404", "422", "500"} <= set(responses)

	def test_responses_use_the_response_models(self, schema):
		paths = schema["paths"]

		agents_schema = (
			paths["/api/agents"]["get"]["responses"]["200"]
			["content"]["application/json"]["schema"]
		)
		move_schema = (
			paths["/api/agents/{agent_name}/move"]["post"]["responses"]["200"]
			["content"]["application/json"]["schema"]
		)

		assert agents_schema["$ref"].endswith("/GetAgentsResponse")
		assert move_schema["$ref"].endswith("/GetMoveResponse")

	def test_move_request_uses_the_request_model(self, schema):
		body = (
			schema["paths"]["/api/agents/{agent_name}/move"]["post"]
			["requestBody"]["content"]["application/json"]["schema"]
		)

		assert body["$ref"].endswith("/GetMoveRequest")

	def test_agent_name_is_a_documented_path_parameter(self, schema):
		parameters = schema["paths"]["/api/agents/{agent_name}/move"]["post"]["parameters"]

		(parameter,) = [p for p in parameters if p["name"] == "agent_name"]

		assert parameter["in"] == "path"
		assert parameter["required"] is True
		assert parameter["description"]


class TestGetMoveEndpointWithRealAgents:
	@pytest.mark.parametrize("agent_name", ["Random", "Dijkstra"])
	@pytest.mark.parametrize("color", ["red", "blue"])
	def test_real_agents_return_a_move_through_the_whole_stack(
		self,
		client,
		move_payload,
		agent_name,
		color,
	):
		if agent_name not in AI_AGENTS:
			pytest.skip(f"{agent_name} is not registered")

		move_payload.update(color=color)

		response = client.post(move_url(agent_name), json=move_payload)

		assert response.status_code == 200

		body = response.json()

		assert 1 <= body["row"] < 6
		assert 1 <= body["col"] < 6

	def test_unknown_agent_through_the_whole_stack_is_a_404(
		self,
		client,
		move_payload,
	):
		response = client.post(move_url("no-such-agent"), json=move_payload)

		assert response.status_code == 404
		assert "no-such-agent" in response.json()["detail"]
		assert "Available agents:" in response.json()["detail"]
