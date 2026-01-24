
import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from risk_aggregator import RiskAggregator

class TestRiskContract(unittest.TestCase):
    def setUp(self):
        self.aggregator = RiskAggregator()

    def test_label_matches_score_invariant(self):
        """
        Invariant: Label must ALWAYS match score threshold.
        <= 0.20 -> LOW
        <= 0.50 -> MEDIUM
        > 0.50 -> HIGH
        """
        test_cases = [
            (0.00, "LOW"),
            (0.15, "LOW"),
            (0.20, "LOW"),
            (0.201, "MEDIUM"), # Boundary check
            (0.21, "MEDIUM"),
            (0.30, "MEDIUM"),
            (0.50, "MEDIUM"),
            (0.51, "HIGH"),    # Boundary check
            (0.60, "HIGH"),
            (0.85, "HIGH"),
            (1.00, "HIGH")
        ]

        for score, expected_label in test_cases:
            # We bypass calculate_risk logic and test the helper strictly first
            label = self.aggregator.get_risk_label(score)
            self.assertEqual(label, expected_label, f"Invariant failed for score {score}")

    def test_calculate_risk_structure_contract(self):
        """
        Contract: Response must contain specific keys and match structure.
        """
        # Mock claims to generate a score (1 Refuted / 5 Total = 0.20 -> LOW)
        claims = [{"verification": {"verdict": "SUPPORTED"}} for _ in range(4)]
        claims.append({"verification": {"verdict": "REFUTED"}})
        
        result = self.aggregator.calculate_risk([], claims)
        
        # Keys
        self.assertIn("overall_risk", result)
        self.assertIn("hallucination_score", result)
        self.assertIn("summary", result)
        
        # Values
        self.assertIsInstance(result["hallucination_score"], float)
        self.assertIsInstance(result["overall_risk"], str)
        self.assertIsInstance(result["summary"], dict)
        
        # Invariant Check on Result
        self.assertEqual(result["overall_risk"], "LOW")
        self.assertAlmostEqual(result["hallucination_score"], 0.20)
        self.assertEqual(result["summary"]["epistemic_claims"], 5)

if __name__ == '__main__':
    unittest.main()
