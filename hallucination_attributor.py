from typing import Dict, Any, List, Optional
from config.core_config import HALLUCINATION_TYPE_CONTRADICTION, HALLUCINATION_TYPE_UNSUPPORTED

class HallucinationAttributor:
    """
    Attributes alignment failures to specific hallucination mechanisms.
    Uses explicit rules only.
    """
    
    def __init__(self):
        pass
        
    def attribute(self, alignment_result: Dict[str, Any], evidence_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Determines if a hallucination flag should be raised based on alignment signal.
        """
        signal = alignment_result.get("signal")
        score = alignment_result.get("score", 0.0)
        
        if signal == "CONTRADICTION":
            return {
                "hallucination_type": HALLUCINATION_TYPE_CONTRADICTION,
                "severity": "CRITICAL",
                "score": score,
                "reason": f"Directly contradicted by evidence: \"{evidence_item.get('snippet', '')[:100]}...\"",
                "evidence_ref": evidence_item.get("evidence_id")
            }
            
        return None
