from fastapi.testclient import TestClient

from web_service import main
from web_service.api import agents


def test_openapi_endpoint():
	app = main.create_app()
	client = TestClient(app)

	response = client.get("/openapi.json")

	assert response.status_code == 200

	openapi = response.json()
	assert openapi["info"]["title"] == "Via Ludus API"


def test_get_agents(monkeypatch):
	expected_agents = ["RandomAgent", "GreedyAgent"]

	monkeypatch.setattr(
		agents,
		"get_agents",
		lambda: expected_agents,
	)

	app = main.create_app()
	client = TestClient(app)

	response = client.get("/api/agents")

	assert response.status_code == 200
	assert response.json() == {
		"agents": expected_agents,
	}


def test_get_move(monkeypatch):
	expected_move = (2, 2)

	def mock_get_move(agent_name, rows, cols, board, color):
		assert agent_name == "RandomAgent"
		assert rows == 7
		assert cols == 7
		assert board == "XRRRRRXBWBWBWBBRWRWRBBWBWBWBBRWRWRBBWBWBWBXRRRRRX"
		assert color == "red"

		return expected_move

	monkeypatch.setattr(
		agents,
		"get_move",
		mock_get_move,
	)

	app = main.create_app()
	client = TestClient(app)

	response = client.post(
		"/api/agents/RandomAgent/move",
		json={
			"rows": 7,
			"cols": 7,
			"board": "XRRRRRXBWBWBWBBRWRWRBBWBWBWBBRWRWRBBWBWBWBXRRRRRX",
			"color": "red",
		},
	)

	assert response.status_code == 200
	assert response.json() == {
		"row": 2,
		"col": 2,
	}


def test_get_move_rejects_invalid_request():
	app = main.create_app()
	client = TestClient(app)

	response = client.post(
		"/api/agents/RandomAgent/move",
		json={
			"rows": 5,
			"cols": 5,
		},
	)

	assert response.status_code == 422


def test_cors_preflight():
	origin = "https://via-ludus.pages.dev"

	app = main.create_app(
		cors_origins=[origin],
	)
	client = TestClient(app)

	response = client.options(
		"/api/agents",
		headers={
			"Origin": origin,
			"Access-Control-Request-Method": "GET",
		},
	)

	assert response.status_code == 200
	assert response.headers["access-control-allow-origin"] == origin

