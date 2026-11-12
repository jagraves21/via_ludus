import inspect
import logging
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from web_service import main
from web_service.api import agents
from web_service.openapi import (
	API_DESCRIPTION,
	API_VERSION,
	OPENAPI_TAGS,
)


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


# ---------------------------------------------------------------------
# create_app: metadata and routing
# ---------------------------------------------------------------------

def test_create_app_returns_a_fastapi_app():
	assert isinstance(main.create_app(), FastAPI)


def test_create_app_sets_the_api_metadata():
	app = main.create_app()

	assert app.title == "Via Ludus API"
	assert app.summary == "API for interacting with Via Ludus game agents."
	assert app.description == API_DESCRIPTION
	assert app.version == API_VERSION
	assert app.openapi_tags == OPENAPI_TAGS


def test_openapi_document_reports_the_api_version():
	client = TestClient(main.create_app())

	info = client.get("/openapi.json").json()["info"]

	assert info["version"] == API_VERSION


def test_openapi_document_lists_the_agent_routes():
	client = TestClient(main.create_app())

	paths = client.get("/openapi.json").json()["paths"]

	assert set(paths) == {"/api/agents", "/api/agents/{agent_name}/move"}


def test_agent_routes_live_under_the_api_prefix(monkeypatch):
	monkeypatch.setattr(agents, "get_agents", lambda: ["Alpha"])
	client = TestClient(main.create_app())

	assert client.get("/api/agents").status_code == 200
	assert client.get("/agents").status_code == 404


# ---------------------------------------------------------------------
# create_app: CORS
# ---------------------------------------------------------------------

def test_cors_allows_every_configured_origin(monkeypatch):
	monkeypatch.setattr(agents, "get_agents", lambda: ["Alpha"])
	origins = ["http://localhost:8080", "http://127.0.0.1:8080"]
	client = TestClient(main.create_app(cors_origins=origins))

	for origin in origins:
		response = client.get("/api/agents", headers={"Origin": origin})

		assert response.headers["access-control-allow-origin"] == origin


def test_cors_does_not_allow_other_origins(monkeypatch):
	monkeypatch.setattr(agents, "get_agents", lambda: ["Alpha"])
	client = TestClient(
		main.create_app(cors_origins=["https://via-ludus.pages.dev"]),
	)

	response = client.get(
		"/api/agents",
		headers={"Origin": "https://evil.example"},
	)

	assert response.status_code == 200
	assert "access-control-allow-origin" not in response.headers


def test_cors_rejects_a_preflight_from_another_origin():
	client = TestClient(
		main.create_app(cors_origins=["https://via-ludus.pages.dev"]),
	)

	response = client.options(
		"/api/agents",
		headers={
			"Origin": "https://evil.example",
			"Access-Control-Request-Method": "GET",
		},
	)

	assert response.status_code == 400
	assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize("cors_origins", [None, []], ids=["none", "empty"])
def test_cors_is_closed_by_default(cors_origins):
	client = TestClient(main.create_app(cors_origins=cors_origins))

	response = client.options(
		"/api/agents",
		headers={
			"Origin": "http://localhost:8080",
			"Access-Control-Request-Method": "GET",
		},
	)

	assert response.status_code == 400
	assert "access-control-allow-origin" not in response.headers


def test_cors_allows_post_requests_with_custom_headers():
	origin = "http://localhost:8080"
	client = TestClient(main.create_app(cors_origins=[origin]))

	response = client.options(
		"/api/agents/RandomAgent/move",
		headers={
			"Origin": origin,
			"Access-Control-Request-Method": "POST",
			"Access-Control-Request-Headers": "content-type, x-custom",
		},
	)

	assert response.status_code == 200
	assert "POST" in response.headers["access-control-allow-methods"]
	assert "x-custom" in response.headers["access-control-allow-headers"].lower()


# ---------------------------------------------------------------------
# create_app: frontend
# ---------------------------------------------------------------------

@pytest.fixture
def frontend_dir(tmp_path):
	directory = tmp_path / "site"
	directory.mkdir()
	(directory / "index.html").write_text("<h1>home</h1>")
	(directory / "about.html").write_text("<h1>about</h1>")

	return directory


def test_no_frontend_is_served_by_default():
	app = main.create_app()
	client = TestClient(app)

	assert client.get("/").status_code == 404
	assert all(getattr(route, "name", None) != "frontend" for route in app.routes)


def test_frontend_directory_is_served_at_the_root(frontend_dir):
	client = TestClient(main.create_app(frontend=frontend_dir))

	response = client.get("/")

	assert response.status_code == 200
	assert response.text == "<h1>home</h1>"


def test_frontend_files_are_served_by_name(frontend_dir):
	client = TestClient(main.create_app(frontend=frontend_dir))

	response = client.get("/about.html")

	assert response.status_code == 200
	assert response.text == "<h1>about</h1>"


