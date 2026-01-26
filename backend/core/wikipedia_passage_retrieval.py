import requests
import re
import spacy
from typing import List, Dict, Optional, Any
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    SentenceTransformer = None
    cosine_similarity = None

class WikipediaPassageRetriever:
    def __init__(self):
        self.API_URL = "https://en.wikipedia.org/w/api.php"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "EpistemicAuditEngine/1.0 (Research Project)"
        })
        
        # Load NLP
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            self.nlp = None
            print("Warning: Spacy model 'en_core_web_sm' not found. Entity filtering will be degraded.")

        # Load SBERT
        self.model = None
        if SentenceTransformer:
            try:
                # Using a small, fast model
                print("Loading SBERT model (all-MiniLM-L6-v2)...")
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                print(f"Warning: Failed to load SBERT model: {e}")

    def extract_passages(self, wiki_url: str, claim_text: str, max_passages: int = 2) -> List[Dict[str, Any]]:
        """
        Fetches, segments, scores, and filters passages from a Wikipedia URL.
        Returns a list of evidence objects.
        """
        if not wiki_url or "wikipedia.org" not in wiki_url:
            return []

        title = self._extract_title_from_url(wiki_url)
        if not title:
            return []

        # 1. Fetch Content
        text_content = self._fetch_plain_text(title)
        if not text_content:
            return []

        # 2. Segment into Paragraphs
        paragraphs = self._segment_paragraphs(text_content)
        if not paragraphs:
            return []

        # 3. Score Paragraphs
        scored_passages = self._score_passages(paragraphs, claim_text)

        # 4. Filter & Select
        selected = []
        for p in scored_passages:
            if len(selected) >= max_passages:
                break
            
            # Acceptance Thresholds
            if p["score"] >= 0.65 and self._has_relevant_entities(p["text"]):
                selected.append({
                    "source": "wikipedia",
                    "url": wiki_url,
                    "snippet": p["text"],
                    "score": float(p["score"]),
                    "textual_evidence": True
                })

        # Epistemic Fallback: If no passages selected, return structurally valid object with null snippet
        if not selected:
            return [{
                "source": "wikipedia",
                "url": wiki_url,
                "snippet": None,
                "score": 0.0,
                "textual_evidence": False
            }]

        return selected

    def _extract_title_from_url(self, url: str) -> Optional[str]:
        try:
            # https://en.wikipedia.org/wiki/Steve_Jobs -> Steve_Jobs
            parts = url.split("/wiki/")
            if len(parts) > 1:
                return parts[1]
        except:
            pass
        return None

    def _fetch_plain_text(self, title: str) -> str:
        params = {
            "action": "query",
            "prop": "extracts",
            "titles": title,
            "explaintext": 1,
            "format": "json",
            "redirects": 1
        }
        try:
            resp = self.session.get(self.API_URL, params=params, timeout=5)
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for pid, page in pages.items():
                if pid == "-1": continue
                return page.get("extract", "")
        except Exception:
            pass
        return ""

    def _segment_paragraphs(self, text: str) -> List[str]:
        # Split by double newlines
        raw_paras = text.split("\n\n")
        clean_passages = []
        
        for p in raw_paras:
            p = p.strip()
            # Heuristic: Must be at least 100 chars
            if len(p) < 100: continue
            if p.startswith("==") or p.startswith("Not to be confused"): continue
            
            # Sub-segment large paragraphs to avoid SBERT truncation (Max 256 tokens approx 1000 chars)
            # We use a safer limit of 800 chars to trigger splitting
            if len(p) > 800:
                sub_chunks = self._split_long_paragraph(p)
                clean_passages.extend(sub_chunks)
            else:
                clean_passages.append(p)
            
        return clean_passages

    def _split_long_paragraph(self, text: str) -> List[str]:
        """
        Splits a long paragraph into sliding windows of sentences.
        """
        if not self.nlp:
            # Fallback naive chunking if SpaCy failed
            return [text[i:i+800] for i in range(0, len(text), 600)]
            
        doc = self.nlp(text)
        sents = [s.text for s in doc.sents]
        
        chunks = []
        # Sliding window: 3 sentences, stride 2
        window_size = 3
        stride = 2
        
        if len(sents) <= window_size:
            return [text]

        for i in range(0, len(sents), stride):
            chunk_sents = sents[i:i+window_size]
            chunk = " ".join(chunk_sents)
            if len(chunk) > 60: 
                chunks.append(chunk)
            
            if i + window_size >= len(sents):
                break
                
        return chunks

    def _score_passages(self, paragraphs: List[str], claim_text: str) -> List[Dict[str, Any]]:
        if not self.model or not cosine_similarity:
            return []

        # Encode claim
        claim_emb = self.model.encode([claim_text])
        
        # Encode paragraphs
        para_embs = self.model.encode(paragraphs)
        
        # Compute cosine similarity
        scores = cosine_similarity(claim_emb, para_embs)[0]
        
        scored = []
        for i, score in enumerate(scores):
            scored.append({
                "text": paragraphs[i],
                "score": score
            })
            
        # Sort descending
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    def _has_relevant_entities(self, text: str) -> bool:
        """
        Checks for Named Entities (ORG, PERSON, DATE, GPE) or Numbers.
        """
        # 1. Regex Heuristics (Fast)
        # Year pattern
        if re.search(r'\b(19|20)\d{2}\b', text):
            return True
            
        # 2. NLP check
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PERSON", "GPE", "DATE", "EVENT", "loc"]:
                    return True
        else:
            # Fallback Capitalization Check
            # At least 2 capitalized words (excluding start of sentence)?
            caps = re.findall(r'\b[A-Z][a-z]+\b', text)
            if len(caps) > 2: return True

        return False
