import sys
import os
sys.path.append("backend")
from pipeline.run_full_audit import AuditPipeline

def run_test():
    print("Initialize Pipeline...")
    pipeline = AuditPipeline()
    
    # CASE 1: LOWER BOUND (Success)
    c1 = {
        "claim_id": "num_1",
        "claim_text": "Alphabet reports over $300 billion in revenue.",
        "claim_type": "FACTUAL_ATTRIBUTE",
        "subject": "Alphabet",
        "predicate": "reports revenue",
        "object": "over $300 billion",
        "evidence": {
            "wikidata": [{
                "source": "WIKIDATA",
                "property": "revenue",
                "value": "307000000000", # 307B
                "snippet": "307 billion USD"
            }]
        }
    }
    
    # CASE 2: UPPER BOUND (Success)
    c2 = {
        "claim_id": "num_2",
        "claim_text": "Alphabet revenue is under $310 billion.",
        "claim_type": "FACTUAL_ATTRIBUTE",
        "evidence": {
            "wikidata": [{
                "source": "WIKIDATA",
                "value": "307 billion"
            }]
        }
    }
    
    # CASE 3: APPROXIMATE (Success - Within 5%)
    # Claim: 300B. Evidence: 307B. Diff 7B. 5% of 300 is 15. 307 is inside [285, 315].
    c3 = {
        "claim_id": "num_3",
        "claim_text": "Alphabet revenue is about $300 billion.",
        "claim_type": "FACTUAL_ATTRIBUTE",
        "evidence": {
            "wikidata": [{
                "source": "WIKIDATA",
                "value": "307 billion"
            }]
        }
    }
    
    # CASE 4: EXACT (Fail)
    # Claim: 300B. Evidence: 307B. Mismatch.
    c4 = {
        "claim_id": "num_4",
        "claim_text": "Alphabet revenue is exactly $300 billion.",
        "claim_type": "FACTUAL_ATTRIBUTE",
        "evidence": {
            "wikidata": [{
                "source": "WIKIDATA",
                "value": "307 billion"
            }]
        }
    }
    
    print("\n--- RUNNING NUMERIC SEMANTICS TEST ---\n")
    # Using verifier directly to trigger detector
    res = pipeline.verifier.verify_claims({"claims": [c1, c2, c3, c4]})
    
    for c in res["claims"]:
        cid = c["claim_id"]
        h_list = [h["hallucination_type"] for h in c.get("hallucinations", [])]
        reason = c.get("hallucinations", [{}])[0].get("reason", "") if h_list else "None"
        print(f"[{cid}] Hallucinations: {h_list} | Reason: {reason}")

    # Check expectations
    h1 = res["claims"][0].get("hallucinations", [])
    if not h1: print("PASS C1 (Lower Bound Allowed)")
    else: print("FAIL C1")

    h2 = res["claims"][1].get("hallucinations", [])
    if not h2: print("PASS C2 (Upper Bound Allowed)")
    else: print("FAIL C2")

    h3 = res["claims"][2].get("hallucinations", [])
    if not h3: print("PASS C3 (Approx Allowed)")
    else: print("FAIL C3")

    h4 = res["claims"][3].get("hallucinations", [])
    if "UNSUPPORTED_SPECIFICITY" in [h["hallucination_type"] for h in h4]: 
        print("PASS C4 (Exact Mismatch Flagged)")
    else: 
        print("FAIL C4 (Should be flagged)")

if __name__ == "__main__":
    run_test()
