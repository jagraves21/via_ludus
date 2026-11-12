# Via Ludus Backend (Python)

The Python side of Via Ludus. It contains two packages, both under `src/`:

| Package | Purpose |
| --- | --- |
| [`via_ludus`](src/via_ludus) | The game library: boards, players, AI agents, tournaments and visualizations. **This is where you write agents.** |
| [`web_service`](src/web_service/README.md) | A small FastAPI app that exposes the agents over HTTP so the browser app can use them. |

## Setup

You need **Python 3.11 or newer**. From this directory (`backend-python/`):

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[web-service,graph-agents,test]"
```

Windows:

```bat
py -m venv .venv
.venv\Scripts\activate
pip install -e ".[web-service,graph-agents,test]"
```

`-e` installs the project in *editable* mode, so changes you make under `src/` take effect without reinstalling.

### Optional Extras

The core library only needs `numpy`. Everything else is installed on demand with an *extra*, for example `pip install -e ".[graph-agents]"`. Combine extras with commas.

| Extra | Installs | What it enables |
| --- | --- | --- |
| `web-service` | `fastapi`, `uvicorn` | Running the web service and the browser app. |
| `graph-agents` | `networkx`, `scipy` | Most of the built-in agents (distance, paths, cuts and centrality). |
| `progress` | `tqdm` | Progress bars when running tournaments. |
| `visualization` | `matplotlib` | Plotting boards and tournament results. |
| `dataframe` | `pandas` | `*_df()` methods on tournament results. |
| `notebooks` | `jupyter`, `tqdm`, `matplotlib`, `pandas` | Everything needed to experiment in Jupyter notebooks. |
| `test` | `pytest`, `pytest-cov`, `httpx2` | Running the test suite. |

If you use a library of your own in an agent, add it to `dependencies` (or an extra) in [`pyproject.toml`](pyproject.toml).

## Running the Game

The easiest way is the script in the repository's `scripts/` directory, which starts the web service and serves the browser app. See [`scripts/README.md`](../scripts/README.md).

To start the web service by hand instead, from this directory:

```bash
python -m web_service.main --frontend ../frontend
```

(`--host`, `--port` and `--cors-origins` are also available. The defaults are `127.0.0.1` and `8080`.)

## Writing and Testing Agents

- To write your own agent, start with the **[agent guide](src/via_ludus/ai/README.md)**.
- To see how well it plays, read the **[tournament guide](src/via_ludus/tournament/README.md)**.

## Layout of `via_ludus`

| Package | What is in it |
| --- | --- |
| [`board/`](src/via_ludus/board/README.md) | `Cell`, `PlayerColor`, and the board implementations. |
| [`player/`](src/via_ludus/player/README.md) | `Player`, `ScoringPlayer`, move selectors and selector mixins. |
| [`ai/`](src/via_ludus/ai/README.md) | `Agent`, `ScoringAgent`, the agent registry, and the built-in agents. |
| [`tournament/`](src/via_ludus/tournament/README.md) | `Game`, matchups, round-robin tournaments and results. |
| `visualizations/` | Plotting for boards and results (needs `matplotlib`). |
| `data_structures/` | Data structures used by the library (union-find). |
| `utils/` | Small helpers: timing, progress bars, optional-dependency handling. |

## Running the Tests

```bash
pytest
```

See [`tests/README.md`](tests/README.md) for how the tests are organized and how to run a subset.

