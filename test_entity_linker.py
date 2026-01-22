import unittest
from unittest.mock import MagicMock, patch
from entity_linker import EntityLinker
from entity_models import ResolvedEntity, EntityCandidate

class TestEntityLinker(unittest.TestCase):
    def setUp(self):
        self.linker = EntityLinker()
        
    @patch("entity_linker.requests.Session.get")
    @patch("entity_linker.requests.Session.head")
    def test_link_unambiguous_entity(self, mock_head, mock_get):
        # Mock HEAD for Grokipedia -> 200 OK
        mock_head.return_value.status_code = 200
        
        # Mock Wikidata Search
        mock_search_resp = MagicMock()
        mock_search_resp.json.return_value = {
            "search": [
                {
                    "id": "Q19837",
                    "label": "Steve Jobs",
                    "description": "American business magnate and entrepreneur",
                    "aliases": ["Steven Paul Jobs"]
                }
            ]
        }
        
        # Mock Wikidata Sitelink Check
        mock_sitelink_resp = MagicMock()
        mock_sitelink_resp.json.return_value = {
            "entities": {
                "Q19837": {
                    "sitelinks": {
                        "enwiki": { "title": "Steve Jobs" }
                    }
                }
            }
        }
        
        def side_effect(*args, **kwargs):
            if kwargs["params"]["action"] == "wbsearchentities":
                if "Steve Jobs" in kwargs["params"]["search"]: return mock_search_resp
                return MagicMock(json=lambda: {"search": []})
            elif kwargs["params"]["action"] == "wbgetentities":
                return mock_sitelink_resp
            return MagicMock()
            
        mock_get.side_effect = side_effect
        
        result = self.linker._resolve_entity("Steve Jobs", "SUBJECT")
        self.assertEqual(result.resolution_status, "RESOLVED")
        self.assertEqual(result.source_status["wikipedia"], "VERIFIED")
        self.assertEqual(result.source_status["grokipedia"], "VERIFIED")
        self.assertEqual(result.entity_type, "PERSON")

    @patch("entity_linker.requests.Session.get")
    def test_ambiguity_gap(self, mock_get):
        # Two very similar candidates
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "search": [
                {"id": "Q1", "label": "Jaguar", "description": "Car brand"},
                {"id": "Q2", "label": "Jaguar", "description": "Animal"}
            ]
        }
        # Assuming our simple scorer gives similar scores if query is "Jaguar"
        # Mock the search response
        
        def side_effect(*args, **kwargs):
             if kwargs["params"]["action"] == "wbsearchentities": return mock_resp
             return MagicMock()
        mock_get.side_effect = side_effect
        
        # Force the candidates to have close scores by mocking _score_candidates or trusting logic
        # Our logic gives: "Jaguar" vs "Jaguar (Car)".
        # Query "Jaguar".
        # 1. "Jaguar (Car)": "Jaguar" in Label. Match? Yes. Substring. Score 0.5 + 0.2 = 0.7.
        # 2. "Jaguar (Animal)": Score 0.7.
        # Gap is 0.
        
        res = self.linker._resolve_entity("Jaguar", "SUBJECT")
        self.assertEqual(res.resolution_status, "UNRESOLVED")
        self.assertEqual(res.decision_reason, "Ambiguity gap too small")

    @patch("entity_linker.requests.Session.get")
    @patch("entity_linker.requests.Session.head")
    def test_role_entity(self, mock_head, mock_get):
        mock_head.return_value.status_code = 404 # Grokipedia missing
        
        # CEO Search
        mock_search = MagicMock()
        mock_search.json.return_value = {
             "search": [{
                 "id": "Q484876", "label": "CEO", 
                 "description": "highest-ranking corporate officer"
             }]
        }
        # Sitelink
        mock_site = MagicMock()
        mock_site.json.return_value = {"entities": {"Q484876": {"sitelinks": {}}}} # No enwiki
        
        def side_effect(*args, **kwargs):
            if kwargs["params"]["action"] == "wbsearchentities": return mock_search
            if kwargs["params"]["action"] == "wbgetentities": return mock_site
            return MagicMock()
        mock_get.side_effect = side_effect
        
        res = self.linker._resolve_entity("CEO", "OBJECT")
        self.assertEqual(res.resolution_status, "RESOLVED")
        self.assertEqual(res.entity_type, "ROLE")
        self.assertTrue(res.requires_binding)
        self.assertEqual(res.source_status["grokipedia"], "ABSENT")
        self.assertEqual(res.source_status["wikipedia"], "UNVERIFIED")
        self.assertEqual(res.sources["wikipedia"], "")

if __name__ == "__main__":
    unittest.main()
