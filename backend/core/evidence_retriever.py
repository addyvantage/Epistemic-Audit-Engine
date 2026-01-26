import requests
import time
import uuid
import spacy
from typing import List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .entity_context import EntityContext

from .property_mapper import PropertyMapper
from .wikipedia_passage_retrieval import WikipediaPassageRetriever
from .grokipedia_client import GrokipediaClient
from .primary_document_retriever import PrimaryDocumentRetriever
from .wikidata_retriever import WikidataRetriever
from config.core_config import EVIDENCE_MODALITY_TEXTUAL, EVIDENCE_MODALITY_STRUCTURED

class EvidenceRetriever:
    def __init__(self):
        self.mapper = PropertyMapper()
        self.passage_retriever = WikipediaPassageRetriever()
        self.grok_client = GrokipediaClient()
        self.primary_retriever = PrimaryDocumentRetriever()
        self.wikidata_retriever = WikidataRetriever()
        
        self.WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
        self.session = requests.Session()
        self.session.headers.update({
             "User-Agent": "EpistemicAuditEngine/1.0 (Research Project)"
        })
        try:
             self.nlp = spacy.load("en_core_web_sm")
        except:
             self.nlp = None
        
        self.entity_cache = {}

    def retrieve_evidence(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry: Appends evidence to linked claims.
        """
        # Phase 1: Tier 1 Retrieval (Primary) which may pre-solve queries
        primary_ev_map = self.primary_retriever.retrieve_evidence(input_data.get("claims", []))
        
        output_claims = []
        for claim in input_data.get("claims", []):
            try:
                cid = claim.get("claim_id")
                p_docs = primary_ev_map.get(cid, [])
                
                processed_claim = self._process_claim(claim, p_docs)
                output_claims.append(processed_claim)
            except Exception as e:
                # Fallback empty structure
                claim["evidence"] = {"wikidata": [], "wikipedia": [], "grokipedia": [], "primary_document": []}
                output_claims.append(claim)
                
        return {"claims": output_claims}

    def _process_claim(self, claim: Dict[str, Any], primary_docs: List[Dict[str, Any]] = []) -> Dict[str, Any]:
        subj_ent = claim.get("subject_entity", {})
        obj_ent = claim.get("object_entity", {})
        predicate = claim.get("predicate", "").lower()
        
        wikidata_ev = []
        wikipedia_ev = []
        grokipedia_ev = []
        
        status = {
            "primary_document": "FOUND" if primary_docs else "ABSENT",
            "wikidata": "NOT_FOUND",
            "wikipedia": "NOT_FOUND",
            "grokipedia": "SKIPPED"
        }
        
        # 1. Wikidata Retrieval (Tier 1)
        direction = self._get_query_direction(predicate)
        query_qid = None
        
        # Accept RESOLVED, RESOLVED_SOFT, and RESOLVED_COREF (v1.4) for evidence retrieval
        valid_statuses = ["RESOLVED", "RESOLVED_SOFT", "RESOLVED_COREF"]

        if direction == "OBJECT" and obj_ent and obj_ent.get("resolution_status") in valid_statuses:
            query_qid = obj_ent.get("entity_id")
        elif subj_ent.get("resolution_status") in valid_statuses:
            query_qid = subj_ent.get("entity_id")

        if query_qid:
            p_ids = self.mapper.get_potential_properties(predicate)
            if p_ids:
                matches = self.wikidata_retriever.retrieve_structured_evidence(query_qid, p_ids, claim)
                if matches:
                    wikidata_ev = matches
                    status["wikidata"] = "FOUND"
        
        # 2. Wikipedia Retrieval (Tier 2 - Narrative)
        wiki_url = subj_ent.get("sources", {}).get("wikipedia")
        if subj_ent.get("source_status", {}).get("wikipedia") == "VERIFIED" and wiki_url:
            passages = self.passage_retriever.extract_passages(wiki_url, claim.get("claim_text", ""))
            
            if passages:
                normalized_passages = []
                for p in passages:
                    normalized_passages.append({
                        "source": "WIKIPEDIA",
                        "modality": EVIDENCE_MODALITY_TEXTUAL, # Tag as TEXTUAL
                        "url": p["url"],
                        "sentence": p["snippet"],
                        "snippet": p["snippet"],
                        "score": p["score"],
                        "textual_evidence": p["textual_evidence"],
                        "evidence_id": self._generate_evidence_id("WIKIPEDIA", p["snippet"] or "null")
                    })
                
                wikipedia_ev = normalized_passages
                if any(p.get("textual_evidence") for p in normalized_passages):
                    status["wikipedia"] = "FOUND"
                else:
                    status["wikipedia"] = "ABSENT"
            else:
                 status["wikipedia"] = "NOT_FOUND"

        # 3. Grokipedia (Tier 3 - Narrative Fallback)
        can_use_grok = (claim.get("claim_type") == "RELATION")
        
        # Mocking logic for testing removed or kept as needed. 
        # Keeping minimal logic.
        
        if can_use_grok and status["wikidata"] == "NOT_FOUND" and status["wikipedia"] == "NOT_FOUND":
            if subj_ent.get("source_status", {}).get("grokipedia") == "VERIFIED":
                 grok_excerpt = self.grok_client.fetch_excerpt(subj_ent.get("canonical_name"))
                 if grok_excerpt:
                     # Add alignment for Grokipedia (Soft)
                     grok_excerpt["alignment"] = {
                         "subject_match": True,
                         "predicate_match": True,
                         "object_match": False, 
                         "temporal_match": False
                     }
                     grok_excerpt["modality"] = EVIDENCE_MODALITY_TEXTUAL
                     grok_excerpt["evidence_id"] = self._generate_evidence_id("GROKIPEDIA", grok_excerpt.get("excerpt", ""))
                     grokipedia_ev = [grok_excerpt]
                     status["grokipedia"] = "FOUND"
                 else:
                     status["grokipedia"] = "ABSENT"
            else:
                 status["grokipedia"] = "ABSENT" if subj_ent.get("source_status", {}).get("grokipedia") == "ABSENT" else "SKIPPED"

        # Anchor Validation (v1.4: include RESOLVED_COREF)
        valid_statuses = ["RESOLVED", "RESOLVED_SOFT", "RESOLVED_COREF"]
        subj_ok = subj_ent.get("resolution_status") in valid_statuses
        obj_ok = True
        if obj_ent:
            obj_ok = obj_ent.get("resolution_status") in valid_statuses
            
        if subj_ok and obj_ok:
            status["anchor_status"] = "ACCEPTED"

        claim["evidence"] = {
            "primary_document": primary_docs,
            "wikidata": wikidata_ev,
            "wikipedia": wikipedia_ev,
            "grokipedia": grokipedia_ev
        }
        claim["evidence_status"] = status
        
        return claim

    def _get_query_direction(self, predicate: str) -> str:
        p = predicate.lower()
        object_centric = ["founded", "invented", "created", "discovered", "directed", "wrote", "authored", "released", "launched", "manufactured", "developed"]
        if any(k in p for k in object_centric):
            return "OBJECT"
        return "SUBJECT"

    def _generate_evidence_id(self, source: str, content: str) -> str:
        unique_str = f"{source}:{content}"
        return str(uuid.uuid5(uuid.NAMESPACE_OID, unique_str))
