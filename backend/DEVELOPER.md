# Epistemic Audit Engine - Backend Developer Guide

## Overview
The Epistemic Audit Engine backend is a FastAPI application that performs multi-stage fact-checking and epistemic risk analysis.

## Project Structure
The backend code is organized to support clean execution from the `backend/` directory without `sys.path` hacks.

```
backend/
├── app.py                  # Main entry point (FastAPI app)
├── config/                 # Configuration modules (Pipeline settings)
├── core/                   # Core logic modules (Extraction, Verification, etc.)
│   ├── claim_extractor.py
│   ├── entity_linker.py
│   ├── evidence_retriever.py
│   └── ...
└── pipeline/
    └── run_full_audit.py   # Pipeline orchestrator
```

## Running the Backend

### Prerequisites
- Python 3.11+
- Installed dependencies (`pip install -r requirements.txt` in root or backend)

### Start Server
Navigate to the `backend/` directory and run `uvicorn`:

```bash
cd backend
uvicorn app:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.
- **Docs**: [http://localhost:8000/docs](http://127.0.0.1:8000/docs)
- **Health**: [http://localhost:8000/health](http://127.0.0.1:8000/health)

## API Usage

### Endpoint: `POST /audit`
Analyzes text for epistemic claims.

**Request:**
```json
{
  "text": "SpaceX was founded in 2002 by Elon Musk."
}
```

**Response:**
```json
{
  "overall_risk": "LOW",
  "hallucination_score": 0.0,
  "claims": [
    {
      "claim_text": "SpaceX was founded in 2002 by Elon Musk",
      "verification": {
        "verdict": "SUPPORTED",
        "confidence": 0.95
      }
    }
  ]
}
```

## Testing
Run the following curl command to verify the pipeline:

```bash
curl -X POST http://127.0.0.1:8000/audit \
  -H "Content-Type: application/json" \
  -d '{"text": "A 2023 study by MIT proved that 97.4% of users improved productivity."}'
```
