# Tests

The test suite uses [pytest](https://docs.pytest.org/). Install the dependencies with the `test` extra (see the [`README.md`](../README.md#setup) in [backend-python/](../)), then run these commands from `backend-python/`.

```bash
pytest                      # everything
pytest tests/web_service    # just the web service
pytest tests/via_ludus      # just the game library
pytest -k round_robin       # tests whose name contains "round_robin"
pytest --cov=src            # with a coverage report
```

## Layout

The tests mirror the structure of the code they test, and each test file is named after the file it tests:

| Source | Test |
| --- | --- |
| `src/web_service/main.py` | `tests/web_service/test_main.py` |
| `src/web_service/api/agents.py` | `tests/web_service/api/test_agents.py` |
| `src/web_service/models/agents.py` | `tests/web_service/models/test_agents.py` |
| `src/web_service/services/agents.py` | `tests/web_service/services/test_agents.py` |
| `src/web_service/api/__init__.py` | `tests/web_service/api/test___init__.py` |

Shared fixtures for the game library live in [`conftest.py`](conftest.py).

### Why `__init__.py` Files?

Several test files share a name (several packages have an `agents.py`, so there are multiple `test_agents.py` files). pytest needs each test module to be importable under a unique name, which the `__init__.py` files in `tests/`, `tests/web_service/` and its sub-directories provide.

`tests/__init__.py` is required for this to work. Without it, pytest would treat `tests/web_service` as a top-level package called `web_service` and hide the real one in `src/`.

## Writing Tests for Your Own Agents

Your agent does not need to be in the test suite to be used, but a test is a good way to make sure it always returns a legal move. For a [`ScoringAgent`](../src/via_ludus/ai/README.md) the pattern is:

```python
from via_ludus import PlayerColor, SearchBoard
from via_ludus.ai.my_agent import MyAgent


def test_my_agent_plays_a_legal_move():
	board = SearchBoard(size=7)

	row, col = MyAgent(PlayerColor.RED).choose_move(board)

	assert (row, col) in board.available
```

