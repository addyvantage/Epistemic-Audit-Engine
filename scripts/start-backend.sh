#!/bin/sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
BACKEND_DIR="$ROOT_DIR/backend"

if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
elif [ -x "$BACKEND_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN=$(command -v python3)
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN=$(command -v python)
else
    echo "No Python interpreter found. Install Python 3 or create .venv first." >&2
    exit 127
fi

if ! "$PYTHON_BIN" -c "import uvicorn" >/dev/null 2>&1; then
    echo "Backend dependencies are missing for $PYTHON_BIN." >&2
    echo "Install them with: $PYTHON_BIN -m pip install -r $BACKEND_DIR/requirements.txt" >&2
    exit 1
fi

export PYTHONPATH="$BACKEND_DIR"

exec "$PYTHON_BIN" -m uvicorn app:app --host 127.0.0.1 --port 8000
