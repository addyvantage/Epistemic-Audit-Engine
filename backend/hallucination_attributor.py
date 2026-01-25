"""
Hallucination Mechanism Attribution Module

Replaces heuristic labels with rule-backed attribution.
Each hallucination type has explicit triggering conditions.

Epistemic Rationale:
Moving from pattern-matching labels to mechanism-based attribution
enables:
1. Explainable hallucination detection
2. Quantitative threshold tuning
3. Reproducible evaluation

H1-H6 Mapping (aligned with evaluation research):
- H1: Unsupported Assertion (low alignment + assertive)
- H2: Numeric Fabrication (specificity without evidence)
- H3: Overconfidence (certainty markers + low support)
- H4: Illicit Inference (causal verbs without KB backing)
- H5: Internal Contradiction (cross-claim conflict)
- H6: Ungrounded Opinion (evaluative language without evidence)
"""

import re
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict


@dataclass
class HallucinationAttribution:
    """Rule-backed hallucination attribution."""
    type: str                          # H1-H6
    mechanism: str                     # Human-readable mechanism name
    trigger: str                       # What triggered detection
    confidence: float                  # Attribution confidence [0,1]
    evidence: List[Dict[str, Any]]     # Supporting signals
    thresholds_used: Dict[str, float]  # For reproducibility

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HallucinationAttributor:
    """
    Rule-backed hallucination attribution engine.

    All thresholds are fixed for determinism and logged for reproducibility.
    """

    # Version for logging
    VERSION = "2.0.0"

    # Fixed thresholds (tuned for epistemic precision over recall)
    THRESHOLDS = {
        # H1: Unsupported Assertion
        "h1_alignment_max": 0.3,          # Below this = unsupported
        "h1_absolutism_min": 0.6,         # Above this = assertive

        # H2: Numeric Fabrication
        "h2_numeric_pattern": r'\b\d+(?:,\d{3})*(?:\.\d+)?\b',

        # H3: Overconfidence
        "h3_alignment_max": 0.5,          # Below this = weak support
        "h3_modal_strength_min": 0.7,     # Above this = high certainty

        # H4: Illicit Inference
        "h4_causal_verbs": {"causes", "leads", "results", "produces", "creates",
                           "triggers", "induces", "generates", "drives"},

        # H5: Internal Contradiction
        # (computed across claims, no single threshold)

        # H6: Ungrounded Opinion
        "h6_alignment_max": 0.4,          # Below this = ungrounded
        "h6_evaluative_terms": {"best", "worst", "amazing", "terrible", "great",
                                "excellent", "poor", "outstanding", "awful",
                                "brilliant", "stupid", "beautiful", "ugly",
                                "innovative", "revolutionary", "groundbreaking"}
    }

    # Certainty markers for H3
    CERTAINTY_MARKERS = {
        "definitely", "certainly", "absolutely", "undoubtedly", "clearly",
        "obviously", "proven", "established", "confirmed", "indisputable",
        "unquestionable", "without doubt", "beyond question"
    }

    # Assertive language markers for H1
    ASSERTIVE_MARKERS = {
        "is", "are", "was", "were", "will be", "has", "have", "had",
        "does", "do", "did", "must", "shall", "always", "never"
    }

    def __init__(self):
        self._contradiction_cache: Dict[str, Set[str]] = {}

    def attribute_hallucinations(
        self,
        claim: Dict[str, Any],
        all_claims: Optional[List[Dict[str, Any]]] = None
    ) -> List[HallucinationAttribution]:
        """
        Analyze a claim and return all applicable hallucination attributions.

        Args:
            claim: Claim with alignment scores, linguistic signals, verification
            all_claims: All claims in document (for H5 cross-claim check)

        Returns:
            List of HallucinationAttribution objects
        """
        attributions = []

        # H1: Unsupported Assertion
        h1 = self._check_h1_unsupported_assertion(claim)
        if h1:
            attributions.append(h1)

        # H2: Numeric Fabrication
        h2 = self._check_h2_numeric_fabrication(claim)
        if h2:
            attributions.append(h2)

        # H3: Overconfidence
        h3 = self._check_h3_overconfidence(claim)
        if h3:
            attributions.append(h3)

        # H4: Illicit Inference
        h4 = self._check_h4_illicit_inference(claim)
        if h4:
            attributions.append(h4)

        # H5: Internal Contradiction (requires all claims)
        if all_claims:
            h5 = self._check_h5_contradiction(claim, all_claims)
            if h5:
                attributions.append(h5)

        # H6: Ungrounded Opinion
        h6 = self._check_h6_ungrounded_opinion(claim)
        if h6:
            attributions.append(h6)

        return attributions

    def _check_h1_unsupported_assertion(
        self,
        claim: Dict[str, Any]
    ) -> Optional[HallucinationAttribution]:
        """
        H1: Unsupported Assertion
        Trigger: alignment_score < 0.3 AND assertive language

        Epistemic Rationale:
        Assertive claims (factual statements) without supporting evidence
        represent a fundamental epistemic failure - confident assertion
        without justification.
        """
        alignment = claim.get("alignment_score", 0.0)
        linguistic = claim.get("confidence_linguistic", {})
        absolutism = linguistic.get("absolutism", 0.0)
        claim_text = claim.get("claim_text", "").lower()

        # Check threshold conditions
        if alignment >= self.THRESHOLDS["h1_alignment_max"]:
            return None

        if absolutism < self.THRESHOLDS["h1_absolutism_min"]:
            # Check for assertive markers in text
            has_assertive = any(m in claim_text for m in self.ASSERTIVE_MARKERS)
            if not has_assertive:
                return None

        # Build evidence
        evidence = [
            {"signal": "alignment_score", "value": alignment, "threshold": self.THRESHOLDS["h1_alignment_max"]},
            {"signal": "absolutism", "value": absolutism, "threshold": self.THRESHOLDS["h1_absolutism_min"]}
        ]

        return HallucinationAttribution(
            type="H1",
            mechanism="unsupported_assertion",
            trigger="low_alignment_with_assertive_language",
            confidence=min(1.0, (self.THRESHOLDS["h1_alignment_max"] - alignment) * 2 + absolutism * 0.5),
            evidence=evidence,
            thresholds_used={
                "h1_alignment_max": self.THRESHOLDS["h1_alignment_max"],
                "h1_absolutism_min": self.THRESHOLDS["h1_absolutism_min"]
            }
        )

    def _check_h2_numeric_fabrication(
        self,
        claim: Dict[str, Any]
    ) -> Optional[HallucinationAttribution]:
        """
        H2: Numeric Fabrication
        Trigger: numeric specificity detected AND no numeric evidence

        Epistemic Rationale:
        Precise numbers carry epistemic weight - they imply measurement
        or authoritative source. Fabricated numbers are particularly
        problematic because they appear credible.
        """
        claim_text = claim.get("claim_text", "")

        # Extract numbers from claim (excluding years)
        pattern = self.THRESHOLDS["h2_numeric_pattern"]
        numbers = re.findall(pattern, claim_text)
        claim_numbers = []
        for n in numbers:
            # Skip years (1900-2099)
            clean = n.replace(",", "")
            if len(clean) == 4 and (clean.startswith("19") or clean.startswith("20")):
                continue
            claim_numbers.append(n)

        if not claim_numbers:
            return None

        # Check if numbers appear in evidence
        evidence_items = claim.get("evidence", {})
        evidence_text = ""
        for source, items in evidence_items.items():
            if isinstance(items, list):
                for item in items:
                    evidence_text += " " + item.get("sentence", "")
                    evidence_text += " " + item.get("snippet", "")
                    evidence_text += " " + str(item.get("value", ""))

        evidence_text = evidence_text.lower()

        # Find unsupported numbers
        unsupported = []
        for num in claim_numbers:
            clean_num = num.replace(",", "")
            if clean_num not in evidence_text and num not in evidence_text:
                unsupported.append(num)

        if not unsupported:
            return None

        return HallucinationAttribution(
            type="H2",
            mechanism="numeric_fabrication",
            trigger="unsupported_numeric_specificity",
            confidence=min(1.0, len(unsupported) * 0.4),
            evidence=[
                {"signal": "claim_numbers", "value": claim_numbers},
                {"signal": "unsupported_numbers", "value": unsupported},
                {"signal": "evidence_checked", "value": True}
            ],
            thresholds_used={}
        )

    def _check_h3_overconfidence(
        self,
        claim: Dict[str, Any]
    ) -> Optional[HallucinationAttribution]:
        """
        H3: Overconfidence
        Trigger: certainty markers AND alignment_score < 0.5

        Epistemic Rationale:
        Epistemic humility requires matching confidence to evidence strength.
        High-confidence language ("definitely", "proven") with weak evidence
        represents overconfidence bias.
        """
        alignment = claim.get("alignment_score", 0.0)
        linguistic = claim.get("confidence_linguistic", {})
        modal_strength = linguistic.get("modal_strength", 0.0)
        claim_text = claim.get("claim_text", "").lower()

        # Check alignment threshold
        if alignment >= self.THRESHOLDS["h3_alignment_max"]:
            return None

        # Check certainty markers
        found_markers = [m for m in self.CERTAINTY_MARKERS if m in claim_text]

        # Also check modal_strength
        if modal_strength < self.THRESHOLDS["h3_modal_strength_min"] and not found_markers:
            return None

        confidence = (
            (self.THRESHOLDS["h3_alignment_max"] - alignment) +
            (modal_strength - self.THRESHOLDS["h3_modal_strength_min"]) * 0.5 +
            len(found_markers) * 0.2
        )

        return HallucinationAttribution(
            type="H3",
            mechanism="overconfidence",
            trigger="certainty_without_support",
            confidence=min(1.0, max(0.0, confidence)),
            evidence=[
                {"signal": "alignment_score", "value": alignment},
                {"signal": "modal_strength", "value": modal_strength},
                {"signal": "certainty_markers", "value": found_markers}
            ],
            thresholds_used={
                "h3_alignment_max": self.THRESHOLDS["h3_alignment_max"],
                "h3_modal_strength_min": self.THRESHOLDS["h3_modal_strength_min"]
            }
        )

    def _check_h4_illicit_inference(
        self,
        claim: Dict[str, Any]
    ) -> Optional[HallucinationAttribution]:
        """
        H4: Illicit Inference
        Trigger: causal verbs AND no causal predicate in KB

        Epistemic Rationale:
        Causal claims carry strong epistemic weight. Asserting causation
        without grounding in verified causal relations is a form of
        inferential overreach.
        """
        predicate = claim.get("predicate", "").lower()
        claim_text = claim.get("claim_text", "").lower()
        claim_type = claim.get("claim_type", "")

        # Check for causal language
        causal_verbs = self.THRESHOLDS["h4_causal_verbs"]
        found_causal = [v for v in causal_verbs if v in predicate or v in claim_text]

        if not found_causal:
            return None

        # Check if evidence supports causal relation
        # Look for Wikidata properties P828 (has cause), P1542 (has effect)
        evidence = claim.get("evidence", {})
        wikidata = evidence.get("wikidata", [])

        causal_props = {"P828", "P1542", "P1479", "P1478"}  # causal properties
        has_causal_evidence = False

        for ev in wikidata:
            if ev.get("property") in causal_props:
                has_causal_evidence = True
                break

        if has_causal_evidence:
            return None

        return HallucinationAttribution(
            type="H4",
            mechanism="illicit_inference",
            trigger="causal_claim_without_kb_backing",
            confidence=0.7,
            evidence=[
                {"signal": "causal_verbs_found", "value": found_causal},
                {"signal": "claim_type", "value": claim_type},
                {"signal": "causal_evidence_found", "value": False}
            ],
            thresholds_used={}
        )

    def _check_h5_contradiction(
        self,
        claim: Dict[str, Any],
        all_claims: List[Dict[str, Any]]
    ) -> Optional[HallucinationAttribution]:
        """
        H5: Internal Contradiction
        Trigger: cross-claim contradiction detected

        Epistemic Rationale:
        Logical consistency is a fundamental epistemic constraint.
        Self-contradiction within a document indicates unreliable
        source or generation failure.
        """
        claim_id = claim.get("claim_id", "")
        subject = claim.get("subject_entity", {}).get("entity_id", "")
        predicate = claim.get("predicate", "").lower()
        obj = claim.get("object", "")
        obj_entity = claim.get("object_entity", {}).get("entity_id", "")

        if not subject:
            return None

        # Build signature for comparison
        def normalize_pred(p):
            """Normalize predicates for comparison."""
            p = p.lower().strip()
            # Temporal predicates
            if any(t in p for t in ["founded", "established", "created", "started"]):
                return "inception"
            if any(t in p for t in ["born", "birth"]):
                return "birth"
            if any(t in p for t in ["died", "death"]):
                return "death"
            return p

        claim_pred = normalize_pred(predicate)

        # Find contradicting claims
        contradictions = []
        for other in all_claims:
            if other.get("claim_id") == claim_id:
                continue

            other_subject = other.get("subject_entity", {}).get("entity_id", "")
            other_pred = normalize_pred(other.get("predicate", ""))
            other_obj = other.get("object", "")
            other_obj_entity = other.get("object_entity", {}).get("entity_id", "")

            # Same subject and predicate type
            if other_subject == subject and other_pred == claim_pred:
                # Different objects = potential contradiction
                if obj_entity and other_obj_entity:
                    if obj_entity != other_obj_entity:
                        contradictions.append({
                            "claim_id": other.get("claim_id"),
                            "object": other_obj,
                            "this_object": obj
                        })
                elif obj.lower() != other_obj.lower():
                    # Text comparison for unlinked entities
                    contradictions.append({
                        "claim_id": other.get("claim_id"),
                        "object": other_obj,
                        "this_object": obj
                    })

        if not contradictions:
            return None

        return HallucinationAttribution(
            type="H5",
            mechanism="internal_contradiction",
            trigger="cross_claim_conflict",
            confidence=min(1.0, len(contradictions) * 0.5),
            evidence=[
                {"signal": "subject", "value": subject},
                {"signal": "predicate", "value": predicate},
                {"signal": "contradicting_claims", "value": contradictions}
            ],
            thresholds_used={}
        )

    def _check_h6_ungrounded_opinion(
        self,
        claim: Dict[str, Any]
    ) -> Optional[HallucinationAttribution]:
        """
        H6: Ungrounded Opinion
        Trigger: evaluative/opinionated language without evidence

        Epistemic Rationale:
        Evaluative claims ("best", "innovative") masquerading as factual
        statements without supporting evidence represent a category error -
        opinion presented as fact.
        """
        claim_text = claim.get("claim_text", "").lower()
        alignment = claim.get("alignment_score", 0.0)

        # Check for evaluative terms
        evaluative_terms = self.THRESHOLDS["h6_evaluative_terms"]
        found_terms = [t for t in evaluative_terms if t in claim_text]

        if not found_terms:
            return None

        # Must have low alignment (ungrounded)
        if alignment >= self.THRESHOLDS["h6_alignment_max"]:
            return None

        return HallucinationAttribution(
            type="H6",
            mechanism="ungrounded_opinion",
            trigger="evaluative_language_without_evidence",
            confidence=min(1.0, len(found_terms) * 0.3 + (self.THRESHOLDS["h6_alignment_max"] - alignment)),
            evidence=[
                {"signal": "evaluative_terms", "value": found_terms},
                {"signal": "alignment_score", "value": alignment}
            ],
            thresholds_used={
                "h6_alignment_max": self.THRESHOLDS["h6_alignment_max"]
            }
        )

    def get_thresholds(self) -> Dict[str, Any]:
        """Return all thresholds for logging/reproducibility."""
        return {
            "version": self.VERSION,
            "thresholds": {k: v if not isinstance(v, set) else list(v)
                          for k, v in self.THRESHOLDS.items()}
        }


def attribute_claim_hallucinations(
    claim: Dict[str, Any],
    all_claims: Optional[List[Dict[str, Any]]] = None,
    attributor: Optional[HallucinationAttributor] = None
) -> Dict[str, Any]:
    """
    Convenience function to attribute hallucinations to a claim.

    Modifies claim in-place by adding 'hallucination_attributions' field.
    Returns the modified claim.
    """
    if attributor is None:
        attributor = HallucinationAttributor()

    attributions = attributor.attribute_hallucinations(claim, all_claims)

    # Convert to dicts and store
    claim["hallucination_attributions"] = [a.to_dict() for a in attributions]

    return claim
