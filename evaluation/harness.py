"""
Evaluation Harness for Epistemic Audit Engine

Measures correctness of verdicts, hallucination detection, and downgrade reasons.
No new models. No new features. Pure measurement.

Usage:
    python -m evaluation.harness                    # Run all cases
    python -m evaluation.harness --case SUPPORT_01  # Run single case
    python -m evaluation.harness --category verdict_supported  # Run category
    python -m evaluation.harness --report           # Generate detailed report
"""

import json
import sys
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.pipeline.run_full_audit import AuditPipeline


class DowngradePhase(Enum):
    """Phase where verdict was downgraded from potential SUPPORTED."""
    EXTRACTION = "extraction"
    ENTITY_LINKING = "entity_linking"
    EVIDENCE_RETRIEVAL = "evidence_retrieval"
    VERIFICATION = "verification"
    HALLUCINATION_DETECTION = "hallucination_detection"
    NONE = "none"


@dataclass
class DowngradeReason:
    """Structured explanation of why a claim was not SUPPORTED."""
    phase: DowngradePhase
    issue: str
    evidence_status: dict = field(default_factory=dict)
    hallucinations_detected: list = field(default_factory=list)
    entity_resolution: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "phase": self.phase.value,
            "issue": self.issue,
            "evidence_status": self.evidence_status,
            "hallucinations_detected": self.hallucinations_detected,
            "entity_resolution": self.entity_resolution
        }


@dataclass
class CaseResult:
    """Result of evaluating a single golden case."""
    case_id: str
    passed: bool
    expected_verdict: Optional[str]
    actual_verdict: Optional[str]
    expected_hallucinations: list
    actual_hallucinations: list
    expected_risk: Optional[str]
    actual_risk: Optional[str]
    downgrade_reason: Optional[DowngradeReason]
    confidence: Optional[float]
    errors: list = field(default_factory=list)
    claim_count: int = 0
    verdict_distribution: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "case_id": self.case_id,
            "passed": self.passed,
            "expected_verdict": self.expected_verdict,
            "actual_verdict": self.actual_verdict,
            "expected_hallucinations": self.expected_hallucinations,
            "actual_hallucinations": self.actual_hallucinations,
            "expected_risk": self.expected_risk,
            "actual_risk": self.actual_risk,
            "downgrade_reason": self.downgrade_reason.to_dict() if self.downgrade_reason else None,
            "confidence": self.confidence,
            "errors": self.errors,
            "claim_count": self.claim_count,
            "verdict_distribution": self.verdict_distribution
        }


