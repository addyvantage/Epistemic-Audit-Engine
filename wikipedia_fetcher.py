import requests
from typing import List, Dict, Optional
import spacy

class WikipediaFetcher:
    def __init__(self):
        self.API_URL = "https://en.wikipedia.org/w/api.php"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "EpistemicAuditEngine/1.0 (Research Project)"
        })
        try:
             self.nlp = spacy.load("en_core_web_sm")
        except:
             self.nlp = None

    def fetch_sentences(self, page_title: str) -> List[Dict[str, str]]:
        """
        Fetches page content and segments into sentences.
        Returns list of { "text": ..., "section": ... }
        """
        if not page_title: 
            return []

        # 1. Fetch extracts (intro + sections)
        # Using 'extracts' prop with 'explaintext' for plain text
        params = {
            "action": "query",
            "prop": "extracts",
            "titles": page_title,
            "explaintext": 1,
            "format": "json",
            "redirects": 1
        }
        
        try:
            resp = self.session.get(self.API_URL, params=params, timeout=5)
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            sentences = []
            
            for pid, page in pages.items():
                if pid == "-1": continue # Missing
                
                full_text = page.get("extract", "")
                if not full_text: continue
                
                # Naive section splitting by newlines or rely on Spacy for whole doc
                # Extracts usually return full text. 
                # Better to use 'plain' text and split.
                
                if self.nlp:
                    doc = self.nlp(full_text)
                    for sent in doc.sents:
                        text = sent.text.strip()
                        if len(text) > 10:
                            sentences.append({
                                "text": text,
                                "section": "Body", # We ignore section parsing for simple extract
                                "url": f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
                            })
                else:
                    # Fallback naive splitting
                    raw_sents = full_text.split(". ")
                    for s in raw_sents:
                         if len(s) > 10:
                            sentences.append({
                                "text": s + ".",
                                "section": "Body",
                                "url": f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
                            })
                            
            return sentences
            
        except Exception:
            return []
