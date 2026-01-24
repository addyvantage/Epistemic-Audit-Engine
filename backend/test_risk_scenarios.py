
import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from risk_aggregator import RiskAggregator

class TestRiskScenarios(unittest.TestCase):
    def setUp(self):
        self.aggregator = RiskAggregator()

    def test_scenarios(self):
        # 1. All Supported
        claims = [{"verification": {"verdict": "SUPPORTED"}} for _ in range(5)]
        res = self.aggregator.calculate_risk([], claims)
        self.assertEqual(res['hallucination_score'], 0.0)
        self.assertEqual(res['overall_risk'], "LOW")
        self.assertEqual(res['summary']['epistemic_claims'], 5)

        # 2. All Uncertain (T=5)
        claims = [{"verification": {"verdict": "UNCERTAIN"}} for _ in range(5)]
        res = self.aggregator.calculate_risk([], claims)
        self.assertEqual(res['hallucination_score'], 0.30)
        self.assertEqual(res['overall_risk'], "MEDIUM")
        self.assertEqual(res['summary']['epistemic_claims'], 5)

        # 3. 1 Refuted / 2 Total (Dampened)
        claims = [
            {"verification": {"verdict": "REFUTED"}},
            {"verification": {"verdict": "SUPPORTED"}}
        ]
        res = self.aggregator.calculate_risk([], claims)
        self.assertEqual(res['hallucination_score'], 0.20)
        self.assertEqual(res['overall_risk'], "LOW")
        self.assertEqual(res['summary']['epistemic_claims'], 2)

        # 4. Mixed (1R, 1U, 1S)
        claims = [
            {"verification": {"verdict": "REFUTED"}},
            {"verification": {"verdict": "UNCERTAIN"}},
            {"verification": {"verdict": "SUPPORTED"}}
        ]
        res = self.aggregator.calculate_risk([], claims)
        self.assertEqual(res['hallucination_score'], 0.26)
        self.assertEqual(res['overall_risk'], "MEDIUM")
        self.assertEqual(res['summary']['epistemic_claims'], 3)

if __name__ == "__main__":
    unittest.main()