def analyze_downgrade(claim: dict) -> DowngradeReason:
    """
    Analyze why a claim received its verdict.
    Traces through pipeline phases to identify the downgrade point.
    """
    verdict = claim.get("verification", {}).get("verdict", "UNKNOWN")

    # Check entity resolution
    subject_entity = claim.get("subject_entity", {})
    object_entity = claim.get("object_entity", {})

    subject_resolved = subject_entity.get("resolution_status") == "RESOLVED"
    object_resolved = object_entity.get("resolution_status") in ["RESOLVED", "RESOLVED_SOFT", None]

    entity_resolution = {
        "subject": {
            "text": subject_entity.get("text"),
            "entity_id": subject_entity.get("entity_id"),
            "status": subject_entity.get("resolution_status"),
            "resolved": subject_resolved
        },
        "object": {
            "text": object_entity.get("text"),
            "entity_id": object_entity.get("entity_id"),
            "status": object_entity.get("resolution_status"),
            "resolved": object_resolved
        }
    }

    # Check evidence status
    evidence = claim.get("evidence", {})
    evidence_status = claim.get("evidence_status", {})

    has_wikidata = len(evidence.get("wikidata", [])) > 0
    has_wikipedia = len(evidence.get("wikipedia", [])) > 0
    has_primary = len(evidence.get("primary_document", [])) > 0

    evidence_summary = {
        "wikidata": evidence_status.get("wikidata", "ABSENT"),
        "wikipedia": evidence_status.get("wikipedia", "ABSENT"),
        "primary_document": evidence_status.get("primary_document", "ABSENT"),
        "has_any": has_wikidata or has_wikipedia or has_primary
    }

    # Check hallucinations
    hallucinations = claim.get("hallucinations", [])
    halluc_types = [h.get("hallucination_type") for h in hallucinations]
    critical_halluc = [h for h in hallucinations if h.get("severity") == "CRITICAL"]

    # Determine downgrade phase and reason
    if verdict == "SUPPORTED":
        return DowngradeReason(
            phase=DowngradePhase.NONE,
            issue="No downgrade - claim supported",
            evidence_status=evidence_summary,
            entity_resolution=entity_resolution
        )

    # Check for critical hallucination (always REFUTED)
    if critical_halluc:
        return DowngradeReason(
            phase=DowngradePhase.HALLUCINATION_DETECTION,
            issue=f"CRITICAL hallucination detected: {[h.get('hallucination_type') for h in critical_halluc]}",
            evidence_status=evidence_summary,
            hallucinations_detected=halluc_types,
            entity_resolution=entity_resolution
        )

    # Check if verdict is REFUTED (evidence contradiction)
    if verdict == "REFUTED":
        verification = claim.get("verification", {})
        contradicted_by = verification.get("contradicted_by", [])
        return DowngradeReason(
            phase=DowngradePhase.VERIFICATION,
            issue=f"Evidence contradiction: {len(contradicted_by)} contradicting evidence(s)",
            evidence_status=evidence_summary,
            hallucinations_detected=halluc_types,
            entity_resolution=entity_resolution
        )

    # Check for non-critical hallucination (blocks SUPPORTED -> UNCERTAIN)
    if hallucinations and verdict == "UNCERTAIN":
        return DowngradeReason(
            phase=DowngradePhase.HALLUCINATION_DETECTION,
            issue=f"Non-critical hallucination blocks support: {halluc_types}",
            evidence_status=evidence_summary,
            hallucinations_detected=halluc_types,
            entity_resolution=entity_resolution
        )

    # Check entity linking failure
    if not subject_resolved:
        return DowngradeReason(
            phase=DowngradePhase.ENTITY_LINKING,
            issue=f"Subject entity not resolved: '{subject_entity.get('text')}'",
            evidence_status=evidence_summary,
            entity_resolution=entity_resolution
        )

    # Check evidence retrieval failure
    if not evidence_summary["has_any"]:
        return DowngradeReason(
            phase=DowngradePhase.EVIDENCE_RETRIEVAL,
            issue="No evidence retrieved from any source",
            evidence_status=evidence_summary,
            entity_resolution=entity_resolution
        )

    # INSUFFICIENT_EVIDENCE with evidence present but not matching
    if verdict == "INSUFFICIENT_EVIDENCE":
        # Check alignment
        for source in ["wikidata", "wikipedia"]:
            for ev in evidence.get(source, []):
                alignment = ev.get("alignment", {})
                if not alignment.get("subject_match"):
                    return DowngradeReason(
                        phase=DowngradePhase.VERIFICATION,
                        issue="Evidence exists but subject does not match",
                        evidence_status=evidence_summary,
                        entity_resolution=entity_resolution
                    )
                if not alignment.get("predicate_match"):
                    return DowngradeReason(
                        phase=DowngradePhase.VERIFICATION,
                        issue="Evidence exists but predicate does not match",
                        evidence_status=evidence_summary,
                        entity_resolution=entity_resolution
                    )

        return DowngradeReason(
            phase=DowngradePhase.VERIFICATION,
            issue="No eligible supporting evidence found",
            evidence_status=evidence_summary,
            entity_resolution=entity_resolution
        )

    # UNCERTAIN with sanity rule
    if verdict == "UNCERTAIN":
        reasoning = claim.get("verification", {}).get("reasoning", "")
        if "sanity" in reasoning.lower():
            return DowngradeReason(
                phase=DowngradePhase.VERIFICATION,
                issue="Sanity rule triggered: >3 claims with zero SUPPORTED",
                evidence_status=evidence_summary,
                entity_resolution=entity_resolution
            )

        return DowngradeReason(
            phase=DowngradePhase.VERIFICATION,
            issue="Downgraded to UNCERTAIN (reason unclear)",
            evidence_status=evidence_summary,
            entity_resolution=entity_resolution
        )

    return DowngradeReason(
        phase=DowngradePhase.VERIFICATION,
        issue=f"Unknown downgrade path for verdict: {verdict}",
        evidence_status=evidence_summary,
        entity_resolution=entity_resolution
    )


