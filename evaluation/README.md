# Evaluation Harness

Correctness measurement for the Epistemic Audit Engine. No new models. No new features. Pure measurement.

## Structure

```
evaluation/
├── golden_cases.json      # Golden test cases with expected verdicts
├── harness.py             # Main evaluation runner
├── downgrade_tracer.py    # Detailed phase-by-phase tracing
├── test_golden_cases.py   # Pytest integration
└── README.md
```

## Usage

### Run All Golden Cases

```bash
python -m evaluation.harness
```

### Run Single Case

```bash
python -m evaluation.harness --case SUPPORT_01
```

### Run Category

```bash
python -m evaluation.harness --category verdict_supported
python -m evaluation.harness --category hallucination_entity_role
python -m evaluation.harness --category downgrade_chain
```

### Generate JSON Report

```bash
python -m evaluation.harness --report
python -m evaluation.harness --report --output report.json
```

### Trace Downgrade Reasons

```bash
python -m evaluation.downgrade_tracer "Apple was founded in 1980."
python -m evaluation.downgrade_tracer "Steve Jobs invented the internet." --verbose
python -m evaluation.downgrade_tracer "Elon Musk designed the Falcon 9." --json
```

### Pytest Integration

```bash
pytest evaluation/test_golden_cases.py -v
pytest evaluation/test_golden_cases.py -v -k "SUPPORT"
pytest evaluation/test_golden_cases.py -v -k "HALLUC"
pytest evaluation/test_golden_cases.py -v -k "downgrade"
```

## Golden Case Categories

| Category | Description |
|----------|-------------|
| `verdict_supported` | Claims that should receive SUPPORTED |
| `verdict_refuted` | Claims that should receive REFUTED |
| `verdict_insufficient` | Claims that should receive INSUFFICIENT_EVIDENCE |
| `verdict_uncertain` | Claims that should receive UNCERTAIN |
| `hallucination_entity_role` | Tests ENTITY_ROLE_CONFLICT detection |
| `hallucination_temporal` | Tests TEMPORAL_FABRICATION detection |
| `hallucination_dosage` | Tests IMPOSSIBLE_DOSAGE detection |
| `hallucination_scope` | Tests SCOPE_OVERGENERALIZATION detection |
| `hallucination_court` | Tests COURT_AUTHORITY_MISATTRIBUTION detection |
| `downgrade_chain` | Tests for proper downgrade reason tracking |
| `edge_case` | Boundary conditions and special cases |
| `risk_calculation` | Risk score and level validation |
| `sanity_rules` | Sanity rule triggering conditions |

## Downgrade Phases

When a claim is not SUPPORTED, the harness identifies which phase blocked it:

1. **extraction** - Claim could not be parsed
2. **entity_linking** - Subject entity could not be resolved
3. **evidence_retrieval** - No evidence found from any source
4. **verification** - Evidence exists but contradicts or doesn't support
5. **hallucination_detection** - Hallucination pattern detected

## Report Output

```json
{
  "summary": {
    "total_cases": 24,
    "passed": 20,
    "failed": 4,
    "pass_rate": "83.3%"
  },
  "verdict_accuracy": {
    "correct": 18,
    "total": 20,
    "accuracy": "90.0%"
  },
  "hallucination_recall": {
    "detected": 7,
    "expected": 8,
    "recall": "87.5%"
  },
  "failures_by_phase": {
    "verification": [...],
    "hallucination_detection": [...]
  }
}
```

## Adding New Golden Cases

Edit `golden_cases.json`:

```json
{
  "case_id": "UNIQUE_ID",
  "category": "verdict_supported",
  "input_text": "Claim text to verify.",
  "expected": {
    "verdict": "SUPPORTED",
    "hallucination_types": [],
    "min_confidence": 0.85,
    "risk_level": "LOW"
  },
  "rationale": "Why this is the expected result."
}
```

### Expected Fields

| Field | Type | Description |
|-------|------|-------------|
| `verdict` | string | Expected verdict for primary claim |
| `hallucination_types` | array | Expected hallucination types |
| `risk_level` | string | Expected overall risk (LOW/MEDIUM/HIGH) |
| `min_confidence` | float | Minimum acceptable confidence |
| `max_hallucination_score` | float | Maximum acceptable score |
| `claims_count` | int | Expected number of extracted claims |
| `verdicts` | object | Verdict distribution for multi-claim cases |
| `downgrade_reason` | object | Expected downgrade phase and issue |

## Design Principles

1. **No new models** - Uses existing pipeline components only
2. **No new features** - Pure measurement, no behavioral changes
3. **Determinism** - Results are reproducible (seed=42)
4. **Phase tracing** - Every downgrade is explained
5. **Minimal overhead** - Runs on existing infrastructure
