# Epistemic Audit Engine

Claim-level reliability auditing for LLM outputs using retrieval, knowledge-graph grounding, and epistemic risk scoring.

## Screenshot

> Placeholder: add an audit workspace screenshot here (for example, `/docs/images/audit-ui.png`).

---

## Table of Contents

- [What It Does](#what-it-does)
- [Why It Exists](#why-it-exists)
- [System Architecture](#system-architecture)
- [Evidence Sources](#evidence-sources)
- [Verdicts \\& Risk Outputs](#verdicts--risk-outputs)
- [UX / Input Rules](#ux--input-rules)
- [Running Locally](#running-locally)
  - [Backend Only](#backend-only)
  - [Frontend Only](#frontend-only)
  - [Run Full Stack (Single Command)](#run-full-stack-single-command)
  - [Health Check](#health-check)
- [Example Usage](#example-usage)
- [Repository Layout](#repository-layout)
- [Development Notes](#development-notes)
- [Limitations](#limitations)
- [Roadmap](#roadmap)
- [License](#license)

---

## What It Does

Epistemic Audit Engine evaluates generated text at the **claim level**.

For each input passage, it:

1. extracts atomic claims,
2. links entities to canonical identifiers,
3. retrieves evidence from structured and narrative sources,
4. assigns claim verdicts,
5. aggregates results into an epistemic risk summary.

The backend API returns this stable top-level shape:

```json
{
  "overall_risk": "LOW | MEDIUM | HIGH",
  "hallucination_score": 0.0,
  "summary": {},
  "claims": []
}
```

---

## Why It Exists

LLM outputs can be fluent while still containing unsupported or contradictory statements.

This project is built for **epistemic auditing**, not answer generation. It helps reviewers inspect what is supported, what is uncertain, and what is contradicted by available evidence.

It is an audit aid, not an oracle.

---

## System Architecture

The application uses a Next.js frontend with API proxy routes and a FastAPI backend pipeline.

```text
[Browser UI: /audit]
        |
        v
[Next.js App Router]
  - /api/health  ---> proxies to backend /health
  - /api/audit   ---> proxies to backend /audit
        |
        v
[FastAPI: backend/app.py]
  - GET  /health
  - POST /audit
        |
        v
[Verification Pipeline]
  1) Claim Extraction
  2) Entity Linking
  3) Evidence Retrieval
  4) Claim Verification
  5) Hallucination Detection + Risk Aggregation
```

### Pipeline Stages (Brief)

- **Claim Extraction**: decomposes text into auditable claim units.
- **Entity Linking**: resolves claim entities to canonical references (e.g., Wikidata QIDs).
- **Evidence Retrieval**: gathers structured and narrative evidence candidates.
- **Claim Verification**: determines support, contradiction, or uncertainty.
- **Risk Aggregation**: computes document-level risk outputs from claim outcomes.

---

## Evidence Sources

### 1) Wikidata (Structured)

- Uses structured entity/property evidence (e.g., property IDs such as `P571`, `P159`, etc.).
- Supports predicate-aware checks and contradiction handling when authoritative values conflict with the claim.

### 2) Wikipedia (Narrative)

- Retrieves sentence-level passages for narrative grounding.
- Includes source links; stable `oldid` links are used when available by retrieval logic.

### Important Note

Evidence availability directly affects verdict confidence and final classification. Missing evidence is not equivalent to falsity.

---

## Verdicts & Risk Outputs

### Claim Verdicts

The verifier may emit:

- `SUPPORTED`
- `REFUTED`
- `UNCERTAIN`
- `INSUFFICIENT_EVIDENCE`
- `PARTIALLY_SUPPORTED`

### Risk Outputs

- `hallucination_score`: normalized scalar risk estimate derived from claim outcomes.
- `overall_risk`: coarse label (`LOW`, `MEDIUM`, `HIGH`) derived from the score.
- `summary`: counts/rollups for claim-level result categories.

---

## UX / Input Rules

The audit input component enforces deterministic behavior:

- **Enter** submits the audit.
- **Shift+Enter** inserts a newline.
- **Hard 5000-character maximum** enforced for typing, paste, and drop.
- Overflow attempts are clamped and trigger inline toast feedback.
- Button submit and keyboard submit share the same validation/submit path.

---

## Running Locally

### Prerequisites

- Python 3.9+
- Node.js 18+

### Backend Only

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
.venv/bin/python -m uvicorn app:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

### Frontend Only

```bash
cd frontend
npm install
npm run dev
```

### Run Full Stack (Single Command)

```bash
(for p in 3000 3001 8000; do lsof -ti :$p | xargs -r kill -9; done; pkill -f "next dev" || true; pkill -f "uvicorn" || true; rm -f frontend/.next/dev/lock; sleep 1; (.venv/bin/python -m uvicorn app:app --app-dir backend --reload --host 127.0.0.1 --port 8000) & (cd frontend && npm run dev))
```

Then open: <http://localhost:3000/audit>

### Health Check

```bash
curl http://127.0.0.1:8000/health
```

Expected payload shape:

```json
{
  "status": "ok",
  "pipeline_ready": true,
  "pid": 12345,
  "uptime_s": 12.34
}
```

---

## Example Usage

### Example Input Text

```text
Google was founded in 1998 by Larry Page and Sergey Brin. The company is headquartered in Mountain View, California. Alphabet reports annual revenue in public filings.
```

### Example Audit Request

```bash
curl -X POST http://127.0.0.1:8000/audit \
  -H "Content-Type: application/json" \
  -d '{"text":"Google was founded in 1998 by Larry Page and Sergey Brin. The company is headquartered in Mountain View, California."}'
```

### Example Response Shape

```json
{
  "overall_risk": "LOW",
  "hallucination_score": 0.18,
  "summary": {
    "total_asserted_claims": 2,
    "supported": 1,
    "partially_supported": 0,
    "refuted": 0,
    "uncertain": 1,
    "insufficient": 0
  },
  "claims": [
    {
      "claim_id": "c1",
      "claim_text": "Google was founded in 1998 by Larry Page and Sergey Brin.",
      "verification": {
        "verdict": "SUPPORTED",
        "confidence": 0.9,
        "reasoning": "Matched structured evidence"
      },
      "evidence": {
        "wikidata": [],
        "wikipedia": [],
        "primary_document": []
      }
    }
  ]
}
```

---

## Repository Layout

```text
.
├── backend/
│   ├── app.py
│   ├── core/
│   ├── pipeline/
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── audit/route.ts
│   │   │   └── health/route.ts
│   │   └── audit/page.tsx
│   └── components/
│       └── AuditInput.tsx
├── tests/
├── package.json
└── README.md
```

---

## Development Notes

- The UI supports **Demo** and **Research** modes.
  - Demo mode uses tighter performance budgets/timeouts.
  - Research mode runs deeper verification settings.
- Next.js may automatically use **port 3001** if 3000 is already occupied.
- Frontend API calls are proxied via:
  - `frontend/app/api/audit/route.ts`
  - `frontend/app/api/health/route.ts`

---

## Limitations

- Knowledge-graph coverage is incomplete for long-tail entities and properties.
- Some narrative claims require context that may not be recoverable from retrieved passages.
- Entity linking can fail for ambiguous or non-resolvable references.
- Numeric financial claims may remain uncertain when exact period/value alignment is unavailable.

---

## Roadmap

- Multi-document audit support.
- Additional domain-specific claim type handling.
- Expanded property mapping and grounding coverage.
- Stronger evaluation harnesses for calibration analysis.

---

## License

MIT License. See [LICENSE](./LICENSE) for details.