def evaluate_case(pipeline: AuditPipeline, case: dict) -> CaseResult:
    """Evaluate a single golden test case against pipeline output."""
    case_id = case["case_id"]
    input_text = case["input_text"]
    expected = case["expected"]

    errors = []

    try:
        result = pipeline.run(input_text)
    except Exception as e:
        return CaseResult(
            case_id=case_id,
            passed=False,
            expected_verdict=expected.get("verdict"),
            actual_verdict=None,
            expected_hallucinations=expected.get("hallucination_types", []),
            actual_hallucinations=[],
            expected_risk=expected.get("risk_level"),
            actual_risk=None,
            downgrade_reason=None,
            confidence=None,
            errors=[f"Pipeline exception: {str(e)}"]
        )

    claims = result.get("claims", [])
    claim_count = len(claims)

    # Calculate verdict distribution
    verdict_dist = {"SUPPORTED": 0, "REFUTED": 0, "UNCERTAIN": 0, "INSUFFICIENT_EVIDENCE": 0}
    for claim in claims:
        v = claim.get("verification", {}).get("verdict", "UNKNOWN")
        if v in verdict_dist:
            verdict_dist[v] += 1

    # Collect all hallucinations
    actual_hallucinations = []
    for claim in claims:
        for h in claim.get("hallucinations", []):
            ht = h.get("hallucination_type")
            if ht and ht not in actual_hallucinations:
                actual_hallucinations.append(ht)

    actual_risk = result.get("overall_risk")
    actual_score = result.get("hallucination_score", 0)

    # For single-claim cases, check the primary claim
    if "verdict" in expected and claims:
        primary_claim = claims[0]
        actual_verdict = primary_claim.get("verification", {}).get("verdict")
        confidence = primary_claim.get("verification", {}).get("confidence")
        downgrade = analyze_downgrade(primary_claim)
    else:
        actual_verdict = None
        confidence = None
        downgrade = None

    # Validation checks
    passed = True

    # Check verdict
    if "verdict" in expected:
        if actual_verdict != expected["verdict"]:
            passed = False
            errors.append(f"Verdict mismatch: expected {expected['verdict']}, got {actual_verdict}")

    # Check verdict distribution for multi-claim cases
    if "verdicts" in expected:
        for v, count in expected["verdicts"].items():
            if verdict_dist.get(v, 0) != count:
                passed = False
                errors.append(f"Verdict count for {v}: expected {count}, got {verdict_dist.get(v, 0)}")

    # Check hallucination types
    if "hallucination_types" in expected:
        expected_ht = set(expected["hallucination_types"])
        actual_ht = set(actual_hallucinations)

        missing = expected_ht - actual_ht
        if missing:
            passed = False
            errors.append(f"Missing hallucination types: {missing}")

        # Extra hallucinations are warnings, not failures (unless unexpected)
        extra = actual_ht - expected_ht
        if extra and expected_ht:  # Only warn if we expected specific types
            errors.append(f"Extra hallucination types (warning): {extra}")

    # Check risk level
    if "risk_level" in expected:
        if actual_risk != expected["risk_level"]:
            passed = False
            errors.append(f"Risk level mismatch: expected {expected['risk_level']}, got {actual_risk}")

    # Check confidence bounds
    if "min_confidence" in expected and confidence is not None:
        if confidence < expected["min_confidence"]:
            passed = False
            errors.append(f"Confidence too low: expected >= {expected['min_confidence']}, got {confidence}")

    # Check hallucination score bounds
    if "min_hallucination_score" in expected:
        if actual_score < expected["min_hallucination_score"]:
            passed = False
            errors.append(f"Hallucination score too low: expected >= {expected['min_hallucination_score']}, got {actual_score}")

    if "max_hallucination_score" in expected:
        if actual_score > expected["max_hallucination_score"]:
            passed = False
            errors.append(f"Hallucination score too high: expected <= {expected['max_hallucination_score']}, got {actual_score}")

    # Check claim count
    if "claims_count" in expected:
        if claim_count != expected["claims_count"]:
            passed = False
            errors.append(f"Claim count mismatch: expected {expected['claims_count']}, got {claim_count}")

    if "claims_count_min" in expected:
        if claim_count < expected["claims_count_min"]:
            passed = False
            errors.append(f"Too few claims: expected >= {expected['claims_count_min']}, got {claim_count}")

    # Check verdict contains
    if "verdict_contains" in expected:
        if verdict_dist.get(expected["verdict_contains"], 0) == 0:
            passed = False
            errors.append(f"Expected at least one {expected['verdict_contains']} verdict")

    return CaseResult(
        case_id=case_id,
        passed=passed,
        expected_verdict=expected.get("verdict"),
        actual_verdict=actual_verdict,
        expected_hallucinations=expected.get("hallucination_types", []),
        actual_hallucinations=actual_hallucinations,
        expected_risk=expected.get("risk_level"),
        actual_risk=actual_risk,
        downgrade_reason=downgrade,
        confidence=confidence,
        errors=errors,
        claim_count=claim_count,
        verdict_distribution=verdict_dist
    )


