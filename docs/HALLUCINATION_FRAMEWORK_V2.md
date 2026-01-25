# Next-Generation Hallucination Detection Framework

## Design Document v2.0

**Scope**: Structural epistemic failure detection
**Constraint**: No new ML models, no LLMs, rule-based only
**Integration**: Extends existing `hallucination_detector.py`

---

## 1. Theoretical Foundation

### 1.1 Definition of Structural Hallucination

A **structural hallucination** is an epistemic failure that arises from the *shape* of a claim rather than its surface-level factual accuracy. It represents a category error in how knowledge is attributed, scoped, or inferred.

**Contrast with Factual Error**:
- Factual error: "Apple was founded in 1980" (wrong date, correct structure)
- Structural hallucination: "Tim Cook invented the transistor" (impossible attribution structure)

### 1.2 Epistemic Failure Taxonomy

```
STRUCTURAL HALLUCINATIONS
├── Attribution Failures
│   ├── AUTHORITY_BLEED (existing)
│   ├── ENTITY_ROLE_CONFLICT (existing)
│   ├── EXPERTISE_DOMAIN_VIOLATION (new)
│   └── COLLECTIVE_TO_INDIVIDUAL (new)
│
├── Temporal Failures
│   ├── TEMPORAL_FABRICATION (existing)
│   ├── ANACHRONISTIC_ATTRIBUTION (new)
│   └── TEMPORAL_COMPRESSION (new)
│
├── Scope Failures
│   ├── SCOPE_OVERGENERALIZATION (existing)
│   ├── JURISDICTION_OVERREACH (new)
│   └── SAMPLE_TO_POPULATION (new)
│
├── Inference Failures
│   ├── ILLICIT_CAUSAL_CHAIN (new)
│   ├── CORRELATION_AS_CAUSATION (new)
│   └── POST_HOC_ATTRIBUTION (new)
│
└── Source Failures
    ├── COURT_AUTHORITY_MISATTRIBUTION (existing)
    ├── SOURCE_LAUNDERING (new)
    └── CIRCULAR_EVIDENCE (new)
```

---

## 2. New Hallucination Class Definitions

### 2.1 Attribution Failures

#### EXPERTISE_DOMAIN_VIOLATION

**Definition**: Attribution of expertise or accomplishment outside an entity's established domain of competence.

**Structural Pattern**:
```
[Person/Org with Domain X] + [Achievement Predicate] + [Object in Domain Y]
where X ∩ Y = ∅
```

**Examples**:
- "Warren Buffett discovered the Higgs boson" (Finance → Physics)
- "CERN developed a new cryptocurrency protocol" (Physics → CS/Finance)
- "The Mayo Clinic released a new programming language" (Medicine → CS)

**Detection Phase**: Phase 4 (requires entity resolution + Wikidata domain lookup)

**Evidence Trigger**:
1. Subject entity resolved with Wikidata ID
2. Query P101 (field of work), P106 (occupation), P452 (industry)
3. Object classified into domain via P31/P279 inheritance
4. Cross-reference: If subject domains share no common ancestor with object domain in Wikidata ontology → violation

**Downgrade**: REFUTED (0.90 confidence)

**Determinism**: Domain classification uses fixed P-ID traversal depth (max 3 hops)

---

#### COLLECTIVE_TO_INDIVIDUAL

**Definition**: Attribution of collective/institutional work to a single individual without qualifier.

**Structural Pattern**:
```
[Individual Person] + [Sole Authorship Predicate] + [Known Collective Work]
where no "led", "co-", "helped", "contributed" modifier present
```

**Examples**:
- "Jonas Salk created the polio vaccine" (team effort, simplified)
- "Vint Cerf invented the internet" (collective, many contributors)
- "Marie Curie discovered radioactivity" (Becquerel discovered first)

**Detection Phase**: Phase 5 (post-verification, requires claim text analysis)

**Evidence Trigger**:
1. Subject is PERSON entity type
2. Predicate is sole-authorship: {invented, created, discovered, built, designed}
3. Predicate lacks collective modifiers: {co-invented, helped, contributed, led the team}
4. Object resolves to Wikidata entity with multiple P61/P50/P170/P178 values

**Downgrade**: UNCERTAIN (0.70 confidence) — not false, but epistemically imprecise

**Determinism**: Modifier detection via fixed keyword set; contributor count from Wikidata

---

### 2.2 Temporal Failures

#### ANACHRONISTIC_ATTRIBUTION

