"""
Entity Context Module
=====================

Provides document-level entity tracking for coreference resolution.

Epistemic Contract:
-------------------
1. Only resolves generic references to DOMINANT entities
2. Dominant = most recently mentioned AND most frequently mentioned
3. Resolution is LOGGED with confidence and explicit reasoning
4. Does NOT resolve ambiguous cases (multiple competing entities of same type)
5. Does NOT introduce new entity information (read-only resolution)

Design Principles:
------------------
- Rule-based, no new ML models
- Explicit and auditable decisions
- Conservative matching (prefer under-resolution to over-resolution)
- Transparent about resolution chain

Usage:
------
    ctx = EntityContext()
    ctx.register_entity(resolved_entity, sentence_idx=0)
    result = ctx.resolve_generic("the company", context_type="SUBJECT")
    if result:
        # Use result.entity_id, result.canonical_name, etc.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class EntityMention:
    """
    Represents a single mention of a named entity in the document.
    """
    entity_id: str
    canonical_name: str
    entity_type: str  # ORG, PERSON, LOC, etc.
    sentence_idx: int
    confidence: float
    sources: Dict[str, str] = field(default_factory=dict)


@dataclass
class CorefResolution:
    """
    Result of coreference resolution with full audit trail.
    """
    entity_id: str
    canonical_name: str
    entity_type: str
    confidence: float
    sources: Dict[str, str]
    resolution_method: str  # "DOMINANT_RECENCY", "DOMINANT_FREQUENCY", etc.
    decision_reason: str    # Human-readable explanation
    source_mention: EntityMention  # The mention this resolves to


class EntityContext:
    """
    Tracks named entities within a document for coreference resolution.

    Thread Safety: Not thread-safe. Create one instance per document.
    """

    # -------------------------------------------------------------------------
    # Generic Reference Patterns
    # -------------------------------------------------------------------------
    # These patterns map to entity types. The system will attempt to resolve
    # these references to the dominant entity of the matching type.
    #
    # Epistemic Note: These patterns are intentionally conservative.
    # We only include references that are unambiguously anaphoric.
    # -------------------------------------------------------------------------
    GENERIC_PATTERNS: Dict[str, List[str]] = {
        "ORG": [
            "the company",
            "the firm",
            "the corporation",
            "the organization",
            "the business",
            "the enterprise",
            "the tech giant",
            "the tech company",
            "the conglomerate",
            "the startup",
            "the subsidiary",
            "the parent company",
        ],
        "PERSON": [
            "the founder",
            "the ceo",
            "the executive",
            "the entrepreneur",
            "the inventor",
            "the scientist",
            "the author",
            "the director",
        ],
        "LOC": [
            "the city",
            "the country",
            "the state",
            "the region",
            "the nation",
            "the capital",
        ],
    }

    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------
    # Minimum confidence required for coreference resolution
    MIN_RESOLUTION_CONFIDENCE = 0.70

    # Dominance gap required when multiple entities of same type exist
    # If gap < threshold, resolution is considered ambiguous
    DOMINANCE_GAP_THRESHOLD = 0.3  # 30% frequency advantage required

    def __init__(self):
        """Initialize empty entity context."""
        # Entities indexed by type for quick lookup
        self.entities_by_type: Dict[str, List[EntityMention]] = {}

        # Ordered list of all mentions for recency tracking
        self.mention_sequence: List[EntityMention] = []

        # Frequency counter for each unique entity
        self.entity_frequency: Dict[str, int] = {}  # entity_id -> count

        # Resolution log for debugging and audit
        self.resolution_log: List[Dict[str, Any]] = []

    def register_entity(self, entity_data: Dict[str, Any], sentence_idx: int) -> None:
        """
        Register a successfully resolved named entity.

        Args:
            entity_data: Dictionary with entity fields from EntityLinker
            sentence_idx: The sentence index where this entity was mentioned

        Note:
            Only entities with resolution_status RESOLVED or RESOLVED_SOFT
            should be registered. UNRESOLVED entities are not tracked.
        """
        resolution_status = entity_data.get("resolution_status", "")
        if resolution_status not in ["RESOLVED", "RESOLVED_SOFT"]:
            return  # Don't track unresolved entities

        entity_id = entity_data.get("entity_id", "")
        if not entity_id:
            return

        mention = EntityMention(
            entity_id=entity_id,
            canonical_name=entity_data.get("canonical_name", ""),
            entity_type=entity_data.get("entity_type", "UNKNOWN"),
            sentence_idx=sentence_idx,
            confidence=entity_data.get("confidence", 0.0),
            sources=entity_data.get("sources", {}),
        )

        # Add to type index
        if mention.entity_type not in self.entities_by_type:
            self.entities_by_type[mention.entity_type] = []
        self.entities_by_type[mention.entity_type].append(mention)

        # Add to sequence
        self.mention_sequence.append(mention)

        # Update frequency
        self.entity_frequency[entity_id] = self.entity_frequency.get(entity_id, 0) + 1

    def resolve_generic(
        self, text: str, context_type: str = "SUBJECT"
    ) -> Optional[CorefResolution]:
        """
        Attempt to resolve a generic reference to a tracked entity.

        Args:
            text: The text to resolve (e.g., "the company")
            context_type: Either "SUBJECT" or "OBJECT" (unused in current impl)

        Returns:
            CorefResolution if successful, None if:
            - Text doesn't match known patterns
            - No dominant entity of matching type
            - Multiple competing entities (ambiguity)

        Epistemic Note:
            This method is intentionally conservative. It will return None
            rather than make a potentially incorrect resolution.
        """
        text_lower = text.lower().strip()

        # 1. Match against generic patterns
        matched_type = None
        for entity_type, patterns in self.GENERIC_PATTERNS.items():
            if text_lower in patterns:
                matched_type = entity_type
                break

        if not matched_type:
            self._log_resolution(text, None, "NO_PATTERN_MATCH", "Text not in generic patterns")
            return None

        # 2. Get entities of this type
        candidates = self.entities_by_type.get(matched_type, [])
        if not candidates:
            self._log_resolution(text, None, "NO_CANDIDATES", f"No {matched_type} entities registered")
            return None

        # 3. Find dominant entity
        dominant, method, reason = self._find_dominant_entity(candidates, matched_type)

        if not dominant:
            self._log_resolution(text, None, "AMBIGUOUS", reason)
            return None

        # 4. Check confidence threshold
        if dominant.confidence < self.MIN_RESOLUTION_CONFIDENCE:
            self._log_resolution(
                text, dominant.entity_id, "LOW_CONFIDENCE",
                f"Entity confidence {dominant.confidence:.2f} < threshold {self.MIN_RESOLUTION_CONFIDENCE}"
            )
            return None

        # 5. Success - create resolution
        resolution = CorefResolution(
            entity_id=dominant.entity_id,
            canonical_name=dominant.canonical_name,
            entity_type=dominant.entity_type,
            confidence=dominant.confidence,
            sources=dominant.sources,
            resolution_method=method,
            decision_reason=reason,
            source_mention=dominant,
        )

        self._log_resolution(text, dominant.entity_id, method, reason)
        return resolution

    def _find_dominant_entity(
        self, candidates: List[EntityMention], entity_type: str
    ) -> tuple:
        """
        Find the dominant entity among candidates of the same type.

        Dominance Criteria (in order):
        1. If only one unique entity: Use it (SINGLETON)
        2. If multiple unique entities: Check frequency dominance
        3. If frequency is close: Check recency as tiebreaker

        Returns:
            (EntityMention or None, method: str, reason: str)
        """
        if not candidates:
            return None, "NO_CANDIDATES", "No candidates available"

        # Get unique entities by ID
        unique_entities: Dict[str, EntityMention] = {}
        for mention in candidates:
            if mention.entity_id not in unique_entities:
                unique_entities[mention.entity_id] = mention
            else:
                # Keep the most recent mention
                if mention.sentence_idx > unique_entities[mention.entity_id].sentence_idx:
                    unique_entities[mention.entity_id] = mention

        # Case 1: Singleton
        if len(unique_entities) == 1:
            entity = list(unique_entities.values())[0]
            return (
                entity,
                "DOMINANT_SINGLETON",
                f"Only {entity_type} entity in document: {entity.canonical_name}"
            )

        # Case 2: Multiple entities - check frequency dominance
        freq_list = [
            (eid, self.entity_frequency.get(eid, 0), mention)
            for eid, mention in unique_entities.items()
        ]
        freq_list.sort(key=lambda x: x[1], reverse=True)

        top_freq = freq_list[0][1]
        second_freq = freq_list[1][1] if len(freq_list) > 1 else 0

        # Calculate dominance gap
        if top_freq > 0:
            gap = (top_freq - second_freq) / top_freq
        else:
            gap = 0

        if gap >= self.DOMINANCE_GAP_THRESHOLD:
            dominant = freq_list[0][2]
            return (
                dominant,
                "DOMINANT_FREQUENCY",
                f"Frequency dominance: {dominant.canonical_name} ({top_freq} mentions) vs runner-up ({second_freq} mentions)"
            )

        # Case 3: Frequency is close - use recency
        # Get most recent mention across all candidates
        most_recent = max(candidates, key=lambda m: m.sentence_idx)

        # Check if the most recent entity is one of the top-frequency candidates
        top_entity_ids = {freq_list[0][0], freq_list[1][0]} if len(freq_list) > 1 else {freq_list[0][0]}

        if most_recent.entity_id in top_entity_ids:
            return (
                most_recent,
                "DOMINANT_RECENCY",
                f"Recency tiebreaker: {most_recent.canonical_name} (sentence {most_recent.sentence_idx})"
            )

        # Case 4: Ambiguous - refuse to resolve
        return (
            None,
            "AMBIGUOUS",
            f"Multiple competing {entity_type} entities with similar frequency: " +
            ", ".join(m.canonical_name for m in unique_entities.values())
        )

    def _log_resolution(
        self, text: str, entity_id: Optional[str], method: str, reason: str
    ) -> None:
        """Log resolution attempt for debugging and audit."""
        self.resolution_log.append({
            "input_text": text,
            "resolved_entity_id": entity_id,
            "method": method,
            "reason": reason,
            "success": entity_id is not None,
        })

    def get_resolution_log(self) -> List[Dict[str, Any]]:
        """Return the resolution log for debugging."""
        return self.resolution_log.copy()

    def get_entity_summary(self) -> Dict[str, Any]:
        """Return summary of tracked entities for debugging."""
        return {
            "total_mentions": len(self.mention_sequence),
            "unique_entities": len(self.entity_frequency),
            "entities_by_type": {
                etype: len(mentions)
                for etype, mentions in self.entities_by_type.items()
            },
            "entity_frequencies": self.entity_frequency.copy(),
        }

    def clear(self) -> None:
        """Clear all tracked entities. Call between documents."""
        self.entities_by_type.clear()
        self.mention_sequence.clear()
        self.entity_frequency.clear()
        self.resolution_log.clear()
