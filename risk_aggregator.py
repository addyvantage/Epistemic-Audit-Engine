from typing import List, Dict, Any
from hallucination_models import HallucinationFlag

class RiskAggregator:
    def __init__(self):
        self.WEIGHTS = {
            "H1": 0.25, # Unsupported Assertion
            "H2": 0.20, # False Specificity
            "H3": 0.15, # Overconfidence
            "H4": 0.25, # Illegitimate Inference
            "H5": 0.30, # Inconsistency
            "H6": 0.15  # Narrative Laundering
        }
    
    def calculate_risk(self, flags: List[HallucinationFlag], claims: List[Dict[str, Any]] = None, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Computes overall risk score (Epistemic Risk).
        Formula: 0.3 * Hallucination + 0.5 * Refutation + 0.2 * Instability
        """
        # 1. Hallucination Component
        h_score_raw = 0.0
        summary = {
            "unsupported_claims": 0,
            "false_specificity": 0,
            "overconfident_language": 0,
            "illegitimate_inference": 0,
            "inconsistencies": 0,
            "narrative_overreach": 0
        }
        type_map = {
            "H1": "unsupported_claims",
            "H2": "false_specificity",
            "H3": "overconfident_language",
            "H4": "illegitimate_inference",
            "H5": "inconsistencies",
            "H6": "narrative_overreach"
        }
        
        for flag in flags:
            htype = flag.hallucination_type
            severity = flag.severity
            w = self.WEIGHTS.get(htype, 0.1)
            mult = 1.5 if severity == "HIGH" else 0.5 if severity == "LOW" else 1.0
            contribution = w * mult
            h_score_raw += contribution / (1 + h_score_raw)
            if type_map.get(htype) in summary: summary[type_map.get(htype)] += 1

        h_score = min(1.0, h_score_raw)
        
        # 2. Epistemic Components
        refuted_ratio = 0.0
        unresolved_ratio = 0.0
        
        if claims:
            total = len(claims)
            if total > 0:
                refuted_count = sum(1 for c in claims if c.get("verification", {}).get("verdict") == "REFUTED")
                unresolved_count = sum(1 for c in claims if c.get("subject_entity", {}).get("resolution_status") == "UNRESOLVED")
                
                refuted_ratio = refuted_count / total
                unresolved_ratio = unresolved_count / total
        
        # Fix 4: Rewards for Epistemic Humility (Fixes Packs A/F)
        humility_bonus = 0.0
        if claims:
            # Map flags for easy lookup
            claim_flags = {}
            for f in flags:
                cid = f.claim_id
                if cid not in claim_flags: claim_flags[cid] = set()
                claim_flags[cid].add(f.hallucination_type)
            
            for c in claims:
                if c.get("epistemic_polarity") == "META_EPISTEMIC":
                    c_flags = claim_flags.get(c.get("claim_id"), set())
                    # Check for disqualifying high-severity errors
                    # H2 (False Spec), H4 (Bad Inference), H5 (Contradiction) negate humility.
                    if not any(bad in c_flags for bad in ["H2", "H4", "H5"]):
                        humility_bonus += 0.05

        # 3. Final Risk Formula (Fix 6)
        # Weights: H=0.3, R=0.5, U=0.2
        final_score = (0.3 * h_score) + (0.5 * refuted_ratio) + (0.2 * unresolved_ratio) - humility_bonus
        final_score = max(0.0, min(1.0, final_score))
        
        # Risk Level (Demo Mode Sensitivity)
        t_low = 0.20 if config and config.get("mode") == "demo" else 0.25
        t_med = 0.50 if config and config.get("mode") == "demo" else 0.60
        
        if final_score <= t_low:
            risk_level = "LOW"
        elif final_score <= t_med:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
            
        return {
            "overall_risk": risk_level,
            "hallucination_score": round(final_score, 2),
            "summary": summary
        }
        

