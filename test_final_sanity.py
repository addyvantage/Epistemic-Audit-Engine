import sys
import os
import json
sys.path.append("backend")
from pipeline.run_full_audit import AuditPipeline

def test_sanity():
    pipeline = AuditPipeline()
    
    # CASE 1: Google (Implicit/Derived + Atomic)
    text1 = "Google was founded in 1998 by Larry Page. It is Alphabet's largest revenue generator."
    print(f"\n--- TEST 1: Google (Factual) ---\nText: {text1}")
    res1 = pipeline.run(text1)
    
    print(f"Risk: {res1['overall_risk']}")
    for c in res1['claims']:
        print(f"Claim: '{c['claim_text']}'")
        print(f"Type: {c['claim_type']}")
        print(f"Source: {c['is_derived']}")
        print(f"Span: {c['span']['start']}-{c['span']['end']}")
        if "highlight_type" in c:
            print(f"Highlight Type: {c['highlight_type']}")
        print(f"Verdict: {c['verification']['verdict']}")
        print("-" * 20)

    # CASE 2: Contested
    text2 = "Critics have argued that Google manipulates search results to favor its own products."
    print(f"\n--- TEST 2: Contested ---\nText: {text2}")
    res2 = pipeline.run(text2)
    
    for c in res2['claims']:
        print(f"Claim: '{c['claim_text']}'")
        print(f"Epistemic Status: {c.get('epistemic_status', 'N/A')}")
        print(f"Verdict: {c['verification']['verdict']}")
        print("-" * 20)

    # CASE 3: Hedging
    text3 = "Google has seemingly remained a dominant player."
    print(f"\n--- TEST 3: Hedging ---\nText: {text3}")
    res3 = pipeline.run(text3)
    
    for c in res3['claims']:
        print(f"Claim: '{c['claim_text']}'")
        print(f"Span Text in Claim: '{c['claim_text']}'") # We want to see if the claim text itself is clean
        # Check actual span in raw text
        start = c['span']['start']
        end = c['span']['end']
        subset = text3[start:end]
        print(f"Highlighted Span: '{subset}'")
        print("-" * 20)

if __name__ == "__main__":
    test_sanity()
