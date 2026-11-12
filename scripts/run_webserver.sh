#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_ROOT/backend-python"

# Extra command line arguments are passed through to the web service,
# for example: ./scripts/run_webserver.sh --port 9000
PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}" \
	python -m web_service.main \
		--frontend "$REPO_ROOT/frontend" \
		--host 0.0.0.0 \
		--cors-origins http://localhost:8080 http://127.0.0.1:8080 \
		"$@"
