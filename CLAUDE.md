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
Phase 1.5: entity_context.py     → Document-level entity tracking (v1.4)
    ↓
Phase 2: entity_linker.py        → Wikidata entity resolution + coreference
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

### Entity Resolution Status (v1.4)

| Status | Description |
|--------|-------------|
| `RESOLVED` | High-confidence direct Wikidata match (≥0.75) |
| `RESOLVED_SOFT` | Famous entity override or contextual disambiguation |
| `RESOLVED_COREF` | Coreference resolution from document context |
| `UNRESOLVED` | No viable candidate found |

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
| `entity_context.py` | Phase 1.5: Document-level entity tracking (v1.4) |
| `entity_linker.py` | Phase 2: Wikidata entity linking + coreference |
| `evidence_retriever.py` | Phase 3: Multi-source evidence collection |
| `claim_verifier.py` | Phase 4: NLI-based verdict assignment |
| `hallucination_detector.py` | Phase 5: Pattern-based anomaly detection |
| `risk_aggregator.py` | Risk score calculation |
| `nli_engine.py` | RoBERTa-MNLI wrapper |
| `property_mapper.py` | Predicate → Wikidata P-ID mapping |
| `config/core_config.py` | Thresholds and feature flags |

## Coverage Improvements (v1.4)

The following improvements reduce INSUFFICIENT_EVIDENCE overproduction while preserving epistemic rigor:

### 1. Document-Level Coreference
Generic references like "the company" are resolved to dominant named entities:
- Tracks ORG, PERSON, LOC entities across document
- Requires frequency or recency dominance
- Conservative: returns None for ambiguous cases

### 2. Structured Evidence Independence
Wikidata evidence can independently yield SUPPORTED:
- No longer requires narrative confirmation
- Alignment metadata computed for each evidence item
- Confidence capped at 0.85 for structured sources

### 3. Weak Support Accumulation
Multiple weak corroborations upgrade INSUFFICIENT → UNCERTAIN:
- Requires 2+ weak support sources
- Average score ≥ 0.68
- Does NOT upgrade to SUPPORTED (honest uncertainty)

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
