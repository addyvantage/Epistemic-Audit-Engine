import requests
from typing import Dict, Optional

class GrokipediaClient:
    def __init__(self):
        # Fictional endpoint or mocked
        self.BASE_URL = "https://grokipedia.com/api" 
        self.session = requests.Session()
        
    def fetch_excerpt(self, entity_name: str) -> Optional[Dict[str, str]]:
        """
        Fetches a short excerpt from Grokipedia.
        Real implementation would query an API.
        For this prototype, we simulate or assume fail if not mocked.
        But we must honor the "No Generation" rule.
        """
        page_name = entity_name.replace(" ", "_")
        url = f"https://grokipedia.com/page/{page_name}"
        
        # In a real scenario:
        # resp = self.session.get(f"{self.BASE_URL}/excerpt?page={page_name}")
        # if resp.ok: return ...
        
        # Here we return None by default so tests can mock it.
        # Logic is: "Can support / Can never override".
        return None 
