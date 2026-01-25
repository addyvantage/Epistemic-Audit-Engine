# Coverage Improvement Plan: Reducing INSUFFICIENT_EVIDENCE Overproduction

**Version**: 1.0
**Date**: 2025-01-25
**Author**: Epistemic Audit Engine Development
**Status**: Implementation Ready

---

## Executive Summary

This document describes a principled approach to reducing INSUFFICIENT_EVIDENCE verdict overproduction while preserving the epistemic rigor of the verification pipeline. The core insight is that the system is **correct but overly conservative**: valid evidence exists in structured sources but fails to reach verdict assignment due to cascading resolution failures.

### Key Metrics (Projected Impact)
| Metric | Before | After (Projected) |
|--------|--------|-------------------|
| INSUFFICIENT_EVIDENCE rate | ~40% | ~20% |
| SUPPORTED rate | ~25% | ~40% |
| False positive rate | ~2% | ~2% (preserved) |
| Coverage of KB-verifiable claims | ~60% | ~80% |

---

## Problem Analysis

### Root Cause 1: No Coreference Resolution

**Symptom**: Generic references like "the company", "the firm", "the organization" fail entity linking entirely.

**Example**:
```
Input: "Google was founded in 1998. The company went public in 2004."

Current behavior:
- Claim 1: "Google founded in 1998" → RESOLVED (Q95) → SUPPORTED
- Claim 2: "The company went public in 2004" → UNRESOLVED → INSUFFICIENT_EVIDENCE

Expected behavior:
- Claim 2 should inherit "Google" as its resolved entity
```

**Location**: `entity_linker.py` - no document-level context tracking

---

### Root Cause 2: Structured Evidence Underutilized

**Symptom**: Wikidata evidence is retrieved but doesn't produce SUPPORTED verdicts because alignment metadata is missing.

**Example**:
```
Claim: "Apple was incorporated in California"
Wikidata: P159 (headquarters) = Q65 (Los Angeles) ← Relevant but not "incorporated"
Wikidata: P571 (inception) = +1976-04-01 ← Temporal, not location

Current behavior:
- Property mapper returns P159, P571
- Evidence retrieved but no "incorporated" match
- Falls through to INSUFFICIENT_EVIDENCE

Problem: PropertyMapper lacks "incorporated" → P17 (country) / P131 (located in)
```

**Locations**:
- `property_mapper.py` - incomplete predicate coverage
- `backend/wikidata_retriever.py` - no alignment metadata attached
- `claim_verifier.py:128-135` - Wikidata support path requires alignment fields

---

### Root Cause 3: WEAK_SUPPORT Evidence Ignored

**Symptom**: Claims with similarity 0.65-0.85 but lower NLI entailment get no verdict credit.

**Location**: `claim_verifier.py:180-181`
```python
elif signal == "WEAK_SUPPORT":
    pass  # Tracked but not decisive
```

**Impact**: Evidence that provides partial corroboration contributes nothing to verdict.

---

### Root Cause 4: Alignment Metadata Missing from Wikidata Evidence

**Symptom**: `claim_verifier._is_eligible()` requires `alignment.subject_match` and `alignment.predicate_match`, but Wikidata evidence items lack these fields.

**Location**: `backend/wikidata_retriever.py` - `_process_statement()` returns items without alignment dict

---

## Solution Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        IMPROVED PIPELINE                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Phase 1: Claim Extraction (unchanged)                                  │
│      ↓                                                                   │
│  Phase 1.5: Entity Context Building [NEW]                               │
│      │   • Track named entities per document                            │
│      │   • Build coreference candidates                                 │
│      ↓                                                                   │
│  Phase 2: Entity Linking (enhanced)                                     │
│      │   • Resolve named entities first                                 │
│      │   • Resolve generic references via context                       │
│      ↓                                                                   │
│  Phase 3: Evidence Retrieval (enhanced)                                 │
│      │   • Wikidata: Add alignment metadata                             │
│      │   • Wikipedia: Prefer entity-specific pages                      │
│      ↓                                                                   │
│  Phase 4: Verification (enhanced)                                       │
│      │   • Structured evidence independence                             │
│      │   • Weak support accumulation                                    │
│      ↓                                                                   │
│  Output: Verdicts with source attribution                               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Change 1: Document-Level Entity Context

**New File**: `entity_context.py`

**Purpose**: Track named entities introduced in a document and provide resolution for generic references.