**Definition**: Attribution of technology, concept, or capability to an entity before its existence or adoption.

**Structural Pattern**:
```
[Entity with inception T1] + [Action at T0] + [Technology with inception T2]
where T0 < T1 OR T0 < T2
```

**Examples**:
- "IBM used machine learning in 1950" (ML term coined 1959)
- "Alexander Graham Bell sent an email in 1880" (email: 1971)
- "The Roman Empire used gunpowder" (gunpowder: 9th century China)

**Detection Phase**: Phase 4 (requires temporal resolution for all entities)

**Evidence Trigger**:
1. Extract temporal anchor from claim (explicit year or inferred from context)
2. Resolve subject and object entities to Wikidata
3. Query P571 (inception), P585 (point in time), P580 (start time)
4. If claim_time < entity_inception_time → anachronism

**Downgrade**: REFUTED (0.95 confidence)

**Determinism**: Temporal comparison uses integer year only; month/day ignored

---

#### TEMPORAL_COMPRESSION

**Definition**: Collapsing distinct temporal events into a single narrative, suggesting simultaneity or direct causation.

**Structural Pattern**:
```
[Event A at T1] + [causal connector] + [Event B at T2]
where |T2 - T1| > threshold AND connector implies immediacy
```

**Examples**:
- "After inventing the lightbulb, Edison immediately founded General Electric" (11 years gap)
- "Following the moon landing, the Space Shuttle program launched" (12 years gap)

**Detection Phase**: Phase 4 (requires temporal evidence for both events)

**Evidence Trigger**:
1. Detect causal/sequential connectors: {after, following, then, led to, resulted in, immediately}
2. Detect immediacy markers: {immediately, quickly, soon after, directly}
3. Resolve temporal anchors for both events from Wikidata
4. If gap > 5 years AND immediacy marker present → compression

**Downgrade**: UNCERTAIN (0.60 confidence) — narrative simplification, not necessarily false

**Determinism**: Fixed threshold (5 years); connector detection via keyword set

---

### 2.3 Scope Failures

#### JURISDICTION_OVERREACH

**Definition**: Attribution of authority or action beyond an entity's established jurisdictional scope.

**Structural Pattern**:
```
[Authority with Jurisdiction J1] + [Action Predicate] + [Target in Jurisdiction J2]
where J1 ⊄ J2 AND J2 ⊄ J1
```

**Examples**:
- "The EU banned firearms in the United States" (EU → US jurisdiction)
- "The California Supreme Court ruled on federal immigration policy" (state → federal)
- "The FDA approved the drug for use in Europe" (US agency → EU territory)

**Detection Phase**: Phase 4 (requires entity resolution and jurisdiction inference)

**Evidence Trigger**:
1. Subject is authority entity (government, court, agency, regulatory body)
2. Query P1001 (applies to jurisdiction) for subject
3. Object or action target has location/jurisdiction
4. Cross-reference: If subject jurisdiction does not contain target jurisdiction → overreach

**Downgrade**: REFUTED (0.90 confidence)

**Determinism**: Jurisdiction containment uses P131 (administrative territory) traversal, max depth 5

---

#### SAMPLE_TO_POPULATION

**Definition**: Generalization from limited sample or study to universal claim without qualifier.

**Structural Pattern**:
```
[Claim with universal quantifier] + [Based on limited study/sample]
where no "in this study", "among participants", "in X region" qualifier
```

**Examples**:
- "Coffee prevents cancer" (based on one observational study)
- "Exercise cures depression" (universal claim from limited trial)
- "All millennials prefer remote work" (from survey of 500 people)

**Detection Phase**: Phase 5 (post-verification, requires claim-evidence comparison)

**Evidence Trigger**:
1. Claim contains universal markers: {all, always, never, everyone, cures, prevents, causes}
2. Claim lacks qualifier markers: {may, can, in some cases, study suggests, research indicates}
3. Evidence (Wikipedia/Wikidata) contains study-limiting language: {study, trial, survey, sample, participants, n=}
4. Mismatch between claim universality and evidence scope → overgeneralization

**Downgrade**: UNCERTAIN (0.75 confidence)

**Determinism**: Marker detection via fixed keyword sets; no probabilistic inference

---

### 2.4 Inference Failures

#### ILLICIT_CAUSAL_CHAIN

**Definition**: Assertion of direct causation through an unstated or invalid intermediate step.

**Structural Pattern**:
```
[Cause A] → [Effect C]
where valid chain is A → B → C, but B is omitted or invalid
```

