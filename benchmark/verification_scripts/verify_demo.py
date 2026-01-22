from backend.pipeline.run_full_audit import AuditPipeline
import json

def verify():
    print("Initializing Pipeline...")
    pipeline = AuditPipeline()
    
    text = """
Apple was founded in 1976 by Steve Jobs, Steve Wozniak, and Ronald Wayne.
Apple was founded in 1978.
Apple released the first iPhone in 2007.
The iPhone single-handedly caused the global smartphone revolution.
"""
    print(f"\nRunning Audit on:\n{text}\n")
    
    result = pipeline.run(text, mode="demo")
    
    print("\n=== RESULTS ===\n")
    for claim in result["claims"]:
        txt = claim["claim_text"]
        verdict = claim["verification"]["verdict"]
        conf = claim["verification"]["confidence"]
        h_types = [h["hallucination_type"] for h in claim.get("hallucinations", [])]
        
        print(f"Claim: {txt}")
        print(f"Verdict: {verdict} ({conf})")
        if h_types:
            print(f"Hallucinations: {h_types}")
        print("-" * 40)

if __name__ == "__main__":
    verify()
