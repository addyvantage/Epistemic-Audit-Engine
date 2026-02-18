#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATA_DIR="$ROOT_DIR/paper/data"
FIGURES_DIR="$ROOT_DIR/figures"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
FIGURE_PYTHON="${FIGURE_PYTHON:-$PYTHON_BIN}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

if ! "$FIGURE_PYTHON" - <<'PY' >/dev/null 2>&1
import matplotlib  # noqa: F401
PY
then
  FIGURE_PYTHON="python3"
fi

mkdir -p "$DATA_DIR" "$ROOT_DIR/paper/scripts" "$FIGURES_DIR"

"$PYTHON_BIN" "$ROOT_DIR/paper/scripts/generate_audit_runs.py"
"$FIGURE_PYTHON" "$ROOT_DIR/paper/scripts/make_all_figures.py"

echo "dataset path: $DATA_DIR/audit_runs.jsonl"
echo "figures path: $FIGURES_DIR"
echo "generated files:"
ls -1 "$FIGURES_DIR"
