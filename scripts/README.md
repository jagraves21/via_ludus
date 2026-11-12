# Scripts

Scripts for running Via Ludus on your own machine.

| Script | Platform |
| --- | --- |
| `run_webserver.sh` | macOS, Linux, and Windows with WSL or Git Bash |
| `run_webserver.bat` | Windows (Command Prompt or PowerShell) |

Both scripts do the same thing: they start the Via Ludus web service **and** serve the browser app from the same address, so one command gives you the whole game.

## Before you Run Them

You need Python 3.11 or newer and the web service dependencies installed in a virtual environment. If you have not done this yet, from the root of the repository:

macOS / Linux:

```bash
cd backend-python
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[web-service,graph-agents]"
cd ..
```

Windows:

```bat
cd backend-python
py -m venv .venv
.venv\Scripts\activate
pip install -e ".[web-service,graph-agents]"
cd ..
```

The `graph-agents` extra installs `networkx` and `scipy`, which most of the built-in agents need. Without it the web service still starts, but only limited agents are available.

Make sure the virtual environment is **active** (your prompt usually shows its name) each time you open a new terminal.

## Running the Web Server

From the root of the repository, with the virtual environment active:

macOS / Linux:

```bash
./scripts/run_webserver.sh
```

Windows:

```bat
scripts\run_webserver.bat
```

Then open **<http://localhost:8080>** in your browser. Stop the server with `Ctrl+C`.

You can run the scripts from any directory. They find the repository on their own.

### Changing the Port or Host

Anything you add after the script name is passed to the web service. The most useful options are:

| Option | Default | Meaning |
| --- | --- | --- |
| `--port` | `8080` | Port to listen on. |
| `--host` | `0.0.0.0` | Address to listen on. |

```bash
./scripts/run_webserver.sh --port 9000
```

```bat
scripts\run_webserver.bat --port 9000
```

By default, the scripts listen only on your local computer (127.0.0.1), so the game is accessible only from your own computer at http://localhost:8080. If you want other devices on your network to access the game, add --host 0.0.0.0 and connect using http://\<your-ip\>:8080.

## What the Scripts Do

1. Find the repository root, relative to the script's own location.
2. Add `backend-python/src` to `PYTHONPATH`, so `via_ludus` and `web_service` can be imported.
3. Run `python -m web_service.main`, which starts the FastAPI web service (see [`web_service`](../backend-python/src/web_service/README.md)).
4. Serve the [`frontend/`](../frontend/README.md) directory at `/` and the API under `/api`.

Besides the game, the running server provides:

- <http://localhost:8080/docs>: interactive API documentation
- <http://localhost:8080/api/agents>: the list of available agents, as JSON

## Troubleshooting

| Problem | What to try |
| --- | --- |
| `ModuleNotFoundError: No module named 'fastapi'` (or `uvicorn`, `numpy`) | The dependencies are not installed in the Python you are running. Activate the virtual environment and run the `pip install` command above. |
| `Address already in use` | Something is already using port 8080. Stop it, or use `--port 9000`. |
| `Permission denied` running the `.sh` script | Run it with `bash scripts/run_webserver.sh`, or make it executable with `chmod +x scripts/run_webserver.sh`. |
| `'python' is not recognized` (Windows) | Install Python 3.11+ from python.org and tick **Add Python to PATH**, or activate your virtual environment first. |
| The player drop-downs only list **Human**, or are empty | The page cannot reach the API. Make sure you opened the page through the server (`http://localhost:8080`) and not by double-clicking `index.html`. |
| Only `Random` and `Dijkstra` are available | The `graph-agents` extra is not installed. Run `pip install -e ".[graph-agents]"` from `backend-python`. |
| I changed my agent but the game does not behave differently | The server does not reload your code. Stop it with `Ctrl+C` and start it again. |

