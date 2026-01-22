import json
from unittest.mock import MagicMock, patch
from claim_verifier import ClaimVerifier

PHASE_3_OUTPUT = "example_evidence_output.json"

def run_phase_4_mock():
    try:
        with open(PHASE_3_OUTPUT, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {PHASE_3_OUTPUT} not found.")
        return

    verifier = ClaimVerifier()
    
    # MOCK NLI
    mock_nli = MagicMock()
    def classify_side_effect(premise, hypothesis):
        if "founded" in premise and "founded" in hypothesis:
            return {"entailment": 0.95, "contradiction": 0.01, "neutral": 0.04}
        return {"entailment": 0.1, "contradiction": 0.1, "neutral": 0.8}
    
    # We must patch properly because `verifier` instance has its own `nli` object
    # We can just override the method on the instance
    verifier.nli.classify = classify_side_effect
    
    # Also we assume Phase 3 output has P571 for "founded".
    # P571 is +1976... (Date).
    # New logic: This is NOT a refutation of "Steve Jobs founded Apple" because Date != Person is not a contradiction.
    # It is Support because alignment has Subject Match + Predicate Match.
    
    result = verifier.verify_claims(data)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    run_phase_4_mock()
