#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$ROOT_DIR/paper/data"
FIGURES_DIR="$ROOT_DIR/figures"
VERIFY_SCRIPT="$ROOT_DIR/paper/scripts/verify_research_setup.py"
PIPELINE_SCRIPT="$ROOT_DIR/paper/scripts/run_research_pipeline.sh"
GEN_SCRIPT="$ROOT_DIR/paper/scripts/generate_audit_runs.py"
FIG_SCRIPT="$ROOT_DIR/paper/scripts/make_all_figures.py"

mkdir -p "$DATA_DIR" "$ROOT_DIR/paper/scripts" "$FIGURES_DIR" "$ROOT_DIR/scripts"

: "${EPI_SYNTH_RUNS:=531}"
: "${EPI_SYNTH_SEED:=42}"
: "${EPI_SYNTH_MODE:=demo}"
export EPI_SYNTH_RUNS EPI_SYNTH_SEED EPI_SYNTH_MODE

PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

if [[ ! -f "$VERIFY_SCRIPT" ]]; then
  echo "Missing setup verifier: $VERIFY_SCRIPT" >&2
  exit 1
fi

"$PYTHON_BIN" "$VERIFY_SCRIPT"

if [[ -f "$PIPELINE_SCRIPT" ]]; then
  bash "$PIPELINE_SCRIPT"
else
  if [[ ! -f "$GEN_SCRIPT" ]]; then
    echo "Missing required script: $GEN_SCRIPT" >&2
    exit 1
  fi
  if [[ ! -f "$FIG_SCRIPT" ]]; then
    echo "Missing required script: $FIG_SCRIPT" >&2
    exit 1
  fi

  "$PYTHON_BIN" "$GEN_SCRIPT"
  "$PYTHON_BIN" "$FIG_SCRIPT"
fi

DATASET_PATH="$DATA_DIR/audit_runs.jsonl"
if [[ ! -f "$DATASET_PATH" ]]; then
  echo "Expected dataset not found: $DATASET_PATH" >&2
  exit 1
fi

LINE_COUNT="$(wc -l < "$DATASET_PATH" | tr -d ' ')"

echo "dataset path: $DATASET_PATH"
echo "figures path: $FIGURES_DIR"
echo "jsonl lines: $LINE_COUNT"
echo "figure files (sorted):"
find "$FIGURES_DIR" -maxdepth 1 -type f \( -name "*.png" -o -name "*.pdf" \) -print | sed "s|$FIGURES_DIR/||" | sort
