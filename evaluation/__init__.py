"""
Evaluation module for Epistemic Audit Engine.

Provides:
- Golden test case management
- Correctness measurement
- Downgrade reason tracking
- Detailed reporting

Usage:
    from evaluation.harness import EvaluationHarness

    harness = EvaluationHarness()
    results = harness.run_all()
    report = harness.generate_report(results)
"""

from .harness import EvaluationHarness, CaseResult, DowngradeReason, DowngradePhase

__all__ = ["EvaluationHarness", "CaseResult", "DowngradeReason", "DowngradePhase"]
