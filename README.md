# Via Ludus

Via Ludus is an educational two-player connection strategy game designed for experimenting with game-playing AI.

You can play it in your browser, against another person or against one of the built-in computer agents, and you can write your own agents in Python and watch them play. The rules are small, the code is readable, and the project is meant to give students a practical environment for implementing and experimenting with game-playing AI.

- [The Game](#the-game)
- [Play it Locally](#play-it-locally)
- [Build Your Own Agent](#build-your-own-agent)
- [Repository Layout](#repository-layout)
- [License](#license)

## The Game

Two players, **Red** and **Blue**, take turns claiming cells on a square board. Each player is trying to build an unbroken path across it:

- **Red** connects the **top edge** to the **bottom edge**.
- **Blue** connects the **left edge** to the **right edge**.

The first player to complete their connection wins immediately.

### The Board

Every cell on the board is one of four types:

| Cell | Meaning |
| --- | --- |
| 🟥 Red | Belongs to Red. |
| 🟦 Blue | Belongs to Blue. |
| ⬜ White | Unclaimed. The only cells a player can claim. |
| ⬛ Wall | Blocked. Never claimable. |

Every game starts from the same pattern. The four corners are Walls, the whole top and bottom edges are Red, and the whole left and right edges are Blue. The interior alternates between prefilled Red/Blue cells and White cells that players can claim. This is the starting position for the default 11 × 11 board:

```text
⬛🟥🟥🟥🟥🟥🟥🟥🟥🟥⬛
🟦⬜🟦⬜🟦⬜🟦⬜🟦⬜🟦
🟦🟥⬜🟥⬜🟥⬜🟥⬜🟥🟦
🟦⬜🟦⬜🟦⬜🟦⬜🟦⬜🟦
🟦🟥⬜🟥⬜🟥⬜🟥⬜🟥🟦
🟦⬜🟦⬜🟦⬜🟦⬜🟦⬜🟦
🟦🟥⬜🟥⬜🟥⬜🟥⬜🟥🟦
🟦⬜🟦⬜🟦⬜🟦⬜🟦⬜🟦
🟦🟥⬜🟥⬜🟥⬜🟥⬜🟥🟦
🟦⬜🟦⬜🟦⬜🟦⬜🟦⬜🟦
⬛🟥🟥🟥🟥🟥🟥🟥🟥🟥⬛
```

### Taking a Turn

1. **Red always moves first**, and the players alternate from there.
2. On your turn you claim **exactly one white cell**. It becomes your color and stays yours for the rest of the game.
3. After every move the board is checked for a winning path. If there is one, the game ends immediately. Otherwise the turn passes to the other player.

You cannot claim a cell that is already Red, Blue, or a Wall, and you cannot move after the game has ended.

### Connections are Orthogonal

Cells connect through their **top, bottom, left and right** neighbors only. Cells that touch at a corner are **not** connected.

```text
🟥⬜        These two Red cells are NOT connected:
⬜🟥        they touch only diagonally.

🟥🟥        These Red cells form one connected group:
⬜🟥        they share edges.
```

A winning path can wander in any direction (left, right, up, down) as long as every consecutive pair of cells shares an edge. It can run through cells that were prefilled at the start as well as cells the player has claimed, and it must be made entirely of that player's color.

### Quick Reference

- Red moves first; players alternate; one move per turn.
- Only white cells can be claimed.
- Red connects top to bottom. Blue connects left to right.
- Connections are orthogonal only.
- The first completed connection wins, and play stops immediately.

These rules can also be found on the **Rules** page of the web app.

## Play it Locally

You need **Python 3.11 or newer**.

**1. Install the dependencies** (once). From the root of this repository:

macOS / Linux:

```bash
cd backend-python
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[web-service,graph-agents]"
cd ..
```

Windows (Command Prompt or PowerShell):

```bat
cd backend-python
py -m venv .venv
.venv\Scripts\activate
pip install -e ".[web-service,graph-agents]"
cd ..
```

**2. Start the server** (with the virtual environment still active):

| Platform | Command |
| --- | --- |
| macOS / Linux | `./scripts/run_webserver.sh` |
| Windows | `scripts\run_webserver.bat` |

**3. Open <http://localhost:8080>** in your browser, pick a board size, choose a player for each color (a human or any of the available agents), and press **Start Game**. Press `Ctrl+C` in the terminal to stop the server.

More detail, options and troubleshooting are in [`scripts/README.md`](scripts/README.md).

## Build Your Own Agent

Via Ludus is designed so that you can write a computer player in a few lines of Python and immediately play against it or pit it against the built-in agents.

Start with the **[agent guide](backend-python/src/via_ludus/ai/README.md)**. It explains how to create an agent, which base class to extend, how to register your agent so it shows up in the game, and how to test it.

## Repository Layout

```text
via_ludus/
├── frontend/            The browser app (plain HTML, CSS and JavaScript)
├── backend-python/
│   ├── src/
│   │   ├── via_ludus/   The game library: board, players, agents, tournaments
│   │   └── web_service/ The FastAPI web service used by the browser app
│   └── tests/           The test suite
├── openapi/             OpenAPI description of the web service
└── scripts/             Scripts to run the web server locally
```

| Directory | What's In It |
| --- | --- |
| [`frontend/`](frontend/) | The web app: play, rules and about pages. |
| [`backend-python/`](backend-python/) | Python backend: setup, packages, and how to run the tests. |
| [`backend-python/src/via_ludus/board/`](backend-python/src/via_ludus/board/) | The board, cells, and player colors. |
| [`backend-python/src/via_ludus/player/`](backend-python/src/via_ludus/player/) | Players, move selectors, and the mixins that configure them. |
| [`backend-python/src/via_ludus/ai/`](backend-python/src/via_ludus/ai/) | **Where student agents go.** Start here to write an agent. |
| [`backend-python/src/via_ludus/ai/via_ludus_agents/`](backend-python/src/via_ludus/ai/via_ludus_agents/) | The built-in agents, which are good examples to read. |
| [`backend-python/src/via_ludus/tournament/`](backend-python/src/via_ludus/tournament/) | Playing games and tournaments to compare agents. |
| [`backend-python/src/web_service/`](backend-python/src/web_service/) | The HTTP API that connects the browser to the agents. |
| [`backend-python/tests/`](backend-python/tests/) | How the tests are organised and run. |
| [`scripts/`](scripts/) | Scripts that start the web server. |

## License

Via Ludus is released under the [MIT License](LICENSE).

