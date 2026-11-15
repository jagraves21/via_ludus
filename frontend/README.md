# Frontend

The browser app for Via Ludus. It is plain HTML, CSS and JavaScript (ES modules), with **no build step** and no dependencies: the files in this directory are exactly what the browser loads.

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
| `index.html` | **Play.** Choose a board size and a player for each colour (a human or any agent), then play. |
| `rules.html` | The rules of the game. |
| `about.html` | About the project. |
| `showcase.html` | A visual reference for the app's reusable interface components (buttons, badges, cards, forms). Currently hidden from the navigation. |

## Layout

| Path | Contents |
| --- | --- |
| `js/index.js` | Entry point of the Play page: starts and ends games, handles clicks, and asks agents for moves. |
| `js/config.js` | Settings (see below). |
| `js/api/` | Calls to the web service: `client.js` (the HTTP helpers every request goes through), `agents.js` (list agents), `moves.js` (request a move), `activity.js` (remembers when the backend last answered and spots slow requests), and `idle.js` (refreshes the agent menus after a long silence). |
| `js/game/` | Client-side game state and rules (board, moves, win detection, players). |
| `js/ui/` | Drawing and updating the page: board, status, controls, player menus, and `wake-notice.js` (the "waking up the agents" card). |
| `js/rules.js` | Script for the rules page. |
| `css/` | Stylesheets: base styles, layout and shared components (`components/`), the board (`custom_components/`), and page-specific styles (`pages/`). |
| `icons/`, `site.webmanifest` | Icons and web app manifest. |

## Settings

The [`config.js`](js/config.js) in [`frontend/js/`](js/) holds the settings, with all times in milliseconds.

| Setting | Default | Meaning |
| --- | --- | --- |
| `API_URL` | `/api` on `localhost` or `127.0.0.1`, otherwise the hosted API | Where the API lives. |
| `AI_MOVE_DELAY` | `250` | The minimum time an agent's turn takes. If the agent answers faster than this, the page waits for the remainder before showing the move, so that moves are easy to follow when two agents play each other. |
| `BACKEND_MAY_SLEEP` | `true` unless running locally | Whether the backend can go to sleep. A local backend never does, so the waking-up notice is never shown locally. |
| `SLOW_REQUEST_THRESHOLD_MS` | `5000` (5 seconds) | A request that has waited this long shows the waking-up notice, if the backend plausibly went to sleep. |
| `IDLE_BACKEND_THRESHOLD_MS` | `600000` (10 minutes) | If the browser has not heard from the backend for this long, it refreshes the agent menus, which also wakes the backend. Keep it shorter than the host's idle limit. |
| `BACKEND_SLEEP_AFTER_MS` | `900000` (15 minutes) | After this long without hearing from the backend, it is assumed to be asleep. Only then does a slow request say that the agents are waking up. Otherwise a slow request is just a slow agent. |
| `REFRESH_COOLDOWN_MS` | `30000` (30 seconds) | The minimum time between automatic refreshes of the agent menus, so that a backend that is down is not asked over and over. |
| `WAKE_MESSAGE_INTERVAL_MS` | `8000` (8 seconds) | How often the waking-up notice moves on to its next message. |

## Cold Starts

The hosted backend puts it to sleep when nobody is using it, and the first request after that can take about a minute. The frontend is built to cope with that:

- **A card above the game settings.** If a request has waited longer than `SLOW_REQUEST_THRESHOLD_MS` and the backend has not been heard from for `BACKEND_SLEEP_AFTER_MS`, a card appears directly above the game settings (the player menus and the Start Game button) with a spinner and a changing message ("the AI agents were napping, waking them up"). It never covers anything or disables anything, and it disappears when the backend answers. A slow request to a backend that is awake (a slow agent, or a local backend) does not show it.
- **Waking the backend before you need it.** `js/api/idle.js` watches for the browser having been silent for `IDLE_BACKEND_THRESHOLD_MS`. It reacts to events instead of polling: it checks when the page becomes visible again, when the window gains focus, when the browser comes back online, and with one timer that is only set while the page is visible. Nothing runs while the page is hidden. When it fires it reloads the agent list, which wakes the backend and shows the card if needed.
- **Menus keep their selection.** Reloading the agent list never changes what is selected. If the list has not changed, the menus are left untouched. If a selected agent has disappeared, the menu falls back to Human, except during a game, which keeps its players.
- **Human vs Human never waits.** The player menus start with Human already in them, and starting a game does not depend on the backend. If the agents cannot be reached, a card says so and Human vs Human still works. The next time you return to the page, the frontend tries again (no more than once per `REFRESH_COOLDOWN_MS`).

## How the App Uses Your Agents

When it loads, the Play page asks `GET /api/agents` for the available agents and fills the **Red Player** and **Blue Player** menus with them. It asks again after a long silence (see [Cold Starts](#cold-starts)). When it is an agent's turn, the page sends the current board to `POST /api/agents/{name}/move` and plays the cell that comes back. The details are in the web service [README.md](../backend-python/src/web_service/README.md) found in [backend-python/src/web_service/](../backend-python/src/web_service/).

The rules are implemented twice: in Python for the agents and in `js/game/` for the browser. If you change the rules, change both.

