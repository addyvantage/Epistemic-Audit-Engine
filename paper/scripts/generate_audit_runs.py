#!/usr/bin/env python3
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from pipeline.run_full_audit import AuditPipeline  # noqa: E402
from core.audit_run_logger import AuditRunLogger, normalize_mode  # noqa: E402

TARGET_BUCKETS = [700, 1200, 2000, 3500, 4800]
MAX_CHARS = 5000
DEFAULT_WEIGHTS = {
    "general": 0.25,
    "tech": 0.20,
    "finance": 0.20,
    "politics": 0.20,
    "medical": 0.15,
}

GENERIC_FILLER = [
    "Context note: this paragraph summarizes publicly available information and operational framing in neutral language for audit evaluation.",
    "Background note: the passage groups timeline, governance, and reporting details so the verifier can evaluate both factual and narrative claims.",
    "Method note: these statements are intentionally mixed to include verifiable facts and soft narrative language with varying evidence strength.",
    "Scope note: this text focuses on institutional history, location, structure, and reporting references without accusations or sensitive allegations.",
    "Review note: wording is descriptive and non-adversarial, designed to stress test claim extraction and evidence matching reliability.",
]

DOMAIN_FILLER = {
    "general": [
        "The organization publishes periodic updates that summarize programs, milestones, and administrative changes.",
        "Public-facing documents often combine formal facts with qualitative statements about community impact.",
    ],
    "tech": [
        "Developer documentation and product announcements may describe adoption trends with varying levels of quantitative backing.",
        "Technology roadmaps typically include both concrete release dates and broad narrative expectations.",
    ],
    "finance": [
        "Annual reports often distinguish audited values from forward-looking commentary.",
        "Investor communications may pair precise accounting figures with strategic narrative language.",
    ],
    "politics": [
        "Civic institutions often publish procedural calendars and implementation guidance before election cycles.",
        "Policy summaries commonly blend statutory details with broad statements about institutional goals.",
    ],
    "medical": [
        "Public health agencies often publish program milestones and trial administration updates in neutral language.",
        "Clinical operations reports can combine enrollment figures with qualitative statements about coordination quality.",
    ],
}


def parse_domain_weights(raw: str) -> Dict[str, float]:
    if not raw:
        return dict(DEFAULT_WEIGHTS)

    parsed: Dict[str, float] = {}
    for chunk in raw.split(","):
        token = chunk.strip()
        if not token or "=" not in token:
            continue
        key, value = token.split("=", 1)
        key_norm = key.strip().lower()
        if key_norm not in DEFAULT_WEIGHTS:
            continue
        try:
            parsed[key_norm] = max(0.0, float(value.strip()))
        except ValueError:
            continue

    if not parsed:
        return dict(DEFAULT_WEIGHTS)

    total = sum(parsed.values())
    if total <= 0:
        return dict(DEFAULT_WEIGHTS)
    return {k: v / total for k, v in parsed.items()}


def choose_weighted(rng: random.Random, weights: Dict[str, float]) -> str:
    items = sorted(weights.items(), key=lambda item: item[0])
    roll = rng.random()
    acc = 0.0
    for key, weight in items:
        acc += weight
        if roll <= acc:
            return key
    return items[-1][0]


