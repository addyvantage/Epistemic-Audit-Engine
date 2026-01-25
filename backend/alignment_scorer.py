"""
Claim-Evidence Alignment Scoring Module

Computes numerical alignment scores in [0,1] using:
- Lexical similarity (BM25/TF-IDF cosine)
- Semantic similarity (embedding-based)

Epistemic Rationale:
Alignment scores provide a quantitative measure of how well retrieved evidence
matches the claim. Unlike boolean flags, continuous scores enable:
1. Gradient-based ranking of evidence quality
2. Threshold-based hallucination triggering
3. Calibration analysis for verdict confidence

No new models: Uses existing SBERT (all-MiniLM-L6-v2) from wikipedia_passage_retrieval.
"""

import re
import math
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter
from dataclasses import dataclass, asdict


@dataclass
class AlignmentScores:
    """Container for multi-dimensional alignment scores."""
    lexical_score: float      # BM25/TF-IDF based
    semantic_score: float     # Embedding cosine similarity
    alignment_score: float    # Weighted aggregate
    component_scores: Dict[str, float]  # Detailed breakdown

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AlignmentScorer:
    """
    Computes claim-evidence alignment using lexical and semantic methods.

    Determinism: All computations use fixed parameters and no random initialization.
    """

    # Fixed weights for aggregate score (tuned for epistemic precision)
    LEXICAL_WEIGHT = 0.3
    SEMANTIC_WEIGHT = 0.5
    STRUCTURAL_WEIGHT = 0.2

    # BM25 parameters (standard values)
    BM25_K1 = 1.5
    BM25_B = 0.75

    def __init__(self, sbert_model=None):
        """
        Initialize scorer with optional SBERT model.
        If not provided, semantic scoring falls back to lexical only.
        """
        self.sbert_model = sbert_model
        self._idf_cache = {}

    def compute_alignment(
        self,
        claim: Dict[str, Any],
        evidence_item: Dict[str, Any],
        corpus_stats: Optional[Dict[str, Any]] = None
    ) -> AlignmentScores:
        """
        Compute full alignment scores for a claim-evidence pair.

        Args:
            claim: Claim dict with claim_text, subject, predicate, object
            evidence_item: Evidence dict with sentence/snippet, alignment flags
            corpus_stats: Optional corpus statistics for IDF computation

        Returns:
            AlignmentScores with lexical, semantic, and aggregate scores
        """
        claim_text = claim.get("claim_text", "")
        evidence_text = self._extract_evidence_text(evidence_item)

        # 1. Lexical similarity (BM25-inspired)
        lexical_score = self._compute_lexical_score(claim_text, evidence_text, corpus_stats)

        # 2. Semantic similarity (embedding-based if available)
        semantic_score = self._compute_semantic_score(claim_text, evidence_text, evidence_item)

        # 3. Structural alignment (from boolean flags)
        structural_score, component_scores = self._compute_structural_score(claim, evidence_item)

        # 4. Weighted aggregate
        alignment_score = (
            self.LEXICAL_WEIGHT * lexical_score +
            self.SEMANTIC_WEIGHT * semantic_score +
            self.STRUCTURAL_WEIGHT * structural_score
        )

        # Clamp to [0, 1]
        alignment_score = max(0.0, min(1.0, alignment_score))

        return AlignmentScores(
            lexical_score=round(lexical_score, 4),
            semantic_score=round(semantic_score, 4),
            alignment_score=round(alignment_score, 4),
            component_scores=component_scores
        )

    def _extract_evidence_text(self, evidence_item: Dict[str, Any]) -> str:
        """Extract text content from evidence item."""
        # Priority: sentence > snippet > value (for Wikidata)
        text = evidence_item.get("sentence", "")
        if not text:
            text = evidence_item.get("snippet", "")
        if not text:
            # Wikidata structured value - convert to text
            val = evidence_item.get("value", "")
            if isinstance(val, str) and val.startswith("+"):
                # ISO date format
                text = f"date: {val}"
            elif isinstance(val, str) and val.startswith("Q"):
                # Entity reference
                text = f"entity: {val}"
            else:
                text = str(val)
        return text

    def _compute_lexical_score(
        self,
        claim_text: str,
        evidence_text: str,
        corpus_stats: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Compute lexical similarity using TF-IDF cosine similarity.

        Epistemic Rationale:
        TF-IDF captures term importance relative to corpus,
        identifying when specific claim terms appear in evidence.
        """
        if not claim_text or not evidence_text:
            return 0.0

        # Tokenize
        claim_tokens = self._tokenize(claim_text)
        evidence_tokens = self._tokenize(evidence_text)

        if not claim_tokens or not evidence_tokens:
            return 0.0

        # Build vocabulary
        vocab = set(claim_tokens) | set(evidence_tokens)

        # Compute TF vectors
        claim_tf = Counter(claim_tokens)
        evidence_tf = Counter(evidence_tokens)

        # Compute IDF (simplified - use claim as "corpus" if no stats provided)
        if corpus_stats:
            doc_count = corpus_stats.get("doc_count", 1)
            doc_freq = corpus_stats.get("doc_freq", {})
        else:
            doc_count = 2  # claim + evidence
            doc_freq = {t: 1 for t in vocab}

        # TF-IDF vectors
        claim_vec = []
        evidence_vec = []

        for term in vocab:
            # IDF with smoothing
            df = doc_freq.get(term, 1)
            idf = math.log((doc_count + 1) / (df + 1)) + 1

            # TF with sublinear scaling
            claim_tf_val = 1 + math.log(claim_tf.get(term, 0) + 1) if claim_tf.get(term, 0) > 0 else 0
            evidence_tf_val = 1 + math.log(evidence_tf.get(term, 0) + 1) if evidence_tf.get(term, 0) > 0 else 0

            claim_vec.append(claim_tf_val * idf)
            evidence_vec.append(evidence_tf_val * idf)

        # Cosine similarity
        dot_product = sum(c * e for c, e in zip(claim_vec, evidence_vec))
        claim_norm = math.sqrt(sum(c * c for c in claim_vec))
        evidence_norm = math.sqrt(sum(e * e for e in evidence_vec))

        if claim_norm == 0 or evidence_norm == 0:
            return 0.0

        return dot_product / (claim_norm * evidence_norm)

    def _compute_semantic_score(
        self,
        claim_text: str,
        evidence_text: str,
        evidence_item: Dict[str, Any]
    ) -> float:
        """
        Compute semantic similarity using embeddings.

        Epistemic Rationale:
        Semantic similarity captures meaning beyond lexical overlap,
        identifying paraphrases and conceptual matches.

        Uses existing SBERT score if available, otherwise computes fresh.
        """
        # Check if evidence already has SBERT score (from Wikipedia retrieval)
        existing_score = evidence_item.get("score")
        if existing_score is not None and evidence_item.get("source") == "WIKIPEDIA":
            return float(existing_score)

        # Compute fresh if SBERT model available
        if self.sbert_model is not None:
            try:
                embeddings = self.sbert_model.encode([claim_text, evidence_text])
                # Cosine similarity
                dot = sum(a * b for a, b in zip(embeddings[0], embeddings[1]))
                norm1 = math.sqrt(sum(a * a for a in embeddings[0]))
                norm2 = math.sqrt(sum(b * b for b in embeddings[1]))
                if norm1 > 0 and norm2 > 0:
                    return float(dot / (norm1 * norm2))
            except Exception:
                pass

        # Fallback: use lexical as proxy for semantic
        return self._compute_lexical_score(claim_text, evidence_text, None)

    def _compute_structural_score(
        self,
        claim: Dict[str, Any],
        evidence_item: Dict[str, Any]
    ) -> Tuple[float, Dict[str, float]]:
        """
        Convert boolean alignment flags to numerical score.

        Epistemic Rationale:
        Structural alignment (subject/predicate/object matching) is
        orthogonal to textual similarity - captures relational correctness.
        """
        alignment = evidence_item.get("alignment", {})

        # Component scores
        subject_score = 1.0 if alignment.get("subject_match", False) else 0.0
        predicate_score = 1.0 if alignment.get("predicate_match", False) else 0.0
        object_score = 1.0 if alignment.get("object_match", False) else 0.0

        # Temporal is optional - score 1.0 if matches, 0.5 if N/A, 0.0 if mismatch
        temporal_match = alignment.get("temporal_match")
        if temporal_match is True:
            temporal_score = 1.0
        elif temporal_match is False:
            temporal_score = 0.0
        else:  # None - not applicable
            temporal_score = 0.5

        # Weighted aggregate (predicate most important for epistemic validity)
        structural_score = (
            0.25 * subject_score +
            0.35 * predicate_score +
            0.25 * object_score +
            0.15 * temporal_score
        )

        component_scores = {
            "subject_match_score": subject_score,
            "predicate_match_score": predicate_score,
            "object_match_score": object_score,
            "temporal_match_score": temporal_score,
            "structural_aggregate": round(structural_score, 4)
        }

        return structural_score, component_scores

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for lexical scoring."""
        # Lowercase and extract alphanumeric tokens
        text = text.lower()
        tokens = re.findall(r'\b[a-z0-9]+\b', text)
        # Remove very short tokens and stopwords
        stopwords = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
                     'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                     'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                     'of', 'to', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                     'as', 'into', 'through', 'during', 'before', 'after',
                     'and', 'but', 'or', 'nor', 'so', 'yet', 'both', 'either',
                     'that', 'which', 'who', 'whom', 'whose', 'this', 'these',
                     'it', 'its', 'they', 'them', 'their', 'he', 'she', 'him', 'her'}
        return [t for t in tokens if len(t) > 1 and t not in stopwords]


