from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

@dataclass
class EntitySource:
    wikidata: Optional[str] = None
    wikipedia: Optional[str] = None
    grokipedia: Optional[str] = None

@dataclass
class ResolvedEntity:
    text: str
    entity_id: str # Q-ID
    canonical_name: str
    entity_type: str # PERSON, ORG, LOC, ROLE, ETC
    sources: Dict[str, str]
    confidence: float
    resolution_status: str # RESOLVED, UNRESOLVED
    source_status: Dict[str, str] = field(default_factory=dict)
    requires_binding: bool = False
    candidates_log: List[Dict[str, Any]] = field(default_factory=list)
    decision_reason: str = ""

    def to_dict(self):
        return {
            "text": self.text,
            "entity_id": self.entity_id,
            "canonical_name": self.canonical_name,
            "entity_type": self.entity_type,
            "sources": self.sources,
            "confidence": self.confidence,
            "resolution_status": self.resolution_status,
            "source_status": self.source_status,
            "requires_binding": self.requires_binding,
            "candidates_log": self.candidates_log,
            "decision_reason": self.decision_reason
        }

@dataclass
class EntityCandidate:
    id: str # Q123
    label: str
    description: str
    aliases: List[str]
    score: float = 0.0
    sitelinks_count: int = 0
    match_type: str = "fuzzy" # exact, alias, fuzzy
    sources: Dict[str, str] = field(default_factory=dict)
