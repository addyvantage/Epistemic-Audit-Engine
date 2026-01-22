from backend.pipeline.run_full_audit import AuditPipeline
import json

def verify():
    print("Initializing Pipeline...")
    pipeline = AuditPipeline()
    
    text = """
The extent of the damage remains debated among scholars.
Evidence suggests it might be possible that the virus originated in a lab.
The outcome remains speculative and is not fully understood.
"""
    print(f"\nRunning Audit on:\n{text}\n")
    
    result = pipeline.run(text, mode="demo")
    
    print("\n=== RESULTS ===\n")
    print(f"Overall Risk: {result['overall_risk']}")
    print(f"Hallucination Score: {result['hallucination_score']}")
    
    for claim in result["claims"]:
        txt = claim["claim_text"]
        pol = claim.get("epistemic_polarity", "N/A")
        h_types = [h["hallucination_type"] for h in claim.get("hallucinations", [])]
        
        print(f"Claim: {txt}")
        print(f"Polarity: {pol}")
        print(f"Hallucinations: {h_types}")
        print("-" * 40)
        
        # Assertions
        if pol == "META_EPISTEMIC":
            if "H3" in h_types:
                print("FAIL: Meta-epistemic claim flagged as H3 (Overconfidence)")
            if "H1" in h_types:
                print("FAIL: Meta-epistemic claim flagged as H1 (Unsupported)")

if __name__ == "__main__":
    verify()
