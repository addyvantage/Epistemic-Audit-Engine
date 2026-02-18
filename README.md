# Epistemic Audit Engine
Claim-level reliability auditing for LLM-generated text using evidence grounding and epistemic risk scoring.

---

## Screenshot
> Placeholder: add an audit workspace screenshot here (for example: `docs/images/audit-ui.png`).

---

## Table of Contents
- [What This System Does](#what-this-system-does)
- [Why It Exists](#why-it-exists)
- [System Architecture](#system-architecture)
- [Verification Pipeline](#verification-pipeline)
- [Evidence Sources](#evidence-sources)
- [Verdicts & Risk Outputs](#verdicts--risk-outputs)
- [Input Interface (UX Rules)](#input-interface-ux-rules)
- [Running Locally](#running-locally)
- [Health Check](#health-check)
- [Example Usage](#example-usage)
- [Repository Layout](#repository-layout)
- [Development Notes](#development-notes)
- [Limitations](#limitations)
- [Roadmap](#roadmap)
- [License](#license)

---

## What This System Does
Epistemic Audit Engine evaluates model output at the **claim level**.

For each submitted text, the system:
- extracts atomic claims,
- links entities to canonical references,
- retrieves external evidence,
- verifies each claim,
- aggregates claim outcomes into risk outputs.

This makes review workflows more transparent: users can inspect which claims are supported, contradicted, or unresolved.

---

## Why It Exists
LLM outputs can sound confident while mixing correct facts with unsupported statements.

This creates **epistemic risk** in research, education, and analysis contexts, where users need to distinguish:
- what is evidence-backed,
- what is uncertain,
- what is contradicted.

**This is an audit aid, not an oracle.**

---

## System Architecture
The application is split between a Next.js frontend and a FastAPI backend pipeline.

```text
[Browser UI (/audit)]
         |
         v
[Next.js API Proxy]
  - /api/audit
  - /api/health
         |
         v
[FastAPI Backend]
  - POST /audit
  - GET  /health
         |
         v
[Verification Pipeline]
         |
         v
[Risk Outputs]
  - overall_risk
  - hallucination_score
  - summary
  - claims
```

---

## Verification Pipeline
### 1) Claim Extraction
Converts input text into atomic, auditable claim units.

### 2) Entity Linking
Resolves claim entities to canonical identifiers when possible (for structured grounding and disambiguation).

### 3) Evidence Retrieval
Collects candidate evidence from structured and narrative sources.

### 4) Claim Verification
Evaluates alignment and contradiction signals to assign a verdict per claim.

### 5) Risk Aggregation
Combines claim-level results into document-level risk outputs.

---

## Evidence Sources
- **Wikidata (structured KG evidence):**
  - Entity/property-based evidence (triples, property IDs such as `P571`, `P159`, etc.).
  - Used for structured support and contradiction checks.
- **Wikipedia (narrative passages):**
  - Sentence-level narrative evidence and source links.

Evidence retrieval quality and source coverage influence verification outcomes.  
**Evidence availability affects verdict confidence.**

---

## Verdicts & Risk Outputs
Claim-level verdicts:
- `SUPPORTED`
- `REFUTED`
- `UNCERTAIN`
- `INSUFFICIENT_EVIDENCE`
- `PARTIALLY_SUPPORTED`

Top-level `/audit` response shape:
- `overall_risk`: coarse label (`LOW`, `MEDIUM`, `HIGH`)
- `hallucination_score`: normalized scalar risk estimate
- `summary`: aggregate counts
- `claims`: detailed claim-level results

---

## Input Interface (UX Rules)
The audit input layer enforces deterministic behavior:
- Press **Enter** to submit.
- Press **Shift+Enter** to insert newline.
- Hard **5000-character cap** on input.
- Overflow paste is clamped to 5000 characters.
- Inline toast feedback appears on overflow.
- Keyboard and button share one submit path.

---

## Running Locally

### Prerequisites
- Python 3.9+
- Node.js 18+

### Backend Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Run backend:
```bash
.venv/bin/python -m uvicorn app:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

### Run Full Stack (Single Command)  ⭐ REQUIRED
```bash
(for p in 3000 3001 8000; do lsof -ti :$p | xargs -r kill -9; done; pkill -f "next dev" || true; pkill -f "uvicorn" || true; rm -f frontend/.next/dev/lock; sleep 1; (.venv/bin/python -m uvicorn app:app --app-dir backend --reload --host 127.0.0.1 --port 8000) & (cd frontend && npm run dev))
```

Open http://localhost:3000/audit

---

## Health Check
```bash
curl http://127.0.0.1:8000/health
```

---

## Example Usage
### Example Input Text
```text
Google was founded in 1998 by Larry Page and Sergey Brin. The company is headquartered in Mountain View, California. Alphabet reports annual revenue in public filings.
```

### Example POST Request
```bash
curl -X POST http://127.0.0.1:8000/audit \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Google was founded in 1998 by Larry Page and Sergey Brin. The company is headquartered in Mountain View, California.",
    "mode": "demo"
  }'
```

### Example Output JSON Shape
```json
{
  "overall_risk": "LOW",
  "hallucination_score": 0.21,
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
        "reasoning": "Matched structured evidence."
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
├── tests/
├── package.json
└── README.md
```

---

## Development Notes
- The UI supports **Demo** and **Research** modes.
  - Demo mode uses a tighter runtime budget.
  - Research mode uses deeper retrieval/verification settings.
- Next.js may fall back to **port 3001** if port 3000 is occupied.
- Frontend API requests are proxied through:
  - `/api/audit`
  - `/api/health`

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
MIT License.