class EvaluationHarness:
    """Main harness for running golden test evaluations."""

    def __init__(self, golden_path: Optional[Path] = None):
        self.golden_path = golden_path or Path(__file__).parent / "golden_cases.json"
        self.pipeline = AuditPipeline()
        self._load_cases()

    def _load_cases(self):
        with open(self.golden_path) as f:
            data = json.load(f)
        self.metadata = data.get("metadata", {})
        self.cases = data.get("cases", [])

    def run_case(self, case_id: str) -> Optional[CaseResult]:
        """Run a single case by ID."""
        for case in self.cases:
            if case["case_id"] == case_id:
                return evaluate_case(self.pipeline, case)
        return None

    def run_category(self, category: str) -> list:
        """Run all cases in a category."""
        results = []
        for case in self.cases:
            if case.get("category") == category:
                results.append(evaluate_case(self.pipeline, case))
        return results

    def run_all(self) -> list:
        """Run all golden cases."""
        return [evaluate_case(self.pipeline, case) for case in self.cases]

    def generate_report(self, results: list) -> dict:
        """Generate a detailed evaluation report."""
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed

        # Group failures by downgrade phase
        failures_by_phase = {}
        for r in results:
            if not r.passed and r.downgrade_reason:
                phase = r.downgrade_reason.phase.value
                if phase not in failures_by_phase:
                    failures_by_phase[phase] = []
                failures_by_phase[phase].append({
                    "case_id": r.case_id,
                    "errors": r.errors,
                    "issue": r.downgrade_reason.issue
                })

        # Verdict accuracy
        verdict_correct = 0
        verdict_total = 0
        for r in results:
            if r.expected_verdict:
                verdict_total += 1
                if r.actual_verdict == r.expected_verdict:
                    verdict_correct += 1

        # Hallucination detection recall
        halluc_expected = 0
        halluc_detected = 0
        for r in results:
            for ht in r.expected_hallucinations:
                halluc_expected += 1
                if ht in r.actual_hallucinations:
                    halluc_detected += 1

        # Risk level accuracy
        risk_correct = 0
        risk_total = 0
        for r in results:
            if r.expected_risk:
                risk_total += 1
                if r.actual_risk == r.expected_risk:
                    risk_correct += 1

        return {
            "summary": {
                "total_cases": len(results),
                "passed": passed,
                "failed": failed,
                "pass_rate": f"{100 * passed / len(results):.1f}%" if results else "N/A"
            },
            "verdict_accuracy": {
                "correct": verdict_correct,
                "total": verdict_total,
                "accuracy": f"{100 * verdict_correct / verdict_total:.1f}%" if verdict_total else "N/A"
            },
            "hallucination_recall": {
                "detected": halluc_detected,
                "expected": halluc_expected,
                "recall": f"{100 * halluc_detected / halluc_expected:.1f}%" if halluc_expected else "N/A"
            },
            "risk_accuracy": {
                "correct": risk_correct,
                "total": risk_total,
                "accuracy": f"{100 * risk_correct / risk_total:.1f}%" if risk_total else "N/A"
            },
            "failures_by_phase": failures_by_phase,
            "detailed_results": [r.to_dict() for r in results]
        }


def main():
    parser = argparse.ArgumentParser(description="Epistemic Audit Evaluation Harness")
    parser.add_argument("--case", type=str, help="Run a single case by ID")
    parser.add_argument("--category", type=str, help="Run all cases in a category")
    parser.add_argument("--report", action="store_true", help="Generate detailed JSON report")
    parser.add_argument("--output", type=str, help="Output file for report (default: stdout)")
    parser.add_argument("--golden", type=str, help="Path to golden cases JSON")

    args = parser.parse_args()

    golden_path = Path(args.golden) if args.golden else None
    harness = EvaluationHarness(golden_path)

    if args.case:
        result = harness.run_case(args.case)
        if result:
            results = [result]
        else:
            print(f"Case not found: {args.case}")
            sys.exit(1)
    elif args.category:
        results = harness.run_category(args.category)
        if not results:
            print(f"No cases found for category: {args.category}")
            sys.exit(1)
    else:
        results = harness.run_all()

    report = harness.generate_report(results)

    if args.report or args.output:
        output = json.dumps(report, indent=2)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Report written to {args.output}")
        else:
            print(output)
    else:
        # Print summary
        print("\n=== Evaluation Results ===\n")
        print(f"Total: {report['summary']['total_cases']}")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Pass Rate: {report['summary']['pass_rate']}")
        print(f"\nVerdict Accuracy: {report['verdict_accuracy']['accuracy']}")
        print(f"Hallucination Recall: {report['hallucination_recall']['recall']}")
        print(f"Risk Accuracy: {report['risk_accuracy']['accuracy']}")

        if report['summary']['failed'] > 0:
            print("\n=== Failed Cases ===\n")
            for r in results:
                if not r.passed:
                    print(f"[FAIL] {r.case_id}")
                    for err in r.errors:
                        print(f"       - {err}")
                    if r.downgrade_reason:
                        print(f"       Phase: {r.downgrade_reason.phase.value}")
                        print(f"       Issue: {r.downgrade_reason.issue}")
                    print()


if __name__ == "__main__":
    main()
