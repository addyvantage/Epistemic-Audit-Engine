#!/usr/bin/env python3
"""Create Figure 6: Risk Score vs Supported-Claim Rate (per audit run)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = BASE_DIR / "data" / "audit_runs.jsonl"
FIGURES_DIR = BASE_DIR / "figures"
OUTPUT_PNG = FIGURES_DIR / "fig6_score_vs_supported_rate.png"
OUTPUT_PDF = FIGURES_DIR / "fig6_score_vs_supported_rate.pdf"


def _warn(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_supported_rate(summary: Any) -> float | None:
    if not isinstance(summary, dict):
        return None

    supported = _to_float(summary.get("supported"))
    if supported is None:
        return None

    total = _to_float(summary.get("total_asserted_claims"))
    if total is None:
        total = _to_float(summary.get("total"))

    if total is None:
        count_keys = [
            "supported",
            "refuted",
            "uncertain",
            "insufficient",
            "insufficient_evidence",
            "partially_supported",
        ]
        observed = [_to_float(summary.get(key)) for key in count_keys if key in summary]
        valid_counts = [value for value in observed if value is not None]
        if valid_counts:
            total = sum(valid_counts)

    if total is None or total <= 0:
        return None

    rate = supported / total
    return max(0.0, min(1.0, rate))


def load_points(path: Path) -> tuple[list[float], list[float]]:
    x_vals: list[float] = []
    y_vals: list[float] = []

    with path.open("r", encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue

            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                _warn(f"Skipping malformed JSON at line {line_number}: {exc}")
                continue

            if not isinstance(payload, dict):
                _warn(f"Skipping non-object JSON at line {line_number}")
                continue

            score = _to_float(payload.get("hallucination_score"))
            if score is None:
                _warn(f"Skipping line {line_number}: missing/invalid hallucination_score")
                continue
            score = max(0.0, min(1.0, score))

            supported_rate = _extract_supported_rate(payload.get("summary"))
            if supported_rate is None:
                _warn(f"Skipping line {line_number}: insufficient summary fields for supported rate")
                continue

            x_vals.append(score)
            y_vals.append(supported_rate)

    return x_vals, y_vals


def make_figure(x_vals: list[float], y_vals: list[float], png_path: Path, pdf_path: Path) -> None:
    plt.rcParams["font.family"] = "DejaVu Sans"

    fig, ax = plt.subplots(figsize=(8, 5), facecolor="white")
    ax.set_facecolor("white")

    ax.scatter(x_vals, y_vals)

    ax.axvline(0.33, linestyle="--", linewidth=1.2, color="black", alpha=0.8)
    ax.axvline(0.66, linestyle="--", linewidth=1.2, color="black", alpha=0.8)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Hallucination / Epistemic Risk Score")
    ax.set_ylabel("Supported Claim Rate")
    ax.grid(True, linestyle="--", linewidth=0.7, alpha=0.35)

    fig.tight_layout()
    fig.savefig(png_path, dpi=300)
    fig.savefig(pdf_path)
    plt.close(fig)


def main() -> int:
    if not INPUT_PATH.exists():
        print(f"ERROR: Input file not found: {INPUT_PATH}", file=sys.stderr)
        return 1

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    x_vals, y_vals = load_points(INPUT_PATH)

    if len(x_vals) < 5:
        _warn(f"Only {len(x_vals)} valid point(s) found; generating figure anyway")

    make_figure(x_vals, y_vals, OUTPUT_PNG, OUTPUT_PDF)

    print(f"SAVED: {OUTPUT_PNG.resolve()}")
    print(f"SAVED: {OUTPUT_PDF.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
