# Games and Tournaments

Tools for playing agents against each other, which is how you find out whether a new agent is any good. Everything here works with agent **classes** (such as `AI_AGENTS["Random"]`), not instances; games create the players themselves.

Install the `progress` extra (`tqdm`) for progress bars, `visualization` (`matplotlib`) for plots, and `dataframe` (`pandas`) for the `*_df()` methods.

## Head-to-Head

`play_head_to_head` plays two agents against each other as both colors:

```python
from via_ludus import AI_AGENTS
from via_ludus.tournament import play_head_to_head

results = play_head_to_head(
	AI_AGENTS["Dijkstra"],
	AI_AGENTS["Random"],
	num_games_per_color=50,
	player_a_name="Dijkstra",
	player_b_name="Random",
)

for row in results.summary():
	print(row["player"], row["total_win_rate"])
```

This plays 50 games with Dijkstra as Red and 50 with Dijkstra as Blue (100 games in total). Always pass `player_a_name` and `player_b_name` so the results use your names.

Useful optional arguments (shared by all the functions below): `board` (a starting board, for example `UnionFindBoard(size=7)`) and `starting_color`.

## One Color Assignment

`play_matchup` plays `num_games` games with a fixed color for each agent:

```python
from via_ludus.tournament import play_matchup

results = play_matchup(
	red_player=AI_AGENTS["Dijkstra"],
	blue_player=AI_AGENTS["Random"],
	num_games=20,
	red_name="Dijkstra",
	blue_name="Random",
)
```

## Round-Robin Tournaments

`RoundRobinTournament` plays every agent against every other agent, in both color orientations:

```python
from via_ludus import AI_AGENTS
from via_ludus.tournament import RoundRobinTournament

# Add your own agent's name to this tuple to see how it ranks.
names = ("Random", "Dijkstra")

tournament = RoundRobinTournament(
	{name: AI_AGENTS[name] for name in names},
	num_games_per_color=20,
)
tournament.run()

for row in tournament.results.summary():
	print(row["player"], row["total_win_rate"])
```

`run(checkpoint_file="results.json")` saves the results after every finished matchup, so a long tournament leaves a usable file behind even if it is interrupted. To resume, load that file and pass it back in; only the games that are still missing are played:

```python
from via_ludus.tournament import TournamentResults

saved = TournamentResults.load("results.json")
tournament = RoundRobinTournament(players, num_games_per_color=20, results=saved)
tournament.run(checkpoint_file="results.json")
```

## Results

All of these return a `TournamentResults` object, which offers:

| Method | What you Get |
| --- | --- |
| `summary()` | A list of dictionaries, one per player: games, wins, win rate, and the same split by Red and Blue. |
| `head_to_head_summary()` | A list of dictionaries, one per ordered pair: win rates and average moves to win. |
| `win_matrix()`, `red_win_matrix()`, `blue_win_matrix()` | Win-rate matrices. |
| `first_move_advantage()` | How much playing first helped. |
| `elo_ratings()` | Elo ratings computed from the games. |
| `plot_win_matrix()` (and Red/Blue versions) | Heat maps of the matrices. Needs `matplotlib`. |
| `summary_df()` and other `*_df()` methods | The same tables as pandas DataFrames. Needs `pandas`. |
| `save(filename)`, `TournamentResults.load(filename)` | Store and reload results. |

## A Single Game

`Game` plays one game, which is useful when you want to look at the final board:

```python
from via_ludus import AI_AGENTS
from via_ludus.tournament import Game

game = Game(AI_AGENTS["Dijkstra"], AI_AGENTS["Random"])
winner = game.play()
print(winner, "won in", game.move_count, "moves")
```

## Determinism Shortcut

When both agents declare themselves deterministic (see [Declaring Determinism](../ai/README.md#declaring-determinism)), every game in a matchup would be identical. The tournament plays the first game and reuses its result for the rest. If an agent declares determinism wrongly, the results are wrong too.

`summary()` reports `deterministic_games` so you can see how many results were reused.

