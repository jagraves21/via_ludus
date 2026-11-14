# Web Service

A small [FastAPI](https://fastapi.tiangolo.com/) application that lets the browser app (or anything else that speaks HTTP) ask Via Ludus's agents for moves.

You normally start it with `scripts/run_webserver.sh` (or `scripts/run_webserver.bat` on Windows). See  [`scripts/README.md`](../../../scripts/README.md) for details.

## How it connects to the agents

```mermaid
flowchart LR
    A["Browser"] -->|HTTP| B["api/agents.py"]
    B --> C["services/agents.py"]
    C --> D["via_ludus.AI_AGENTS"]
```

- The list of agents comes straight from `via_ludus.AI_AGENTS`. If you [register a new agent](../via_ludus/ai/README.md#step-3-register-the-agent), it appears in the game's player drop-downs after the server is restarted.
- **A new agent object is created for every move request.** An agent cannot remember anything between moves, so compute everything from the board you are given.
- The web service always hands agents a `SearchBoard` (see [via_ludus/backend-python/src/via_ludus/board/README.md](../via_ludus/board/README.md)).

## API

All routes live under `/api`. Interactive documentation is served at `/docs`, and the machine-readable schema at `/openapi.json`.

### `GET /api/agents`

Returns the names of the available agents.

```bash
curl http://localhost:8080/api/agents
```

For example (shortened; the real list is longer):

```json
{"agents": ["Random", "Dijkstra"]}
```

### `POST /api/agents/{agent_name}/move`

Asks an agent for a move.

| Field | Type | Description |
| --- | --- | --- |
| `rows` | integer, at least 5 | Number of rows in the board. |
| `cols` | integer, at least 5 | Number of columns in the board. |
| `board` | string | The cells in row-major order, exactly `rows * cols` characters. `R` is red, `B` is blue, `W` is white and `X` is a wall. |
| `color` | `"red"` or `"blue"` | The colour the agent is playing. |

```bash
curl -X POST http://localhost:8080/api/agents/Random/move \
  -H "Content-Type: application/json" \
  -d '{"rows": 7, "cols": 7, "color": "red",
       "board": "XRRRRRXBWBWBWBBRWRWRBBWBWBWBBRWRWRBBWBWBWBXRRRRRX"}'
```

```json
{"row": 3, "col": 3}
```

`row` and `col` are zero-based. The move is always an interior cell: the first and last rows and columns are never valid.

### Errors

| Status | When |
| --- | --- |
| `404` | There is no agent with that name. The message lists the available agents. |
| `422` | The request is invalid: a malformed body, a bad `rows`, `cols` or `color`, or a `board` that is the wrong length or contains characters other than `R`, `B`, `W`, `X`. |
| `500` | The agent raised an error while choosing a move, or returned a cell outside the interior of the board. The error is logged on the server. |

## Starting it by Hand

```bash
cd backend-python
PYTHONPATH=src python -m web_service.main --frontend ../frontend
```

| Option | Default | Meaning |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Address to listen on. |
| `--port` | `8080` | Port to listen on. |
| `--frontend` | none | Directory of the browser app to serve at `/`. Without it only the API is served. |
| `--cors-origins` | none | Origins allowed to call the API from a browser on a different address. Not needed when the browser app is served by the same server. |

## Code Layout

| Path | Purpose |
| --- | --- |
| `main.py` | Builds the app (`create_app`), command line options, and the entry point. |
| `api/agents.py` | The two routes, and the mapping of errors to HTTP status codes. |
| `models/agents.py` | Request and response models (validated by pydantic). |
| `services/agents.py` | Looks up the agent, builds the board, and asks the agent for a move. |
| `exceptions.py` | `AgentComputationError`, raised when an agent fails. |
| `openapi.py` | Title, description and tags for the API documentation. |

The tests mirror this layout under [`backend-python/tests/web_service/`](../../tests/README.md).

