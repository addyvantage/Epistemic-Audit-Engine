import sys
import os
import json
import random
import time
from typing import Dict, Any, Optional, List
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Core imports (Clean relative-to-root via 'core' package)
from core.claim_extractor import ClaimExtractor
from core.entity_linker import EntityLinker
from core.evidence_retriever import EvidenceRetriever
from core.claim_verifier import ClaimVerifier
from core.hallucination_detector import HallucinationDetector
from core.risk_aggregator import RiskAggregator
from core.entity_context import EntityContext

class AuditPipeline:
    def __init__(self, config_path: str = None):
        logger.info("Loading Pipeline Components...")
        
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
        
        self.risk_aggregator = RiskAggregator()
        
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
        
        self.risk_aggregator = RiskAggregator()
        
        logger.info("Pipeline Ready.")

    def _load_config(self, path: str = None) -> Dict[str, Any]:
        default_path = os.path.join(os.path.dirname(__file__), "../../config/reproducibility.json")
        target_path = path or default_path
        if os.path.exists(target_path):
            try:
                with open(target_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Warning: Failed to load config from {target_path}: {e}")
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
        logger.info(f"Global seed set to {seed} (Deterministic Mode)")

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
        logger.info(f"Phase 1: Extraction ({len(text)} chars)...")
        p1 = self.extractor.extract(text)
        p1["pipeline_config"] = pipeline_config
        p1["metadata"]["mode"] = mode

        # Phase 1.5: Initialize Entity Context (v1.4)
        # The EntityContext tracks named entities across the document for coreference resolution.
        # This enables generic references like "the company" to resolve to previously mentioned entities.
        entity_context = EntityContext()
        self.linker.set_context(entity_context)

        # Phase 2: Linking with Entity Context
        logger.info("Phase 2: Linking...")

        # Two-pass linking for coreference support:
        # Pass 1: Link claims to gather named entities
        # Pass 2: Entity context is populated, coreference can resolve generic references
        #
        # Implementation: We process claims in order, registering resolved entities
        # to the context after each claim. This allows later claims to reference
        # entities introduced earlier in the document.
        linked_claims = []
        for claim in p1.get("claims", []):
            # Link this claim (may use context for generic references)
            linked_result = self.linker.link_claims({"claims": [claim]})
            linked_claim = linked_result["claims"][0]

            # Register resolved entities to context for subsequent claims
            subj_ent = linked_claim.get("subject_entity", {})
            if subj_ent.get("resolution_status") in ["RESOLVED", "RESOLVED_SOFT"]:
                entity_context.register_entity(subj_ent, claim.get("sentence_id", 0))

            obj_ent = linked_claim.get("object_entity", {})
            if obj_ent and obj_ent.get("resolution_status") in ["RESOLVED", "RESOLVED_SOFT"]:
                entity_context.register_entity(obj_ent, claim.get("sentence_id", 0))

            linked_claims.append(linked_claim)

        p2 = {"claims": linked_claims, "metadata": p1.get("metadata", {})}
        p2["pipeline_config"] = pipeline_config

        # Clear context after linking (optional, for memory)
        self.linker.clear_context()
        
        # Phase 3: Evidence
        logger.info("Phase 3: Evidence...")
        
        # Pre-Filter (v1.2 Performance)
        claims_to_retrieve = []
        skipped_claims = []
        
        logger.info("Running Structural Pre-Filter...")
        for claim in p2.get("claims", []):
            structural_h = self.detector.detect_structural(claim)
            if structural_h:
                # Direct Refutation from Structure
                # We skip evidence retrieval for these to save time/cost.
                claim["evidence"] = {"wikidata": [], "wikipedia": [], "grokipedia": [], "primary_document": []}
                # We can pre-fill verification data, but Verifier will re-run detection.
                # However, Verifier needs 'hallucinations' key populated if we want it to skip hard work?
                # Actually, Verifier calls detector.detect() which includes structural checks.
                # So we just empty evidence and let Verifier handle it.
                skipped_claims.append(claim)
            else:
                claims_to_retrieve.append(claim)
                
        logger.info(f"Pre-filtered {len(skipped_claims)} claims (Structural Hallucinations). Retrieving {len(claims_to_retrieve)} claims.")
        
        # Create temp input for retriever
        p2_filtered = {"claims": claims_to_retrieve, "metadata": p2.get("metadata", {}), "pipeline_config": pipeline_config}
        
        p3 = self.retriever.retrieve_evidence(p2_filtered)
        
        # Re-merge
        p3["claims"].extend(skipped_claims)
        p3["pipeline_config"] = pipeline_config
        
        # Phase 4: Verification
        logger.info("Phase 4: Verification...")
        p4 = self.verifier.verify_claims(p3)
        p4["pipeline_config"] = pipeline_config
        
        # Phase 5: Hallucination Detection (Merged into Phase 4)
        # claim_verifier now handles detection to inform verdicts.
        # We skip separate detection step.
        logger.info("Phase 5: Hallucinations (Merged)...")
            
        final_claims = []
        disable_canonical = ablation_config.get("disable_canonical_override", False)

        for claim in p4.get("claims", []):
            cid = claim.get("claim_id")
            
            # Stabilization Logic (Fix 3 & 5)
            verdict = claim.get("verification", {}).get("verdict")
            subj = claim.get("subject_entity", {})
            is_resolved = subj.get("resolution_status") in ["RESOLVED", "RESOLVED_SOFT", "RESOLVED_COREF"]
            
            canonical_predicates = ["founded", "founder", "launched", "released", "created", "born", "died", "established", "inception"]
            is_canonical = any(k in claim.get("predicate", "").lower() for k in canonical_predicates)
            is_temporal = claim.get("claim_type") == "TEMPORAL"
            
            # Preserve hallucinations from Verifier
            hallucinations = claim.get("hallucinations", [])
            
            # Global Override (Fix 3 & 4) - REMOVED for v1.1 Hardening
            # Principle: Absence of evidence != Evidence.
            # We do not upgrade INSUFFICIENT to SUPPORTED just because it sounds canonical.
            
            # Fix 4: Safety Check against Authorized Temporal Contradiction (Keep?)
            # If verdict is SUPPORTED (via normal means), check temporal.
            if is_canonical and is_temporal and verdict == "SUPPORTED" and claim.get("verification", {}).get("used_evidence_ids"):
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
            
            # Key based on IDs if resolved, else text (v1.4: include RESOLVED_COREF)
            valid_statuses = ["RESOLVED", "RESOLVED_SOFT", "RESOLVED_COREF"]
            sid = subj.get("entity_id") if subj.get("resolution_status") in valid_statuses else c.get("subject", "").lower()
            oid = obj.get("entity_id") if obj and obj.get("resolution_status") in valid_statuses else c.get("object", "").lower()
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
            # Narrowed Guard (Fix Epistemic Violation)
            # It is illegal to Refute a claim that has Support UNLESS a Critical Hallucination exists.
            has_critical = any(h.get("severity") == "CRITICAL" for h in c.get("hallucinations", []))
            
            if verdict == "REFUTED" and has_support and not has_critical:
                 # This is the forbidden state: Refuted despite support, and no critical override.
                 raise RuntimeError(f"Epistemic violation: Refuted despite authoritative support without Critical Hallucination. Claim ID: {c.get('claim_id')}")
                
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

        # 4. Canonical Risk Contract (v1.3.9)
        risk_result = self.risk_aggregator.calculate_risk([], final_claims)

        return {
            "overall_risk": risk_result["overall_risk"],
            "hallucination_score": risk_result["hallucination_score"],
            "summary": risk_result["summary"],
            "claims": final_claims
        }
