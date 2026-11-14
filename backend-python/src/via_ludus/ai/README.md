# Writing Your Own Agent

This directory is where student agents live. An **agent** is a Python class that plays Via Ludus: it is given the current board and the color it is playing, and it decides which cell to claim. The game takes care of everything else: turns, rules, detecting a winner, the browser app and tournaments.

If you have not read the rules yet, start with the root [README.md](../../../../README.md#the-game).

**Contents**

- [Before You Start](#before-you-start)
- [Step 1: Choose a Base Class](#step-1-choose-a-base-class)
- [Step 2: Write the Agent](#step-2-write-the-agent)
  - [Option A: Extend `Agent`](#option-a-extend-agent)
  - [Option B: Extend `ScoringAgent`](#option-b-extend-scoringagent)
- [Step 3: Register the Agent](#step-3-register-the-agent)
- [Step 4: Test your Agent](#step-4-test-your-agent)
- [Step 5: Play Against it in the Browser](#step-5-play-against-it-in-the-browser)
- [What Your Agent Receives](#what-your-agent-receives)
- [Rules Your Agent Must Follow](#rules-your-agent-must-follow)
- [Troubleshooting](#troubleshooting)
- [Examples to Study](#examples-to-study)

## Before you Start

1. Set up the backend (Python 3.11+, a virtual environment, and `pip install -e ".[web-service,graph-agents]"`). See the [`README.md`](../../../README.md#setup) in [`backend-python/`](../../../).
2. Make sure you can run the game. See the [`README.md`](../../../../scripts/README.md) in [`scripts/`](../../../../scripts/).
3. Skim the built-in agents in [`backend-python/src/via_ludus/ai/via_ludus_agents/`](./via_ludus_agents/). Reading [`random_agent.py`](./via_ludus_agents/random_agent.py) and [`shortest_path_agent.py`](./via_ludus_agents/shortest_path_agent.py) takes five minutes and shows you the shape of an agent.

## Step 1: Choose a Base Class

Every agent extends one of two classes from [`agent.py`](agent.py):

| | `Agent` | `ScoringAgent` |
| --- | --- | --- |
| **You Write** | `select_move(self, board, color)` | `evaluate_move_options(self, board, color)` |
| **You Return** | The one move to play, as `(row, col)`. | A dictionary that gives a score for each move you want to consider. |
| **Who Picks the Final Move** | You. | A *selector*, which you configure by adding a mixin. |
| **Good For** | Algorithms that reason about whole games: minimax, alpha-beta, Monte Carlo tree search. | Heuristics: "how good is each cell?" |
| **Mixins you can add** | `DeterministicMoveSelectionMixin` (optional). | A selector mixin (such as `RandomMaxSelectorMixin`) and `DeterministicScoringMixin` (optional). |

**Rule of thumb:** if your idea can be phrased as "give every cell a number, then play the best one", use `ScoringAgent`. It is less code, you get tie-breaking and random exploration for free, and your agent's scores are easy to inspect and compare. If you need full control over how the final move is chosen, use `Agent`.

## Step 2: Write the Agent

Create a new `.py` file in **this directory** (`backend-python/src/via_ludus/ai/`), for example `my_agents.py`. One file can contain several agents. Every agent needs a class attribute called `name`, the label that appears in the game's player menus. Names must be unique.

Inside this directory, import like this:

```python
from ..board import Cell, PlayerColor        # only if you need them
from ..player import RandomMinSelectorMixin  # selector / determinism mixins
from .agent import Agent, ScoringAgent
```

### Option A: Extend `Agent`

Implement one method, `select_move(self, board, color)`. It must return the `(row, col)` of the cell that `color` should claim.

When your agent plays a game, the game calls `choose_move(board)`, which calls your `select_move` with your agent's own color. You never need to write `choose_move` yourself.

```python
import random

from .agent import Agent


class MyRandomAgent(Agent):
	name = "MyRandom"

	def select_move(self, board, color):
		row, col = random.choice(sorted(board.available))
		return int(row), int(col)
```

Inside `select_move` you can use:

- `board`: the current position. See [What Your Agent Receives](#what-your-agent-receives).
- `color`: the color to choose a move for (`PlayerColor.RED` or `PlayerColor.BLUE`). Assume it is this color's turn. Use `color` rather than assuming you are Red or Blue, and use `color.opponent` for the other side.
- `self.color`: the color this agent plays. When the agent is playing a game it is the same as `color`.
- `self.opponent_color`: the other color (`self.color.opponent`).
- `self.cell`: the `Cell` value that marks this agent's own cells (`Cell.RED` or `Cell.BLUE`).

**Asking what you would play for the opponent.** Because `select_move` takes a color, your algorithm can be asked about either side. If your code calls `self.select_move(board, self.opponent_color)`, it gets the move your algorithm would pick for the opponent in that position. This is useful when searching ahead, for example to model how the opponent is likely to reply. The game itself only ever asks for your own color.

To search ahead, play moves on a **copy** of the board (`board.copy()`) and look at the result. Never change the board you were given.

**Declaring determinism (optional).** If your agent always plays the same move for the same position (no randomness, and no memory of earlier moves or games), you can say so by adding `DeterministicMoveSelectionMixin` **before** `Agent` in the class definition:

```python
from ..player import DeterministicMoveSelectionMixin


class MyAgent(DeterministicMoveSelectionMixin, Agent):
	name = "Mine"
	...
```

The tournament tools use this to avoid replaying identical games. See [Declaring Determinism](#declaring-determinism) for what that means and when it is safe to use.

### Option B: Extend `ScoringAgent`

Implement one method, `evaluate_move_options(self, board, color)`. It returns a dictionary that maps moves to scores:

```python
{
	(1, 1): 4.0,
	(1, 3): 2.5,
	(2, 2): 7.0,
}
```

`color` is the color you are choosing a move for. Use it instead of hard-coding Red or Blue, so the same agent can play either side.

Here is a complete example. It prefers cells close to the middle of the board. The score is the distance from the centre, so **lower is better**, and we say so by adding `RandomMinSelectorMixin`:

```python
from ..player import RandomMinSelectorMixin
from .agent import ScoringAgent


class CenterAgent(RandomMinSelectorMixin, ScoringAgent):
	name = "Center"

	def evaluate_move_options(self, board, color):
		center_row = (board.rows - 1) / 2
		center_col = (board.cols - 1) / 2

		return {
			(row, col): abs(row - center_row) + abs(col - center_col)
			for row, col in board.available
		}
```

You do **not** write `select_move` or `choose_move`. `ScoringAgent` provides them: it calls your method and then hands the scores to a selector, which picks the move (see below).

#### How a Move is Chosen

When it is your agent's turn:

1. Your `evaluate_move_options` returns a dictionary of scores.
2. Moves that are not available (not currently white) are dropped.
3. Scores that are `NaN` or infinite are ignored.
4. The **selector** chooses one move from what remains.

Two practical consequences:

- You may leave cells out of the dictionary. Cells without a score are never chosen.
- At least one move must have a finite score. Otherwise the agent fails with `ValueError: No available moves with finite scores`.

#### Selector Mixins

The selector decides *how* scores turn into a move. You choose it by adding a **selector mixin** to the class definition. These are all in `via_ludus.player` (and `via_ludus`):

| Mixin | Plays | If Several Moves Tie |
| --- | --- | --- |
| *(none)*, or `MaxSelectorMixin` | The **highest** score. | Always the same one: the middle of the tied moves, sorted by `(row, col)`. |
| `MinSelectorMixin` | The **lowest** score. | Always the same one: the middle of the tied moves, sorted by `(row, col)`. |
| `RandomMaxSelectorMixin` | The **highest** score. | A random one of the tied moves. |
| `RandomMinSelectorMixin` | The **lowest** score. | A random one of the tied moves. |
| `SoftmaxSelectorMixin` | A random move, with **higher** scores more likely. | Tied moves are equally likely. |
| `SoftminSelectorMixin` | A random move, with **lower** scores more likely. | Tied moves are equally likely. |

How to choose:

- **Is a high score good, or a low one?** If a bigger number means a better move (e.g., a win probability), use the *Max* family. If a smaller number is better (a distance or a cost), use the *Min* family. Flipping the sign of your scores and switching between the two gives identical play.
- **Should ties be broken randomly?** The plain `Max`/`Min` mixins always pick the same move among equals, so the agent can look repetitive and always plays the same opening. The `RandomMax`/`RandomMin` mixins vary their play, which is usually what you want in a tournament.
- **Should the agent sometimes play a weaker move?** The `Softmax`/`Softmin` mixins sample *every* move with probability proportional to `exp(score / temperature)` (`Softmin` uses the negated score). This is useful for exploration, or for building a weaker opponent. A **low temperature** makes the agent nearly always choose the best move; a **high temperature** makes it closer to uniformly random. The default temperature is `1.0`.

**Put mixins before `ScoringAgent`.** Python looks for methods from left to right in the list of base classes, so a mixin only works if it is listed first:

```python
class Works(RandomMinSelectorMixin, ScoringAgent):    # correct
	...

class Ignored(ScoringAgent, RandomMinSelectorMixin):  # mixin silently has no effect!
	...
```

The second version does not fail. It quietly falls back to the default selector. If a mixin seems to have no effect, check the order first.

#### Customising a Selector

The mixins use each selector's default settings. To change them, for example to set the temperature of a softmax selector or to seed the random number generator for reproducible experiments, override `create_selector` in your class:

```python
from ..player import SoftmaxSelector
from .agent import ScoringAgent


class CautiousSoftmaxAgent(ScoringAgent):
	name = "CautiousSoftmax"

	def create_selector(self):
		return SoftmaxSelector(temperature=0.25, seed=42)

	def evaluate_move_options(self, board, color):
		...
```

The selector classes are `MaxSelector`, `MinSelector`, `RandomMaxSelector`, `RandomMinSelector`, `SoftmaxSelector` and `SoftminSelector`. The random ones accept a `seed`, and the soft ones also accept a `temperature`. When you create an agent yourself (in a notebook or a test), you can also pass one in directly: `CenterAgent(PlayerColor.RED, selector=SoftmaxSelector(temperature=0.5))`. The browser always creates agents with their defaults, so use `create_selector` for anything the browser should see.

More detail is in the player [`README.md`](../player/README.md) found at [`backend-python/src/via_ludus/player/`](../player/).

#### Declaring Determinism

An agent is **deterministic** if it always makes the same move in the same position: no random numbers, and no dependence on earlier moves or games. You can **declare** this to the tournament tools with a mixin. It is optional and has no effect on how the agent plays.

| Class | Mixin | What it Promises |
| --- | --- | --- |
| `Agent` | `DeterministicMoveSelectionMixin` | `choose_move` (the agent playing as its own color) returns the same move for the same position. |
| `ScoringAgent` | `DeterministicScoringMixin` | `evaluate_move_options` returns the same scores for the same position and color. |

For a `ScoringAgent` the selector matters as well, so the tournament tools combine both. An agent with deterministic scoring is treated as fully deterministic with `Max`/`Min` selectors, deterministic *move by move* with `RandomMax`/`RandomMin` selectors (a move is deterministic whenever a single best move exists), and not deterministic with `Softmax`/`Softmin`.

```python
from ..player import DeterministicScoringMixin, RandomMaxSelectorMixin
from .agent import ScoringAgent


class MyHeuristicAgent(
	DeterministicScoringMixin,
	RandomMaxSelectorMixin,
	ScoringAgent,
):
	name = "MyHeuristic"
	...
```

Determinism is only about `choose_move`, the move the agent plays in a game. It makes no promise about `select_move` when that is asked about the *other* color.

**Why it matters:** when two deterministic agents play each other, every game is identical, so a tournament plays the first game and reuses its result for the rest, which is much faster.

**The promise is not checked.** If you declare an agent deterministic and it is not (it uses randomness, or remembers earlier moves), the tournament will copy the first game's result for every other game and report wrong statistics without any warning. When in doubt, leave the mixin out. It only costs some speed.

## Step 3: Register the Agent

Writing the class is not quite enough. Two small edits in [`ai/__init__.py`](__init__.py) make the game aware of it.

**1. Import your module.** Python only creates (and registers) your class when your file is imported. Add an import next to the existing `via_ludus_agents` import:

```python
from . import via_ludus_agents
from . import my_agents            # <-- add this line
```

**2. Add your agent's name to `agent_order`.** Lower down in the same file is a list called `agent_order`. It controls which agents are exposed to the game and the order they appear in the menus. An agent that is not in this list is **silently left out**. Add the exact `name` string from your class, for example at the end:

```python
agent_order = [
	"Mark", "Piraveenan", "Bellman-Moore", ...
	"Katz", "Warshall", "Random",
	"Center",                      # <-- add your agent's name
]
```

**3. Restart the web server.** It does not reload your code.

About names:

- `name` must be set **on the class itself**. A subclass of your agent does not inherit it and needs its own.
- Names must be unique across all agents. A repeat stops the program with `ValueError: Duplicate agent name`.
- Without a `name`, the class name is used and you get a warning. Set one explicitly.

## Step 4: Test your Agent

### Ask it for a Move

From `backend-python/`, with the virtual environment active, start Python and run:

```python
from via_ludus import AI_AGENTS, PlayerColor, SearchBoard

board = SearchBoard(size=7)
agent = AI_AGENTS["Center"](PlayerColor.RED)

print(agent.choose_move(board))    # (3, 3)
```

If your agent is not registered yet, you can import the class directly instead of using `AI_AGENTS`, for example `from via_ludus.ai.my_agents import CenterAgent`.

### Play it Against Other Agents

The [`tournament`](../tournament/README.md) package plays many games and reports win rates. Here your agent plays 50 games as each color against the built-in `Random` agent:

```python
from via_ludus import AI_AGENTS
from via_ludus.tournament import play_head_to_head

results = play_head_to_head(
	AI_AGENTS["Center"],
	AI_AGENTS["Random"],
	num_games_per_color=50,
	player_a_name="Center",
	player_b_name="Random",
)

for row in results.summary():
	print(f"{row['player']:8} won {row['total_win_rate']:.0%} of {row['total_games']} games")
```

A good agent should beat `Random` almost every time. `Dijkstra` is a much stronger baseline to measure yourself against, and `RoundRobinTournament` compares many agents at once. See the tournament [`README.md`](../tournament/README.md) in [`backend-python/src/via_ludus/tournament/`](../tournament/).

### Write a Test

To make sure your agent always returns a legal move, see [Writing Tests for Your Own Agents](../../../tests/README.md#writing-tests-for-your-own-agents).

## Step 5: Play Against It in the Browser

1. Stop the web server (`Ctrl+C`) and start it again with `scripts/run_webserver.sh` (or `run_webserver.bat` on Windows). See the [`README.md`](../../../../scripts/README.md) in [`scripts/`](../../../../scripts/).
2. Open <http://localhost:8080>.
3. Choose your agent from the **Red Player** or **Blue Player** menu, and set the other player to **Human** to play against it, or to another agent to watch them play.

## What Your Agent Receives

Agents are given a `board` object. The most useful parts:

| Expression | Meaning |
| --- | --- |
| `board.rows`, `board.cols`, `board.shape` | The dimensions. |
| `board.available` | The set of `(row, col)` cells that can still be claimed (the white cells). |
| `board.get(row, col)` | The `Cell` at a position: `Cell.RED`, `Cell.BLUE`, `Cell.WHITE` or `Cell.WALL`. |
| `board.neighbors(row, col)` | The orthogonally adjacent positions that are on the board. |
| `board.red_cells`, `board.blue_cells` | Sets of `(row, col)` positions for each color. |
| `board.positions_of(cell)` | The set of positions holding a given `Cell`. |
| `board.copy()` | An independent copy you can safely experiment on. |
| `board.set(row, col, cell)` | Claims a white cell (raises an error if it is not white). Use it on a copy. |
| `board.reset(row, col)` | Un-claims a cell that was claimed with `set`, which is handy for search. |
| `board.winner` | `PlayerColor.RED`, `PlayerColor.BLUE`, or `None` if nobody has won yet. |
| `board.is_game_over` | `True` once somebody has won. |

Coordinates are **zero-based** `(row, col)`. Row 0 is the top row and column 0 is the left column. Red needs a path from row 0 to the last row, and Blue needs a path from column 0 to the last column.

To try a move on a copy and see what it does:

```python
trial = board.copy()
trial.set(row, col, color.cell)

if trial.winner == color:
	...  # that move wins the game
```

See the [`README.md`](../board/README.md) in [`backend-python/src/via_ludus/board/`](../board/) for the full board API.

> Your agent must work with *any* board, because the web service and the tournament tools use different board classes behind the same interface.

## Rules Your Agent Must Follow

- **Return plain Python ints.** Return `(row, col)` as ordinary `int` values. If your code produces numpy integers, convert them with `int(...)`.
- **Only play available cells.** The move must be one of `board.available`. Scoring agents get this check for free (see [How a Move is Chosen](#how-a-move-is-chosen)); plain `Agent`s must make sure themselves.
- **Never modify the board you are given.** Always experiment on `board.copy()`. In tournaments that board is the live game.
- **Do not assume a color.** Use the `color` argument of `select_move` and `evaluate_move_options` rather than assuming you are Red, and rather than reading `self.color` there. Your agent will be asked to play both sides, and the same code should answer for either color.
- **Do not rely on memory between moves.** In the browser a *new* agent object is created for every move request, so anything stored on `self` is gone by the next turn. Work everything out from the board you are given.
- **Give every agent a unique `name`.**
- **Keep each move quick.** There is no built-in time limit. A slow agent just makes the browser wait, and large boards (up to $19 \times19$) have many more cells to consider.
- **Declare extra libraries.** If your agent needs a package that is not already installed, add it to [`pyproject.toml`](../../../pyproject.toml) in [`backend-python/`](../../../). An error while importing your file stops the *whole* game library from loading (see below).

## Troubleshooting

| Problem | Likely cause |
| --- | --- |
| My agent is not in the player menus. | You did not complete [Step 3](#step-3-register-the-agent): the module is not imported in `ai/__init__.py`, the name is missing from `agent_order` (or does not match your `name` exactly), or the server was not restarted. |
| The server fails to start, with a traceback that mentions my file. | Python could not import your file: a syntax error, a wrong import, or a missing package. Fix the error shown. Any error in your file affects the whole `via_ludus` package. |
| `ValueError: Duplicate agent name: ...` | Two agent classes use the same `name`. |
| `UserWarning: ... does not define a custom agent name` | Add a `name = "..."` attribute to the class. |
| `TypeError: Can't instantiate abstract class ...` | You did not implement the required method: `select_move` for an `Agent`, or `evaluate_move_options` for a `ScoringAgent`. Defining only `choose_move` is not enough. |
| `ValueError: No available moves with finite scores` | `evaluate_move_options` returned an empty dictionary, scores for cells that are not available, or only `NaN`/infinite scores. |
| The browser shows `API request failed: 500`. | Your agent raised an error. The full traceback is printed in the terminal where the server is running. |
| My agent always plays the same move. | You are using a plain `Max`/`Min` selector (or no mixin) and several moves have the same score. Use `RandomMax`/`RandomMin`, or add a tie-breaker to your scores. |
| A selector mixin has no effect. | The mixin is listed *after* `ScoringAgent` in the class definition. Move it before. |
| My changes have no effect in the browser. | The server was not restarted. |

## Examples to Study

The built-in agents are in `via_ludus_agents/` (see the [`README.md`](via_ludus_agents/README.md) in [`backend-python/src/via_ludus/ai/via_ludus_agents/`](via_ludus_agents/)):

- [`random_agent.py`](via_ludus_agents/random_agent.py) is the simplest possible agent, and the example to read for extending `Agent`. It picks a random available move and returns it as a pair of plain Python integers. Its docstring explains why the cast matters: moves computed with NumPy are NumPy integers, not Python ones.
- [`shortest_path_agent.py`](via_ludus_agents/shortest_path_agent.py) is the example to read for extending `ScoringAgent`, and it is a real heuristic. It finds the shortest route for the player and scores the cells along it. It uses deterministic scoring together with a random tie-breaking selector, exactly the combination described above, and its docstring walks through the mixins and the rules for the scores dictionary.
- [`graph_agents/`](via_ludus_agents/graph_agents) turns the board into a graph and scores cells with graph measures from `networkx`. A good place to look once you want something more advanced.

