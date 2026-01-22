import unittest
from hallucination_detector import HallucinationDetector

class TestPhase5Hallucinations(unittest.TestCase):
    def setUp(self):
        self.detector = HallucinationDetector()

    def test_h1_unsupported_assertion(self):
        # Verdict Insufficient + High Absolutism
        claim = {
            "claim_id": "c1",
            "confidence_linguistic": {"absolutism": 0.9, "hedging": 0.0},
            "verification": {"verdict": "INSUFFICIENT_EVIDENCE"}
        }
        res = self.detector.detect({"claims": [claim]})
        flags = res["flags"]
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0]["hallucination_type"], "H1")
        # Score check: H1 weight is 0.25 (High severity * 1.5) = 0.375?
        # Aggregator logic: W=0.25. Severity=HIGH -> Mult=1.5. Score = 0.375.
        self.assertAlmostEqual(res["hallucination_score"], 0.38, places=2)

    def test_h2_false_specificity(self):
        # Unsupported + Number. avoid H1 by High Hedging.
        claim = {
            "claim_id": "c2",
            "claim_text": "Founded in 1976",
            "confidence_linguistic": {"temporal_specificity": 1.0, "hedging": 1.0},
            "verification": {"verdict": "INSUFFICIENT_EVIDENCE"}
        }
        res = self.detector.detect({"claims": [claim]})
        flags = res["flags"]
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0]["hallucination_type"], "H2")

    def test_refuted_no_h2(self):
        # Refuted + Numeric -> Should NOT trigger H2 (Evidence exists but contradicts)
        claim = {
            "claim_id": "c2_ref",
            "claim_text": "Founded in 1999",
            "confidence_linguistic": {"temporal_specificity": 1.0},
            "verification": {"verdict": "REFUTED"}
        }
        res = self.detector.detect({"claims": [claim]})
        flags = res["flags"]
        # Should be 0 flags (H2 requires Insufficient)
        # H3 might trigger if Overconfident? Default modal is 0.0.
        self.assertEqual(len(flags), 0)

    def test_h3_overconfidence_refuted(self):
        # Refuted + High Modal -> H3 High
        claim = {
             "claim_id": "c3_ref",
             "confidence_linguistic": {"modal_strength": 0.9},
             "verification": {"verdict": "REFUTED"}
        }
        res = self.detector.detect({"claims": [claim]})
        flags = res["flags"]
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0]["hallucination_type"], "H3")
        self.assertEqual(flags[0]["severity"], "HIGH")

    def test_h4_illegitimate_inference(self):
        # Causal + Not Supported. Avoid H1.
        claim = {
            "claim_id": "c4",
            "claim_type": "CAUSAL",
            "confidence_linguistic": {"hedging": 1.0},
            "verification": {"verdict": "INSUFFICIENT_EVIDENCE"}
        }
        res = self.detector.detect({"claims": [claim]})
        flags = res["flags"]
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0]["hallucination_type"], "H4")

    def test_h5_inconsistency_resolved(self):
        # Two conflicting claims, but one IS SUPPORTED -> No Hallucination (Conflict resolved)
        c1 = {
            "claim_id": "c5a",
            "claim_type": "TEMPORAL",
            "subject_entity": {"entity_id": "Q1"},
            "predicate": "born",
            "object_entity": {"text": "1990"},
            "verification": {"verdict": "SUPPORTED"}
        }
        c2 = {
            "claim_id": "c5b",
            "claim_type": "TEMPORAL",
            "subject_entity": {"entity_id": "Q1"},
            "predicate": "born",
            "object_entity": {"text": "1991"},
            "verification": {"verdict": "REFUTED"}
        }
        res = self.detector.detect({"claims": [c1, c2]})
        flags = res["flags"]
        self.assertEqual(len(flags), 0)

    def test_h6_narrative_laundering(self):
        # Insufficient + Grokipedia + High Absolutism
        claim = {
            "claim_id": "c6",
            "evidence": {"grokipedia": [1]},
            "confidence_linguistic": {"absolutism": 0.8},
            "verification": {"verdict": "INSUFFICIENT_EVIDENCE"}
        }
        res = self.detector.detect({"claims": [claim]})
        flags = res["flags"]
        types = [f["hallucination_type"] for f in flags]
        self.assertIn("H6", types)

    def test_risk_saturation(self):
        # Add many H1 flags. Weight 0.25 * 1.5 = 0.375.
        # 3 flags -> 0.375 / 1 + ...
        # Standard sum > 1.0. Diminishing returns < Sum?
        # Just check it works and is capped.
        claim = {
            "claim_id": "c1",
            "confidence_linguistic": {"absolutism": 0.9, "hedging": 0.0},
            "verification": {"verdict": "INSUFFICIENT_EVIDENCE"}
        }
        # Detect for 5 identical claims
        res = self.detector.detect({"claims": [claim]*5})
        score = res["hallucination_score"]
        self.assertLessEqual(score, 1.0)
        self.assertGreater(score, 0.5)

if __name__ == "__main__":
    unittest.main()