def build_core_paragraphs(domain: str, rng: random.Random) -> List[str]:
    if domain == "tech":
        company = rng.choice(["Microsoft", "Intel", "NVIDIA", "Adobe", "Cisco"])
        founded_year = rng.choice([1975, 1968, 1993, 1982, 1984])
        hq = rng.choice(["Redmond, Washington", "Santa Clara, California", "San Jose, California"])
        parent = rng.choice(["a publicly listed independent company", "a business unit within a larger holding group"])
        report_year = rng.choice([2022, 2023, 2024])
        revenue = rng.choice(["211.9", "63.1", "52.9", "19.4"])
        return [
            f"{company} was founded in {founded_year}. {company} is headquartered in {hq}.",
            f"In organizational terms, {company} is structured as {parent}.",
            f"In {report_year}, {company} reported approximately {revenue} billion USD in annual revenue.",
            f"Industry observers often describe {company}'s ecosystem influence as broad, though this statement is partly qualitative.",
        ]

    if domain == "finance":
        institution = rng.choice(["Goldman Sachs", "JPMorgan Chase", "BlackRock", "Morgan Stanley"])
        founded_year = rng.choice([1869, 1799, 1988, 1935])
        hq = rng.choice(["New York City", "Chicago", "Boston"])
        relation = rng.choice(["publicly traded financial institution", "subsidiary within a diversified financial group"])
        report_year = rng.choice([2022, 2023, 2024])
        metric = rng.choice(["net revenue", "assets under management", "operating income"])
        value = rng.choice(["47.4", "10.0", "14.4", "6.2"])
        return [
            f"{institution} was established in {founded_year} and is headquartered in {hq}.",
            f"The institution operates as a {relation}.",
            f"In {report_year}, it reported {metric} near {value} billion USD according to public filings.",
            "Analysts frequently describe its market position as strong, which is a soft narrative claim that may have mixed evidence support.",
        ]

    if domain == "politics":
        body = rng.choice([
            "the national election commission",
            "the parliamentary budget office",
            "the civic data authority",
            "the public ethics commission",
        ])
        established = rng.choice([1992, 1998, 2004, 2010])
        city = rng.choice(["Washington, D.C.", "Ottawa", "Canberra", "Wellington"])
        relationship = rng.choice(["reports to the legislature", "operates under a ministry of civic affairs"])
        year = rng.choice([2020, 2022, 2024])
        number = rng.choice(["12", "18", "24", "30"])
        return [
            f"{body.title()} was established in {established} and is based in {city}.",
            f"It {relationship} under existing public-law procedures.",
            f"In {year}, the institution published oversight updates covering {number} regional implementation programs.",
            "Commentary often describes these reforms as confidence-building, which is qualitative and may remain uncertain.",
        ]

    if domain == "medical":
        institution = rng.choice([
            "the national vaccine research center",
            "the public clinical trials network",
            "the infectious disease surveillance office",
            "the biomedical standards institute",
        ])
        year = rng.choice([2001, 2006, 2012, 2016])
        hq = rng.choice(["Geneva", "London", "Atlanta", "Stockholm"])
        relation = rng.choice(["operates under a public health agency", "is coordinated by a national health ministry"])
        report_year = rng.choice([2021, 2022, 2023, 2024])
        participants = rng.choice(["240", "380", "520", "760"])
        return [
            f"{institution.title()} was launched in {year} and maintains headquarters in {hq}.",
            f"The institution {relation}.",
            f"In {report_year}, one phase II program reported enrollment of about {participants} participants across multiple sites.",
            "Stakeholders often describe coordination quality as improving, which is narrative language rather than a strict measurable endpoint.",
        ]

    organization = rng.choice([
        "the international climate data consortium",
        "the global education innovation forum",
        "the urban resilience partnership",
        "the digital public infrastructure alliance",
    ])
    founded = rng.choice([1999, 2005, 2011, 2018])
    hq = rng.choice(["Geneva", "Berlin", "Toronto", "Singapore"])
    relation = rng.choice(["is affiliated with a multilateral network", "operates as a program under a nonprofit federation"])
    year = rng.choice([2021, 2022, 2023, 2024])
    value = rng.choice(["120", "180", "240", "300"])
    return [
        f"{organization.title()} was founded in {founded} and is headquartered in {hq}.",
        f"It {relation}.",
        f"In {year}, the consortium announced support for roughly {value} projects in public documentation.",
        "Observers frequently characterize its policy impact as significant, a narrative claim that can remain uncertain.",
    ]


def target_length(base_paragraphs: List[str], target_chars: int, domain: str, rng: random.Random) -> str:
    target_chars = min(MAX_CHARS, max(250, int(target_chars)))
    fillers = list(DOMAIN_FILLER.get(domain, [])) + list(GENERIC_FILLER)
    working = list(base_paragraphs)

    text = "\n\n".join(working)
    while len(text) < target_chars:
        working.append(rng.choice(fillers))
        text = "\n\n".join(working)
        if len(working) > 200:
            break

    while len(text) > target_chars and len(working) > len(base_paragraphs):
        working.pop()
        text = "\n\n".join(working)

    if len(text) > target_chars:
        candidate = text[:target_chars]
        boundary = max(candidate.rfind(". "), candidate.rfind("\n"))
        if boundary > int(target_chars * 0.60):
            candidate = candidate[:boundary + 1]
        text = candidate.strip()

    return text[:MAX_CHARS]


