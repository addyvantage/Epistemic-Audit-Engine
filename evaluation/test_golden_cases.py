"""
Pytest integration for golden test cases.

Run with:
    pytest evaluation/test_golden_cases.py -v
    pytest evaluation/test_golden_cases.py -v -k "SUPPORT"   # Run only SUPPORT cases
    pytest evaluation/test_golden_cases.py -v -k "HALLUC"    # Run only hallucination cases
"""

import pytest
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.pipeline.run_full_audit import AuditPipeline
from evaluation.harness import evaluate_case


# Load golden cases
GOLDEN_PATH = Path(__file__).parent / "golden_cases.json"
with open(GOLDEN_PATH) as f:
    GOLDEN_DATA = json.load(f)
    GOLDEN_CASES = GOLDEN_DATA.get("cases", [])


# Create shared pipeline instance (expensive to initialize)
@pytest.fixture(scope="module")
def pipeline():
    return AuditPipeline()


def case_ids():
    """Generate test IDs from golden cases."""
    return [case["case_id"] for case in GOLDEN_CASES]


def get_case_by_id(case_id: str) -> dict:
    """Retrieve a golden case by ID."""
    for case in GOLDEN_CASES:
        if case["case_id"] == case_id:
            return case
    raise ValueError(f"Case not found: {case_id}")


class TestGoldenCases:
    """Test class for golden evaluation cases."""

    @pytest.fixture(autouse=True)
    def setup(self, pipeline):
        self.pipeline = pipeline

    @pytest.mark.parametrize("case_id", case_ids())
    def test_golden_case(self, case_id):
        """Run a single golden test case."""
        case = get_case_by_id(case_id)
        result = evaluate_case(self.pipeline, case)

        # Build detailed failure message
        if not result.passed:
            msg_parts = [f"\nCase: {case_id}"]
            msg_parts.append(f"Input: {case['input_text']}")
            msg_parts.append(f"Category: {case.get('category')}")

            for error in result.errors:
                msg_parts.append(f"Error: {error}")

            if result.downgrade_reason:
                msg_parts.append(f"Blocking Phase: {result.downgrade_reason.phase.value}")
                msg_parts.append(f"Issue: {result.downgrade_reason.issue}")

            pytest.fail("\n".join(msg_parts))


class TestVerdictCategories:
    """Tests grouped by verdict type."""

    @pytest.fixture(autouse=True)
    def setup(self, pipeline):
        self.pipeline = pipeline

    def get_cases_by_category(self, category: str) -> list:
        return [c for c in GOLDEN_CASES if c.get("category") == category]

    def test_supported_verdicts(self):
        """All SUPPORTED test cases should pass."""
        cases = self.get_cases_by_category("verdict_supported")
        for case in cases:
            result = evaluate_case(self.pipeline, case)
            assert result.passed, f"{case['case_id']}: {result.errors}"

    def test_refuted_verdicts(self):
        """All REFUTED test cases should pass."""
        cases = self.get_cases_by_category("verdict_refuted")
        for case in cases:
            result = evaluate_case(self.pipeline, case)
            assert result.passed, f"{case['case_id']}: {result.errors}"

    def test_insufficient_verdicts(self):
        """All INSUFFICIENT_EVIDENCE test cases should pass."""
        cases = self.get_cases_by_category("verdict_insufficient")
        for case in cases:
            result = evaluate_case(self.pipeline, case)
            assert result.passed, f"{case['case_id']}: {result.errors}"

    def test_uncertain_verdicts(self):
        """All UNCERTAIN test cases should pass."""
        cases = self.get_cases_by_category("verdict_uncertain")
        for case in cases:
            result = evaluate_case(self.pipeline, case)
            assert result.passed, f"{case['case_id']}: {result.errors}"


