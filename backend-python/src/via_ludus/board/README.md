# Boards, Cells and Colors

The game state.

Rules of the game can be found in the root [README.md](../../../../README.md#the-game); this page describes how they are represented in code.

## `Cell` and `PlayerColor`

`Cell` is an enum with four values: `Cell.RED`, `Cell.BLUE`, `Cell.WHITE` and `Cell.WALL`. Only `Cell.WHITE` cells can be claimed.

`PlayerColor` is an enum with two values, `PlayerColor.RED` and `PlayerColor.BLUE`. It has two helpers:

| Expression | Meaning |
| --- | --- |
| `color.opponent` | The other color. |
| `color.cell` | The `Cell` that marks that color's cells. |

## The `Board` Interface

Every board class provides the following. Agents should only use this interface, because the web service and the tournament tools use different board classes.

| Expression | Meaning |
| --- | --- |
| `rows`, `cols`, `shape` | The dimensions. |
| `available` | The set of `(row, col)` positions that can still be claimed (same as `empty_cells`). |
| `empty_cells`, `red_cells`, `blue_cells` | Position sets for each kind of cell. |
| `positions_of(cell)` | The set of positions holding a `Cell`. |
| `get(row, col)` | The `Cell` at a position. |
| `set(row, col, cell)` | Claims a white cell for `Cell.RED` or `Cell.BLUE`. Raises an error if the cell is not white. |
| `reset(row, col)` | Un-claims a cell that was claimed with `set`. Cells that were prefilled at the start cannot be reset. |
| `neighbors(row, col)` | The orthogonally adjacent positions that lie on the board. |
| `copy()` | An independent copy of the board, of the same class. |
| `winner` | `PlayerColor.RED`, `PlayerColor.BLUE`, or `None`. |
| `is_game_over` | `True` when `winner` is not `None`. |
| `serialize()` | The board as text. See below. |
| `plot()` | Draws the board (needs the `visualization` extra). |
| `Board.from_board(other)` | A class method that builds a board of this class from any other board. |

Coordinates are zero-based `(row, col)`, with row 0 at the top and column 0 at the left.

## Board Classes

| Class | Used By | How it Detects a Winner |
| --- | --- | --- |
| `SearchBoard` | The web service | Searches for a path each time `winner` is read. Simple. |
| `UnionFindBoard` | Games and tournaments (the default) | Tracks connected groups with a union-find structure as cells are claimed. Faster when playing many games. |

Both behave identically through the interface above.

## The Starting Position

`SearchBoard(size=11)` (or `UnionFindBoard(size=11)`) builds the starting position:

- The four corners are `WALL`.
- The top and bottom edges are `RED`. The left and right edges are `BLUE`.
- Inside the board, cells where `row + col` is even start `WHITE`. The rest are prefilled: `BLUE` on odd rows and `RED` on even rows.

Boards are square when you create them with `size`, which must be at least 3. Use an odd size: even sizes work but produce a warning, because they contain redundant white cells near the last row and column. The browser offers odd sizes from 5 to 19.

## Serialization

`board.serialize()` returns text in the form `rows,cols,cells`. The cells are listed row by row, one character each:

- `R` red,
- `B` blue,
- `W` white, and
- `X` wall. 

For example, the starting $5 \times 5$ board is:

```text
5,5,XRRRXBWBWBBRWRBBWBWBXRRRX
```

`SearchBoard.deserialize(text)` rebuilds a board from this text. The web service uses the same cell string as the `board` field of its [move requests](../../web_service/README.md#post-apiagentsagent_namemove).

