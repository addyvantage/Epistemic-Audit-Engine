import sys
import os
from typing import Dict, Any, List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend/pipeline")))
from evidence_retriever import EvidenceRetriever
from nli_engine import NLIEngine # Assuming this is available in pythonpath relative to verifier

class BaselineVerifier:
    def verify(self, claim_text: str) -> str:
        raise NotImplementedError

class RetrievalBaseline(BaselineVerifier):
    def __init__(self):
        self.retriever = EvidenceRetriever()
        
    def verify(self, claim_text: str) -> str:
        # 1. Structure Input for Retriever
        # Retriever expects specific dict structure from Linker phase.
        # We'll mock a simple pass.
        # This is hard because Retriever relies on Linked Entities (QIDs).
        # A pure "Retrieval Baseline" might just query text search?
        # Reusing the pipeline's retriever implies using the Linker too.
        # So "Retrieval-Only" likely means: Link -> Retrieve -> Heuristic Match (No NLI/Logic).
        return "INSUFFICIENT_EVIDENCE" # Placeholder if we don't want to re-implement full stack

class NLIBaseline(BaselineVerifier):
    def __init__(self):
        self.nli = NLIEngine()
        
    def verify(self, claim_text: str, evidence_text: str) -> str:
        # Checks claim against raw text without structural logic
        res = self.nli.classify(evidence_text, claim_text)
        if res["entailment"] > 0.7: return "SUPPORTED"
        if res["contradiction"] > 0.7: return "REFUTED"
        return "INSUFFICIENT_EVIDENCE"