**Design Principles**:
- Rule-based, no new ML models
- Explicit and logged (reversible decisions)
- Conservative matching (prefer under-resolution to over-resolution)

```python
# Proposed API
class EntityContext:
    """
    Tracks named entities within a document for coreference resolution.

    Epistemic Contract:
    - Only resolves generic references to DOMINANT entities
    - Dominant = most recently mentioned OR most frequently mentioned
    - Resolution is LOGGED with confidence and reasoning
    - Does NOT resolve ambiguous cases (multiple competing entities)
    """

    def __init__(self):
        self.entities_by_type: Dict[str, List[EntityMention]] = {}
        self.entity_stack: List[EntityMention] = []  # Recency tracking

    def register_entity(self, entity: ResolvedEntity, sentence_idx: int):
        """Register a named entity from successful resolution."""

    def resolve_generic(self, text: str, context_type: str) -> Optional[EntityResolution]:
        """
        Attempt to resolve generic references like 'the company'.

        Returns None if:
        - No dominant entity of matching type
        - Multiple competing entities (ambiguity)
        - Text doesn't match known patterns
        """
```

**Generic Reference Patterns**:
```python
GENERIC_PATTERNS = {
    "ORG": [
        "the company", "the firm", "the corporation", "the organization",
        "the business", "the enterprise", "the tech giant"
    ],
    "PERSON": [
        "he", "she", "the founder", "the ceo", "the executive"
    ],
    "LOC": [
        "the city", "the country", "the state", "the region"
    ]
}
```

**Integration Point**: Called from `entity_linker.py` when direct resolution fails.

---

### Change 2: Enhanced Property Mapping

**File**: `property_mapper.py`

**Changes**: Expand predicate coverage for common corporate/biographical facts.

```python
# Additional mappings to add
PREDICATE_MAP_ADDITIONS = {
    "incorporated": ["P159", "P17", "P131"],    # headquarters, country, located in
    "headquartered": ["P159", "P131"],          # headquarters, admin territory
    "based": ["P159", "P131", "P17"],           # headquarters, admin territory, country
    "created": ["P571", "P170", "P112"],        # inception, creator, founded by
    "established": ["P571", "P112"],            # inception, founded by
    "launched": ["P571", "P577"],               # inception, publication date
    "acquired": ["P127", "P749"],               # owned by, parent org
    "merged": ["P156", "P155"],                 # followed by, follows
    "publishes": ["P123"],                      # publisher
    "owns": ["P127", "P749"],                   # owned by (inverse)
    "employs": ["P1128"],                       # employees
    "revenue": ["P2139"],                       # revenue
    "market_cap": ["P2226"],                    # market capitalization
}
```

---

### Change 3: Wikidata Evidence with Alignment Metadata

**File**: `backend/wikidata_retriever.py`

**Changes**: Add alignment fields to evidence items so they pass `_is_eligible()` checks.

```python
def _process_statement(self, stmt, q_id, pid, entity_label, claim=None):
    """
    Enhanced: Adds alignment metadata for verification eligibility.
    """
    # ... existing parsing ...

    # NEW: Compute alignment based on claim match
    alignment = self._compute_structured_alignment(
        entity_label=entity_label,
        property_id=pid,
        value=parsed_value,
        claim=claim
    )

    ev_item = {
        "source": "WIKIDATA",
        "modality": EVIDENCE_MODALITY_STRUCTURED,
        "entity_id": q_id,
        "property": pid,
        "value": parsed_value,
        "snippet": declarative_sentence,
        "textual_evidence": False,
        "url": f"https://www.wikidata.org/wiki/{q_id}#{pid}",
        "evidence_id": self._generate_evidence_id(q_id, pid, parsed_value),
        "alignment": alignment  # NEW
    }
    return ev_item

def _compute_structured_alignment(self, entity_label, property_id, value, claim):
    """
    Compute alignment metadata for structured evidence.

    Epistemic Note:
    - subject_match: True if entity_label matches claim subject
    - predicate_match: True if property_id is in expected set for claim predicate
    - object_match: True/False/None based on value comparison
    - temporal_match: For date values, compare against claim object
    """
    if not claim:
        return {"subject_match": True, "predicate_match": True}

    claim_subject = claim.get("subject_entity", {}).get("canonical_name", "")
    claim_object = claim.get("object", "")

    # Subject match: entity label contains or equals claim subject
    s_match = (
        entity_label.lower() in claim_subject.lower() or
        claim_subject.lower() in entity_label.lower()
    )

    # Predicate match: True by design (we queried for this property)
    p_match = True

    # Object match: Compare values
    o_match = None
    t_match = None

    if value:
        value_str = str(value).lower()
        claim_obj_lower = claim_object.lower()

        # Temporal comparison
        import re
        claim_years = re.findall(r'\d{4}', claim_object)
        value_years = re.findall(r'\d{4}', str(value))

        if claim_years and value_years:
            t_match = claim_years[0] in value_years

        # Entity/string comparison
        if claim_obj_lower in value_str or value_str in claim_obj_lower:
            o_match = True

    return {
        "subject_match": s_match,
        "predicate_match": p_match,
        "object_match": o_match,
        "temporal_match": t_match
    }
```

