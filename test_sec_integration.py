import sys
import os
sys.path.append("backend")
from pipeline.run_full_audit import AuditPipeline

def test_sec():
    pipeline = AuditPipeline()
    
    # Success Condition: "Google earns the majority of its revenue from online advertising."
    text = "Google earns the majority of its revenue from online advertising."
    
    print(f"\n--- TEST: SEC Integration ---\nText: {text}")
    res = pipeline.run(text)
    
    found_sec = False
    
    for c in res['claims']:
        print(f"Claim: '{c['claim_text']}'")
        print(f"Verdict: {c['verification']['verdict']}")
        print(f"Confidence: {c['verification']['confidence']}")
        print(f"Reasoning: {c['verification']['reasoning']}")
        
        # Check evidence sources
        pd = c.get('evidence', {}).get('primary_document', [])
        if pd:
            found_sec = True
            print("Types Found: PRIMARY_DOCUMENT found!")
            for item in pd:
                print(f"   SEC Details: {item.get('fact')} -> {item.get('value')}")
        else:
            print("Types Found: No Primary Documents.")
            
        print("-" * 20)

    if found_sec:
         print("\nSUCCESS: Primary Document Integration Verified.")
    else:
         print("\nFAILURE: No Primary Documents found for trigger text.")

if __name__ == "__main__":
    test_sec()
