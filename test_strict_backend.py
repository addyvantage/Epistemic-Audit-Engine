import unittest
from alignment_scorer import AlignmentScorer
from hallucination_attributor import HallucinationAttributor
from config.core_config import (
    ALIGN_THRESH_SIM_HIGH, ALIGN_THRESH_ENT_MED, 
    HALLUCINATION_TYPE_CONTRADICTION
)

class TestStrictBackend(unittest.TestCase):
    
    def setUp(self):
        self.scorer = AlignmentScorer()
        self.attributor = HallucinationAttributor()
        
    def test_alignment_scorer_support(self):
        """Test Strong Support Trigger"""
        # High Sim + Medium Entailment
        ev = {"score": ALIGN_THRESH_SIM_HIGH}
        nli = {"entailment": ALIGN_THRESH_ENT_MED + 0.01, "contradiction": 0.0, "neutral": 0.0}
        
        res = self.scorer.score_alignment("claim", ev, nli)
        self.assertEqual(res["signal"], "SUPPORT")
        self.assertGreater(res["score"], 0.6) # Combined
        
    def test_alignment_scorer_contradiction(self):
        """Test Contradiction Trigger"""
        ev = {"score": 0.5}
        nli = {"entailment": 0.0, "contradiction": 0.8, "neutral": 0.2}
        
        res = self.scorer.score_alignment("claim", ev, nli)
        self.assertEqual(res["signal"], "CONTRADICTION")
        
    def test_alignment_scorer_neutral(self):
        """Test Neutral/Insufficient"""
        ev = {"score": 0.4} # Low sim
        nli = {"entailment": 0.1, "contradiction": 0.1, "neutral": 0.8}
        
        res = self.scorer.score_alignment("claim", ev, nli)
        self.assertEqual(res["signal"], "NEUTRAL")

    def test_attribution_trigger(self):
        """Test Hallucination Attribution"""
        align_res = {"signal": "CONTRADICTION", "score": 0.9}
        ev = {"evidence_id": "test_ev_1", "snippet": "Evidence says no."}
        
        flag = self.attributor.attribute(align_res, ev)
        self.assertIsNotNone(flag)
        self.assertEqual(flag["hallucination_type"], HALLUCINATION_TYPE_CONTRADICTION)
        self.assertEqual(flag["evidence_ref"], "test_ev_1")
        
    def test_attribution_no_trigger(self):
        align_res = {"signal": "SUPPORT", "score": 0.9}
        ev = {"evidence_id": "test_ev_1", "snippet": "Evidence says yes."}
        
        flag = self.attributor.attribute(align_res, ev)
        self.assertIsNone(flag)

class TestEndToEndIntegration(unittest.TestCase):
    def test_pipeline_instantiation(self):
        """Verify pipeline loads with new modules"""
        from backend.pipeline.run_full_audit import AuditPipeline
        try:
            pipeline = AuditPipeline()
            self.assertTrue(hasattr(pipeline.verifier, "alignment_scorer"))
            self.assertTrue(hasattr(pipeline.verifier, "attributor"))
        except Exception as e:
            self.fail(f"Pipeline instantiation failed: {e}")

if __name__ == "__main__":
    unittest.main()
