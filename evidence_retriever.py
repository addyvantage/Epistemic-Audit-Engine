import requests
import time
import uuid
import spacy
from typing import List, Dict, Any, Optional
from property_mapper import PropertyMapper
from property_mapper import PropertyMapper
from backend.wikipedia_passage_retrieval import WikipediaPassageRetriever
from grokipedia_client import GrokipediaClient

class EvidenceRetriever:
    def __init__(self):
        self.mapper = PropertyMapper()
        self.passage_retriever = WikipediaPassageRetriever()
        self.grok_client = GrokipediaClient()
        self.WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
        self.session = requests.Session()
        self.session.headers.update({
             "User-Agent": "EpistemicAuditEngine/1.0 (Research Project)"
        })
        try:
             self.nlp = spacy.load("en_core_web_sm")
        except:
             self.nlp = None

    def retrieve_evidence(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry: Appends evidence to linked claims.
        """
        output_claims = []
        for claim in input_data.get("claims", []):
            try:
                processed_claim = self._process_claim(claim)
                output_claims.append(processed_claim)
            except Exception as e:
                # print(f"Error processing claim {claim.get('claim_id')}: {e}")
                claim["evidence"] = {"wikidata": [], "wikipedia": [], "grokipedia": []}
                claim["evidence_status"] = {"wikidata": "ERROR", "wikipedia": "ERROR", "grokipedia": "ERROR"}
                output_claims.append(claim)
                
        return {"claims": output_claims}

    def _process_claim(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        subj_ent = claim.get("subject_entity", {})
        obj_ent = claim.get("object_entity", {})
        predicate = claim.get("predicate", "").lower()
        
        wikidata_ev = []
        wikipedia_ev = []
        grokipedia_ev = []
        
        status = {
            "wikidata": "NOT_FOUND",
            "wikipedia": "NOT_FOUND",
            "grokipedia": "SKIPPED"
        }
        
        # 1. Wikidata Retrieval
        # Determine Direction
        direction = self._get_query_direction(predicate)
        query_qid = None
        target_qid = None # The "other" entity to match in value
        
        if direction == "OBJECT" and obj_ent and obj_ent.get("resolution_status") in ["RESOLVED", "RESOLVED_SOFT"]:
            query_qid = obj_ent.get("entity_id")
            target_qid = subj_ent.get("entity_id") # We expect Subject in the value
        elif subj_ent.get("resolution_status") in ["RESOLVED", "RESOLVED_SOFT"]:
            query_qid = subj_ent.get("entity_id")
            target_qid = obj_ent.get("entity_id") if obj_ent else None

        if query_qid:
            p_ids = self.mapper.get_potential_properties(predicate)
            if p_ids:
                matches = self._fetch_wikidata_statements(query_qid, p_ids, target_qid, claim)
                if matches:
                    wikidata_ev = matches
                    status["wikidata"] = "FOUND"
        
        # 2. Wikipedia Retrieval
        # Query Subject page usually
        wiki_url = subj_ent.get("sources", {}).get("wikipedia")
        if subj_ent.get("source_status", {}).get("wikipedia") == "VERIFIED" and wiki_url:
            passages = self.passage_retriever.extract_passages(wiki_url, claim.get("claim_text", ""))
            
            if passages:
                wikipedia_ev = passages
                # If we have at least one passage with textual evidence, marked as FOUND
                # The fallback object has textual_evidence=False
                if any(p.get("textual_evidence") for p in passages):
                    status["wikipedia"] = "FOUND"
                else:
                    status["wikipedia"] = "ABSENT" # Found structure but no text match
            else:
                 status["wikipedia"] = "NOT_FOUND"

        # 3. Grokipedia Retrieval (Hard Gating)
        # Block if claim_type is TEMPORAL or FACTUAL_ATTRIBUTE
        # Only RELATION allowed.
        can_use_grok = (claim.get("claim_type") == "RELATION")
        
        if can_use_grok and status["wikidata"] == "NOT_FOUND" and status["wikipedia"] == "NOT_FOUND":
            if subj_ent.get("source_status", {}).get("grokipedia") == "VERIFIED":
                 grok_excerpt = self.grok_client.fetch_excerpt(subj_ent.get("canonical_name"))
                 if grok_excerpt:
                     # Add alignment for Grokipedia (Soft)
                     grok_excerpt["alignment"] = {
                         "subject_match": True,  # Fetched by Subject Name
                         "predicate_match": True, # Assumed relevant by context search
                         "object_match": False, 
                         "temporal_match": False
                     }
                     grok_excerpt["evidence_id"] = self._generate_evidence_id("GROKIPEDIA", grok_excerpt.get("excerpt", ""))
                     grokipedia_ev = [grok_excerpt]
                     status["grokipedia"] = "FOUND"
                 else:
                     status["grokipedia"] = "ABSENT"
            else:
                 status["grokipedia"] = "ABSENT" if subj_ent.get("source_status", {}).get("grokipedia") == "ABSENT" else "SKIPPED"
        else:
            status["grokipedia"] = "SKIPPED"

        # Anchor Validation (Fix 2)
        subj_ok = subj_ent.get("resolution_status") in ["RESOLVED", "RESOLVED_SOFT"]
        obj_ok = True
        if obj_ent:
            obj_ok = obj_ent.get("resolution_status") in ["RESOLVED", "RESOLVED_SOFT"]
            
        if subj_ok and obj_ok:
            status["anchor_status"] = "ACCEPTED"

        claim["evidence"] = {
            "wikidata": wikidata_ev,
            "wikipedia": wikipedia_ev,
            "grokipedia": grokipedia_ev
        }
        claim["evidence_status"] = status
        
        return claim

    def _get_query_direction(self, predicate: str) -> str:
        """
        Returns 'SUBJECT' or 'OBJECT' to indicate which entity to query in Wikidata.
        """
        p = predicate.lower()
        # predicates where the Object is the entity holding the property 'created by', 'founded by'
        # e.g. "Apple" (Object) has "founded by" (Subject)
        object_centric = ["founded", "invented", "created", "discovered", "directed", "wrote", "authored"]
        if any(k in p for k in object_centric):
            return "OBJECT"
        return "SUBJECT"

    def _fetch_wikidata_statements(self, q_id: str, p_ids: List[str], target_qid: Optional[str], claim: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetches claims from Wikidata.
        """
        import re
        props = "|".join(p_ids)
        params = {
            "action": "wbgetentities",
            "ids": q_id,
            "props": "claims",
            "format": "json"
        }
        found = []
        try:
            resp = self.session.get(self.WIKIDATA_API_URL, params=params, timeout=5)
            data = resp.json()
            entity = data.get("entities", {}).get(q_id, {})
            claims_data = entity.get("claims", {})
            
            # Helper for Year Extraction
            def get_year(text_val: str) -> Optional[int]:
                # Handle ISO timestamp: +1976-04-01T...
                if text_val.startswith("+"):
                    try:
                        return int(text_val[1:5])
                    except:
                        pass
                # Handle simple year in text
                m = re.search(r'\b(19|20)\d{2}\b', text_val)
                if m: return int(m.group(0))
                return None

            claim_text = claim.get("claim_text", "")
            claim_year = get_year(claim_text)
            is_temporal_claim = (claim.get("claim_type") == "TEMPORAL") or (claim_year is not None)

            for pid in p_ids:
                if pid in claims_data:
                    stmts = claims_data[pid]
                    for stmt in stmts:
                        mainsnak = stmt.get("mainsnak", {})
                        if mainsnak.get("snaktype") == "value":
                            val = mainsnak.get("datavalue", {}).get("value")
                            parsed_val = str(val)
                            val_qid = None
                            val_year = None
                            
                            if isinstance(val, dict):
                                if "id" in val: 
                                    parsed_val = val["id"]
                                    val_qid = val["id"]
                                elif "time" in val: 
                                    parsed_val = val["time"]
                                    val_year = get_year(parsed_val)

                            # Compute Alignment
                            # Subject Match: True (queried)
                            # Predicate Match: True (found property)
                            
                            # Object Match
                            obj_match = False
                            if target_qid and val_qid == target_qid:
                                obj_match = True
                            
                            # Temporal Match
                            # Rule: TRUE if Evidence Value is Time AND (Claim is Temporal OR has Year) AND Years Match
                            # Rule: FALSE if Evidence Value is Entity (val_qid) OR (No temporal signal in claim)
                            # Rule: NULL if Claim has no temporal component
                            
                            if not is_temporal_claim:
                                temp_match = None
                            elif val_qid:
                                temp_match = False # Value is entity, not time
                            elif val_year and claim_year:
                                temp_match = (val_year == claim_year)
                            elif val_year and is_temporal_claim:
                                # Claim is TEMPORAL but derived (no year in text?), or year parsing failed?
                                # If claim is TEMPORAL derived e.g. "Apple founded in 1976" -> "Apple was founded" (without year?)
                                # Usually Temporal claims have the date.
                                # If claim text has no year but is Temporal, and we found a year?
                                # We can't match.
                                temp_match = False 
                            else:
                                temp_match = False

                            ev_item = {
                                "source": "WIKIDATA",
                                "entity_id": q_id,
                                "property": pid,
                                "value": parsed_val,
                                "qualifiers": stmt.get("qualifiers", {}),
                                "alignment": {
                                    "subject_match": True,
                                    "predicate_match": True,
                                    "object_match": obj_match,
                                    "temporal_match": temp_match
                                }
                            }
                            ev_item["evidence_id"] = self._generate_evidence_id("WIKIDATA", f"{q_id}-{pid}-{parsed_val}")
                            found.append(ev_item)
            return found
        except Exception:
            return []

    def _align_sentences(self, sentences: List[Dict[str, Any]], claim: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filters sentences using strict lemma matching and token-based entity matching.
        """
        import re
        aligned = []
        
        subj_ent = claim.get("subject_entity", {})
        subj_canon = subj_ent.get("canonical_name", "").lower()
        # Fallback to text if canonical empty
        if not subj_canon: subj_canon = subj_ent.get("text", "").lower()
            
        obj_ent = claim.get("object_entity")
        # We focus on Subject Match per requirements "FIX 2"
        
        pred_lemma = claim.get("predicate", "").lower()
        
        # Lemmatize Predicate
        pred_lemmas = [pred_lemma]
        if self.nlp:
            pred_lemmas = [t.lemma_ for t in self.nlp(pred_lemma)]
            if "found" in pred_lemma or "founding" in pred_lemma:
                 pred_lemmas.extend(["founder", "found", "founding", "establish", "creation", "formed"])

        # Prepare Subject Tokens (Canonical + Alias)
        # We need to tokenize canonical name to handle "Steve Jobs" -> {"steve", "jobs"}
        # And "Jobs" match.
        subj_tokens = set()
        if self.nlp:
            doc_s = self.nlp(subj_canon)
            subj_tokens.update([t.text.lower() for t in doc_s if not t.is_stop])
        else:
            subj_tokens.update([t for t in subj_canon.split() if len(t) > 2])

        # Temporal Setup
        def get_year(text_val: str) -> Optional[int]:
            m = re.search(r'\b(19|20)\d{2}\b', text_val)
            if m: return int(m.group(0))
            return None
            
        claim_text = claim.get("claim_text", "")
        claim_year = get_year(claim_text)
        is_temporal_claim = (claim.get("claim_type") == "TEMPORAL") or (claim_year is not None)

        for s in sentences:
            text = s["text"]
            text_lower = text.lower()
            
            doc = self.nlp(text) if self.nlp else None
            
            # Subject Match: Token Intersection
            # "Jobs founded..." -> "Jobs" in tokens
            s_match = False
            if doc:
                sent_tokens = [t.text.lower() for t in doc] # Keep casing logic simple or lower
                # Check if ANY non-stop subject token is in sentence
                # But "Jobs" is common? "Steve" is common?
                # Requirement: "A non-stopword alias token appears (e.g., 'Jobs' for 'Steve Jobs')"
                # "Steve Jobs" -> "Jobs" ok. "Steve" ok? Maybe "Steve" matches "Steve Wozniak".
                # Strict: "Canonical entity name tokens appear... OR non-stopword alias".
                # We'll stick to overlap
                sent_tokens_set = set(sent_tokens)
                if not subj_tokens.isdisjoint(sent_tokens_set):
                    s_match = True
            else:
                s_match = subj_canon in text_lower # Fallback substring

            # Predicate Match
            p_match = False
            if doc:
                sent_lemmas = {t.lemma_.lower() for t in doc}
                p_match = any(pl in sent_lemmas for pl in pred_lemmas)
            else:
                p_match = any(pl in text_lower for pl in pred_lemmas)

            # Object Match (Substring fallback for now as not focus of task)
            o_match = False
            if obj_ent:
                o_txt = obj_ent.get("text", "").lower()
                o_match = o_txt in text_lower

            # Temporal Match for Wikipedia
            # Extract year from sentence
            sent_year = get_year(text)
            
            if not is_temporal_claim:
                temp_match = None
            elif sent_year and claim_year:
                temp_match = (sent_year == claim_year)
            else:
                temp_match = False

            # Strict Filter: Must have (Subject OR Object) AND Predicate
            if (s_match or o_match) and p_match:
                ev_item = {
                    "source": "WIKIPEDIA",
                    "page": s.get("url", ""),
                    "sentence": text,
                    "url": s.get("url", ""),
                    "alignment": {
                        "subject_match": s_match,
                        "predicate_match": p_match,
                        "object_match": o_match,
                        "temporal_match": temp_match
                    }
                }
                ev_item["evidence_id"] = self._generate_evidence_id("WIKIPEDIA", text)
                aligned.append(ev_item)
        
        return aligned

    def _generate_evidence_id(self, source: str, content: str) -> str:
        """
        Deterministic UUID5.
        """
        unique_str = f"{source}:{content}"
        return str(uuid.uuid5(uuid.NAMESPACE_OID, unique_str))
