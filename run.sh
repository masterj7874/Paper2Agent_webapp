#!/usr/bin/env bash
# Paper2Agent Studio — one-shot launcher (backend + built frontend on one port)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${PORT:-8765}"
cd "$HERE/backend"
if [ ! -x .venv/bin/python ]; then
  echo "[setup] creating backend venv"; uv venv .venv --python 3.10 >/dev/null
  uv pip install --python .venv/bin/python -r requirements.txt
fi
if [ ! -f "$HERE/frontend/dist/index.html" ] || [ "${REBUILD:-0}" = "1" ]; then
  echo "[setup] building frontend"; (cd "$HERE/frontend" && npm install --no-audit --no-fund && npm run build)
fi
mkdir -p "$HERE/data"
echo "[run] http://localhost:$PORT"
exec .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" "$@"
