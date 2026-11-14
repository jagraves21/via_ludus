# Frontend

The browser app for Via Ludus; it is plain HTML, CSS and JavaScript (ES modules), with **no build step** and no dependencies: the files in this directory are exactly what the browser loads.

## Running It

Run it through the web service, which serves these files and the API they talk to (see the [`README.md`](../scripts/README.md) in [`scripts/`](../scripts/)):

```bash
./scripts/run_webserver.sh      # macOS / Linux
scripts\run_webserver.bat       # Windows
```

Then open <http://localhost:8080>.

Opening `index.html` directly from disk will not work. Browsers refuse to load ES modules from `file://` URLs, and the page needs the API to list the available agents and ask them for moves.

## Pages

| File | Page |
| --- | --- |
| `index.html` | **Play.** Choose a board size and a player for each color (a human or any agent), then play. |
| `rules.html` | The rules of the game. |
| `about.html` | About the project. |
| `showcase.html` | A visual reference for the app's reusable interface components (buttons, badges, cards, forms). Currently hidden from the navigation. |

## Layout

| Path | Contents |
| --- | --- |
| `js/index.js` | Entry point of the Play page: starts and ends games, handles clicks, and asks agents for moves. |
| `js/config.js` | Settings (see below). |
| `js/api/` | Calls to the web service (`client.js` for the HTTP helpers, `agents.js` to list agents, `moves.js` to request a move). |
| `js/game/` | Client-side game state and rules (board, moves, win detection, players). |
| `js/ui/` | Drawing and updating the page (board, status, controls, player menus). |
| `js/rules.js` | Script for the rules page. |
| `css/` | Stylesheets: base styles, layout and shared components (`components/`), the board (`custom_components/`), and page-specific styles (`pages/`). |
| `icons/`, `site.webmanifest` | Icons and web app manifest. |

## Settings

The [`config.js`](js/config.js) in [`frontend/js/`](js/) holds two settings:

- `API_URL`: where the API lives. On `localhost` or `127.0.0.1` the app uses the same server that served the page (`/api`). On any other host it uses the hosted API.
- `AI_MOVE_DELAY`: the minimum time (in milliseconds) an agent's turn takes. If the agent answers faster than this, the page waits for the remainder before showing the move, so that moves are easy to follow when two agents play each other.

## How the App Uses Your Agents

When it loads, the Play page asks `GET /api/agents` for the available agents and fills the **Red Player** and **Blue Player** menus with them. When it is an agent's turn, the page sends the current board to `POST /api/agents/{name}/move` and plays the cell that comes back. The details are in the [`README.md`](../backend-python/src/web_service/README.md) in [`backend-python/src/web_service/`](../backend-python/src/web_service/).

The rules are implemented twice: in Python for the agents and in `js/game/` for the browser. If you change the rules, change both.