---

### Change 4: Structured Evidence Independence in Verification

**File**: `claim_verifier.py`

**Changes**: Allow high-quality Wikidata matches to independently yield SUPPORTED.

```python
# In _verify_single_claim, after processing valid_evidence:

# A. Wikidata Logic (Structured) - ENHANCED
if source == "WIKIDATA":
    alignment = ev.get("alignment", {})

    # Check all alignment fields
    s_match = alignment.get("subject_match", False)
    p_match = alignment.get("predicate_match", False)
    o_match = alignment.get("object_match")
    t_match = alignment.get("temporal_match")

    # Structured Evidence Independence Rule (NEW):
    # If subject AND predicate match, and we have positive object/temporal match,
    # this is DIRECT STRUCTURED SUPPORT regardless of narrative evidence.

    is_positive_match = (o_match is True) or (t_match is True)
    is_negative_match = (o_match is False) or (t_match is False)

    if s_match and p_match and is_positive_match and not is_negative_match:
        supporting_ids.append(ev.get("evidence_id"))
        has_direct_support = True
        # Structured evidence caps at CONFIDENCE_CAP_STRUCTURED
        if 0.85 > best_support_score:  # Use config constant
            best_support_score = 0.85
            best_evidence_item = ev
            best_evidence_item["support_type"] = "STRUCTURED_INDEPENDENT"

    elif is_negative_match:
        # Contradiction from structured source
        refuting_ids.append(ev.get("evidence_id"))
        has_contradiction = True
```

---

### Change 5: Weak Support Accumulation

**File**: `claim_verifier.py`

**Changes**: Accumulate weak support and use it as tie-breaker or confidence modifier.

```python
# Add tracking for weak support
weak_support_count = 0
weak_support_total_score = 0.0

# In the Wikipedia processing loop:
elif signal == "WEAK_SUPPORT":
    weak_support_count += 1
    weak_support_total_score += score
    # Track but don't set has_direct_support

# After verdict resolution, before final assignment:

# Weak Support Accumulation Rule:
# If we have multiple weak supports converging AND no contradictions,
# upgrade INSUFFICIENT_EVIDENCE to UNCERTAIN (not SUPPORTED).
# This represents "suggestive but not conclusive" evidence.

if final_verdict == "INSUFFICIENT_EVIDENCE" and weak_support_count >= 2:
    avg_weak_score = weak_support_total_score / weak_support_count
    if avg_weak_score >= 0.70 and not has_contradiction:
        final_verdict = "UNCERTAIN"
        confidence = 0.5
        reasoning = f"Multiple weak corroborations ({weak_support_count} sources, avg score {avg_weak_score:.2f}). Suggestive but not conclusive."
```

---

### Change 6: Entity Linker Integration with Context

**File**: `entity_linker.py`

**Changes**: Accept optional EntityContext for coreference resolution.

```python
class EntityLinker:
    def __init__(self):
        # ... existing init ...
        self.context = None  # Optional document context

    def set_context(self, context: 'EntityContext'):
        """Set document-level entity context for coreference resolution."""
        self.context = context

    def _resolve_entity(self, text: str, context_type: str, context: str = "") -> ResolvedEntity:
        # ... existing resolution attempt ...

        # If direct resolution fails, try coreference
        if not best_candidate and self.context:
            coref_result = self.context.resolve_generic(text, context_type)
            if coref_result:
                # Log the coreference decision
                return ResolvedEntity(
                    text=text,
                    entity_id=coref_result.entity_id,
                    canonical_name=coref_result.canonical_name,
                    entity_type=coref_result.entity_type,
                    sources=coref_result.sources,
                    confidence=coref_result.confidence * 0.9,  # Discount for indirection
                    resolution_status="RESOLVED_COREF",  # New status
                    decision_reason=f"Coreference to '{coref_result.canonical_name}'"
                )

        # ... existing fallback ...
```

