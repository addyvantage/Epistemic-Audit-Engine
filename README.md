# Epistemic Audit Engine
Claim-level reliability auditing for LLM-generated text with evidence grounding and epistemic risk scoring.

---

## Why this exists
LLM outputs can be fluent and confident while still containing unsupported or contradictory claims. In practice, reviewers need more than a single “good/bad” score: they need to inspect **which claims are grounded**, **which are uncertain**, and **why**.

Epistemic Audit Engine is built for that workflow.

- It audits generated text at the **claim level**.
- It links each claim to available evidence.
- It aggregates claim outcomes into an overall risk signal.

This is an audit aid, not an oracle.

---

## What it does
For each audit request, the backend pipeline runs:

1. **Claim Extraction**: split text into atomic claims.
2. **Entity Linking**: resolve subjects/objects to canonical entities where possible.
3. **Evidence Retrieval**: gather structured and narrative evidence.
4. **Claim Verification**: assign epistemic verdicts per claim.
5. **Risk Aggregation**: compute document-level risk outputs.

---

## What you get
After running the research pipeline you get two artifact classes:

1. **Append-only run dataset**
- `paper/data/audit_runs.jsonl`

2. **Figure set (14 analyses, each PNG + PDF)**
- `figures/fig01_...` through `figures/fig14_...`

---

## System architecture
```text
[Browser UI: /audit]
        |
        v
[Next.js frontend]
  - /api/audit  (proxy)
  - /api/health (proxy)
        |
        v
[FastAPI backend: backend/app.py]
  - POST /audit
  - GET  /health
        |
        v
[Verification pipeline]
  - Claim Extraction
  - Entity Linking
  - Evidence Retrieval
  - Claim Verification
  - Risk Aggregation
        |
        v
[Risk outputs]
  - overall_risk
  - hallucination_score
  - summary
  - claims
```

---

## Key features
- Claim-level auditing instead of document-only scoring.
- Structured evidence grounding via Wikidata properties/entities.
- Narrative passage retrieval via Wikipedia.
- Verdict classes:
  - `SUPPORTED`
  - `PARTIALLY_SUPPORTED`
  - `REFUTED`
  - `UNCERTAIN`
  - `INSUFFICIENT_EVIDENCE`
- Always-on backend logging for every `/audit` call to JSONL.
- Synthetic dataset generation with deterministic seed controls.
- End-to-end figure pipeline generating 14 research figures in PNG/PDF.
- Root one-command research runner: `scripts/run_research.sh`.

---

## API

### `GET /health`
Backend health endpoint.

```bash
curl http://127.0.0.1:8000/health
```

Expected shape:

```json
{
  "status": "ok",
  "pipeline_ready": true,
  "pid": 12345,
  "uptime_s": 12.34
}
```

### `POST /audit`
Audit a text payload.

```bash
curl -X POST http://127.0.0.1:8000/audit \
  -H "Content-Type: application/json" \
  -d '{"text":"Microsoft was founded in 1975.","mode":"demo"}'
```

High-level response shape:

```json
{
  "overall_risk": "LOW | MEDIUM | HIGH",
  "hallucination_score": 0.0,
  "summary": {},
  "claims": []
}
```

### Logging behavior
Every `/audit` request is logged server-side (backend) to:

- `paper/data/audit_runs.jsonl`

Logging is append-only and failure-tolerant (logging errors do not break `/audit`).

---

## Quickstart (Local) 🚀

### Prerequisites
- Python 3.9+
- Node.js 18+

### Backend setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Run backend:

```bash
.venv/bin/python -m uvicorn app:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

### Frontend setup
```bash
cd frontend
npm install
npm run dev
```

Open:
- Audit UI: `http://localhost:3000/audit`

### Full stack command
```bash
(for p in 3000 3001 8000; do lsof -ti :$p | xargs -r kill -9; done; pkill -f "next dev" || true; pkill -f "uvicorn" || true; rm -f frontend/.next/dev/lock; sleep 1; (.venv/bin/python -m uvicorn app:app --app-dir backend --reload --host 127.0.0.1 --port 8000) & (cd frontend && npm run dev))
```

---

## Reproducible Research Run (531 synthetic audits)
This is the primary one-command workflow for dataset + figures:

```bash
bash scripts/run_research.sh
```

### Defaults (if not set)
The root runner sets:
- `EPI_SYNTH_RUNS=531`
- `EPI_SYNTH_SEED=42`
- `EPI_SYNTH_MODE=demo`

### Behavior
`bash scripts/run_research.sh` will:
1. Verify required research scripts (`verify_research_setup.py`).
2. Generate synthetic runs (plus optional custom testcases if present).
3. Append new records to `paper/data/audit_runs.jsonl`.
4. Regenerate the 14 figures in `figures/` as PNG + PDF.
5. Print dataset path, figures path, JSONL line count, and sorted figure filenames.