class TestHallucinationDetection:
    """Tests for specific hallucination type detection."""

    @pytest.fixture(autouse=True)
    def setup(self, pipeline):
        self.pipeline = pipeline

    def get_hallucination_cases(self) -> list:
        return [c for c in GOLDEN_CASES if c.get("category", "").startswith("hallucination_")]

    def test_all_hallucination_types_detected(self):
        """Verify all expected hallucination types are detected."""
        cases = self.get_hallucination_cases()
        for case in cases:
            result = evaluate_case(self.pipeline, case)
            expected_types = case["expected"].get("hallucination_types", [])
            for ht in expected_types:
                assert ht in result.actual_hallucinations, (
                    f"{case['case_id']}: Expected {ht} not detected. "
                    f"Got: {result.actual_hallucinations}"
                )


class TestDowngradeChains:
    """Tests for downgrade reason tracking."""

    @pytest.fixture(autouse=True)
    def setup(self, pipeline):
        self.pipeline = pipeline

    def get_downgrade_cases(self) -> list:
        return [c for c in GOLDEN_CASES if c.get("category") == "downgrade_chain"]

    def test_downgrade_reasons_captured(self):
        """Verify downgrade reasons are properly captured."""
        cases = self.get_downgrade_cases()
        for case in cases:
            result = evaluate_case(self.pipeline, case)
            assert result.downgrade_reason is not None, (
                f"{case['case_id']}: No downgrade reason captured"
            )

            # Check expected phase if specified
            expected_reason = case["expected"].get("downgrade_reason", {})
            if "phase" in expected_reason:
                assert result.downgrade_reason.phase.value == expected_reason["phase"], (
                    f"{case['case_id']}: Expected phase {expected_reason['phase']}, "
                    f"got {result.downgrade_reason.phase.value}"
                )


class TestRiskCalculation:
    """Tests for risk score and level calculation."""

    @pytest.fixture(autouse=True)
    def setup(self, pipeline):
        self.pipeline = pipeline

    def get_risk_cases(self) -> list:
        return [c for c in GOLDEN_CASES if c.get("category") == "risk_calculation"]

    def test_risk_levels(self):
        """Verify risk levels are correctly calculated."""
        cases = self.get_risk_cases()
        for case in cases:
            result = evaluate_case(self.pipeline, case)
            expected_risk = case["expected"].get("risk_level")
            if expected_risk:
                assert result.actual_risk == expected_risk, (
                    f"{case['case_id']}: Expected risk {expected_risk}, "
                    f"got {result.actual_risk}"
                )


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.fixture(autouse=True)
    def setup(self, pipeline):
        self.pipeline = pipeline

    def get_edge_cases(self) -> list:
        return [c for c in GOLDEN_CASES if c.get("category") == "edge_case"]

    def test_edge_cases(self):
        """Verify edge cases are handled correctly."""
        cases = self.get_edge_cases()
        for case in cases:
            result = evaluate_case(self.pipeline, case)
            assert result.passed, f"{case['case_id']}: {result.errors}"


class TestDeterminism:
    """Tests for pipeline determinism."""

    @pytest.fixture(autouse=True)
    def setup(self, pipeline):
        self.pipeline = pipeline

    def test_repeated_runs_same_result(self):
        """Same input should produce identical output."""
        test_text = "Apple was founded in 1976."

        result1 = self.pipeline.run(test_text)
        result2 = self.pipeline.run(test_text)

        # Compare verdicts
        claims1 = result1.get("claims", [])
        claims2 = result2.get("claims", [])

        assert len(claims1) == len(claims2), "Claim count differs between runs"

        for c1, c2 in zip(claims1, claims2):
            v1 = c1.get("verification", {}).get("verdict")
            v2 = c2.get("verification", {}).get("verdict")
            assert v1 == v2, f"Verdict differs: {v1} vs {v2}"

            conf1 = c1.get("verification", {}).get("confidence")
            conf2 = c2.get("verification", {}).get("confidence")
            assert conf1 == conf2, f"Confidence differs: {conf1} vs {conf2}"
