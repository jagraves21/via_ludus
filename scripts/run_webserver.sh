#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_ROOT/backend-python"

PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}" 
	python -m web_service.main \
		--frontend "$REPO_ROOT/frontend" \
		--host 0.0.0.0 \
		--cors-origins http://localhost:8080 http://127.0.0.1:8080

