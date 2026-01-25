# CLAUDE.md — Epistemic Audit Engine

## Project Identity

This is a **research-grade verification pipeline** for auditing factual claims in text against external knowledge sources. It is an NLP/IR system, not a web application.

## What This System IS

- A 5-phase Python pipeline: Extract → Link → Retrieve → Verify → Detect
- A deterministic audit tool producing structured verdicts (SUPPORTED, REFUTED, INSUFFICIENT_EVIDENCE, UNCERTAIN)
- A hallucination risk scorer using rule-based pattern detection
- A research prototype with a thin FastAPI wrapper for pipeline invocation

## What This System IS NOT

- NOT a SaaS product, web app, or user-facing application
- NOT a system requiring authentication, users, sessions, or login
- NOT a system that uses LLMs for generation (no GPT, no Claude API calls)
- NOT a CRUD application with database models

## Architecture

```
Input Text
    ↓
Phase 1: claim_extractor.py      → Atomic claims via spaCy dependency parsing
    ↓
Phase 2: entity_linker.py        → Wikidata entity resolution
    ↓
Phase 3: evidence_retriever.py   → Wikidata statements + Wikipedia passages (SBERT)
    ↓
Phase 4: claim_verifier.py       → Verdict assignment via NLI (RoBERTa-MNLI)
    ↓
Phase 5: hallucination_detector.py → Rule-based anomaly flags
    ↓
Output: { overall_risk, hallucination_score, claims[] }
```

Orchestrator: `backend/pipeline/run_full_audit.py`

## Component Classification

| Type | Components |
|------|------------|
| **Deterministic/Rule-based** | claim filtering, entity disambiguation, property mapping, hallucination patterns, risk formula |
| **Statistical/ML (local models)** | spaCy NER/parsing, Sentence-BERT similarity, RoBERTa-MNLI classification |
| **External APIs (read-only)** | Wikidata API, Wikipedia API |
| **Mocked/Stubbed** | SEC EDGAR, Grokipedia |

## Hard Constraints

1. **No LLM integration** — Do not add OpenAI, Anthropic, or any generative AI APIs
2. **No authentication** — Do not add users, login, sessions, OAuth, JWT
3. **No database models** — No ORMs, no user tables, no persistent storage beyond config
4. **No SaaS patterns** — No billing, subscriptions, rate limiting, API keys for users
5. **Preserve determinism** — Random seeds are fixed; pipeline must be reproducible

## External Knowledge Sources

| Source | Usage | Status |
|--------|-------|--------|
| Wikidata | Entity resolution, structured facts | Active |
| Wikipedia | Narrative evidence passages | Active |
| SEC EDGAR | Financial/corporate facts | Mocked |
| Grokipedia | Supplementary narrative | Stubbed (returns None) |

## Key Files

| File | Purpose |
|------|---------|
| `backend/pipeline/run_full_audit.py` | Pipeline orchestrator |
| `claim_extractor.py` | Phase 1: spaCy-based claim decomposition |
| `entity_linker.py` | Phase 2: Wikidata entity linking |
| `evidence_retriever.py` | Phase 3: Multi-source evidence collection |
| `claim_verifier.py` | Phase 4: NLI-based verdict assignment |
| `hallucination_detector.py` | Phase 5: Pattern-based anomaly detection |
| `risk_aggregator.py` | Risk score calculation |
| `nli_engine.py` | RoBERTa-MNLI wrapper |
| `property_mapper.py` | Predicate → Wikidata P-ID mapping |

## When Modifying Code

- Fix bugs in existing pipeline logic
- Improve heuristics with justification
- Add test cases for edge cases
- Extend evidence sources (read-only APIs only)

## When NOT Modifying Code

- Do not add user management or authentication
- Do not add payment/billing systems
- Do not refactor into microservices
- Do not replace local models with LLM API calls
- Do not add features unrelated to claim verification

## Running the Pipeline

```bash
source .venv/bin/activate
python -c "
from backend.pipeline.run_full_audit import AuditPipeline
pipeline = AuditPipeline()
result = pipeline.run('Your text here')
print(result)
"
```

## Frontend Note

The `frontend/` directory contains a Next.js visualization layer for displaying audit results. It is a **read-only display component**, not an application with user flows. Do not add authentication, user accounts, or SaaS features to it.
