from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class HallucinationFlag:
    claim_id: str
    hallucination_type: str # H1-H6
    severity: str # LOW, MEDIUM, HIGH
    reason: str
    explanation: str
    supporting_signals: List[str]

@dataclass
class HallucinationReport:
    overall_risk: str # LOW, MEDIUM, HIGH
    hallucination_score: float
    flags: List[Dict[str, Any]]
    summary: Dict[str, int]
