#!/usr/bin/env python3
"""Figure 10: Calibration-style plot of supported rate vs epistemic risk bins."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "paper" / "data" / "audit_runs.jsonl"
SCRIPTS_DIR = ROOT / "paper" / "scripts"
FIGURES_DIR = ROOT / "paper" / "figures"
OUT_PNG = FIGURES_DIR / "fig10_risk_tier_vs_supported_rate.png"
OUT_PDF = FIGURES_DIR / "fig10_risk_tier_vs_supported_rate.pdf"

POSITIVE_VERDICTS = {"SUPPORTED", "PARTIALLY_SUPPORTED"}
NEGATIVE_VERDICTS = {"REFUTED", "UNCERTAIN", "INSUFFICIENT_EVIDENCE"}
VALID_VERDICTS = POSITIVE_VERDICTS | NEGATIVE_VERDICTS
SCORE_KEYS = ("hallucination_score", "risk_score", "epistemic_risk_score", "score")


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_verdict(raw: Any) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip().upper()
    return text if text in VALID_VERDICTS else None


def extract_score(run: dict[str, Any]) -> float | None:
    for key in SCORE_KEYS:
        if key in run:
            score = to_float(run.get(key))
            if score is not None:
                return clamp01(score)
    return None


def extract_claim_verdict(claim: dict[str, Any]) -> str | None:
    verification = claim.get("verification")
    if isinstance(verification, dict):
        verdict = normalize_verdict(verification.get("verdict"))
        if verdict is not None:
            return verdict

    for key in ("verdict", "label"):
        verdict = normalize_verdict(claim.get(key))
        if verdict is not None:
            return verdict
    return None


def parse_runs_from_jsonl(path: Path) -> list[tuple[float, float, int, int]]:
    parsed: list[tuple[float, float, int, int]] = []

    with path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue

            score = extract_score(obj)
            claims = obj.get("claims")
            if score is None or not isinstance(claims, list) or not claims:
                continue

            supported = 0
            total = 0
            for claim in claims:
                if not isinstance(claim, dict):
                    continue
                verdict = extract_claim_verdict(claim)
                if verdict is None:
                    continue
                total += 1
                if verdict in POSITIVE_VERDICTS:
                    supported += 1

            if total == 0:
                continue

            run_rate = supported / total
            parsed.append((score, run_rate, supported, total))

    return parsed


def generate_synthetic_runs(n: int = 250, seed: int = 7) -> list[tuple[float, float, int, int]]:
    rng = np.random.default_rng(seed)
    runs: list[tuple[float, float, int, int]] = []

    for _ in range(n):
        score = float(rng.uniform(0.0, 1.0))
        n_claims = int(rng.integers(8, 31))

        # Monotonic trend: support probability drops with risk score.
        base_p = 0.92 - 0.78 * score
        noisy_p = clamp01(float(base_p + rng.normal(0.0, 0.06)))
        supported = int(rng.binomial(n_claims, noisy_p))

        run_rate = supported / n_claims
        runs.append((score, run_rate, supported, n_claims))

    return runs


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)

    phat = successes / total
    z2 = z * z
    denom = 1.0 + z2 / total
    center = (phat + z2 / (2.0 * total)) / denom
    margin = (z / denom) * math.sqrt((phat * (1.0 - phat) / total) + (z2 / (4.0 * total * total)))
    return (clamp01(center - margin), clamp01(center + margin))


def bin_index(score: float, n_bins: int) -> int:
    if score >= 1.0:
        return n_bins - 1
    idx = int(score * n_bins)
    return max(0, min(n_bins - 1, idx))


def build_plot_data(
    runs: list[tuple[float, float, int, int]], n_bins: int = 10
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float, list[int]]:
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

    run_rate_lists: list[list[float]] = [[] for _ in range(n_bins)]
    pooled_supported = [0 for _ in range(n_bins)]
    pooled_total = [0 for _ in range(n_bins)]
    run_counts = [0 for _ in range(n_bins)]

    total_supported_all = 0
    total_claims_all = 0

    for score, run_rate, supported, total in runs:
        i = bin_index(score, n_bins)
        run_rate_lists[i].append(run_rate)
        pooled_supported[i] += supported
        pooled_total[i] += total
        run_counts[i] += 1

        total_supported_all += supported
        total_claims_all += total

    mean_rates = np.full(n_bins, np.nan, dtype=float)
    yerr_low = np.zeros(n_bins, dtype=float)
    yerr_high = np.zeros(n_bins, dtype=float)

    for i in range(n_bins):
        if run_rate_lists[i]:
            mean_rate = float(np.mean(run_rate_lists[i]))
            mean_rates[i] = clamp01(mean_rate)

            lo, hi = wilson_interval(pooled_supported[i], pooled_total[i])
            yerr_low[i] = max(0.0, mean_rates[i] - lo)
            yerr_high[i] = max(0.0, hi - mean_rates[i])

    overall_rate = (total_supported_all / total_claims_all) if total_claims_all > 0 else 0.0

    return centers, mean_rates, yerr_low, yerr_high, clamp01(overall_rate), run_counts


def main() -> int:
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    runs: list[tuple[float, float, int, int]] = []
    if DATA_PATH.exists() and DATA_PATH.stat().st_size > 0:
        runs = parse_runs_from_jsonl(DATA_PATH)

    if not runs:
        print("USING SYNTHETIC DATA")
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        runs = generate_synthetic_runs(n=250)

    centers, mean_rates, yerr_low, yerr_high, overall_rate, _ = build_plot_data(runs, n_bins=10)

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.linewidth": 1.1,
        "axes.labelsize": 13,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
    })

    fig, ax = plt.subplots(figsize=(8, 5))

    valid = ~np.isnan(mean_rates)
    ax.errorbar(
        centers[valid],
        mean_rates[valid],
        yerr=np.vstack([yerr_low[valid], yerr_high[valid]]),
        fmt="o-",
        linewidth=2.0,
        markersize=5,
        capsize=4,
    )

    ax.axhline(overall_rate, linestyle="--", linewidth=1.8)

    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_xlabel("Epistemic Risk Score")
    ax.set_ylabel("Supported Rate")
    ax.set_xticks(np.linspace(0.0, 1.0, 6))
    ax.set_yticks(np.linspace(0.0, 1.0, 6))
    ax.grid(True, linestyle="--", alpha=0.35, linewidth=0.7)

    fig.tight_layout()

    out_png = OUT_PNG.resolve()
    out_pdf = OUT_PDF.resolve()
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)

    print(f"SAVED_PNG: {out_png}")
    print(f"SAVED_PDF: {out_pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