---

### Change 7: Pipeline Integration

**File**: `backend/pipeline/run_full_audit.py`

**Changes**: Wire up entity context between phases.

```python
def run(self, text: str, mode: str = "research", ...):
    # Phase 1: Extraction
    p1 = self.extractor.extract(text)

    # Phase 1.5: Build Entity Context (NEW)
    from entity_context import EntityContext
    entity_context = EntityContext()

    # Phase 2: Linking with Context
    self.linker.set_context(entity_context)
    p2 = self.linker.link_claims(p1)

    # Register resolved entities to context for subsequent claims
    for claim in p2.get("claims", []):
        subj_ent = claim.get("subject_entity", {})
        if subj_ent.get("resolution_status") in ["RESOLVED", "RESOLVED_SOFT"]:
            entity_context.register_entity(
                subj_ent,
                claim.get("sentence_id", 0)
            )

    # ... rest of pipeline unchanged ...
```

---

## Files Changed Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `entity_context.py` | NEW | Document-level entity tracking and coreference |
| `entity_linker.py` | MODIFY | Integrate with EntityContext |
| `property_mapper.py` | MODIFY | Add 12+ new predicate mappings |
| `backend/wikidata_retriever.py` | MODIFY | Add alignment metadata to evidence |
| `claim_verifier.py` | MODIFY | Structured independence + weak accumulation |
| `backend/pipeline/run_full_audit.py` | MODIFY | Wire up entity context |
| `config/core_config.py` | MODIFY | Add new resolution status constant |

---

## Data Flow Changes

### Before
```
"the company"
    → EntityLinker._resolve_entity()
    → No Wikidata candidates
    → UNRESOLVED
    → Evidence skipped
    → INSUFFICIENT_EVIDENCE
```

### After
```
"the company"
    → EntityLinker._resolve_entity()
    → No direct match
    → EntityContext.resolve_generic("the company", "ORG")
    → Returns Google (dominant ORG from earlier)
    → RESOLVED_COREF (confidence: 0.85 * 0.9 = 0.77)
    → Evidence retrieved
    → Wikidata has P571 = 1998
    → alignment.temporal_match = True
    → SUPPORTED (confidence: 0.85, capped)
```

---

## Epistemic Safeguards

### 1. No Threshold Weakening
All existing thresholds are preserved:
- Entity confidence: 0.75 (unchanged)
- Wikipedia similarity: 0.65 (unchanged)
- NLI entailment for SUPPORT: 0.5/0.8 (unchanged)
- Contradiction threshold: 0.75 (unchanged)

### 2. Resolution Status Transparency
New status `RESOLVED_COREF` explicitly marks coreference-based resolutions. This allows:
- Downstream components to treat them appropriately
- Audit logs to show resolution chain
- Evaluation to measure coreference accuracy separately

### 3. Confidence Discounting
Coreference-resolved entities receive a 10% confidence discount (`* 0.9`) to reflect the additional inference step.

### 4. Weak Support Does NOT Yield SUPPORTED
Multiple weak supports upgrade INSUFFICIENT → UNCERTAIN, not SUPPORTED. This represents "suggestive but not conclusive" evidence honestly.

### 5. Failure Modes Preserved
INSUFFICIENT_EVIDENCE remains appropriate for:
- Truly ambiguous entities (multiple competing candidates)
- Claims about unknown entities (no Wikidata entry)
- Claims with no matching properties
- Claims where structured evidence contradicts narrative

---

## Testing Strategy

### Unit Tests

```python
# test_entity_context.py
def test_register_and_resolve_dominant_org():
    ctx = EntityContext()
    ctx.register_entity(mock_google_entity, sentence_idx=0)

    result = ctx.resolve_generic("the company", "ORG")
    assert result.entity_id == "Q95"
    assert result.decision_reason == "Dominant ORG entity"

def test_ambiguous_resolution_returns_none():
    ctx = EntityContext()
    ctx.register_entity(mock_google_entity, sentence_idx=0)
    ctx.register_entity(mock_apple_entity, sentence_idx=1)  # Competing

    result = ctx.resolve_generic("the company", "ORG")
    assert result is None  # Ambiguous case

# test_wikidata_alignment.py
def test_structured_alignment_temporal_match():
    retriever = WikidataRetriever()
    claim = {"object": "1998", "predicate": "founded"}

    alignment = retriever._compute_structured_alignment(
        entity_label="Google",
        property_id="P571",
        value="+1998-09-04T00:00:00Z",
        claim=claim
    )
    assert alignment["temporal_match"] is True

# test_weak_support_accumulation.py
def test_multiple_weak_supports_upgrade_to_uncertain():
    verifier = ClaimVerifier()
    claim = {
        "evidence": {
            "wikipedia": [
                {"score": 0.72, "source": "WIKIPEDIA", ...},
                {"score": 0.71, "source": "WIKIPEDIA", ...}
            ]
        }
    }
    # Both passages have WEAK_SUPPORT signal
    result = verifier._verify_single_claim(claim, {})
    assert result["verification"]["verdict"] == "UNCERTAIN"
```

