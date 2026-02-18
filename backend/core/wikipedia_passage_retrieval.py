import logging
import re
import requests
import spacy
from typing import List, Dict, Optional, Any

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    SentenceTransformer = None
    cosine_similarity = None

logger = logging.getLogger(__name__)


class WikipediaPassageRetriever:
    def __init__(self):
        self.API_URL = "https://en.wikipedia.org/w/api.php"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "EpistemicAuditEngine/1.0 (Research Project)"
        })

        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            self.nlp = None
            logger.warning("SpaCy model 'en_core_web_sm' not found. Sentence segmentation will use regex fallback.")

        self.model = None
        if SentenceTransformer:
            try:
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as exc:
                logger.warning("Failed to load SBERT model: %s", exc)

    def extract_passages(self, wiki_url: str, claim_text: str, max_passages: int = 2) -> List[Dict[str, Any]]:
        """
        Fetch, score, and select concise narrative snippets from Wikipedia.
        Returns 1-2 sentence-level snippets with best-effort section anchors.
        """
        if not wiki_url or "wikipedia.org" not in wiki_url:
            return []

        title = self._extract_title_from_url(wiki_url)
        if not title:
            return []

        text_content = self._fetch_plain_text(title)
        if not text_content:
            return []

        sections = self._fetch_sections(title)
        sentences = self._segment_sentences(text_content)
        if not sentences:
            return []

        scored_sentences = self._score_sentences(sentences, claim_text)
        if not scored_sentences:
            return []

        selected: List[Dict[str, Any]] = []
        threshold = 0.35

        for candidate in scored_sentences:
            if len(selected) >= max_passages:
                break
            if candidate["score"] < threshold:
                continue

            sentence = self._trim_words(candidate["text"], max_words=60)
            anchor = self._choose_section_anchor(claim_text, sentence, sections)
            url = f"{wiki_url}#{anchor}" if anchor else wiki_url

            selected.append({
                "source": "wikipedia",
                "url": url,
                "snippet": sentence,
                "sentence": sentence,
                "score": float(candidate["score"]),
                "textual_evidence": True,
                "section_anchor": anchor,
                "matched_terms": candidate.get("matched_terms", {}),
                "explanation": self._build_explanation(candidate.get("matched_terms", {}))
            })

        # If strict threshold misses, return closest sentence rather than null snippet.
        if not selected and scored_sentences:
            best = scored_sentences[0]
            sentence = self._trim_words(best["text"], max_words=60)
            anchor = self._choose_section_anchor(claim_text, sentence, sections)
            url = f"{wiki_url}#{anchor}" if anchor else wiki_url
            selected.append({
                "source": "wikipedia",
                "url": url,
                "snippet": sentence,
                "sentence": sentence,
                "score": float(best["score"]),
                "textual_evidence": True,
                "section_anchor": anchor,
                "matched_terms": best.get("matched_terms", {}),
                "explanation": "Closest narrative sentence found for this claim."
            })

        return selected

    def _extract_title_from_url(self, url: str) -> Optional[str]:
        try:
            parts = url.split("/wiki/")
            if len(parts) > 1:
                return parts[1].split("#")[0]
        except Exception:
            return None
        return None

    def _fetch_plain_text(self, title: str) -> str:
        params = {
            "action": "query",
            "prop": "extracts",
            "titles": title,
            "explaintext": 1,
            "format": "json",
            "redirects": 1,
        }
        try:
            response = self.session.get(self.API_URL, params=params, timeout=7)
            response.raise_for_status()
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            for pid, page in pages.items():
                if pid == "-1":
                    continue
                return page.get("extract", "")
        except Exception as exc:
            logger.warning("Failed to fetch Wikipedia plain text for %s: %s", title, exc)
        return ""

    def _fetch_sections(self, title: str) -> List[Dict[str, str]]:
        params = {
            "action": "parse",
            "page": title,
            "prop": "sections",
            "format": "json",
            "redirects": 1,
        }
        try:
            response = self.session.get(self.API_URL, params=params, timeout=7)
            response.raise_for_status()
            data = response.json()
            return data.get("parse", {}).get("sections", [])
        except Exception:
            return []

    def _segment_sentences(self, text: str) -> List[str]:
        text = text.strip()
        if not text:
            return []

        sentences: List[str] = []
        if self.nlp:
            doc = self.nlp(text)
            for sent in doc.sents:
                clean = sent.text.strip()
                if self._is_candidate_sentence(clean):
                    sentences.append(clean)
        else:
            raw = re.split(r"(?<=[.!?])\s+", text)
            for sent in raw:
                clean = sent.strip()
                if self._is_candidate_sentence(clean):
                    sentences.append(clean)

        return sentences

    def _is_candidate_sentence(self, sentence: str) -> bool:
        if len(sentence) < 35:
            return False
        if sentence.startswith("="):
            return False
        if "may refer to" in sentence.lower():
            return False
        return True

    def _score_sentences(self, sentences: List[str], claim_text: str) -> List[Dict[str, Any]]:
        claim_features = self._extract_claim_features(claim_text)
        claim_keywords = claim_features["keywords"]
        claim_years = claim_features["years"]
        claim_numbers = claim_features["numbers"]

        semantic_scores: List[float] = [0.0 for _ in sentences]
        if self.model and cosine_similarity and sentences:
            try:
                claim_emb = self.model.encode([claim_text])
                sent_emb = self.model.encode(sentences)
                semantic_scores = cosine_similarity(claim_emb, sent_emb)[0].tolist()
            except Exception as exc:
                logger.debug("SBERT scoring failed; using lexical-only scoring: %s", exc)

        scored: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            sent_lower = sentence.lower()

            keyword_hits = [kw for kw in claim_keywords if kw in sent_lower]
            year_hits = [y for y in claim_years if y in sentence]
            number_hits = [n for n in claim_numbers if n in sentence]

            lexical = (len(keyword_hits) / max(1, len(claim_keywords))) if claim_keywords else 0.0
            semantic = semantic_scores[idx] if idx < len(semantic_scores) else 0.0

            score = 0.55 * lexical + 0.35 * semantic
            if year_hits:
                score += 0.15
            if number_hits:
                score += 0.15
            if year_hits and number_hits:
                score += 0.10
            if any(term in sent_lower for term in ["revenue", "advertising", "headquarters", "found", "founded", "acquired", "subsidiary", "parent"]):
                score += 0.08

            scored.append({
                "text": sentence,
                "score": float(min(score, 1.0)),
                "matched_terms": {
                    "keywords": keyword_hits,
                    "years": year_hits,
                    "numbers": number_hits,
                },
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    def _extract_claim_features(self, claim_text: str) -> Dict[str, List[str]]:
        text = (claim_text or "").lower()
        years = re.findall(r"\b(1\d{3}|20\d{2})\b", text)
        numbers = re.findall(r"\b\d+(?:\.\d+)?\b", text)

        stopwords = {
            "the", "and", "for", "with", "from", "that", "this", "was", "were", "are", "is", "in", "on", "of", "to", "by", "as", "at",
            "a", "an", "it", "its", "their", "his", "her", "or", "be", "been", "has", "have", "had", "into", "than", "most"
        }
        tokens = re.findall(r"[a-z][a-z0-9_\-]{2,}", text)
        keywords = [t for t in tokens if t not in stopwords]

        return {
            "keywords": keywords[:20],
            "years": years,
            "numbers": numbers,
        }

    def _choose_section_anchor(self, claim_text: str, sentence: str, sections: List[Dict[str, str]]) -> Optional[str]:
        if not sections:
            return None

        features = self._extract_claim_features(f"{claim_text} {sentence}")
        keywords = set(features["keywords"])

        best_anchor = None
        best_score = 0

        for sec in sections:
            line = (sec.get("line") or "").lower()
            anchor = sec.get("anchor")
            if not line or not anchor:
                continue

            section_tokens = set(re.findall(r"[a-z][a-z0-9_\-]{2,}", line))
            overlap = len(section_tokens.intersection(keywords))

            if overlap > best_score:
                best_score = overlap
                best_anchor = anchor

        return best_anchor if best_score > 0 else None

    def _build_explanation(self, matched_terms: Dict[str, List[str]]) -> str:
        keywords = matched_terms.get("keywords", [])
        years = matched_terms.get("years", [])
        numbers = matched_terms.get("numbers", [])

        parts: List[str] = []
        if keywords:
            parts.append("keyword overlap")
        if years:
            parts.append("year match")
        if numbers:
            parts.append("numeric match")

        if not parts:
            return "Narrative evidence from a relevant Wikipedia sentence."

        return "Matched on " + ", ".join(parts) + "."

    def _trim_words(self, text: str, max_words: int = 60) -> str:
        words = text.split()
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words]).rstrip() + "..."
