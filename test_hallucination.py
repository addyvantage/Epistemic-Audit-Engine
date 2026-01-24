import sys
import os
sys.path.append("backend")
from pipeline.run_full_audit import AuditPipeline

def test_hallucination():
    pipeline = AuditPipeline()
    
    # Test Case: "Google released the first iPhone."
    # Expect: REFUTED (ENTITY_ROLE_CONFLICT)
    text = "Google released the first iPhone."
    print(f"\n--- TEST: Hallucination Detection ---\nText: {text}")
    res = pipeline.run(text)
    
    passed = False
    
    for c in res['claims']:
        print(f"Claim: '{c['claim_text']}'")
        print(f"Verdict: {c['verification']['verdict']}")
        print(f"Confidence: {c['verification']['confidence']}")
        print(f"Reasoning: {c['verification']['reasoning']}")
        
        h_list = c.get('hallucinations', [])
        if h_list:
            print("Hallucinations Detected:")
            for h in h_list:
                print(f"  - [{h['hallucination_type']}] {h['reason']} (Score: {h.get('score')})")
                
            if any(h['hallucination_type'] == "ENTITY_ROLE_CONFLICT" for h in h_list):
                if c['verification']['verdict'] == "REFUTED":
                    passed = True
        else:
            print("No Hallucinations Detected.")
            
        print("-" * 20)

    if passed:
         print("\nSUCCESS: Hallucination 'Google released iPhone' correctly REFUTED.")
    else:
         print("\nFAILURE: Hallucination not detected or verdict incorrect.")

if __name__ == "__main__":
    test_hallucination()
