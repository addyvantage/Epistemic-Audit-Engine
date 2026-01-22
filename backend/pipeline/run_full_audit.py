import sys
import os
import json
import random
import time
from typing import Dict, Any, Optional

# Add root directory to path to import Phase 1-5 modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from claim_extractor import ClaimExtractor
from entity_linker import EntityLinker
from evidence_retriever import EvidenceRetriever
from claim_verifier import ClaimVerifier
from hallucination_detector import HallucinationDetector

class AuditPipeline:
    def __init__(self, config_path: str = None):
        print("Loading Pipeline Components...")
        
        # Load Config
        self.config = self._load_config(config_path)
        
        # Reproducibility (Phase 1.2)
        if self.config.get("reproducibility", {}).get("deterministic", True):
            seed = self.config.get("reproducibility", {}).get("fixed_seed", 42)
            self._seed_everything(seed)
            
        self.extractor = ClaimExtractor()
        # Defensive assertion for API compatibility
        assert (
            hasattr(self.extractor, "extract")
            or hasattr(self.extractor, "run")
        ), "ClaimExtractor API mismatch: expected extract() or run()"
        
        self.linker = EntityLinker()
        assert hasattr(self.linker, "link_claims"), "EntityLinker API mismatch: expected link_claims()"
        
        self.retriever = EvidenceRetriever()
        assert hasattr(self.retriever, "retrieve_evidence"), "EvidenceRetriever API mismatch: expected retrieve_evidence()"
        
        self.verifier = ClaimVerifier()
        assert hasattr(self.verifier, "verify_claims"), "ClaimVerifier API mismatch: expected verify_claims()"
        
        self.detector = HallucinationDetector()
        assert hasattr(self.detector, "detect"), "HallucinationDetector API mismatch: expected detect()"
        
        print("Pipeline Ready.")

    def _load_config(self, path: str = None) -> Dict[str, Any]:
        default_path = os.path.join(os.path.dirname(__file__), "../../config/reproducibility.json")
        target_path = path or default_path
        if os.path.exists(target_path):
            try:
                with open(target_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load config from {target_path}: {e}")
        return {"reproducibility": {"deterministic": True, "fixed_seed": 42}, "ablation": {}}

    def _seed_everything(self, seed: int):
        random.seed(seed)
        try:
            import numpy as np
            np.random.seed(seed)
        except ImportError:
            pass
        try:
            import torch
            torch.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
        except ImportError:
            pass
        os.environ["PYTHONHASHSEED"] = str(seed)
        print(f"Global seed set to {seed} (Deterministic Mode)")

    def run(self, text: str, mode: str = "research", ablation_overrides: Dict[str, bool] = None) -> Dict[str, Any]:
        # Merge config
        repro_config = self.config.get("reproducibility", {})
        ablation_config = self.config.get("ablation", {}).copy()
        if ablation_overrides:
            ablation_config.update(ablation_overrides)
        
        pipeline_config = {
            "mode": mode,
            "ablation": ablation_config,
            "reproducibility": repro_config
        }

        # Phase 1: Extraction
        print(f"Phase 1: Extraction ({len(text)} chars)...")
        p1 = self.extractor.extract(text)
        p1["pipeline_config"] = pipeline_config
        p1["metadata"]["mode"] = mode
        
        # Phase 2: Linking
        print("Phase 2: Linking...")
        p2 = self.linker.link_claims(p1)
        p2["pipeline_config"] = pipeline_config
        
        # Phase 3: Evidence
        print("Phase 3: Evidence...")
        p3 = self.retriever.retrieve_evidence(p2)
        p3["pipeline_config"] = pipeline_config
        
        # Phase 4: Verification
        print("Phase 4: Verification...")
        p4 = self.verifier.verify_claims(p3)
        p4["pipeline_config"] = pipeline_config
        
        # Phase 5: Hallucination Detection
        print("Phase 5: Hallucinations...")
        p5 = self.detector.detect(p4)
        
        # Merge Claims from P4 (which has verification) with Hallucination Flags from P5
        # P5 Output structure: {"overall_risk":..., "hallucination_score":..., "flags":..., "summary":...}
        # We want to return the Full Claim List enhanced with everything.
        # P5 logic reads P4 but output structure is Hallucinations Report.
        # We need to construct the Final Response merging Claims + Hallucinations.
        
        # Let's map flags to claim_ids
        flags_by_id = {}
        for flag in p5.get("flags", []):
            cid = flag.get("claim_id")
            if cid not in flags_by_id: flags_by_id[cid] = []
            flags_by_id[cid].append(flag)
            
        final_claims = []
        disable_canonical = ablation_config.get("disable_canonical_override", False)

        for claim in p4.get("claims", []):
            cid = claim.get("claim_id")
            
            # Stabilization Logic (Fix 3 & 5)
            verdict = claim.get("verification", {}).get("verdict")
            subj = claim.get("subject_entity", {})
            is_resolved = subj.get("resolution_status") in ["RESOLVED", "RESOLVED_SOFT"]
            
            canonical_predicates = ["founded", "founder", "launched", "released", "created", "born", "died", "established", "inception"]
            is_canonical = any(k in claim.get("predicate", "").lower() for k in canonical_predicates)
            is_temporal = claim.get("claim_type") == "TEMPORAL"
            
            hallucinations = flags_by_id.get(cid, [])
            
            # Global Override (Fix 3 & 4) - Subject to Ablation
            if is_resolved and not disable_canonical:
                # Fix 3: Override Wrong Refutations for Canonical Facts
                # Fix B (User Request): Only override INSUFFICIENT, never REFUTED (Epistemic Safety).
                if is_canonical and verdict == "INSUFFICIENT_EVIDENCE":
                    claim["verification"]["verdict"] = "SUPPORTED"
                    claim["verification"]["reasoning"] = "Canonical fact (Global Safety Override)"
                    claim["verification"]["confidence"] = max(claim["verification"].get("confidence", 0.0), 0.75)
                    # Strip epistemic misrepresentation flags
                    hallucinations = [h for h in hallucinations if h["hallucination_type"] not in ["H1", "H2", "H3"]]
                
                elif is_temporal and verdict == "INSUFFICIENT_EVIDENCE":
                    claim["verification"]["verdict"] = "SUPPORTED_WEAK"
                    claim["verification"]["reasoning"] = "Temporal fact; evidence gating upstream"
                    hallucinations = [h for h in hallucinations if h["hallucination_type"] not in ["H1", "H2", "H3"]]

                # Fix 4: Safety Check against Authorized Temporal Contradiction
                if is_canonical and is_temporal and claim["verification"]["verdict"] == "SUPPORTED" and claim["verification"].get("used_evidence_ids"):
                     # Check for strict temporal mismatch in used evidence or all evidence?
                     # Prompt says "for ev in claim.get('evidence', {}).get('WIKIDATA', [])..."
                     for ev in claim.get("evidence", {}).get("WIKIDATA", []):
                         if ev.get("alignment", {}).get("temporal_match") is False:
                             claim["verification"]["verdict"] = "REFUTED"
                             claim["verification"]["confidence"] = 0.9
                             claim["verification"]["reasoning"] = "Contradicted by authoritative temporal record"
                             break

            claim["hallucinations"] = hallucinations
            final_claims.append(claim)
            
        # Fix 7: Deduplication
        deduped = []
        seen_keys = set()
        for c in final_claims:
            subj = c.get("subject_entity", {})
            obj = c.get("object_entity", {})
            
            # Key based on IDs if resolved, else text
            sid = subj.get("entity_id") if subj.get("resolution_status") in ["RESOLVED", "RESOLVED_SOFT"] else c.get("subject", "").lower()
            oid = obj.get("entity_id") if obj and obj.get("resolution_status") in ["RESOLVED", "RESOLVED_SOFT"] else c.get("object", "").lower()
            pred = c.get("predicate", "").lower()
            
            key = (sid, pred, oid)
            if key in seen_keys:
                continue
            
            seen_keys.add(key)
            deduped.append(c)
            
        final_claims = deduped

        # Fix 8: Final Guarantee Assertions (Phase 4.2)
        canonical_predicates = ["founded", "founder", "launched", "released", "created", "born", "died", "established", "inception"]
        
        for c in final_claims:
            v = c.get("verification", {})
            verdict = v.get("verdict")
            has_support = len(v.get("used_evidence_ids", [])) > 0
            
            is_canonical = any(k in c.get("predicate", "").lower() for k in canonical_predicates)
            
            # 1. Evidence Consistency
            if verdict == "REFUTED" and has_support:
                raise RuntimeError(f"Epistemic violation: Refuted despite authoritative support. Claim ID: {c.get('claim_id')}")
                
            if verdict == "SUPPORTED" and not has_support and not is_canonical:
                 # Note: SUPPORTED_WEAK is allowed to have no support if it's temporal? No, only canonicals/temporals via override.
                 # But override sets them to SUPPORTED/SUPPORTED_WEAK.
                 # If verdict is explicitly SUPPORTED (Emerald), it MUST have evidence OR be Canonical Override.
                 # If it is SUPPORTED_WEAK, it might be Temporal Override (which is fine).
                 # Assertion says "No SUPPORTED claim". Does it include WEAK?
                 # "No SUPPORTED claim has zero evidence unless explicitly canonical".
                 # I'll check strict "SUPPORTED".
                 raise RuntimeError(f"Epistemic violation: Supported claim with no evidence and not canonical. Claim ID: {c.get('claim_id')}")

            # 2. Confidence Consistency
            conf = v.get("confidence", 0.0)
            if verdict == "SUPPORTED" and conf == 0.0:
                 raise RuntimeError(f"Epistemic violation: Green verdict (SUPPORTED) with 0.00 confidence. Claim ID: {c.get('claim_id')}")

            # 3. Hallucination Consistency
            h_types = [h["hallucination_type"] for h in c.get("hallucinations", [])]
            if verdict == "SUPPORTED" and "H1" in h_types:
                 raise RuntimeError(f"Epistemic violation: Supported claim flagged as Unsupported (H1). Claim ID: {c.get('claim_id')}")

        return {
            "overall_risk": p5.get("overall_risk"),
            "hallucination_score": p5.get("hallucination_score"),
            "summary": p5.get("summary"),
            "claims": final_claims
        }
