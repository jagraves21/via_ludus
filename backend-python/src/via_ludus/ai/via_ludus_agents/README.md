# Built-In Agents

The agents that ship with Via Ludus. They are registered automatically, so they appear in the game's player menus and are ready to play against, and they are good examples to read before writing your own. To write your own agent, see the [agent guide](../README.md).

## Where to Start Teading

| File | Why Read It |
| --- | --- |
| [`random_agent.py`](random_agent.py) | The simplest possible agent, and the model for extending `Agent`. It implements `select_move`, picks a random available move, and returns it as plain Python integers. |
| [`shortest_path_agent.py`](shortest_path_agent.py) | The model for extending `ScoringAgent`, and a real heuristic. It finds the player's shortest route across the board and scores the cells on it. It declares deterministic scoring and breaks ties randomly, a combination explained in the [agent guide](../README.md#declaring-determinism). |
| [`graph_agents/`](graph_agents) | Agents that turn the board into a graph and score cells with graph algorithms. More advanced. |

Both of these files begin with a docstring that explains the technique. `Random` is the only built-in agent that extends `Agent` directly; every other built-in agent is a `ScoringAgent`.

## The Agents

Agents are listed in the menus in the order given by `agent_order` in [`ai/__init__.py`](../__init__.py). Each agent's menu label is its `name`.

### Baselines

| Name | Class | Extends |
| --- | --- | --- |
| `Random` | `RandomAgent` | `Agent` |
| `Dijkstra` | `ShortestPathAgent` | `ScoringAgent` |

These two need nothing beyond the core library.

### Graph Agents

The rest are built on [`networkx`](https://networkx.org/) and [`scipy`](https://scipy.org/), so they need the `graph-agents` extra (`pip install -e ".[graph-agents]"` from `backend-python/`). Without it, only the baselines above are available. They are grouped by the kind of graph measure they score cells with:

| Source file | Names (classes) |
| --- | --- |
| [`distance_agent.py`](graph_agents/distance_agent.py) | `Floyd` (`OffensiveDistanceAgent`), `Warshall` (`DefensiveDistanceAgent`), `Roy` (`CombinedDistanceAgent`) |
| [`paths_agent.py`](graph_agents/paths_agent.py) | `Bellman` (`OffensivePathsAgent`), `Moore` (`DefensivePathsAgent`), `Bellman-Moore` (`CombinedPathsAgent`) |
| [`vertex_cut_agent.py`](graph_agents/vertex_cut_agent.py) | `Fulkerson` (`OffensiveCutAgent`), `Ford` (`DefensiveCutAgent`), `Menger` (`OffensiveOverlapCutAgent`), `Whitney` (`DefensiveOverlapCutAgent`) |
| [`vertex_centrality_agent.py`](graph_agents/vertex_centrality_agent.py) | `Shaw` (degree), `Anthonisse` (betweenness), `Brandes` (betweenness, subset), `Bavelas` (closeness), `Marchiori` (harmonic), `Bonacich` (eigenvector), `Katz`, `Goh` (load), `Newman` (current-flow betweenness), `Bozzo` (approximate current-flow betweenness), `Fleischer` (current-flow betweenness, subset), `Zelen` (current-flow closeness), `Stephenson` (information), `Higham` (communicability betweenness), `Estrada` (subgraph), `Rodriguez-Velazquez` (subgraph, exponential), `Piraveenan` (percolation), `Kermarrec` (second-order), `Qi` (Laplacian) |
| [`edge_centrality_agent.py`](graph_agents/edge_centrality_agent.py) | `Girvan` (edge betweenness), `Ulrik` (edge betweenness, subset), `Daniel` (edge current-flow betweenness), `Mark` (edge current-flow betweenness, subset), `Kwang-Il` (edge load) |

The shared base class and helpers for these agents are in [`graph_agent.py`](graph_agents/graph_agent.py), [`graph_builder_mixins.py`](graph_agents/graph_builder_mixins.py) and [`graph_utils/`](graph_agents/graph_utils). The centrality measures come from `networkx`, so its documentation explains what each one computes.

## Using Them

Look an agent up by name:

```python
from via_ludus import AI_AGENTS, PlayerColor, SearchBoard

agent = AI_AGENTS["Dijkstra"](PlayerColor.RED)
print(agent.choose_move(SearchBoard(size=7)))
```

Or compare several of them with the [tournament tools](../../tournament/README.md).

