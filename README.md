# Epistemic Audit Engine

## Overview
Epistemic Audit Engine is a claim-level reliability auditing system for model-generated text. It addresses a practical LLM reliability problem: fluent responses can contain unsupported, uncertain, or contradicted statements that are hard to detect at document level.

Instead of scoring text as a single unit, the system decomposes outputs into atomic epistemic claims, verifies them against retrieved evidence, and returns structured verdicts plus an aggregate hallucination-risk estimate.

## Motivation
As LLMs are used in research, education, and analysis workflows, reliability failures are often epistemic rather than stylistic: claims may be plausible but weakly grounded. A useful auditor therefore needs to evaluate claims individually, expose evidence provenance, and quantify residual uncertainty.

This project is designed for that use case: transparent claim verification, contradiction detection, and risk-aware review of generated text.

## System Architecture
The system uses a web interface for audit orchestration and a Python verification pipeline for claim grounding.

- **Frontend (Next.js + React):** audit interface, claim selection, source highlighting, evidence inspection, mode switching.
- **Backend (FastAPI):** `/audit` and `/health` endpoints; orchestrates extraction, linking, retrieval, verification, and aggregation.
- **Retrieval layer:** narrative evidence retrieval plus structured evidence retrieval.
- **Knowledge graph grounding:** Wikidata entity/property evidence for canonical and relational checks.
- **Verdict + risk aggregation:** per-claim verdicts are aggregated into overall epistemic risk outputs.

```text
[User Text]
    |
    v
[Next.js Audit UI]
    |
    v
[/api/audit proxy]
    |
    v
[FastAPI /audit]
    |
    v
[Pipeline]
  1) Claim Extraction
  2) Entity Linking
  3) Evidence Retrieval (Wikidata + narrative sources)
  4) Claim Verification
  5) Hallucination Detection + Risk Aggregation
    |
    v
{ overall_risk, hallucination_score, summary, claims }
```

## Audit Workflow
1. **Input text** is submitted from the audit interface.
2. **Claim decomposition** converts text into atomic claims.
3. **Entity linking** resolves subjects/objects to canonical entities when possible.
4. **Evidence retrieval** collects structured and narrative evidence.
5. **Claim verification** evaluates support/contradiction using alignment signals.
6. **Verdict classification** assigns structured outcomes per claim.
7. **Risk scoring** aggregates claim outcomes into document-level risk.

## Input Interface (UX)
The input layer now enforces deterministic submission and strict length control:

- **Enter** submits the audit.
- **Shift+Enter** inserts a newline.
- **Hard 5000-character limit** is enforced for typing, paste, and drop.
- **Inline toast feedback** appears when extra text is rejected.
- **Unified submit path**: keyboard submit and button submit use the same validation flow.
- **Character counter never exceeds** `5000 / 5000`.

## Key Features
- Claim-level decomposition of generated text.
- Retrieval-based claim verification.
- Predicate-aware contradiction detection.
- Structured epistemic verdict assignment.
- Hallucination risk score aggregation.
- UI safeguards for input validity and length constraints.
- Demo mode and Research mode with different verification budgets.

## Running Locally

### 1. Backend Only
```bash
cd backend
source ../.venv/bin/activate
uvicorn app:app --reload --port 8000
```

### 2. Frontend Only
```bash
cd frontend
npm install
npm run dev
```

### 3. Run Full Stack (Recommended)
```bash
(for p in 3000 3001 8000; do lsof -ti :$p | xargs -r kill -9; done; pkill -f "next dev" || true; pkill -f "uvicorn" || true; pkill -f "StatReload" || true; rm -f frontend/.next/dev/lock; sleep 1; (.venv/bin/python -m uvicorn app:app --app-dir backend --reload --host 127.0.0.1 --port 8000) & (cd frontend && npm run dev))
```

Open [http://localhost:3000/audit](http://localhost:3000/audit)

## Demo Mode vs Research Mode
- **Demo mode:** uses a faster verification budget for interactive auditing.
- **Research mode:** uses deeper verification settings for broader evidence coverage.

Both modes preserve the same top-level `/audit` response contract.

## Tech Stack
- Next.js (App Router)
- React
- Tailwind CSS
- FastAPI
- Python
- Claim extraction / linking / retrieval / verification pipeline
- Wikidata grounding for structured evidence checks

## Limitations
- Knowledge graph coverage is incomplete for long-tail entities and properties.
- Narrative-only claims may remain difficult to verify with high confidence.
- Non-resolvable entities can reduce verification depth.
- Numeric financial claims can remain uncertain when exact values are unavailable in retrieved evidence.

## Future Work
- Multi-document audit workflows.
- Domain-specific claim type extensions.
- Expanded KG property coverage and grounding heuristics.

## License
MIT License. See [LICENSE](./LICENSE) for details.