### Expected console output (example shape)
```text
Research setup verification passed.
Scripts checked: 2
Logging directory ready: .../paper/data
...
[DONE] dataset_path=.../paper/data/audit_runs.jsonl
DATASET: .../paper/data/audit_runs.jsonl
FIGURES_DIR: .../figures
GENERATED_FILES:
fig01_claim_verdict_distribution.pdf
fig01_claim_verdict_distribution.png
...
fig14_mode_comparison_or_top_entities.pdf
fig14_mode_comparison_or_top_entities.png
dataset path: .../paper/data/audit_runs.jsonl
figures path: .../figures
jsonl lines: <N>
figure files (sorted):
...
```

### Override defaults
Examples:

```bash
EPI_SYNTH_RUNS=1000 bash scripts/run_research.sh
```

```bash
EPI_SYNTH_RUNS=200 EPI_SYNTH_SEED=7 EPI_SYNTH_MODE=research bash scripts/run_research.sh
```

---

## Data & outputs

### JSONL dataset path
- `paper/data/audit_runs.jsonl`

### JSONL record fields
Each line is one JSON object. Core keys include:
- `run_id`
- `ts_iso`
- `mode`
- `input_text`
- `input_chars`
- `input_sha256`
- `pipeline_version`
- `result` (full backend result payload)
- `overall_risk`
- `hallucination_score`
- `summary`
- `timings_ms` (from `result.debug_timings_ms` if available, else `null`)

Additional metadata may be present when generated via scripts:
- `request_wall_ms`
- `domain`
- `run_source`
- `target_chars`
- `synthetic_index`
- `custom_id`

### Figure outputs
Output directory:
- `figures/`

Expected files (each as `.png` and `.pdf`):
1. `fig01_claim_verdict_distribution`
2. `fig02_risk_score_distribution`
3. `fig03_risk_tier_distribution`
4. `fig04_score_vs_supported_rate`
5. `fig05_score_vs_refuted_rate`
6. `fig06_calibration_bad_outcome_rate`
7. `fig07_evidence_source_usage_rates`
8. `fig08_risk_tier_vs_supported_rate`
9. `fig09_claims_per_document_distribution`
10. `fig10_claim_evidence_coverage`
11. `fig11_claim_contradiction_rate`
12. `fig12_insufficient_uncertain_split`
13. `fig13_runtime_breakdown_or_latency_proxy`
14. `fig14_mode_comparison_or_top_entities`

---

## Input UX constraints (frontend)
Current input behavior in the audit UI:
- `Enter` submits.
- `Shift+Enter` inserts newline.
- Hard 5000-character cap (typing/paste/drop clamped).
- Inline toast feedback on overflow.
- Keyboard and button submission share one code path.

---

## Troubleshooting

### 1) `matplotlib` missing in `.venv`
`paper/scripts/run_research_pipeline.sh` attempts a matplotlib check and falls back to `python3` for figure generation if needed.

If your system Python lacks matplotlib, install it in either environment:

```bash
.venv/bin/python -m pip install matplotlib
```

or

```bash
python3 -m pip install matplotlib
```

### 2) PyTorch / NLI warnings
You may see warnings such as:
- `PyTorch was not found...`
- `Failed to load NLI model...`

Impact: pipeline still runs, but NLI-dependent checks may be reduced, which can increase uncertain/insufficient outcomes.

### 3) Port conflicts
If 3000/3001/8000 are occupied, use the full stack reset command from Quickstart (kills conflicting processes and clears Next lock file).

### 4) Missing scripts in research run
Run:

```bash
python3 paper/scripts/verify_research_setup.py
```

It reports missing files and exits non-zero when setup is incomplete.

---

## Repository layout
```text
.
├── backend/
│   ├── app.py
│   ├── core/
│   │   └── audit_run_logger.py
│   └── pipeline/
├── frontend/
│   ├── app/
│   │   ├── audit/page.tsx
│   │   └── api/
│   │       ├── audit/route.ts
│   │       └── health/route.ts
│   └── components/
├── paper/
│   ├── data/
│   │   └── audit_runs.jsonl
│   └── scripts/
│       ├── generate_audit_runs.py
│       ├── make_all_figures.py
│       ├── run_research_pipeline.sh
│       └── verify_research_setup.py
├── scripts/
│   └── run_research.sh
├── figures/
└── README.md
```

---

## Limitations
- Verdict quality depends on evidence availability and coverage.
- Long-tail entities and niche claims may remain unresolved.
- Narrative claims can remain uncertain without strong textual evidence.
- Synthetic generation is template-based and not a substitute for manually curated benchmark datasets.

---

## Roadmap / Future work
- Add richer custom testcase packs for domain-specific audits.
- Expand evidence-source analytics in figure pipeline.
- Improve uncertainty diagnostics and reporting slices.
- Add lightweight CI checks for research scripts and figure artifacts.

---

## License
MIT License.
