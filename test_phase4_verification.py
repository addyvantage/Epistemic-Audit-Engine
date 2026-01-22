import unittest
from unittest.mock import MagicMock, patch
from claim_verifier import ClaimVerifier

class TestPhase4Verification(unittest.TestCase):
    def setUp(self):
        self.verifier = ClaimVerifier()

    def test_temporal_contradiction(self):
        # Claim: Founded in 1977. Evidence: 1976. (Phase 3 would mark temporal_match=False)
        claim = {
            "claim_text": "Founded in 1977",
            "claim_type": "TEMPORAL",
            "evidence": {
                "wikidata": [{
                    "source": "WIKIDATA", 
                    "evidence_id": "ev1",
                    "alignment": {"subject_match": True, "predicate_match": True, "temporal_match": False} 
                }]
            }
        }
        res = self.verifier._verify_single_claim(claim)
        self.assertEqual(res["verification"]["verdict"], "REFUTED")
        self.assertIn("ev1", res["verification"]["contradicted_by"])

    def test_relation_support(self):
        # Wikidata support
        claim = {
            "claim_type": "RELATION",
            "evidence": {
                "wikidata": [{
                    "source": "WIKIDATA", 
                    "evidence_id": "ev2",
                    "alignment": {"subject_match": True, "predicate_match": True, "object_match": True} 
                }]
            }
        }
        res = self.verifier._verify_single_claim(claim)
        self.assertEqual(res["verification"]["verdict"], "SUPPORTED")
        self.assertIn("ev2", res["verification"]["used_evidence_ids"])

    def test_narrative_only(self):
        # Only Grokipedia
        claim = {
            "claim_type": "RELATION",
            "evidence": {
                "grokipedia": [{"source": "GROKIPEDIA"}]
            }
        }
        res = self.verifier._verify_single_claim(claim)
        self.assertEqual(res["verification"]["verdict"], "INSUFFICIENT_EVIDENCE")
        self.assertIn("narrative", res["verification"]["reasoning"])

    def test_object_mismatch_refutes(self):
        # Relation claim where object explicitly contradicts (Different Entity)
        claim = {
            "claim_type": "RELATION",
            "evidence": {
                "wikidata": [{
                    "source": "WIKIDATA", 
                    "evidence_id": "ev3",
                    "value": "Q999", # Different QID
                    "alignment": {"subject_match": True, "predicate_match": True, "object_match": False} 
                }]
            }
        }
        res = self.verifier._verify_single_claim(claim)
        self.assertEqual(res["verification"]["verdict"], "REFUTED")

    def test_date_property_does_not_refute_relation(self):
        # Relation claim "Steve Jobs founded Apple"
        # Evidence: Apple inception date (P571). Value is Date.
        # This provides temporal info but shouldn't refute the "Who" relation.
        # It should actually SUPPORT the premise "Apple was founded" (Subject+Predicate match).
        claim = {
            "claim_type": "RELATION",
            "evidence": {
                "wikidata": [{
                    "source": "WIKIDATA", 
                    "evidence_id": "ev_date",
                    "value": "+1976-04-01T00:00:00Z", # Date value
                    "alignment": {"subject_match": True, "predicate_match": True, "object_match": False} # Mismatch only because value is date
                }]
            }
        }
        res = self.verifier._verify_single_claim(claim)
        self.assertEqual(res["verification"]["verdict"], "SUPPORTED")
        self.assertIn("ev_date", res["verification"]["used_evidence_ids"])

    def test_confidence_formula(self):
        # Base 0.6 + 0.15*1 + 0.1 (WD) = 0.85
        claim = {
            "confidence_linguistic": {"hedging": 0.0},
            "evidence": {
                "wikidata": [{
                    "source": "WIKIDATA", 
                    "evidence_id": "ev_conf",
                    "value": "Q123",
                    "alignment": {"subject_match": True, "predicate_match": True, "object_match": True} 
                }]
            }
        }
        res = self.verifier._verify_single_claim(claim)
        self.assertEqual(res["verification"]["verdict"], "SUPPORTED")
        self.assertAlmostEqual(res["verification"]["confidence"], 0.85)

        # With Hedging > 0.5 -> -0.2 -> 0.65
        claim["confidence_linguistic"]["hedging"] = 0.8
        res = self.verifier._verify_single_claim(claim)
        self.assertAlmostEqual(res["verification"]["confidence"], 0.65)

    @patch("nli_engine.NLIEngine.classify")
    def test_wikipedia_entailment(self, mock_classify):
        # Mock NLI Entailment
        mock_classify.return_value = {"entailment": 0.9, "contradiction": 0.05, "neutral": 0.05}
        
        claim = {
            "claim_text": "Steve Jobs founded Apple",
            "claim_type": "RELATION",
            "evidence": {
                "wikipedia": [{
                    "source": "WIKIPEDIA",
                    "sentence": "Steve Jobs founded Apple.",
                    "evidence_id": "ev4",
                    "alignment": {"subject_match": True, "predicate_match": True, "object_match": True}
                }]
            }
        }
        res = self.verifier._verify_single_claim(claim)
        self.assertEqual(res["verification"]["verdict"], "SUPPORTED")
        self.assertIn("ev4", res["verification"]["used_evidence_ids"])

    @patch("nli_engine.NLIEngine.classify")
    def test_wikipedia_contradiction(self, mock_classify):
        # Mock NLI Contradiction
        mock_classify.return_value = {"entailment": 0.05, "contradiction": 0.9, "neutral": 0.05}
        
        claim = {
            "claim_text": "Steve Jobs founded Apple",
            "claim_type": "RELATION",
            "evidence": {
                "wikipedia": [{
                    "source": "WIKIPEDIA",
                    "sentence": "Steve Jobs did not found Apple.",
                    "evidence_id": "ev5",
                    "alignment": {"subject_match": True, "predicate_match": True, "object_match": True}
                }]
            }
        }
        res = self.verifier._verify_single_claim(claim)
        self.assertEqual(res["verification"]["verdict"], "REFUTED")
        self.assertIn("ev5", res["verification"]["contradicted_by"])

if __name__ == "__main__":
    unittest.main()
