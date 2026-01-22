import unittest
from unittest.mock import MagicMock, patch
from evidence_retriever import EvidenceRetriever

class TestPhase3Evidence(unittest.TestCase):
    def setUp(self):
        self.retriever = EvidenceRetriever()

    @patch("evidence_retriever.requests.Session.get")
    def test_wikidata_direction_founded(self, mock_get):
        # "Steve Jobs founded Apple" -> Predicate "founded" -> Queries OBJECT (Apple, Q312)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "entities": {
                "Q312": { # Apple
                    "claims": {
                        "P571": [ # Inception
                            {
                                "mainsnak": {
                                    "snaktype": "value",
                                    "datavalue": {
                                        "value": {"time": "+1976-04-01T00:00:00Z"}
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        mock_get.return_value = mock_resp

        claim = {
            "claim_id": "1",
            "subject_entity": {"entity_id": "Q19837", "resolution_status": "RESOLVED"}, # Jobs
            "predicate": "founded",
            "object_entity": {"entity_id": "Q312", "resolution_status": "RESOLVED"}, # Apple
            "claim_type": "RELATION"
        }
        
        # We assume mapper maps "founded" to P571/P112
        processed = self.retriever.retrieve_evidence({"claims": [claim]})["claims"][0]
        
        # Verify the mock was called with ids=Q312 (Apple), NOT Q19837 (Jobs)
        call_args = mock_get.call_args[1]["params"]
        self.assertEqual(call_args["ids"], "Q312") 
        
        # Verify alignment metadata
        ev = processed["evidence"]["wikidata"][0]
        self.assertTrue("alignment" in ev)
        self.assertTrue(ev["alignment"]["subject_match"])
        self.assertTrue(ev["alignment"]["predicate_match"])
        # Object match logic: Value is timestamp. Target QID is Jobs (Q19837).
        # Timestamp != Jobs QID. So object_match should be False (or None logic). 
        # But for Inception, value is date. Target QID (Subject) is person.
        # Wait, if I query "Apple" for "founded/inception", Subject is Person.
        # But Inception P571 value is Date. Founded By P112 value is Person.
        # If I get P571, value is date. Target QID was Jobs.
        # So object_match is False. Correct.
        self.assertFalse(ev["alignment"]["object_match"])

    @patch("evidence_retriever.GrokipediaClient.fetch_excerpt")
    def test_grokipedia_gating(self, mock_fetch):
        # TEMPORAL claim should BLOCK Grokipedia
        mock_fetch.return_value = {"excerpt": "Narrative."}
        
        claim = {
             "subject_entity": {
                 "canonical_name": "Steve Jobs",
                 "resolution_status": "RESOLVED",
                 "source_status": {"grokipedia": "VERIFIED"}
             },
             "predicate": "born",
             "claim_type": "TEMPORAL" # Should block
        }
        
        # Mock others failing
        with patch.object(self.retriever, '_fetch_wikidata_statements', return_value=[]), \
             patch.object(self.retriever.wiki_fetcher, 'fetch_sentences', return_value=[]):
             
             processed = self.retriever.retrieve_evidence({"claims": [claim]})["claims"][0]
             
        # Should be SKIPPED
        self.assertEqual(len(processed["evidence"]["grokipedia"]), 0)
        self.assertEqual(processed["evidence_status"]["grokipedia"], "SKIPPED")

    def test_evidence_id_determinism(self):
        source = "WIKIPEDIA"
        content = "Steve Jobs founded Apple."
        id1 = self.retriever._generate_evidence_id(source, content)
        id2 = self.retriever._generate_evidence_id(source, content)
        self.assertEqual(id1, id2)
        
    @patch("evidence_retriever.WikipediaFetcher.fetch_sentences")
    def test_wikipedia_lemmatization(self, mock_fetch):
        # "founded" vs "founding"
        mock_fetch.return_value = [
            {"text": "The founding of Apple was key.", "url": "wiki"},
            {"text": "He ate apples.", "url": "wiki"}
        ]
        
        claim = {
            "subject_entity": {"text": "Apple", "source_status": {"wikipedia": "VERIFIED"}},
            "predicate": "founded",
            "claim_type": "RELATION"
        }
        
        processed = self.retriever.retrieve_evidence({"claims": [claim]})["claims"][0]
        wiki_ev = processed["evidence"]["wikipedia"]
        
        # Should match "founding" with "founded"
        self.assertEqual(len(wiki_ev), 1)
        self.assertEqual(wiki_ev[0]["sentence"], "The founding of Apple was key.")
        self.assertTrue(wiki_ev[0]["alignment"]["predicate_match"])

    @patch("evidence_retriever.requests.Session.get")
    def test_temporal_mismatch(self, mock_get):
        # Claim: "founded in 1977". Evidence: 1976.
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "entities": {
                "Q312": {
                    "claims": {
                        "P571": [
                            {
                                "mainsnak": {
                                    "snaktype": "value",
                                    "datavalue": {"value": {"time": "+1976-04-01T00:00:00Z"}}
                                }
                            }
                        ]
                    }
                }
            }
        }
        mock_get.return_value = mock_resp

        claim = {
            "claim_id": "1",
            "subject_entity": {"entity_id": "Q19837", "resolution_status": "RESOLVED"},
            "predicate": "founded",
            "object_entity": {"entity_id": "Q312", "resolution_status": "RESOLVED"},
            "claim_text": "Steve Jobs founded Apple in 1977", # Mismatch year
            "claim_type": "TEMPORAL"
        }
        
        processed = self.retriever.retrieve_evidence({"claims": [claim]})["claims"][0]
        ev = processed["evidence"]["wikidata"][0]
        
        # Should be False due to mismatch
        self.assertFalse(ev["alignment"]["temporal_match"])
        self.assertTrue(ev["alignment"]["subject_match"])

    @patch("evidence_retriever.WikipediaFetcher.fetch_sentences")
    def test_token_subject_match(self, mock_fetch):
        # "Jobs founded..." matches "Steve Jobs" via Token "Jobs"
        mock_fetch.return_value = [
            {"text": "Jobs founded Apple in 1976.", "url": "wiki"},
            {"text": "He founded Apple.", "url": "wiki"}
        ]
        
        claim = {
            # Canonical: Steve Jobs. Text: Steve Jobs.
            "subject_entity": {"canonical_name": "Steve Jobs", "text": "Steve Jobs", "source_status": {"wikipedia": "VERIFIED"}},
            "predicate": "founded",
            "claim_text": "Steve Jobs founded Apple in 1976",
            "claim_type": "RELATION"
        }
        
        processed = self.retriever.retrieve_evidence({"claims": [claim]})["claims"][0]
        wiki_ev = processed["evidence"]["wikipedia"]
        
        # Expect 1 sentences: "Jobs founded..."
        # "He founded..." should fail subject alignment (Pronoun excluded from tokens)
        
        self.assertEqual(len(wiki_ev), 1)
        self.assertEqual(wiki_ev[0]["sentence"], "Jobs founded Apple in 1976.")
        self.assertTrue(wiki_ev[0]["alignment"]["subject_match"])

    @patch("evidence_retriever.WikipediaFetcher.fetch_sentences")
    def test_pronoun_filter(self, mock_fetch):
         mock_fetch.return_value = [{"text": "He founded Apple.", "url": "wiki"}]
         claim = {
            "subject_entity": {"canonical_name": "Steve Jobs", "text": "Steve Jobs", "source_status": {"wikipedia": "VERIFIED"}},
            "predicate": "founded",
            "claim_type": "RELATION"
         }
         processed = self.retriever.retrieve_evidence({"claims": [claim]})["claims"][0]
         # Should be empty because "He" does not match "Steve" or "Jobs" tokens
         self.assertEqual(len(processed["evidence"]["wikipedia"]), 0)

if __name__ == "__main__":
    unittest.main()
