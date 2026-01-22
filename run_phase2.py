import json
from unittest.mock import MagicMock, patch
from entity_linker import EntityLinker

# Mock Data
MOCK_DATA = {
    "Steve Jobs": {
        "search": [{
            "id": "Q19837",
            "label": "Steve Jobs",
            "description": "American business magnate and co-founder of Apple Inc.",
            "aliases": ["Steven Paul Jobs"]
        }]
    },
    "Apple": {
        "search": [{
            "id": "Q312",
            "label": "Apple Inc.",
            "description": "American multinational technology company",
            "aliases": ["Apple", "Apple Computer"]
        }]
    },
    "in 1976": { "search": [] }, # Temporal object, likely unresolved or formatted date?
    # Dates usually shouldn't be linked to Q-IDs in this specific "Entity Linking" phase unless it's an Event. 
    # But "in 1976" is the text. Wikidata search for "in 1976" might fail or return randomness.
    # Ideally Phase 1 should have cleaned "in 1976" to "1976"?
    # Phase 2 goal is "Real world entity". Dates are entities (Q6927 for 1976).
    # But usually EL is for Named Entities.
    # We will let it fail or wrap valid dates?
    # Let's mock failure for dates to keep it simple, or mock 1976 if simple.
    
    # "as CEO" -> "CEO" (Q484876)
    "as CEO": { "search": [] }, # Preposition might mess it up.
    "CEO": {
        "search": [{
            "id": "Q484876",
            "label": "chief executive officer",
            "description": "highest-ranking corporate officer",
            "aliases": ["CEO"]
        }]
    }
}

def mock_get(url, params=None, timeout=None):
    query = params["search"]
    resp = MagicMock()
    # Simple substring check or exact key
    data = {"search": []}
    
    # Handle "Steve Jobs"
    if query in MOCK_DATA:
        data = MOCK_DATA[query]
    # Handle "Apple"
    elif "Apple" in query:
        data = MOCK_DATA["Apple"]
    # Handle "CEO"
    elif "CEO" in query:
        data = MOCK_DATA["CEO"]
        
    resp.json.return_value = data
    return resp

def run_phase_2():
    # Load Phase 1 output
    with open("example_output.json", "r") as f:
        phase1_data = json.load(f)
        
    linker = EntityLinker()
    
    # Patch the session
    with patch("requests.Session.get", side_effect=mock_get):
        result = linker.link_claims(phase1_data)
        
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    run_phase_2()
