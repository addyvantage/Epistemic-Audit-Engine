from typing import Dict, Any, List
from hallucination_models import HallucinationFlag, HallucinationReport
from risk_aggregator import RiskAggregator
import re

class HallucinationDetector:
    def __init__(self):
        self.aggregator = RiskAggregator()

    def detect(self, phase4_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detects hallucinations in verified claims.
        """
        flags = []
        claims = phase4_output.get("claims", [])
        ablation = phase4_output.get("pipeline_config", {}).get("ablation", {})
        
        # 1. H5 Check (Global)
        flags.extend(self._detect_inconsistency(claims, ablation))
        
        # Per-claim checks
        for claim in claims:
            # Fix 1: Epistemic Polarity Classifier
            claim["epistemic_polarity"] = self._get_epistemic_polarity(claim.get("claim_text", ""))
            
            flags.extend(self._detect_unsupported_assertion(claim))
            flags.extend(self._detect_false_specificity(claim))
            flags.extend(self._detect_overconfidence(claim, ablation))
            flags.extend(self._detect_illegitimate_inference(claim))
            flags.extend(self._detect_narrative_laundering(claim))
            
        # Aggregate Risk
        risk_data = self.aggregator.calculate_risk(flags, claims, phase4_output.get("pipeline_config"))
        
        return {
            "overall_risk": risk_data["overall_risk"],
            "hallucination_score": risk_data["hallucination_score"],
            "flags": [self._flag_to_dict(f) for f in flags],
            "summary": risk_data["summary"],
            "pipeline_config": phase4_output.get("pipeline_config")
        }
    
    # ... _flag_to_dict ...

    # ... _detect_unsupported_assertion ...
    # ... _detect_false_specificity ...

    def _detect_overconfidence(self, claim: Dict[str, Any], ablation: Dict[str, bool] = {}) -> List[HallucinationFlag]:
        # H3: Strong Modal > 0.8 + Verdict Confidence < 0.8
        # Ablation check
        if ablation.get("disable_overconfidence"):
            return []

        # Fix 2: Meta-epistemic claims can NEVER trigger H3 (Overconfidence).
        if claim.get("epistemic_polarity") == "META_EPISTEMIC":
            return []

        # Fix: Do not trigger if entity is RESOLVED (Canonical Fact check).
        # Fix: Do not trigger if Refuted (Being wrong != Hallucinating).
        
        flags = []
        verdict = claim.get("verification", {}).get("verdict")
        if verdict == "REFUTED": return flags

        ling = claim.get("confidence_linguistic", {})
        modal = ling.get("modal_strength", 0.0)
        ver_conf = claim.get("verification", {}).get("confidence", 0.0)
        
        # Check for resolution status to avoid flagging canonical facts
        subj = claim.get("subject_entity", {})
        is_resolved = subj.get("resolution_status") in ["RESOLVED", "RESOLVED_SOFT"]
             
        if not is_resolved:
             if modal > 0.8 and ver_conf < 0.8:
                 flags.append(HallucinationFlag(
                    claim_id=claim.get("claim_id"),
                    hallucination_type="H3",
                    severity="MEDIUM",
                    reason="Overconfident Language",
                    explanation="Certainty of language exceeds strength of evidence.",
                    supporting_signals=[f"modal_strength={modal}", f"verification_confidence={ver_conf}"]
                ))
        return flags

    def _detect_inconsistency(self, claims: List[Dict[str, Any]], ablation: Dict[str, bool] = {}) -> List[HallucinationFlag]:
        # H5: Pairwise check. Same Subject + Predicate, Conflicting Object.
        if ablation.get("disable_cross_claim"):
            return []
            
        flags = []
        
        from collections import defaultdict
        grouped = defaultdict(list)
        
        for c in claims:
            if c.get("claim_type") == "RELATION" or c.get("claim_type") == "TEMPORAL":
                subj = c.get("subject_entity", {}).get("entity_id")
                pred = c.get("predicate", "").lower()
                if subj and pred:
                    grouped[(subj, pred)].append(c)
        
        for (subj, pred), group in grouped.items():
            if len(group) < 2: continue
            
            single_val_preds = ["born", "died", "inception", "founded on", "created on"]
            is_single = any(sv in pred for sv in single_val_preds) or (len(group) > 0 and group[0].get("claim_type") == "TEMPORAL")
            
            if is_single:
                vals = set()
                has_supported = False
                for c in group:
                    obj_txt = c.get("object_entity", {}).get("text", "").lower()
                    if obj_txt: vals.add(obj_txt)
                    if c.get("verification", {}).get("verdict") == "SUPPORTED":
                        has_supported = True
                
                # Rule: Inconsistency is Hallucination (Confusion) only if unresolved
                if len(vals) > 1 and not has_supported:
                    for c in group:
                         flags.append(HallucinationFlag(
                            claim_id=c.get("claim_id"),
                            hallucination_type="H5",
                            severity="HIGH",
                            reason="Cross-Claim Inconsistency",
                            explanation=f"Contradictory claims for {pred} regarding {subj} without resolution.",
                            supporting_signals=[f"conflicting_values={list(vals)}"]
                        ))
        return flags

    def _flag_to_dict(self, flag: HallucinationFlag) -> Dict[str, Any]:
        return {
            "claim_id": flag.claim_id,
            "hallucination_type": flag.hallucination_type,
            "severity": flag.severity,
            "reason": flag.reason,
            "explanation": flag.explanation,
            "supporting_signals": flag.supporting_signals
        }

    def _detect_unsupported_assertion(self, claim: Dict[str, Any]) -> List[HallucinationFlag]:
        # H1: Verdict=INSUFFICIENT + High Absolutism OR Low Hedging
        # Fix 3: Restrict H1 to object-level factual claims.
        if claim.get("epistemic_polarity") == "META_EPISTEMIC":
            return []
            
        flags = []
        verdict = claim.get("verification", {}).get("verdict")
        ling = claim.get("confidence_linguistic", {})
        
        if verdict == "INSUFFICIENT_EVIDENCE":
            # Fix: Do not trigger H1 if entities are resolved (implies missing evidence, not hallucination)
            subj = claim.get("subject_entity", {})
            is_resolved = subj.get("resolution_status") in ["RESOLVED", "RESOLVED_SOFT"]
            
            if is_resolved:
                return flags

            absolutism = ling.get("absolutism", 0.0)
            hedging = ling.get("hedging", 0.0)
            
            if absolutism > 0.5 or hedging < 0.2:
                flags.append(HallucinationFlag(
                    claim_id=claim.get("claim_id"),
                    hallucination_type="H1",
                    severity="HIGH",
                    reason="Unsupported Assertion",
                    explanation="Claim presented as fact without evidence support.",
                    supporting_signals=[f"verdict={verdict}", f"absolutism={absolutism}", f"hedging={hedging}"]
                ))
        return flags

    def _detect_false_specificity(self, claim: Dict[str, Any]) -> List[HallucinationFlag]:
        # H2: High Specificity (Numeric) + Verdict == INSUFFICIENT
        # Fix: Require explicit numeric/date precision (Fabricated Precision).
        flags = []
        verdict = claim.get("verification", {}).get("verdict")
        ling = claim.get("confidence_linguistic", {})
        
        # Check resolution status (Fix: Don't flag canonical facts as false specificity)
        subj = claim.get("subject_entity", {})
        is_resolved = subj.get("resolution_status") in ["RESOLVED", "RESOLVED_SOFT"]

        if verdict == "INSUFFICIENT_EVIDENCE" and not is_resolved:
            txt = claim.get("claim_text", "")
            has_number = bool(re.search(r'\d+', txt))
            
            if has_number:
                flags.append(HallucinationFlag(
                    claim_id=claim.get("claim_id"),
                    hallucination_type="H2",
                    severity="HIGH",
                    reason="False Specificity",
                    explanation="Specific numeric/date details asserted without evidence.",
                    supporting_signals=[f"verdict={verdict}", f"has_number={has_number}"]
                ))
        return flags



    def _detect_illegitimate_inference(self, claim: Dict[str, Any]) -> List[HallucinationFlag]:
        # H4: Causal/Correlational claim not Supported
        flags = []
        c_type = claim.get("claim_type")
        verdict = claim.get("verification", {}).get("verdict")
        
        if c_type == "CAUSAL" and verdict != "SUPPORTED":
            flags.append(HallucinationFlag(
                claim_id=claim.get("claim_id"),
                hallucination_type="H4",
                severity="HIGH",
                reason="Illegitimate Inference",
                explanation="Causal link asserted without evidence.",
                supporting_signals=[f"claim_type={c_type}", f"verdict={verdict}"]
            ))
        return flags



    def _detect_narrative_laundering(self, claim: Dict[str, Any]) -> List[HallucinationFlag]:
        # H6: Verdict=INSUFFICIENT, has Grokipedia, Absolutism > 0.5
        flags = []
        verdict = claim.get("verification", {}).get("verdict")
        evidence = claim.get("evidence", {})
        ling = claim.get("confidence_linguistic", {})
        
        has_grok = bool(evidence.get("grokipedia"))
        absolutism = ling.get("absolutism", 0.0)
        
        if verdict == "INSUFFICIENT_EVIDENCE" and has_grok and absolutism > 0.5:
             flags.append(HallucinationFlag(
                claim_id=claim.get("claim_id"),
                hallucination_type="H6",
                severity="MEDIUM",
                reason="Narrative Laundering",
                explanation="Narrative source presented as factual certainty.",
                supporting_signals=[f"has_grokipedia={has_grok}", f"absolutism={absolutism}"]
            ))
        return flags

    def _get_epistemic_polarity(self, text: str) -> str:
        """
        Classifies claim as OBJECT_LEVEL (factual) or META_EPISTEMIC (discourse/uncertainty).
        """
        if not text: return "OBJECT_LEVEL"
        t = text.lower()
        
        meta_markers = [
            r"remains debated",
            r"remains speculative",
            r"uncertain",
            r"hypothetical",
            r"\bmay\b",
            r"\bmight\b",
            r"\bcould\b",
            r"it is possible that",
            r"evidence suggests",
            r"scholars argue",
            r"scholars debate",
            r"extent is unclear",
            r"not fully understood",
            r"preliminary evidence"
        ]
        
        for m in meta_markers:
            if re.search(m, t):
                return "META_EPISTEMIC"
                
        return "OBJECT_LEVEL"
