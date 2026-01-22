import json
from unittest.mock import MagicMock, patch
from evidence_retriever import EvidenceRetriever

# Inherit from Phase 2 Output
PHASE_2_OUTPUT = "example_entity_output.json"

def run_phase_3_mock():
    # Load Phase 2 Output
    try:
        with open(PHASE_2_OUTPUT, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {PHASE_2_OUTPUT} not found.")
        return

    retriever = EvidenceRetriever()

    # MOCK Wikidata Response
    mock_wd_resp = MagicMock()
    mock_wd_resp.json.return_value = {
        "entities": {
            "Q312": { # Apple
                "claims": {
                    "P571": [ # Inception (founded)
                        {
                            "mainsnak": {
                                "snaktype": "value",
                                "datavalue": {"value": {"time": "+1976-04-01T00:00:00Z"}}
                            }
                        }
                    ]
                }
            },
            "Q19837": { # Steve Jobs
                 "claims": {} 
            }
        }
    }
    
    # MOCK Wikipedia Response
    # For Steve Jobs -> "Steve Jobs founded Apple in 1976."
    mock_wiki_fetch = MagicMock()
    def fetch_side_effect(title):
        if "Steve Jobs" in title:
            return [{"text": "Steve Jobs founded Apple in 1976.", "url": "wiki/Steve_Jobs"}]
        return []
    mock_wiki_fetch.side_effect = fetch_side_effect

    with patch("evidence_retriever.requests.Session.get", return_value=mock_wd_resp), \
         patch("evidence_retriever.WikipediaFetcher.fetch_sentences", side_effect=fetch_side_effect):
         
        result = retriever.retrieve_evidence(data)
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    run_phase_3_mock()