def test_missing_frontend_files_are_not_found(frontend_dir):
	client = TestClient(main.create_app(frontend=frontend_dir))

	assert client.get("/missing.html").status_code == 404


def test_api_routes_take_precedence_over_the_frontend(
	monkeypatch,
	frontend_dir,
):
	monkeypatch.setattr(agents, "get_agents", lambda: ["Alpha"])
	client = TestClient(main.create_app(frontend=frontend_dir))

	response = client.get("/api/agents")

	assert response.status_code == 200
	assert response.json() == {"agents": ["Alpha"]}


def test_relative_frontend_path_is_resolved_when_the_app_is_created(
	monkeypatch,
	tmp_path,
	frontend_dir,
):
	monkeypatch.chdir(tmp_path)
	app = main.create_app(frontend=Path("site"))

	elsewhere = tmp_path / "elsewhere"
	elsewhere.mkdir()
	monkeypatch.chdir(elsewhere)

	response = TestClient(app).get("/")

	assert response.status_code == 200
	assert response.text == "<h1>home</h1>"


# ---------------------------------------------------------------------
# main
# ---------------------------------------------------------------------

@pytest.fixture
def server(monkeypatch):
	"""Replace uvicorn and logging setup; returns the calls made, in order."""
	calls = []

	monkeypatch.setattr(
		main.uvicorn,
		"run",
		lambda app, **kwargs: calls.append(("run", app, kwargs)),
	)
	monkeypatch.setattr(
		main.logging,
		"basicConfig",
		lambda **kwargs: calls.append(("basicConfig", kwargs)),
	)

	return calls


def test_main_runs_the_app_on_the_given_host_and_port(server):
	main.main(
		host="0.0.0.0",
		port=9000,
		frontend=None,
		cors_origins=[],
	)

	(run,) = [call for call in server if call[0] == "run"]
	_, app, kwargs = run

	assert isinstance(app, FastAPI)
	assert kwargs == {"host": "0.0.0.0", "port": 9000}


def test_main_builds_the_app_from_its_arguments(monkeypatch, server):
	created = []
	sentinel = object()

	def fake_create_app(**kwargs):
		created.append(kwargs)

		return sentinel

	monkeypatch.setattr(main, "create_app", fake_create_app)

	main.main(
		host="127.0.0.1",
		port=8080,
		frontend=Path("web"),
		cors_origins=["http://localhost:8080"],
	)

	assert created == [
		{
			"cors_origins": ["http://localhost:8080"],
			"frontend": Path("web"),
		},
	]

	(run,) = [call for call in server if call[0] == "run"]

	assert run[1] is sentinel


def test_main_configures_info_level_logging_before_starting_the_server(server):
	main.main(
		host="127.0.0.1",
		port=8080,
		frontend=None,
		cors_origins=[],
	)

	assert [call[0] for call in server] == ["basicConfig", "run"]

	kwargs = server[0][1]

	assert kwargs["level"] == logging.INFO
	assert "%(levelname)s" in kwargs["format"]
	assert "%(name)s" in kwargs["format"]
	assert "%(message)s" in kwargs["format"]


# ---------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------

def test_parse_args_defaults(monkeypatch):
	monkeypatch.setattr(sys, "argv", ["web_service.main"])

	assert main.parse_args() == {
		"host": "127.0.0.1",
		"port": 8080,
		"frontend": None,
		"cors_origins": [],
	}


def test_parse_args_reads_every_option(monkeypatch):
	monkeypatch.setattr(
		sys,
		"argv",
		[
			"web_service.main",
			"--host", "0.0.0.0",
			"--port", "9000",
			"--frontend", "web",
			"--cors-origins", "http://a.example", "http://b.example",
		],
	)

	assert main.parse_args() == {
		"host": "0.0.0.0",
		"port": 9000,
		"frontend": Path("web"),
		"cors_origins": ["http://a.example", "http://b.example"],
	}


def test_parse_args_accepts_cors_origins_without_values(monkeypatch):
	monkeypatch.setattr(
		sys,
		"argv",
		["web_service.main", "--cors-origins"],
	)

	assert main.parse_args()["cors_origins"] == []


def test_parse_args_rejects_a_non_numeric_port(monkeypatch, capsys):
	monkeypatch.setattr(
		sys,
		"argv",
		["web_service.main", "--port", "abc"],
	)

	with pytest.raises(SystemExit) as excinfo:
		main.parse_args()

	assert excinfo.value.code == 2
	assert "--port" in capsys.readouterr().err


def test_parse_args_rejects_unknown_options(monkeypatch):
	monkeypatch.setattr(
		sys,
		"argv",
		["web_service.main", "--unknown"],
	)

	with pytest.raises(SystemExit) as excinfo:
		main.parse_args()

	assert excinfo.value.code == 2


def test_parse_args_matches_the_parameters_of_main(monkeypatch):
	monkeypatch.setattr(sys, "argv", ["web_service.main"])

	assert set(main.parse_args()) == set(
		inspect.signature(main.main).parameters
	)
