# Tests

The test suite uses [pytest](https://docs.pytest.org/). Install the dependencies with the `test` extra (see the [`README.md`](../README.md#setup) in [backend-python/](../)), then run these commands from `backend-python/`.

```bash
pytest                      # everything
pytest tests/web_service    # just the web service
pytest tests/via_ludus      # just the game library
pytest -k tournament        # tests whose name contains "tournament"
pytest --cov=src            # with a coverage report
```

## Layout

The tests mirror the structure of the code they test, and each test file is named after the file it tests. `tests/web_service/` mirrors `src/web_service/` and `tests/via_ludus/` mirrors `src/via_ludus/`:

| Source | Test |
| --- | --- |
| `src/web_service/main.py` | `tests/web_service/test_main.py` |
| `src/web_service/api/agents.py` | `tests/web_service/api/test_agents.py` |
| `src/web_service/models/agents.py` | `tests/web_service/models/test_agents.py` |
| `src/web_service/services/agents.py` | `tests/web_service/services/test_agents.py` |
| `src/web_service/api/__init__.py` | `tests/web_service/api/test___init__.py` |
| `src/via_ludus/board/base.py` | `tests/via_ludus/board/test_base.py` |
| `src/via_ludus/tournament/tournament.py` | `tests/via_ludus/tournament/test_tournament.py` |
| `src/via_ludus/tournament/results.py` | `tests/via_ludus/tournament/test_results.py` |
| `src/via_ludus/utils/optional_dependencies.py` | `tests/via_ludus/utils/test_optional_dependencies.py` |
| `src/via_ludus/ai/via_ludus_agents/utils/agent_utils.py` | `tests/via_ludus/ai/via_ludus_agents/utils/test_agent_utils.py` |
| `src/via_ludus/board/__init__.py` | `tests/via_ludus/board/test___init__.py` |

Every source file has exactly one test file, including each package's `__init__.py` (which is tested for its exports, `__all__` and any code it defines, such as `resolve_board`). If a test file gets long, keep it as one file and divide it into sections with comments rather than splitting it, as `test_results.py` and `board/test_base.py` do. These two files also hold the tests that compare behaviour across implementations (`SearchBoard` against `UnionFindBoard`) and the property tests.

Not yet covered: `via_ludus_agents/graph_agents/` and `via_ludus_agents/monte_carlo_agents/`. They have no test directories yet; when they get them, add an `__init__.py` to each.

Shared fixtures for the game library live in [`tests/conftest.py`](conftest.py).

### Why `__init__.py` Files?

**Every directory under `tests/` has an `__init__.py` file, whether or not it is needed yet.** Several test files share a name (several packages have an `agents.py`, so there are multiple `test_agents.py` files, and any package's `__init__.py` is tested by a `test___init__.py`). pytest needs each test module to be importable under a unique name, and the `__init__.py` files give every test module a unique, package-qualified name. Adding the file to every directory means a new test file can reuse a name used elsewhere without anyone having to think about it.

`tests/__init__.py` is required for this to work. Without it, pytest would treat `tests/web_service` as a top-level package called `web_service` and hide the real one in `src/`.

When you add a new test directory, add an empty `__init__.py` to it.

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

