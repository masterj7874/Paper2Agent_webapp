#!/usr/bin/env bash
# Dev mode: backend with auto-reload on :8765 + Vite dev server on :5173 (proxies /api)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
(cd "$HERE/backend" && exec .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload) &
BACK=$!
trap 'kill $BACK 2>/dev/null' EXIT
(cd "$HERE/frontend" && npm run dev -- --host)