def build_synthetic_sample(domain: str, target_chars: int, rng: random.Random) -> str:
    core = build_core_paragraphs(domain, rng)
    return target_length(core, target_chars, domain, rng)


def load_custom_testcases(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    output: List[Dict[str, str]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            print(f"[WARN] Skipping malformed custom testcase line {line_no}")
            continue
        text = str(obj.get("text", "")).strip()
        if not text:
            print(f"[WARN] Skipping custom testcase line {line_no} (missing text)")
            continue
        output.append(
            {
                "id": str(obj.get("id", f"custom-{line_no}")),
                "domain": str(obj.get("domain", "custom")),
                "mode": str(obj.get("mode", "")).strip(),
                "text": text,
            }
        )
    return output


def main() -> None:
    runs = int(os.getenv("EPI_SYNTH_RUNS", "500"))
    seed = int(os.getenv("EPI_SYNTH_SEED", "42"))
    mode_default = normalize_mode(os.getenv("EPI_SYNTH_MODE", "demo"))
    weights = parse_domain_weights(os.getenv("EPI_DOMAIN_WEIGHTS", ""))
    custom_path = ROOT / "paper" / "data" / "custom_testcases.jsonl"
    log_path = ROOT / "paper" / "data" / "audit_runs.jsonl"
    os.environ.setdefault("DEBUG_TIMINGS", "1")

    rng = random.Random(seed)
    logger = AuditRunLogger(log_path=log_path)
    pipeline = AuditPipeline()

    log_path.parent.mkdir(parents=True, exist_ok=True)

    synthetic_success = 0
    synthetic_failed = 0
    print(f"[INFO] Writing audit runs to: {log_path}")
    print(f"[INFO] Synthetic runs={runs}, seed={seed}, mode={mode_default}")
    print(f"[INFO] Domain weights={weights}")

    for idx in range(runs):
        domain = choose_weighted(rng, weights)
        target_chars = rng.choice(TARGET_BUCKETS)
        text = build_synthetic_sample(domain, target_chars, rng)
        mode = mode_default
        started = time.perf_counter()
        try:
            result = pipeline.run(text, mode=mode)
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            logger.log_run(
                input_text=text,
                mode=mode,
                result=result,
                extra_metadata={
                    "run_source": "synthetic",
                    "domain": domain,
                    "target_chars": target_chars,
                    "synthetic_index": idx,
                    "request_wall_ms": elapsed_ms,
                },
            )
            synthetic_success += 1
        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            logger.log_run(
                input_text=text,
                mode=mode,
                result={"status_code": 500, "detail": str(exc)},
                extra_metadata={
                    "run_source": "synthetic",
                    "domain": domain,
                    "target_chars": target_chars,
                    "synthetic_index": idx,
                    "request_wall_ms": elapsed_ms,
                    "error": "pipeline_exception",
                },
            )
            synthetic_failed += 1

    custom_cases = load_custom_testcases(custom_path)
    custom_success = 0
    custom_failed = 0
    if custom_cases:
        print(f"[INFO] Running {len(custom_cases)} custom testcases from {custom_path}")
    for case in custom_cases:
        text = case["text"][:MAX_CHARS]
        mode = normalize_mode(case.get("mode") or mode_default)
        domain = (case.get("domain") or "custom").strip().lower() or "custom"
        started = time.perf_counter()
        try:
            result = pipeline.run(text, mode=mode)
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            logger.log_run(
                input_text=text,
                mode=mode,
                result=result,
                extra_metadata={
                    "run_source": "custom_testcase",
                    "domain": domain,
                    "custom_id": case.get("id"),
                    "request_wall_ms": elapsed_ms,
                },
            )
            custom_success += 1
        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            logger.log_run(
                input_text=text,
                mode=mode,
                result={"status_code": 500, "detail": str(exc)},
                extra_metadata={
                    "run_source": "custom_testcase",
                    "domain": domain,
                    "custom_id": case.get("id"),
                    "request_wall_ms": elapsed_ms,
                    "error": "pipeline_exception",
                },
            )
            custom_failed += 1

    print("[DONE] Synthetic generation complete.")
    print(f"[DONE] synthetic_success={synthetic_success} synthetic_failed={synthetic_failed}")
    print(f"[DONE] custom_success={custom_success} custom_failed={custom_failed}")
    print(f"[DONE] dataset_path={log_path}")


if __name__ == "__main__":
    main()
