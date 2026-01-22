# Epistemic Audit Benchmark

This directory contains the gold-standard dataset for evaluating the Epistemic Audit Engine.

## Schema

### documents.json
Raw input texts.
- `doc_id`: Unique identifier
- `text`: Full text content

### claims.json
Extracted atomic claims (can be pre-populated or generated).
- `claim_id`: Unique identifier
- `doc_id`: Foreign key
- `text`: The claim text

### gold_labels.json
Ground truth for epistemic auditing (NOT just fact checking).
- `expected_verdict`: SUPPORTED | REFUTED | INSUFFICIENT_EVIDENCE
- `expected_hallucination_types`: List of [H1, H2, H3, H4, H5, H6]
- `justification`: Reasoning for the label.

## Metrics
Evaluation should measure:
1. Verdict Accuracy (Weighted by risk class)
2. Hallucination Recall (Per type)
3. False Alarm Rate (Valid claims flagged as H1/H2)
4. Calibration Error (Confidence vs Correctness)
