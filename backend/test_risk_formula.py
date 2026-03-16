
import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from core.risk_aggregator import RiskAggregator

class TestRiskFormula(unittest.TestCase):
    def setUp(self):
        self.aggregator = RiskAggregator()

    def test_all_verified(self):
        claims = [{"verification": {"verdict": "SUPPORTED"}} for _ in range(5)]
        result = self.aggregator.calculate_risk([], claims)
        self.assertEqual(result["hallucination_score"], 0.0)

    def test_all_uncertain_large(self):
        claims = [{"verification": {"verdict": "UNCERTAIN"}} for _ in range(5)]
        result = self.aggregator.calculate_risk([], claims)
        # Score = 0.3 * 1.0 = 0.30
        self.assertAlmostEqual(result["hallucination_score"], 0.30)

    def test_one_refuted_five_total(self):
        claims = [{"verification": {"verdict": "SUPPORTED"}} for _ in range(4)]
        claims.append({"verification": {"verdict": "REFUTED"}})
        result = self.aggregator.calculate_risk([], claims)
        # T=5. r=0.2. Score=0.2.
        self.assertAlmostEqual(result["hallucination_score"], 0.20)

    def test_one_refuted_two_total_dampened(self):
        claims = [
            {"verification": {"verdict": "SUPPORTED"}},
            {"verification": {"verdict": "REFUTED"}}
        ]
        result = self.aggregator.calculate_risk([], claims)
        # Small-sample floor keeps a refuted claim from collapsing to LOW risk.
        self.assertAlmostEqual(result["hallucination_score"], 0.625)
        self.assertEqual(result["overall_risk"], "HIGH")

    def test_mixed_scenario_dampened(self):
        """Small-sample mixed scenario should still reflect the refuted claim materially."""
        claims = [
            {"verification": {"verdict": "REFUTED"}},
            {"verification": {"verdict": "UNCERTAIN"}},
            {"verification": {"verdict": "SUPPORTED"}}
        ]
        result = self.aggregator.calculate_risk([], claims)
        self.assertAlmostEqual(result["hallucination_score"], 0.5667, delta=0.01)
        self.assertEqual(result["overall_risk"], "HIGH")

    def test_single_insufficient_claim_is_not_low(self):
        claims = [{"verification": {"verdict": "INSUFFICIENT_EVIDENCE"}}]
        result = self.aggregator.calculate_risk([], claims)
        self.assertAlmostEqual(result["hallucination_score"], 0.42, delta=0.01)
        self.assertEqual(result["overall_risk"], "MEDIUM")

    def test_single_refuted_claim_is_high_risk(self):
        claims = [{"verification": {"verdict": "REFUTED"}}]
        result = self.aggregator.calculate_risk([], claims)
        self.assertAlmostEqual(result["hallucination_score"], 0.80, delta=0.01)
        self.assertEqual(result["overall_risk"], "HIGH")

    def test_multiple_refuted_large(self):
        """Strict Math: T=10, R=4 -> r=0.4 -> Score=0.4"""
        claims = [{"verification": {"verdict": "REFUTED"}} for _ in range(4)]
        claims += [{"verification": {"verdict": "SUPPORTED"}} for _ in range(6)]
        result = self.aggregator.calculate_risk([], claims)
        self.assertAlmostEqual(result["hallucination_score"], 0.40)

if __name__ == '__main__':
    unittest.main()