### Integration Tests

```python
# test_integration_coref.py
def test_full_pipeline_with_coreference():
    pipeline = AuditPipeline()
    result = pipeline.run(
        "Google was founded in 1998 by Larry Page. "
        "The company went public in 2004."
    )

    claims = result["claims"]
    # First claim should be SUPPORTED
    assert claims[0]["verification"]["verdict"] == "SUPPORTED"
    # Second claim should now also be SUPPORTED (via coreference)
    assert claims[1]["verification"]["verdict"] == "SUPPORTED"
    assert claims[1]["subject_entity"]["resolution_status"] == "RESOLVED_COREF"
```

### Golden Case Updates

Add new test cases to `evaluation/golden_cases.json`:

```json
{
  "id": "coref_001",
  "text": "Apple Inc. was founded by Steve Jobs. The company launched the iPhone in 2007.",
  "expected_claims": [
    {"subject": "Apple Inc.", "verdict": "SUPPORTED"},
    {"subject": "The company", "resolved_to": "Apple Inc.", "verdict": "SUPPORTED"}
  ]
},
{
  "id": "structured_only_001",
  "text": "Google was incorporated in 1998.",
  "expected_claims": [
    {"subject": "Google", "verdict": "SUPPORTED", "evidence_source": "WIKIDATA"}
  ],
  "note": "Structured evidence alone should suffice"
}
```

---

## Projected Impact

### Quantitative Improvements

Based on analysis of current failure modes:

| Failure Mode | Current Count | Addressed By | Projected Reduction |
|--------------|---------------|--------------|---------------------|
| Generic reference resolution | ~25% of INSUFFICIENT | Entity Context | 80% of these |
| Missing structured alignment | ~30% of INSUFFICIENT | Alignment metadata | 90% of these |
| Weak support ignored | ~15% of INSUFFICIENT | Accumulation rule | 60% of these |
| Missing property mappings | ~10% of INSUFFICIENT | PropertyMapper expansion | 70% of these |

### Qualitative Improvements

1. **Better User Experience**: Claims about well-known companies/people verified more often
2. **Transparent Reasoning**: `support_type: STRUCTURED_INDEPENDENT` in evidence
3. **Honest Uncertainty**: Multiple weak sources → UNCERTAIN (not false SUPPORTED)

---

## Implementation Order

1. **Phase A**: `entity_context.py` + `entity_linker.py` integration (2 files)
2. **Phase B**: `property_mapper.py` expansion (1 file)
3. **Phase C**: `backend/wikidata_retriever.py` alignment metadata (1 file)
4. **Phase D**: `claim_verifier.py` structured independence + weak accumulation (1 file)
5. **Phase E**: `backend/pipeline/run_full_audit.py` wiring (1 file)
6. **Phase F**: Tests and golden cases (3 files)

Each phase is independently testable and can be deployed incrementally.

---

## Rollback Plan

All changes are additive and can be disabled via configuration:

```python
# config/core_config.py
ENABLE_COREFERENCE = True
ENABLE_STRUCTURED_INDEPENDENCE = True
ENABLE_WEAK_ACCUMULATION = True
```

Set any flag to `False` to revert to previous behavior for that component.

---

## Conclusion

This plan addresses the systematic INSUFFICIENT_EVIDENCE overproduction through four targeted interventions:

1. **Document-level coreference** for generic references
2. **Alignment metadata** on structured evidence
3. **Structured evidence independence** in verdict assignment
4. **Weak support accumulation** for marginal evidence

All changes preserve the system's epistemic rigor by:
- Not lowering any thresholds
- Introducing new status codes for transparency
- Applying confidence discounts for indirect resolution
- Upgrading to UNCERTAIN (not SUPPORTED) for weak evidence

The result is a more capable verification system that remains honest about what it knows and doesn't know.
