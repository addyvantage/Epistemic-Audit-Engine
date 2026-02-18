import logging
import re
import copy
from html import unescape
from typing import List, Dict, Optional, Any
from urllib.parse import quote, urlparse, parse_qs

import requests
import spacy

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

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
        self.request_timeout_s = 8.0

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
        self._parse_cache: Dict[str, Dict[str, Any]] = {}
        self._revision_cache: Dict[str, Optional[int]] = {}
        self._passage_cache: Dict[str, List[Dict[str, Any]]] = {}

    def extract_passages(self, wiki_url: str, claim_text: str, max_passages: int = 2) -> List[Dict[str, Any]]:
        """
        Extract high-signal narrative snippets copied directly from Wikipedia parse HTML,
        with stable oldid-backed links when available.
        """
        title = self._extract_title_from_url(wiki_url)
        if not title:
            return []
        cache_key = f"{title}|{claim_text.strip().lower()}|{int(max_passages)}"
        cached = self._passage_cache.get(cache_key)
        if cached is not None:
            return copy.deepcopy(cached)

        parsed = self._fetch_parsed_page(title)
        if not parsed.get("html"):
            return []

        revision_id = self._fetch_revision_id(title)
        sentence_records = self._extract_sentence_records(parsed["html"], parsed.get("sections", []))
        if not sentence_records:
            return []

        scored_records = self._score_sentences(sentence_records, claim_text)
        selected = self._select_top_sentences(scored_records, max_passages=max_passages)

        evidence_items: List[Dict[str, Any]] = []
        for record in selected:
            section_anchor = record.get("anchor") or self._fallback_section_anchor(
                claim_text,
                record.get("sentence", ""),
                parsed.get("sections", []),
            )
            url = self._build_stable_url(title, revision_id, section_anchor)
            explanation = self._build_explanation(record.get("matched_terms", {}))

            evidence_items.append({
                "source": "wikipedia",
                "url": url,
                "snippet": record.get("sentence", ""),
                "sentence": record.get("sentence", ""),
                "score": float(record.get("score", 0.0)),
                "textual_evidence": True,
                "section_anchor": section_anchor,
                "matched_terms": record.get("matched_terms", {}),
                "explanation": explanation,
            })

        self._passage_cache[cache_key] = copy.deepcopy(evidence_items)
        return evidence_items

    def _extract_title_from_url(self, url: str) -> Optional[str]:
        try:
            if "/wiki/" in url:
                title = url.split("/wiki/", 1)[1].split("#", 1)[0]
                return title.strip()

            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            title = params.get("title", [""])[0]
            return title.strip() or None
        except Exception:
            return None

    def _fetch_parsed_page(self, title: str) -> Dict[str, Any]:
        cached = self._parse_cache.get(title)
        if cached is not None:
            return cached
        params = {
            "action": "parse",
            "page": title,
            "prop": "text|sections",
            "format": "json",
            "redirects": 1,
        }
        try:
            response = self.session.get(self.API_URL, params=params, timeout=self.request_timeout_s)
            response.raise_for_status()
            data = response.json().get("parse", {})
            html = data.get("text", {}).get("*", "")
            sections = data.get("sections", [])
            payload = {"html": html, "sections": sections}
            self._parse_cache[title] = payload
            return payload
        except Exception as exc:
            logger.warning("Failed parse fetch for '%s': %s", title, exc)
            return {"html": "", "sections": []}

    def _fetch_revision_id(self, title: str) -> Optional[int]:
        if title in self._revision_cache:
            return self._revision_cache[title]
        params = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "ids",
            "titles": title,
            "format": "json",
            "redirects": 1,
        }
        try:
            response = self.session.get(self.API_URL, params=params, timeout=self.request_timeout_s)
            response.raise_for_status()
            pages = response.json().get("query", {}).get("pages", {})
            for page in pages.values():
                revisions = page.get("revisions", [])
                if not revisions:
                    continue
                rev = revisions[0]
                self._revision_cache[title] = rev.get("revid")
                return self._revision_cache[title]
        except Exception:
            self._revision_cache[title] = None
            return None
        self._revision_cache[title] = None
        return None

    def _extract_sentence_records(self, html: str, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if BeautifulSoup:
            return self._extract_with_bs4(html)
        return self._extract_with_regex(html)

    def _extract_with_bs4(self, html: str) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        soup = BeautifulSoup(html, "html.parser")
        root = soup.find("div", class_="mw-parser-output") or soup

        current_anchor = None
        for child in root.children:
            name = getattr(child, "name", None)
            if not name:
                continue

            if name in {"h2", "h3", "h4"}:
                headline = child.find(class_="mw-headline")
                if headline and headline.get("id"):
                    current_anchor = headline.get("id")
                continue

            if name != "p":
                continue

            paragraph = " ".join(child.stripped_strings)
            paragraph = self._clean_text(paragraph)
            if len(paragraph) < 40:
                continue

            for sentence in self._split_sentences(paragraph):
                sentence = self._clean_text(sentence)
                if len(sentence) < 25:
                    continue
                records.append({
                    "sentence": sentence,
                    "anchor": current_anchor,
                })

        return records

    def _extract_with_regex(self, html: str) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        current_anchor = None

        for match in re.finditer(r"<(h[2-4]|p)\b[^>]*>(.*?)</\1>", html, flags=re.IGNORECASE | re.DOTALL):
            tag_name = (match.group(1) or "").lower()
            body = match.group(2) or ""

            if tag_name.startswith("h"):
                anchor_match = re.search(r'class="mw-headline"[^>]*id="([^"]+)"', body)
                if anchor_match:
                    current_anchor = unescape(anchor_match.group(1))
                continue

            text = self._clean_text(re.sub(r"<[^>]+>", " ", body))
            if len(text) < 40:
                continue

            for sentence in self._split_sentences(text):
                sentence = self._clean_text(sentence)
                if len(sentence) < 25:
                    continue
                records.append({
                    "sentence": sentence,
                    "anchor": current_anchor,
                })

        return records

    def _split_sentences(self, text: str) -> List[str]:
        if self.nlp:
            doc = self.nlp(text)
            return [s.text.strip() for s in doc.sents if s.text.strip()]
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

    def _score_sentences(self, records: List[Dict[str, Any]], claim_text: str) -> List[Dict[str, Any]]:
        features = self._extract_claim_features(claim_text)
        semantic_scores = [0.0] * len(records)

        if self.model and cosine_similarity and records:
            try:
                claim_embedding = self.model.encode([claim_text])
                sentence_embeddings = self.model.encode([r["sentence"] for r in records])
                semantic_scores = cosine_similarity(claim_embedding, sentence_embeddings)[0].tolist()
            except Exception as exc:
                logger.debug("SBERT scoring unavailable: %s", exc)

        scored: List[Dict[str, Any]] = []
        for idx, record in enumerate(records):
            sentence = record.get("sentence", "")
            sentence_lower = sentence.lower()

            keyword_hits = [kw for kw in features["keywords"] if kw in sentence_lower]
            year_hits = [year for year in features["years"] if year in sentence]
            number_hits = [num for num in features["numbers"] if num in sentence]

            keyword_score = len(keyword_hits) / max(1, len(features["keywords"])) if features["keywords"] else 0.0
            semantic_score = semantic_scores[idx] if idx < len(semantic_scores) else 0.0

            score = 0.55 * keyword_score + 0.30 * semantic_score
            if year_hits:
                score += 0.12
            if number_hits:
                score += 0.12
            if year_hits and number_hits:
                score += 0.08

            enriched = dict(record)
            enriched["score"] = min(1.0, float(score))
            enriched["matched_terms"] = {
                "keywords": keyword_hits,
                "years": year_hits,
                "numbers": number_hits,
            }
            scored.append(enriched)

        scored.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return scored

    def _select_top_sentences(self, scored: List[Dict[str, Any]], max_passages: int = 2) -> List[Dict[str, Any]]:
        selected: List[Dict[str, Any]] = []
        seen_sentences = set()

        for record in scored:
            if len(selected) >= max_passages:
                break

            sentence = record.get("sentence", "")
            if not sentence or sentence in seen_sentences:
                continue

            word_count = len(sentence.split())
            if word_count > 60:
                continue

            if record.get("score", 0.0) < 0.22 and selected:
                break

            selected.append(record)
            seen_sentences.add(sentence)

        if selected:
            return selected

        if scored:
            fallback = dict(scored[0])
            fallback["sentence"] = self._clip_words(fallback.get("sentence", ""), max_words=60)
            return [fallback]

        return []

    def _fallback_section_anchor(self, claim_text: str, sentence: str, sections: List[Dict[str, Any]]) -> Optional[str]:
        if not sections:
            return None

        combined = f"{claim_text} {sentence}".lower()
        preferred_sections = []
        if any(token in combined for token in ["founded", "founder", "inception", "born", "established"]):
            preferred_sections.append("history")
        if any(token in combined for token in ["revenue", "profit", "income", "financial", "advertising"]):
            preferred_sections.extend(["finance", "financials"])
        if any(token in combined for token in ["headquarters", "located", "based"]):
            preferred_sections.extend(["headquarters", "location"])

        for preferred in preferred_sections:
            for section in sections:
                anchor = section.get("anchor")
                line = (section.get("line") or "").lower()
                if anchor and preferred in line:
                    return anchor

        features = self._extract_claim_features(f"{claim_text} {sentence}")
        keywords = set(features["keywords"])

        best_anchor = None
        best_overlap = 0
        for section in sections:
            anchor = section.get("anchor")
            line = (section.get("line") or "").lower()
            if not anchor or not line:
                continue

            section_tokens = set(re.findall(r"[a-z][a-z0-9_\-]{2,}", line))
            overlap = len(section_tokens.intersection(keywords))
            if overlap > best_overlap:
                best_overlap = overlap
                best_anchor = anchor

        return best_anchor

    def _build_stable_url(self, title: str, revision_id: Optional[int], anchor: Optional[str]) -> str:
        title_encoded = quote(title.replace(" ", "_"), safe="()_:/")
        if revision_id:
            base = f"https://en.wikipedia.org/w/index.php?title={title_encoded}&oldid={revision_id}"
        else:
            base = f"https://en.wikipedia.org/wiki/{title_encoded}"

        if anchor:
            return f"{base}#{quote(anchor, safe=':_-')}"
        return base

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

    def _build_explanation(self, matched_terms: Dict[str, List[str]]) -> str:
        keywords = matched_terms.get("keywords", [])
        years = matched_terms.get("years", [])
        numbers = matched_terms.get("numbers", [])

        parts: List[str] = []
        if keywords:
            parts.append("keyword")
        if years:
            parts.append("year")
        if numbers:
            parts.append("number")

        if not parts:
            return "Matched on topical sentence relevance."

        return "Matched on " + "+".join(parts) + "."

    def _clean_text(self, text: str) -> str:
        text = unescape(text or "")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _clip_words(self, sentence: str, max_words: int = 60) -> str:
        words = sentence.split()
        if len(words) <= max_words:
            return sentence
        return " ".join(words[:max_words]).rstrip() + "..."
