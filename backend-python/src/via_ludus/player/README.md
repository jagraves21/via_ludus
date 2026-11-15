# Players, Move Selectors, and Mixins

This package defines what a *player* is, and the building blocks that agents are made from. If you are writing an agent, the [README.md](../ai/README.md) in [backend-python/src/via_ludus/ai/](../ai/) covers everything you need. This page is the reference behind it.

## Classes

| Class | Purpose |
| --- | --- |
| `Player` | Abstract base class for anything that plays. Subclasses implement `select_move(board, color)`. Provides `choose_move(board)`, `color`, `opponent_color`, `cell`, `make_move(board)` and `is_winner(board)`. |
| `ScoringPlayer` | A `Player` that works in two stages: `score_moves(board, color)` gives each move a score, and a **selector** picks the move to play. It implements `select_move` for you; subclasses implement `score_moves`. |
| `MoveSelector` and Its Subclasses | Turn a dictionary of `{move: score}` into one chosen move. |
| Selector Mixins | Small classes that choose which selector a `ScoringPlayer` uses. |
| Determinism Nixins | Declare that a player always makes the same move in the same position. |

## `choose_move` and `select_move`

| Method | Meaning |
| --- | --- |
| `select_move(board, color)` | The move this player would select for `color`. It assumes it is `color`'s turn, and `color` need not be the player's own color, so a player can be asked what it would play for its opponent (for example to model the opponent during a search). Abstract: this is what subclasses implement. |
| `choose_move(board)` | The move this player plays in a game. It is `select_move(board, self.color)`. Games, tournaments and the web service only ever call this. |

`Agent` and `ScoringAgent` in [`ai/agent.py`](../ai/agent.py) are `Player` and `ScoringPlayer` plus a registry, so that every agent appears in the game by name.

## Move Selectors

A selector receives a dictionary mapping `(row, col)` to a score. It first discards any move whose score is `NaN` or infinite. If nothing remains it raises `ValueError("No available moves with finite scores")`.

| Selector | Chooses | Ties | Options |
| --- | --- | --- | --- |
| `MaxSelector` (also `BestSelector`) | The highest score. | The middle of the tied moves, sorted by `(row, col)`. | |
| `MinSelector` | The lowest score. | The middle of the tied moves, sorted by `(row, col)`. | |
| `RandomMaxSelector` | The highest score. | Uniformly at random. | `seed` |
| `RandomMinSelector` | The lowest score. | Uniformly at random. | `seed` |
| `SoftmaxSelector` | Any move, with probability proportional to `exp(score / temperature)`. | Equally likely. | `temperature` (default `1.0`, must be finite and greater than 0), `seed` |
| `SoftminSelector` | Any move, with probability proportional to `exp(-score / temperature)`. | Equally likely. | `temperature`, `seed` |

A low temperature concentrates the probability on the best move, and a high temperature spreads it out towards uniform. Providing a `seed` makes the random selectors reproducible.

## Selector mixins

A `ScoringPlayer` asks `create_selector()` for its selector when it is created. The mixins override that method:

| Mixin | `create_selector()` returns |
| --- | --- |
| `MaxSelectorMixin` | `MaxSelector()` |
| `MinSelectorMixin` | `MinSelector()` |
| `RandomMaxSelectorMixin` | `RandomMaxSelector()` |
| `RandomMinSelectorMixin` | `RandomMinSelector()` |
| `SoftmaxSelectorMixin` | `SoftmaxSelector()` |
| `SoftminSelectorMixin` | `SoftminSelector()` |

Without a mixin, `ScoringPlayer.create_selector()` returns a `BestSelector`, which behaves like `MaxSelector`.

**A mixin must come before the player class** in the list of base classes, otherwise `ScoringPlayer`'s own `create_selector` is found first and the mixin is silently ignored:

```python
class Works(RandomMaxSelectorMixin, ScoringAgent): ...
class Ignored(ScoringAgent, RandomMaxSelectorMixin): ...
```

To use non-default selector settings, override `create_selector` yourself, or pass a ready-made selector when constructing the player: `MyAgent(color, selector=SoftmaxSelector(temperature=0.5, seed=1))`.

## Determinism

Tournaments can save time on matchups between deterministic players: if every move in the first game was deterministic, the remaining games would be identical, so the result is reused instead of replayed. Players tell the tournament code whether they qualify:

| Class | Mixin | Meaning |
| --- | --- | --- |
| `Player` | `DeterministicMoveSelectionMixin` | `choose_move` returns the same move for equivalent board states, regardless of history or earlier calls. This covers `choose_move` only: `select_move` asked about another color makes no promise. |
| `ScoringPlayer` | `DeterministicScoringMixin` | `score_moves` returns the same scores for equivalent board states and colors. |

For a `ScoringPlayer`, `is_deterministic` is true when the scoring is deterministic **and** the selector is not random (`MaxSelector`, `MinSelector`). With `RandomMax`/`RandomMin` selectors, `choose_move_with_determinism` still reports a move as deterministic whenever one move has the single best score. With a softmax or softmin selector a move is deterministic only if there is a single candidate.

These contracts are **declarations, not checks**. A player that declares determinism and then isn't deterministic makes tournament results wrong without any error. Leave the mixins out when in doubt.

## Validation helpers

`is_player`, `is_scoring_player`, `is_player_class` and `is_scoring_player_class` return `True` or `False`. The matching `validate_*` functions raise `TypeError` instead.