**Examples**:
- "Increased CO2 directly raises sea levels" (missing: temperature → ice melt)
- "Vaccination causes autism" (no valid intermediate mechanism)
- "Reading books makes you wealthy" (unstated confounders)

**Detection Phase**: Phase 5 (requires claim structure analysis + evidence gap detection)

**Evidence Trigger**:
1. Claim contains causal predicate: {causes, leads to, results in, creates, produces}
2. Subject and object are not directly linked in Wikidata (no P1542 cause_of or P828 has_cause)
3. Check for intermediate entities that would complete the chain
4. If no valid intermediate path exists in Wikidata → illicit chain

**Downgrade**: UNCERTAIN (0.70 confidence) — may be valid but not verifiable

**Determinism**: Wikidata path search with max depth 2; no inference beyond stated relations

---

#### CORRELATION_AS_CAUSATION

**Definition**: Treatment of statistical correlation as direct causal relationship.

**Structural Pattern**:
```
[Variable A correlates with Variable B] → [A causes B]
without mechanistic or experimental evidence
```

**Examples**:
- "Ice cream sales cause drowning deaths" (both correlate with summer)
- "Countries with more chocolate consumption have more Nobel laureates"

**Detection Phase**: Phase 5 (requires linguistic pattern detection)

**Evidence Trigger**:
1. Claim uses causal language: {causes, leads to, results in}
2. Evidence uses correlation language: {correlates, associated with, linked to, relationship between}
3. Evidence lacks experimental/mechanistic language: {experiment, mechanism, controlled study, RCT}
4. If claim asserts causation but evidence only shows correlation → violation

**Downgrade**: UNCERTAIN (0.65 confidence)

**Determinism**: Language classification via fixed keyword categories

---

#### POST_HOC_ATTRIBUTION

**Definition**: Attribution of causation based solely on temporal sequence (post hoc ergo propter hoc).

**Structural Pattern**:
```
[Event A at T1] + [Event B at T2 where T2 > T1] → [A caused B]
without mechanistic link
```

**Examples**:
- "After the CEO changed, stock prices rose, proving his strategy worked" (correlation only)
- "The economy improved after the policy, so the policy caused the improvement"

**Detection Phase**: Phase 5 (requires temporal + causal pattern detection)

**Evidence Trigger**:
1. Claim contains temporal-causal connector: {after X, Y happened; following X, Y}
2. Claim contains causal attribution: {because, caused, resulted in, led to, proving}
3. No mechanistic evidence linking A → B (Wikidata P828/P1542 absent)
4. Pattern matches post-hoc structure → violation

**Downgrade**: UNCERTAIN (0.60 confidence)

**Determinism**: Pattern matching via regex; no probabilistic causation inference

---

### 2.5 Source Failures

#### SOURCE_LAUNDERING

**Definition**: Citation of a secondary or derivative source as if it were the primary/authoritative source.

**Structural Pattern**:
```
[Claim attributed to Source S]
where S is actually quoting/citing Source P (primary)
```

**Examples**:
- "According to the New York Times, the study found..." (NYT reporting on Nature study)
- "Wikipedia states that Einstein said..." (Wikipedia quoting Einstein)

**Detection Phase**: Phase 3 (evidence retrieval) + Phase 5 (post-verification)

**Evidence Trigger**:
1. Claim contains attribution: {according to, X says, X reports, X states}
2. Attributed source is narrative (Wikipedia, news, Grokipedia)
3. Evidence from attributed source contains secondary attribution: {citing, according to, study by, research from}
4. If claim treats secondary as primary → laundering

**Downgrade**: UNCERTAIN (0.50 confidence) — often acceptable simplification

**Determinism**: Source type classification from evidence metadata

---

#### CIRCULAR_EVIDENCE

**Definition**: Claim appears to be supported by evidence that itself derives from the claim or its source.

**Structural Pattern**:
```
Claim C supported by Evidence E
where E.source = C.source OR E cites C
```

**Examples**:
- Press release claim verified by article quoting the press release
- Wikipedia claim verified by blog citing Wikipedia

**Detection Phase**: Phase 4 (verification) — cross-reference evidence sources

**Evidence Trigger**:
1. Track original claim source (if available from document metadata)
2. For each evidence item, check if source URL/domain matches claim source
3. Check Wikipedia evidence for citations that lead back to claim source
4. If evidence provenance traces to claim origin → circular

