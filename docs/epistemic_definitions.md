# Epistemic Audit Engine: Formal Definitions

This document defines the core epistemic concepts used within the auditing pipeline. These definitions distinguish the system's operational logic from philosophical truth.

## 1. Core Entities

### Claim
A discrete, falsifiable statement extracted from the input text.
- **Structure**: Subject + Predicate + Object (optional) + Modifiers.
- **Scope**: The system processes atomic factual claims (e.g., "Apple released iPhone") and attributed claims (e.g., "The report states X"). Opinions and purely subjective statements are filtered or tagged as `EXISTENTIAL`/`FACTUAL_ATTRIBUTE`.

### Atomic Claim
A claim that cannot be further decomposed without losing its core truth condition.
- **Example**: "Steve Jobs founded Apple in 1976" ->
  1. "Steve Jobs founded Apple" (Relation)
  2. "Apple was founded in 1976" (Temporal)

### Subject Entity
The primary entity about which the claim asserts a property or relation.
- **Resolution**: Subjects are linked to canonical Knowledge Base (KB) identifiers (Wikidata QIDs).
- **Ambiguity**: Unresolved subjects increase epistemic risk (Instability).

### Object Entity
The target entity or value in a relational claim.

## 2. Verification Verdicts

Verdicts represent the system's confidence in the claim's alignment with authoritative evidence, **not** binary absolute truth.

| Verdict | Definition | Epistemic Implication |
| :--- | :--- | :--- |
| **SUPPORTED** (`Emerald`) | Evaluation finds explicit, authoritative evidence (Wikidata/Wikipedia) matching the claim's subject, predicate, and object. | The user can trust this statement is grounded in the KB. |
| **SUPPORTED_WEAK** (`Lime`) | Evidence supports the core claim but lacks density, or the claim is a canonical fact (e.g. "founded") inferred from strong entity resolution despite evidence gating. | Likely true/canonical, but less rigorously corroborated than `SUPPORTED`. |
| **INSUFFICIENT_EVIDENCE** (`Amber`) | No confirming or refuting evidence found in the KB. Logic cannot determine truth value. | Epistemic ignorance. The system does not know. **Not a hallucination**. |
| **REFUTED** (`Red`) | Authoritative evidence explicitly contradicts the claim (e.g., Object Mismatch on a functional property, or Temporal Contradiction). | The statement is epistemically false according to the KB. |

## 3. Hallucination Types

Hallucination is defined as **epistemic failure**, not just factual error.

| Type | Name | Definition |
| :--- | :--- | :--- |
| **H1** | **Unsupported Assertion** | A claim involving unresolved entities or totally lacking evidence, presented as fact. |
| **H2** | **Fabricated Specificity** | Asserting precise numeric/temporal details (e.g., "sold 13.2 million units") without any evidence match. |
| **H3** | **Overconfidence** | High linguistic certainty ("definitely", "proven") applied to a claim with `INSUFFICIENT_EVIDENCE`. |
| **H4** | **Illegitimate Inference** | (Not currently active in benchmark) Deduction not supported by premises. |
| **H5** | **Inconsistency** | Contradiction between two claims within the same document. |
| **H6** | **Narrative Overreach** | (Not currently active) Broader narrative not supported by atomic facts. |

**Crucial Distinction**: A `REFUTED` claim (e.g., getting a date wrong) is an **Error**, not necessarily a **Hallucination**, unless it also exhibits H2 (Fabricated Specificity).

## 4. Epistemic Metrics

### Epistemic Confidence
A normalized score (0.0 - 1.0) strictly reflecting the strength of evidence.
- `0.0`: Insufficient Evidence.
- `0.6 - 0.9`: Supported (depending on source density/authority).
- `0.9+`: Refuted (high confidence in falsehood).

### Risk Score
A composite metric indicating the danger level of the content.
- **Formula**: `Risk = 0.3 * HallucinationScore + 0.5 * RefutationRatio + 0.2 * UnresolvedRatio`
- **Purpose**: To warn users of content that is either fabricated (Hallucination) or explicitly false (Refutation).

### Canonical Fact Override
A safety mechanism where foundational facts (e.g., "founded", "released") about Resolved entities are forced to `SUPPORTED` status if not explicitly refuted, preventing false positives due to retrieval noise.
