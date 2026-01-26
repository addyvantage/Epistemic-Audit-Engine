from typing import Dict, Any, Optional
from config.core_config import (
    ALIGN_THRESH_SIM_HIGH, ALIGN_THRESH_SIM_MED, ALIGN_THRESH_SIM_ULTRA,
    ALIGN_THRESH_ENT_HIGH, ALIGN_THRESH_ENT_MED, ALIGN_THRESH_CON_HIGH,
    ALIGN_THRESH_SIM_WEAK
)

class AlignmentScorer:
    """
    Computes alignment scores between Claims and Evidence using NLI and Similarity.
    Strictly adheres to established thresholds.
    """
    
    def __init__(self):
        pass

    def score_alignment(self, claim_text: str, evidence_item: Dict[str, Any], nli_result: Dict[str, float]) -> Dict[str, Any]:
        """
        Computes alignment status and combined score based on NLI and Similarity.
        Does NOT decide final verdict, only alignment signal.
        """
        sim_score = evidence_item.get("score", 0.0)
        entailment = nli_result.get("entailment", 0.0)
        contradiction = nli_result.get("contradiction", 0.0)
        neutral = nli_result.get("neutral", 0.0)
        
        signal = "NEUTRAL"
        confidence = 0.0
        
        # 1. Strong Support Logic
        # (High Sim + Entailment) OR (Very High Sim)
        is_strong_support = (
            (sim_score >= ALIGN_THRESH_SIM_HIGH and entailment > ALIGN_THRESH_ENT_MED) or
            (sim_score >= ALIGN_THRESH_SIM_MED and entailment > ALIGN_THRESH_ENT_HIGH) or
            (sim_score >= ALIGN_THRESH_SIM_ULTRA)
        )
        
        if is_strong_support:
            signal = "SUPPORT"
            # Combined score averaging
            confidence = (sim_score + entailment) / 2
            
        # 2. Contradiction Logic
        elif contradiction > ALIGN_THRESH_CON_HIGH:
            signal = "CONTRADICTION"
            confidence = contradiction
            
        # 3. Weak Support Logic
        elif sim_score > ALIGN_THRESH_SIM_WEAK:
            signal = "WEAK_SUPPORT"
            confidence = sim_score
            
        return {
            "signal": signal,
            "score": float(confidence),
            "components": {
                "similarity": sim_score,
                "nli": nli_result
            }
        }