**Downgrade**: INSUFFICIENT_EVIDENCE (evidence excluded from consideration)

**Determinism**: URL/domain comparison; no probabilistic source attribution

---

## 3. Detection Architecture

### 3.1 Phase Integration Matrix

| Hallucination Type | Detection Phase | Requires Evidence | Pre-Filterable |
|-------------------|-----------------|-------------------|----------------|
| AUTHORITY_BLEED | 3 (pre-filter) | No | Yes |
| ENTITY_ROLE_CONFLICT | 4 | Yes (Wikidata) | No |
| TEMPORAL_FABRICATION | 4 | Yes (Wikidata) | No |
| COURT_AUTHORITY_MISATTRIBUTION | 4 | Yes (Wikipedia) | No |
| IMPOSSIBLE_DOSAGE | 3 (pre-filter) | No | Yes |
| SCOPE_OVERGENERALIZATION | 3 (pre-filter) | No | Yes |
| UNSUPPORTED_SPECIFICITY | 5 | Yes (all) | No |
| EXPERTISE_DOMAIN_VIOLATION | 4 | Yes (Wikidata) | No |
| COLLECTIVE_TO_INDIVIDUAL | 5 | Yes (Wikidata) | No |
| ANACHRONISTIC_ATTRIBUTION | 4 | Yes (Wikidata) | No |
| TEMPORAL_COMPRESSION | 4 | Yes (Wikidata) | No |
| JURISDICTION_OVERREACH | 4 | Yes (Wikidata) | No |
| SAMPLE_TO_POPULATION | 5 | Yes (Wikipedia) | No |
| ILLICIT_CAUSAL_CHAIN | 5 | Yes (Wikidata) | No |
| CORRELATION_AS_CAUSATION | 5 | Yes (Wikipedia) | No |
| POST_HOC_ATTRIBUTION | 5 | No (pattern) | Partial |
| SOURCE_LAUNDERING | 5 | Yes (metadata) | No |
| CIRCULAR_EVIDENCE | 4 | Yes (metadata) | No |

### 3.2 Detection Pipeline Flow

```
Phase 3: Structural Pre-Filter (No Evidence Required)
├── AUTHORITY_BLEED
├── IMPOSSIBLE_DOSAGE
├── SCOPE_OVERGENERALIZATION
└── POST_HOC_ATTRIBUTION (partial: pattern only)

Phase 4: Evidence-Based Detection (During Verification)
├── ENTITY_ROLE_CONFLICT
├── TEMPORAL_FABRICATION
├── COURT_AUTHORITY_MISATTRIBUTION
├── EXPERTISE_DOMAIN_VIOLATION
├── ANACHRONISTIC_ATTRIBUTION
├── TEMPORAL_COMPRESSION
├── JURISDICTION_OVERREACH
└── CIRCULAR_EVIDENCE

Phase 5: Post-Verification Detection (After Verdict)
├── UNSUPPORTED_SPECIFICITY
├── COLLECTIVE_TO_INDIVIDUAL
├── SAMPLE_TO_POPULATION
├── ILLICIT_CAUSAL_CHAIN
├── CORRELATION_AS_CAUSATION
├── SOURCE_LAUNDERING
└── POST_HOC_ATTRIBUTION (full: with evidence gap check)
```

### 3.3 Severity Classification

**CRITICAL** (→ REFUTED):
- ENTITY_ROLE_CONFLICT
- TEMPORAL_FABRICATION
- ANACHRONISTIC_ATTRIBUTION
- COURT_AUTHORITY_MISATTRIBUTION
- IMPOSSIBLE_DOSAGE
- SCOPE_OVERGENERALIZATION
- EXPERTISE_DOMAIN_VIOLATION
- JURISDICTION_OVERREACH

**NON_CRITICAL** (→ UNCERTAIN, blocks SUPPORTED):
- AUTHORITY_BLEED
- UNSUPPORTED_SPECIFICITY
- COLLECTIVE_TO_INDIVIDUAL
- TEMPORAL_COMPRESSION
- SAMPLE_TO_POPULATION
- ILLICIT_CAUSAL_CHAIN
- CORRELATION_AS_CAUSATION
- POST_HOC_ATTRIBUTION
- SOURCE_LAUNDERING

**EXCLUSIONARY** (→ INSUFFICIENT_EVIDENCE, evidence discarded):
- CIRCULAR_EVIDENCE

---

## 4. Detection Rules (Pseudo-Specification)

### 4.1 EXPERTISE_DOMAIN_VIOLATION

