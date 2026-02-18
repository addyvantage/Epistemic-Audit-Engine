from typing import List, Dict, Any
from .hallucination_models import HallucinationFlag

class RiskAggregator:
    def __init__(self):
        pass
    
    def calculate_risk(self, flags: List[HallucinationFlag], claims: List[Dict[str, Any]] = None, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Computes Epistemic Risk Score (v1.3.8 Canonical Model).
        Formula: (1.0 * r) + (0.6 * i) + (0.3 * u)
        Dampened for small samples.
        """
        # 1. Canonical Claim Set (Meaningful Participation)
        # Filter for verdicts that impact risk calculus
        valid_verdicts = {
            "REFUTED", 
            "INSUFFICIENT_EVIDENCE", 
            "UNCERTAIN", 
            "PARTIALLY_SUPPORTED",
            "SUPPORTED", 
            "SUPPORTED_WEAK"
        }
        
        epistemic_claims = [
            c for c in (claims or [])
            if c.get("verification", {}).get("verdict") in valid_verdicts
        ]
        
        T = len(epistemic_claims)
        safe_T = max(1, T)
        
        # 2. Counts
        R_count = sum(1 for c in epistemic_claims if c.get("verification", {}).get("verdict") == "REFUTED")
        I_count = sum(1 for c in epistemic_claims if c.get("verification", {}).get("verdict") == "INSUFFICIENT_EVIDENCE")
        partial_count = sum(1 for c in epistemic_claims if c.get("verification", {}).get("verdict") == "PARTIALLY_SUPPORTED")
        U_count = sum(1 for c in epistemic_claims if c.get("verification", {}).get("verdict") == "UNCERTAIN") + partial_count
        S_count = sum(1 for c in epistemic_claims if c.get("verification", {}).get("verdict") in ["SUPPORTED", "SUPPORTED_WEAK"]) 
        
        # 3. Ratios
        r = R_count / safe_T
        i = I_count / safe_T
        u = U_count / safe_T
        
        # 4. Canonical Risk Equation
        raw_score = (1.0 * r) + (0.6 * i) + (0.3 * u)
        
        # 5. Small-Sample Saturation Dampening
        if T < 5:
            raw_score *= (T / 5.0)
            
        # 6. Clamp + Precision
        hallucination_score = round(max(0.0, min(1.0, raw_score)), 3)
        
        # 7. Label Mapping
        
        # 7. Label Mapping (Strict Contract)
        overall_risk = self.get_risk_label(hallucination_score)
        
        summary = {
            "total_asserted_claims": len(claims or []),
            "epistemic_claims": T,
            "refuted": R_count,
            "insufficient": I_count,
            "uncertain": U_count,
            "supported": S_count,
            "partially_supported": partial_count
        }
            
        return {
            "overall_risk": overall_risk,
            "hallucination_score": hallucination_score,
            "summary": summary
        }

    def get_risk_label(self, score: float) -> str:
        """
        Hard-Bind Label to Score (NO FALLBACKS)
        """
        if score <= 0.20:
            return "LOW"
        elif score <= 0.50:
            return "MEDIUM"
        else:
            return "HIGH"
