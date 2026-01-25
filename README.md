# Epistemic Audit Engine

### Research-Grade Verification of AI Outputs

The **Epistemic Audit Engine** is a specialized system designed to verify the factual and epistemic integrity of LLM-generated text. Unlike traditional fact-checking tools, it focuses on **claim atomicity**, **narrative grounding**, and **epistemic risk assessment**—detecting not just what is false, but what is unsupported, overstated, or structurally hallucinated.

## Abstract

As Large Language Models (LLMs) are increasingly integrated into critical workflows, the need for rigorous, automated verification has grown. This system implements a multi-stage pipeline that extracts atomic claims from raw text, links entities to the Wikidata knowledge graph, retrieves semantic evidence from Wikipedia, and performs NLI-based verification. A novel component of this engine is its **Hallucination Risk Scoring**, which aggregates failure modes (e.g., entity mismatch, temporal contradiction, overconfidence) into a single scalar metric, allowing for precise auditing of AI reliability.

---

## Capabilities

### What This System Is
- **An Epistemic Auditor**: It evaluates whether a text's claims are justified by available external evidence.
- **A Risk Analyzer**: It quantifies the likelihood of hallucination based on structural and semantic signals.
- **Transparent**: It provides granular, claim-level evidence linkage.

### What This System Is NOT
- **A "Truth Oracle"**: It does not determine absolute truth, but rather *verification against a corpus*.
- **A General Search Engine**: It is optimized for specific entity-centric fact verification, not open-ended queries.

### Core Features
- **Atomic Claim Extraction**: Decomposes complex sentences into independent, verifiable logic units.
- **Knowledge-Graph Verification**: Validates entities and relationships against Wikidata.
- **Narrative Evidence Grounding**: Retrieves (via Wikipedia) and scores textual passages using Sentence-BERT to verify nuanced claims.
- **Epistemic Polarity Classification**: Distinguishes between `SUPPORTED`, `REFUTED`, and `INSUFFICIENT_EVIDENCE`.
- **Hallucination Risk Scoring**: Calculates a normalized risk score (0.0–1.0) based on weighted failure signals.
- **Evidence-Linked UI**: A React/Next.js interface that highlights claims and displays exact source snippets.

### Detection Scope

**What The System Detects:**
- **Atomic Factual Errors**: Direct contradictions with Wikipedia/Wikidata evidence (e.g., wrong dates, wrong entities).
- **Structural Hallucinations**: Universal claims without scope, impossible dosages, and entity role conflicts.
- **Epistemic Overconfidence**: Asserting certainty ("definitely", "always") when evidence is weak.

**What It Explicitly Does NOT Detect:**
- **Reasoning Flaws**: It does not evaluate the logical coherence of arguments, only the factual basis of atomic premises.
- **Style/Tone Issues**: It ignores sentiment unless it impacts factual integrity.
- **Omission**: It cannot detect relevant facts that were *left out*, only errors in what was *included*.

**Required Human Interpretation:**
- Users must review the "Evidence Snippets" to validate the system's alignment.
- High Risk scores indicate a *probability* of failure, requiring manual audit.
- Zero Risk does not imply perfect truth, only alignment with available corpus data.

---

## Architecture

```
epistemic-audit-engine/
├── backend/
│   ├── app.py                  # API Entry Point (FastAPI)
│   ├── pipeline/               # Core audit pipeline logic
│   └── ...
├── frontend/                   # Next.js Application
│   ├── app/                    # App Router pages
│   └── components/             # React UI components (AuditSummary, ClaimInspector)
├── claim_extractor.py          # NLP Extraction Module
├── entity_linker.py            # Wikidata Linking Module
├── evidence_retriever.py       # Multi-source Evidence Retrieval
├── claim_verifier.py           # Logic Verification Module
└── hallucination_detector.py   # Risk Scoring Module
```

---

## Development Instructions

### Prerequisites
- Python 3.9+
- Node.js 18+
- Anaconda (recommended for environment management)

### 1. Backend Setup (FastAPI)
The backend is a lightweight FastAPI service orchestrating the Python audit modules.

```bash
# Verify you are in the project root
cd "Research Tool/backend" (or root if using script setup)

# Install dependencies (from root)
pip install -r backend/requirements.txt
python -m spacy download en_core_web_sm

# Start the API Server
cd backend
uvicorn app:app --reload --port 8000
```
Server will be available at: `http://localhost:8000`

### 2. Frontend Setup (Next.js)
The frontend is a modern Next.js 16 (Turbopack) application.

```bash
cd frontend

# Install dependencies
npm install

# Start Development Server
npm run dev
```
UI will be available at: `http://localhost:3000`

---

## Status

- **Backend**: v1.1 (Frozen Phase) - Core logic stabilized; entity linkage and passage retrieval finalized.
- **Frontend**: v1.5.1 (Final) - Production UI with normalized summary metrics and visual polish.
- **Optimization**: Calibration is set to "Conservative," prioritizing low false-positive rates for hallucination detection.

## License

MIT License. See [LICENSE](./LICENSE) for details.