```
Input: claim, evidence
Output: hallucination_flag or None

1. IF subject_entity.resolution_status != RESOLVED:
     RETURN None

2. subject_domains = query_wikidata(subject_entity.id, [P101, P106, P452])

3. IF object_entity.resolution_status == RESOLVED:
     object_domains = infer_domain_from_type(object_entity.id)
   ELSE:
     object_domains = infer_domain_from_keywords(claim.object)

4. overlap = domain_ontology_intersection(subject_domains, object_domains)

5. IF overlap.is_empty():
     RETURN {
       type: EXPERTISE_DOMAIN_VIOLATION,
       severity: CRITICAL,
       reason: f"Domain mismatch: {subject_domains} vs {object_domains}",
       score: 0.90
     }

6. RETURN None
```

### 4.2 ANACHRONISTIC_ATTRIBUTION

```
Input: claim, evidence
Output: hallucination_flag or None

1. claim_year = extract_year(claim.claim_text)
   IF claim_year is None:
     RETURN None

2. subject_inception = query_wikidata(subject_entity.id, P571)
   IF subject_inception and parse_year(subject_inception) > claim_year:
     RETURN {
       type: ANACHRONISTIC_ATTRIBUTION,
       severity: CRITICAL,
       reason: f"Subject did not exist in {claim_year} (inception: {subject_inception})",
       score: 0.95
     }

3. object_inception = query_wikidata(object_entity.id, P571)
   IF object_inception and parse_year(object_inception) > claim_year:
     RETURN {
       type: ANACHRONISTIC_ATTRIBUTION,
       severity: CRITICAL,
       reason: f"Object did not exist in {claim_year} (inception: {object_inception})",
       score: 0.95
     }

4. RETURN None
```

### 4.3 ILLICIT_CAUSAL_CHAIN

```
Input: claim, evidence
Output: hallucination_flag or None

1. IF not contains_causal_predicate(claim.predicate):
     RETURN None

2. subject_id = claim.subject_entity.entity_id
   object_id = claim.object_entity.entity_id

3. IF subject_id is None or object_id is None:
     RETURN None  # Can't verify chain

4. direct_link = query_wikidata_relation(subject_id, object_id, [P1542, P828])
   IF direct_link:
     RETURN None  # Direct causal relation exists

5. intermediate_paths = find_causal_paths(subject_id, object_id, max_depth=2)
   IF intermediate_paths.is_empty():
     RETURN {
       type: ILLICIT_CAUSAL_CHAIN,
       severity: NON_CRITICAL,
       reason: "No verifiable causal chain in knowledge base",
       score: 0.70
     }

6. RETURN None
```

---

## 5. Determinism Guarantees

### 5.1 Fixed Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Domain traversal depth | 3 | Balance precision vs. API calls |
| Jurisdiction traversal depth | 5 | Country → State → City |
| Temporal gap threshold | 5 years | Avoids over-flagging |
| Causal path max depth | 2 | Direct or one-hop |
| Approximate numeric tolerance | 5% | Standard rounding |

### 5.2 Keyword Sets (Immutable)

All keyword sets are defined as frozen sets in detector initialization:
- `CAUSAL_PREDICATES`
- `SOLE_AUTHORSHIP_PREDICATES`
- `COLLECTIVE_MODIFIERS`
- `UNIVERSAL_MARKERS`
- `STUDY_LIMITING_LANGUAGE`
- `CORRELATION_LANGUAGE`
- `CAUSATION_LANGUAGE`

### 5.3 Non-Deterministic Edge Cases

The following produce UNCERTAIN rather than false confidence:
1. Entity not resolved → skip check, do not flag
2. Wikidata property missing → skip check, do not flag
3. Ambiguous domain classification → do not flag

---

## 6. Integration Points

### 6.1 Module: `hallucination_detector.py`

**Current Structure**:
```python
class HallucinationDetector:
    def detect_structural(claim) -> Optional[Dict]  # Pre-filter
    def detect(claim, evidence) -> List[Dict]       # Full detection
```

**Proposed Extension**:
```python
class HallucinationDetector:
    # Phase 3: Pre-filter (existing)
    def detect_structural(claim) -> Optional[Dict]

    # Phase 4: Evidence-based (extended)
    def detect_with_evidence(claim, evidence) -> List[Dict]

    # Phase 5: Post-verification (new)
    def detect_post_verification(claim, evidence, verdict) -> List[Dict]

    # Unified entry (for orchestrator)
    def detect(claim, evidence, phase="all") -> List[Dict]
```

