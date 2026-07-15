#!/usr/bin/env bash
# JARVIS OS — one-command launch (Iron Man style boot)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT"

if [[ -f "$ROOT/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
fi

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     J.A.R.V.I.S. OS — BOOT SEQUENCE      ║"
echo "╚══════════════════════════════════════════╝"
echo "  Console → http://127.0.0.1:8000/console"
echo ""

exec python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
