#!/usr/bin/env python3
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT / "paper" / "data" / "audit_runs.jsonl"
FIGURES_DIR = ROOT / "figures"
VERDICTS = [
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "REFUTED",
    "UNCERTAIN",
    "INSUFFICIENT_EVIDENCE",
]
EVIDENCE_SOURCES = ["wikidata", "wikipedia", "primary_document", "grokipedia"]


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    records: List[Dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                records.append(obj)
        except json.JSONDecodeError:
            continue
    return records


def get_claims(record: Dict[str, Any]) -> List[Dict[str, Any]]:
    result = record.get("result", {})
    if not isinstance(result, dict):
        return []
    claims = result.get("claims", [])
    if not isinstance(claims, list):
        return []
    return [claim for claim in claims if isinstance(claim, dict)]


def verdict_for_claim(claim: Dict[str, Any]) -> str:
    verification = claim.get("verification", {})
    if not isinstance(verification, dict):
        return "UNCERTAIN"
    verdict = str(verification.get("verdict", "UNCERTAIN")).strip().upper()
    if verdict == "SUPPORTED_WEAK":
        return "SUPPORTED"
    return verdict


def claim_has_source(claim: Dict[str, Any], source: str) -> bool:
    evidence = claim.get("evidence", {})
    if not isinstance(evidence, dict):
        return False
    items = evidence.get(source)
    return isinstance(items, list) and len(items) > 0


def claim_has_any_evidence(claim: Dict[str, Any]) -> bool:
    return any(claim_has_source(claim, source) for source in EVIDENCE_SOURCES)


def claim_has_contradiction(claim: Dict[str, Any]) -> bool:
    verification = claim.get("verification", {})
    if isinstance(verification, dict):
        contradicted = verification.get("contradicted_by")
        if isinstance(contradicted, list) and len(contradicted) > 0:
            return True
    return verdict_for_claim(claim) == "REFUTED"


def risk_tier(score: float) -> str:
    if score < 0.33:
        return "LOW"
    if score < 0.66:
        return "MEDIUM"
    return "HIGH"


def mean(values: Iterable[float]) -> float:
    values_list = [float(v) for v in values]
    if not values_list:
        return 0.0
    return sum(values_list) / len(values_list)


def binned_mean(xs: List[float], ys: List[float], edges: List[float]) -> Tuple[List[float], List[float]]:
    centers: List[float] = []
    means: List[float] = []
    for idx in range(len(edges) - 1):
        left = edges[idx]
        right = edges[idx + 1]
        bucket: List[float] = []
        for x, y in zip(xs, ys):
            if idx == len(edges) - 2:
                in_bucket = left <= x <= right
            else:
                in_bucket = left <= x < right
            if in_bucket:
                bucket.append(y)
        centers.append((left + right) / 2.0)
        means.append(mean(bucket) if bucket else 0.0)
    return centers, means


def setup_axes(ax: plt.Axes, xlabel: str, ylabel: str) -> None:
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.tick_params(axis="both", labelsize=10)
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def save_figure(fig: plt.Figure, stem: str, generated: List[str]) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    png_path = FIGURES_DIR / f"{stem}.png"
    pdf_path = FIGURES_DIR / f"{stem}.pdf"
    fig.tight_layout()
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white", transparent=False)
    fig.savefig(pdf_path, bbox_inches="tight", facecolor="white", transparent=False)
    plt.close(fig)
    generated.append(png_path.name)
    generated.append(pdf_path.name)


def aggregate(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    scores: List[float] = []
    modes: List[str] = []
    supported_rates: List[float] = []
    refuted_rates: List[float] = []
    bad_rates: List[float] = []
    claims_per_doc: List[int] = []
    domains: List[str] = []
    run_bad_rates_by_domain: List[Tuple[str, float]] = []
    timings: List[Dict[str, float]] = []
    request_wall_ms: List[float] = []
    verdict_counter: Counter = Counter()
    source_claim_counter: Counter = Counter()
    entity_counter: Counter = Counter()
    total_claims = 0
    claims_with_any_evidence = 0
    claims_with_contradiction = 0

    for idx, record in enumerate(records):
        mode = str(record.get("mode", "research")).strip().lower()
        if mode not in {"demo", "research"}:
            mode = "research"
        modes.append(mode)

        score_value = record.get("hallucination_score")
        score = float(score_value) if is_number(score_value) else None
        if score is not None:
            score = max(0.0, min(1.0, score))
            scores.append(score)
        else:
            scores.append(0.0)

        claims = get_claims(record)
        n_claims = len(claims)
        claims_per_doc.append(n_claims)
        total_claims += n_claims

        local_counter: Counter = Counter()
        local_supported = 0
        local_refuted = 0
        local_uncertain = 0
        local_insufficient = 0

        for claim in claims:
            verdict = verdict_for_claim(claim)
            local_counter[verdict] += 1
            verdict_counter[verdict] += 1

            if verdict == "SUPPORTED":
                local_supported += 1
            elif verdict == "REFUTED":
                local_refuted += 1
            elif verdict == "UNCERTAIN":
                local_uncertain += 1
            elif verdict == "INSUFFICIENT_EVIDENCE":
                local_insufficient += 1

            for source in EVIDENCE_SOURCES:
                if claim_has_source(claim, source):
                    source_claim_counter[source] += 1

            if claim_has_any_evidence(claim):
                claims_with_any_evidence += 1
            if claim_has_contradiction(claim):
                claims_with_contradiction += 1

            subject_entity = claim.get("subject_entity", {})
            if isinstance(subject_entity, dict):
                canonical = str(subject_entity.get("canonical_name", "")).strip()
                if canonical:
                    entity_counter[canonical] += 1
                else:
                    subj_text = str(claim.get("subject", "")).strip()
                    if subj_text:
                        entity_counter[subj_text] += 1

        if n_claims > 0:
            supported_rates.append(local_supported / n_claims)
            refuted_rates.append(local_refuted / n_claims)
            bad_rate = (local_refuted + local_uncertain + local_insufficient) / n_claims
            bad_rates.append(bad_rate)
        else:
            supported_rates.append(0.0)
            refuted_rates.append(0.0)
            bad_rates.append(0.0)

        raw_domain = record.get("domain")
        if not raw_domain:
            generator_meta = record.get("generator_meta", {})
            if isinstance(generator_meta, dict):
                raw_domain = generator_meta.get("domain")
        domain = str(raw_domain).strip().lower() if raw_domain else ""
        if domain:
            domains.append(domain)
            run_bad_rates_by_domain.append((domain, bad_rates[-1]))

        timing_obj = record.get("timings_ms")
        if isinstance(timing_obj, dict):
            numeric_timing = {k: float(v) for k, v in timing_obj.items() if is_number(v)}
            if numeric_timing:
                timings.append(numeric_timing)

        wall_ms = record.get("request_wall_ms")
        if is_number(wall_ms):
            request_wall_ms.append(float(wall_ms))

    return {
        "scores": scores,
        "modes": modes,
        "supported_rates": supported_rates,
        "refuted_rates": refuted_rates,
        "bad_rates": bad_rates,
        "claims_per_doc": claims_per_doc,
        "domains": domains,
        "run_bad_rates_by_domain": run_bad_rates_by_domain,
        "timings": timings,
        "request_wall_ms": request_wall_ms,
        "verdict_counter": verdict_counter,
        "source_claim_counter": source_claim_counter,
        "entity_counter": entity_counter,
        "total_claims": total_claims,
        "claims_with_any_evidence": claims_with_any_evidence,
        "claims_with_contradiction": claims_with_contradiction,
    }


def main() -> None:
    plt.rcParams["font.family"] = "DejaVu Sans"
    records = load_jsonl(DATASET_PATH)
    data = aggregate(records)
    generated: List[str] = []

    # 1) Claim verdict distribution
    fig, ax = plt.subplots(figsize=(8, 5), facecolor="white")
    verdict_counts = [data["verdict_counter"].get(v, 0) for v in VERDICTS]
    bars = ax.bar(VERDICTS, verdict_counts, edgecolor="black", linewidth=0.8)
    for bar, value in zip(bars, verdict_counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1, str(value), ha="center", va="bottom", fontsize=9)
    setup_axes(ax, "Claim Verdict", "Count")
    save_figure(fig, "fig01_claim_verdict_distribution", generated)

    # 2) Risk score distribution
    fig, ax = plt.subplots(figsize=(8, 5), facecolor="white")
    ax.hist(data["scores"], bins=10, edgecolor="black", linewidth=0.8)
    ax.set_xlim(0, 1)
    setup_axes(ax, "Epistemic Risk Score", "Frequency")
    save_figure(fig, "fig02_risk_score_distribution", generated)

    # 3) Risk tier distribution
    fig, ax = plt.subplots(figsize=(8, 5), facecolor="white")
    tier_counts = Counter(risk_tier(score) for score in data["scores"])
    tiers = ["LOW", "MEDIUM", "HIGH"]
    values = [tier_counts.get(tier, 0) for tier in tiers]
    bars = ax.bar(tiers, values, edgecolor="black", linewidth=0.8)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1, str(value), ha="center", va="bottom", fontsize=9)
    setup_axes(ax, "Risk Tier", "Number of Runs")
    save_figure(fig, "fig03_risk_tier_distribution", generated)

    # 4) Score vs supported rate
    fig, ax = plt.subplots(figsize=(8, 5), facecolor="white")
    edges = [i / 10 for i in range(11)]
    centers, means = binned_mean(data["scores"], data["supported_rates"], edges)
    ax.plot(centers, means, marker="o", linewidth=1.6)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    setup_axes(ax, "Hallucination Score (Bin Center)", "Supported Claim Rate")
    save_figure(fig, "fig04_score_vs_supported_rate", generated)

    # 5) Score vs refuted rate
    fig, ax = plt.subplots(figsize=(8, 5), facecolor="white")
    centers, means = binned_mean(data["scores"], data["refuted_rates"], edges)
    ax.plot(centers, means, marker="o", linewidth=1.6)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    setup_axes(ax, "Hallucination Score (Bin Center)", "Refuted Claim Rate")
    save_figure(fig, "fig05_score_vs_refuted_rate", generated)

    # 6) Calibration-style bad outcome rate
    fig, ax = plt.subplots(figsize=(8, 5), facecolor="white")
    centers, means = binned_mean(data["scores"], data["bad_rates"], edges)
    ax.plot(centers, means, marker="o", linewidth=1.6, label="Observed Bad Outcome Rate")
    ax.plot([0, 1], [0, 1], linestyle="--", linewidth=1.0, label="Ideal y=x")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    setup_axes(ax, "Model Score", "Bad Outcome Rate (Refuted+Uncertain+Insufficient)")
    ax.legend(fontsize=9)
    save_figure(fig, "fig06_calibration_bad_outcome_rate", generated)

    # 7) Evidence source usage rates
    fig, ax = plt.subplots(figsize=(8, 5), facecolor="white")
    total_claims = max(1, data["total_claims"])
    source_rates = [
        (data["source_claim_counter"].get(source, 0) / total_claims) * 100.0 for source in EVIDENCE_SOURCES
    ]
    bars = ax.bar(EVIDENCE_SOURCES, source_rates, edgecolor="black", linewidth=0.8)
    for bar, value in zip(bars, source_rates):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2, f"{value:.1f}%", ha="center", va="bottom", fontsize=9)
    setup_axes(ax, "Evidence Source", "Claims Using Source (%)")
    save_figure(fig, "fig07_evidence_source_usage_rates", generated)

    # 8) Risk tier vs supported rate
    fig, ax = plt.subplots(figsize=(8, 5), facecolor="white")
    tier_to_rates: Dict[str, List[float]] = defaultdict(list)
    for score, rate in zip(data["scores"], data["supported_rates"]):
        tier_to_rates[risk_tier(score)].append(rate)
    tier_supported = [mean(tier_to_rates[tier]) for tier in ["LOW", "MEDIUM", "HIGH"]]
    bars = ax.bar(["LOW", "MEDIUM", "HIGH"], tier_supported, edgecolor="black", linewidth=0.8)
    for bar, value in zip(bars, tier_supported):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01, f"{value:.2f}", ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, 1)
    setup_axes(ax, "Risk Tier", "Average Supported Claim Rate")
    save_figure(fig, "fig08_risk_tier_vs_supported_rate", generated)

    # 9) Distribution of claims per document
    fig, ax = plt.subplots(figsize=(8, 5), facecolor="white")
    bins = min(12, max(4, len(set(data["claims_per_doc"])) or 4))
    ax.hist(data["claims_per_doc"], bins=bins, edgecolor="black", linewidth=0.8)
    setup_axes(ax, "Claims per Run", "Frequency")
    save_figure(fig, "fig09_claims_per_document_distribution", generated)

    # 10) Coverage with any evidence
    fig, ax = plt.subplots(figsize=(8, 5), facecolor="white")
    covered = data["claims_with_any_evidence"]
    uncovered = max(0, data["total_claims"] - covered)
    coverage_values = [covered, uncovered]
    labels = ["With Evidence", "Without Evidence"]
    bars = ax.bar(labels, coverage_values, edgecolor="black", linewidth=0.8)
    for bar, value in zip(bars, coverage_values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1, str(value), ha="center", va="bottom", fontsize=9)
    setup_axes(ax, "Coverage Category", "Claim Count")
    save_figure(fig, "fig10_claim_evidence_coverage", generated)

    # 11) Claims with contradictions
    fig, ax = plt.subplots(figsize=(8, 5), facecolor="white")
    contradicted = data["claims_with_contradiction"]
    not_contradicted = max(0, data["total_claims"] - contradicted)
    bars = ax.bar(["Contradicted", "Not Contradicted"], [contradicted, not_contradicted], edgecolor="black", linewidth=0.8)
    for bar, value in zip(bars, [contradicted, not_contradicted]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1, str(value), ha="center", va="bottom", fontsize=9)
    setup_axes(ax, "Contradiction Status", "Claim Count")
    save_figure(fig, "fig11_claim_contradiction_rate", generated)

    # 12) Insufficient/uncertain rate split
    fig, ax = plt.subplots(figsize=(8, 5), facecolor="white")
    group_labels: List[str] = []
    group_values: List[float] = []
    by_domain: Dict[str, List[float]] = defaultdict(list)
    for domain, rate in data["run_bad_rates_by_domain"]:
        by_domain[domain].append(rate)

    if len(by_domain) >= 2:
        for domain in sorted(by_domain.keys()):
            group_labels.append(domain)
            group_values.append(mean(by_domain[domain]))
        xlabel = "Domain"
    else:
        quartile_buckets: Dict[str, List[float]] = defaultdict(list)
        total_runs = len(data["bad_rates"])
        for idx, rate in enumerate(data["bad_rates"]):
            quartile_idx = int((idx * 4) / max(1, total_runs))
            quartile_idx = min(3, quartile_idx)
            quartile_buckets[f"Q{quartile_idx + 1}"].append(rate)
        for label in ["Q1", "Q2", "Q3", "Q4"]:
            group_labels.append(label)
            group_values.append(mean(quartile_buckets.get(label, [])))
        xlabel = "Run Index Quartile"

    bars = ax.bar(group_labels, group_values, edgecolor="black", linewidth=0.8)
    for bar, value in zip(bars, group_values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01, f"{value:.2f}", ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, 1)
    setup_axes(ax, xlabel, "Insufficient/Uncertain Rate")
    save_figure(fig, "fig12_insufficient_uncertain_split", generated)

    # 13) Runtime timings breakdown or latency proxy
    fig, ax = plt.subplots(figsize=(8, 5), facecolor="white")
    if data["timings"]:
        phases = ["extract", "link", "retrieve", "verify", "aggregate", "total"]
        phase_means = []
        for phase in phases:
            values = [timing.get(phase) for timing in data["timings"] if is_number(timing.get(phase))]
            phase_means.append(mean(values))
        bars = ax.bar(phases, phase_means, edgecolor="black", linewidth=0.8)
        for bar, value in zip(bars, phase_means):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, f"{value:.1f}", ha="center", va="bottom", fontsize=9)
        setup_axes(ax, "Pipeline Phase", "Average Runtime (ms)")
    else:
        latencies = data["request_wall_ms"]
        if latencies:
            metrics = {
                "mean": mean(latencies),
                "p50": statistics.median(latencies),
                "p90": sorted(latencies)[int(0.9 * (len(latencies) - 1))],
            }
        else:
            metrics = {"mean": 0.0, "p50": 0.0, "p90": 0.0}
        bars = ax.bar(list(metrics.keys()), list(metrics.values()), edgecolor="black", linewidth=0.8)
        for bar, value in zip(bars, metrics.values()):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, f"{value:.1f}", ha="center", va="bottom", fontsize=9)
        setup_axes(ax, "Latency Proxy Metric", "Latency (ms)")
    save_figure(fig, "fig13_runtime_breakdown_or_latency_proxy", generated)

    # 14) Mode comparison if both modes exist, otherwise top entities
    fig, ax = plt.subplots(figsize=(8, 5), facecolor="white")
    scores_by_mode: Dict[str, List[float]] = defaultdict(list)
    for mode, score in zip(data["modes"], data["scores"]):
        scores_by_mode[mode].append(score)

    if scores_by_mode.get("demo") and scores_by_mode.get("research"):
        ax.hist(scores_by_mode["demo"], bins=10, alpha=0.6, edgecolor="black", linewidth=0.8, label="demo")
        ax.hist(scores_by_mode["research"], bins=10, alpha=0.6, edgecolor="black", linewidth=0.8, label="research")
        ax.set_xlim(0, 1)
        setup_axes(ax, "Hallucination Score", "Frequency")
        ax.legend(fontsize=9)
    else:
        top_entities = data["entity_counter"].most_common(10)
        if not top_entities:
            top_entities = [("No entities", 0)]
        labels = [item[0] for item in top_entities]
        values = [item[1] for item in top_entities]
        bars = ax.bar(labels, values, edgecolor="black", linewidth=0.8)
        for tick in ax.get_xticklabels():
            tick.set_rotation(35)
            tick.set_ha("right")
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1, str(value), ha="center", va="bottom", fontsize=8)
        setup_axes(ax, "Entity", "Frequency")
    save_figure(fig, "fig14_mode_comparison_or_top_entities", generated)

    print(f"DATASET: {DATASET_PATH}")
    print(f"FIGURES_DIR: {FIGURES_DIR}")
    print("GENERATED_FILES:")
    for filename in sorted(generated):
        print(filename)


if __name__ == "__main__":
    main()
