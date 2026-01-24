import sys
import os
import json
sys.path.append("backend")
from pipeline.run_full_audit import AuditPipeline

def test_google():
    pipeline = AuditPipeline()
    text = "Google was founded in 1998 by Larry Page and Sergey Brin. It is Alphabet's largest revenue generator."
    
    print(f"Auditing text: {text}")
    result = pipeline.run(text)
    
    print("\n--- RESULTS ---")
    print(f"Overall Risk: {result['overall_risk']}")
    print(f"Summary: {result['summary']}")
    
    print("\n--- CLAIMS ---")
    verified_count = 0
    for c in result['claims']:
        print(f"Claim: '{c['claim_text']}'")
        print(f"Span: {c['span']['start']}-{c['span']['end']} (Len: {c['span']['end'] - c['span']['start']})")
        print(f"Verdict: {c['verification']['verdict']}")
        print(f"Confidence: {c['verification']['confidence']}")
        print(f"Reasoning: {c['verification']['reasoning']}")
        print("-" * 30)
        
        if c['verification']['verdict'] == "SUPPORTED":
            verified_count += 1
            
    print(f"\nTotal Claims: {len(result['claims'])}")
    print(f"Verified Claims: {verified_count}")
    
    if verified_count == 0:
        print("FAIL: No verified claims.")
        sys.exit(1)
    else:
        print("SUCCESS: Pipeline verified canonical facts.")

if __name__ == "__main__":
    test_google()