### 6.2 Module: `claim_verifier.py`

**Current**: Calls `detector.detect(claim, evidence)` after verdict assignment

**Proposed**:
1. Call `detector.detect_with_evidence(claim, evidence)` before verdict
2. Use CRITICAL results to set verdict = REFUTED
3. Call `detector.detect_post_verification(claim, evidence, verdict)` after verdict
4. Use NON_CRITICAL results to downgrade SUPPORTED → UNCERTAIN

### 6.3 Module: `run_full_audit.py`

**Current**: Pre-filter in Phase 3, merged detection in Phase 4/5

**Proposed**: No structural change; detector encapsulates phase logic

### 6.4 New Module: `domain_classifier.py` (Required)

Maps entities to domains using Wikidata ontology:
```python
class DomainClassifier:
    def get_entity_domains(entity_id: str) -> Set[str]
    def get_object_domain(object_text: str) -> Set[str]
    def domains_overlap(d1: Set, d2: Set) -> bool
```

### 6.5 New Module: `causal_graph.py` (Required)

Queries Wikidata for causal relations:
```python
class CausalGraph:
    def has_direct_causal_link(subj_id: str, obj_id: str) -> bool
    def find_causal_path(subj_id: str, obj_id: str, max_depth: int) -> List
```

---

## 7. Evaluation Metrics

### 7.1 Per-Hallucination Metrics

- **Precision**: True flags / All flags
- **Recall**: True flags / All actual hallucinations (requires labeled corpus)
- **False Positive Rate**: False flags / Total non-hallucinations

### 7.2 System-Level Metrics

- **Structural Detection Rate**: Structural flags / Total claims
- **Downgrade Accuracy**: Correct downgrades / Total downgrades
- **Determinism Score**: Variance across N runs (should be 0.0)

### 7.3 Golden Test Case Categories

Add to `evaluation/golden_cases.json`:
```json
{
  "category": "hallucination_expertise_domain",
  "category": "hallucination_anachronistic",
  "category": "hallucination_collective",
  "category": "hallucination_jurisdiction",
  "category": "hallucination_sample_population",
  "category": "hallucination_causal_chain",
  "category": "hallucination_correlation",
  "category": "hallucination_posthoc",
  "category": "hallucination_source_laundering",
  "category": "hallucination_circular"
}
```

---

## 8. Limitations and Non-Goals

### 8.1 Explicitly Out of Scope

1. **Semantic reasoning beyond keyword matching**: No NLU, no embeddings
2. **Probabilistic causation**: No Bayesian networks, no causal inference models
3. **Dynamic knowledge base updates**: Wikidata state at query time is authoritative
4. **Multi-hop inference chains beyond depth 2**: Computational and precision limits
5. **Context-dependent hallucinations**: No discourse analysis

### 8.2 Known Failure Modes

1. **Novel entities**: If subject/object not in Wikidata, checks are skipped
2. **Domain ambiguity**: Interdisciplinary work may false-positive on EXPERTISE_DOMAIN
3. **Legitimate simplification**: COLLECTIVE_TO_INDIVIDUAL may flag acceptable shorthand
4. **Historical anachronism edge cases**: Retroactive naming (e.g., "Byzantine Empire")

### 8.3 Mitigation Strategy

For known failure modes, the framework:
1. Returns UNCERTAIN rather than REFUTED
2. Provides detailed `reason` string for manual review
3. Logs `decision_reason` for downstream analysis

---

## 9. Summary

This framework extends the existing hallucination detector with 10 new structural failure types, organized into 5 categories:

1. **Attribution Failures**: Who did what (EXPERTISE_DOMAIN, COLLECTIVE_TO_INDIVIDUAL)
2. **Temporal Failures**: When things happened (ANACHRONISTIC, TEMPORAL_COMPRESSION)
3. **Scope Failures**: How broadly claims apply (JURISDICTION, SAMPLE_TO_POPULATION)
4. **Inference Failures**: How conclusions are drawn (CAUSAL_CHAIN, CORRELATION, POST_HOC)
5. **Source Failures**: Where information comes from (SOURCE_LAUNDERING, CIRCULAR)

All detection is rule-based, deterministic, and integrates into the existing 5-phase pipeline without new ML models or external APIs beyond Wikidata/Wikipedia.

---

*Document Version*: 2.0
*Author*: Epistemic Audit Engine Research Team
*Status*: Design Only — No Implementation