def enrich_claim_with_alignment(
    claim: Dict[str, Any],
    scorer: AlignmentScorer
) -> Dict[str, Any]:
    """
    Enrich a claim with alignment scores for all evidence items.

    Modifies claim in-place and returns it.
    Adds:
      - claim.alignment_score (best evidence alignment)
      - claim.lexical_score (best lexical)
      - claim.semantic_score (best semantic)
      - Each evidence item gets alignment_scores
    """
    evidence = claim.get("evidence", {})

    best_alignment = 0.0
    best_lexical = 0.0
    best_semantic = 0.0

    for source, items in evidence.items():
        if not isinstance(items, list):
            continue

        for ev_item in items:
            scores = scorer.compute_alignment(claim, ev_item)

            # Store in evidence item
            ev_item["alignment_scores"] = scores.to_dict()

            # Track best scores
            if scores.alignment_score > best_alignment:
                best_alignment = scores.alignment_score
            if scores.lexical_score > best_lexical:
                best_lexical = scores.lexical_score
            if scores.semantic_score > best_semantic:
                best_semantic = scores.semantic_score

    # Store claim-level scores
    claim["alignment_score"] = round(best_alignment, 4)
    claim["lexical_score"] = round(best_lexical, 4)
    claim["semantic_score"] = round(best_semantic, 4)

    return claim
