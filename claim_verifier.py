from typing import Dict, Any, List
import re
from nli_engine import NLIEngine

class ClaimVerifier:
    def __init__(self):
        self.nli = NLIEngine()

    def verify_claims(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for Phase 4.
        """
        output_claims = []
        config = input_data.get("pipeline_config", {})
        
        for claim in input_data.get("claims", []):
            try:
                verified_claim = self._verify_single_claim(claim, config)
                output_claims.append(verified_claim)
            except Exception as e:
                # print(f"Verification Failed for {claim.get('claim_id')}: {e}")
                claim["verification"] = {
                    "verdict": "INSUFFICIENT_EVIDENCE",
                    "reasoning": f"Verification error: {str(e)}",
                    "confidence": 0.0
                }
                output_claims.append(claim)
        
        return {"claims": output_claims}

    def _verify_single_claim(self, claim: Dict[str, Any], config: Dict[str, Any] = {}) -> Dict[str, Any]:
        evidence = claim.get("evidence", {}) # wikidata, wikipedia lists
        disable_nli = config.get("ablation", {}).get("disable_nli", False)
        
        supporting_ids = []
        refuting_ids = []
        
        # 1. Evidence Eligibility Filter
        valid_evidence = []
        for source, items in evidence.items():
            if source == "grokipedia": continue # Narrative evidence rule: Unsupported alone
            
            for item in items:
                if self._is_eligible(item, claim):
                    valid_evidence.append(item)

        # 2. Logic Check per Item
        nli_stats = {"entailed": 0, "contradicted": 0, "neutral": 0}
        has_wikidata_support = False
        
        for ev in valid_evidence:
            source = ev.get("source")
            alignment = ev.get("alignment", {})
            val = ev.get("value", "") # Wikidata value
            
            # A. Wikidata Logic (Structured)
            if source == "WIKIDATA":
                # Check for Refutation
                is_refutation = False
                
                # Object Mismatch Refutation Rule:
                # Refute only if:
                # 1. Claim Type is RELATION
                # 2. Object is RESOLVED (checked during alignment flag usually, but double check)
                # 3. Evidence Value IS an Entity (starts with Q) AND differs from Claim Object
                # 4. If Evidence Value is a Date (starts with +), it does NOT refute a Relation claim (it just provides metadata)
                
                obj_match = alignment.get("object_match")
                is_entity_val = val.startswith("Q") and val[1].isdigit() if val else False
                
                if claim.get("claim_type") == "RELATION" and obj_match is False:
                    # Only refute if evidence provides a conflicting Entity
                    # Fix 1: Dates (+YYYY...) cannot refute Relations via object mismatch
                    if is_entity_val and not val.startswith("+"):
                         is_refutation = True
                         refuting_ids.append(ev.get("evidence_id"))
                
                # Temporal Refutation Rule:
                # Refute if temporal_match is explicitly False, UNLESS compatible (granularity fix)
                elif alignment.get("temporal_match") is False:
                     # Fix 2: Granularity check
                     c_val = claim.get("object", "")
                     if not self._temporal_compatible(c_val, val):
                         is_refutation = True
                         refuting_ids.append(ev.get("evidence_id"))

                if not is_refutation:
                    # Supports
                    supporting_ids.append(ev.get("evidence_id"))
                    has_wikidata_support = True
            
            # B. Wikipedia Logic (Textual -> NLI)
            elif source == "WIKIPEDIA":
                sent_text = ev.get("sentence", "")
                claim_text = claim.get("claim_text", "")
                
                if disable_nli:
                    # Fallback: Lexical Overlap
                    s_tokens = set(re.findall(r'\w+', sent_text.lower()))
                    c_tokens = set(re.findall(r'\w+', claim_text.lower()))
                    if not c_tokens: overlap = 0.0
                    else: overlap = len(s_tokens.intersection(c_tokens)) / len(c_tokens)
                    
                    if overlap > 0.6:
                        verdict = {"entailment": 0.9, "contradiction": 0.0, "neutral": 0.1}
                    else:
                        verdict = {"entailment": 0.0, "contradiction": 0.0, "neutral": 1.0}
                else:
                    verdict = self.nli.classify(sent_text, claim_text)
                
                # Check strict NLI thresholds
                if verdict["contradiction"] > 0.7:
                    nli_stats["contradicted"] += 1
                    refuting_ids.append(ev.get("evidence_id"))
                elif verdict["entailment"] > 0.7:
                    nli_stats["entailed"] += 1
                    supporting_ids.append(ev.get("evidence_id"))
                else:
                    nli_stats["neutral"] += 1
                    # Can't support or refute

        # 3. Aggregation Verdict
        final_verdict = "INSUFFICIENT_EVIDENCE"
        confidence = 0.0
        reasoning = "No authoritative evidence found."
        
        # 3. Aggregation Verdict (Fix 1: Dominant Evidence)
        final_verdict = "INSUFFICIENT_EVIDENCE"
        confidence = 0.0
        reasoning = "No authoritative evidence found."
        
        support_count = len(supporting_ids)
        refute_count = len(refuting_ids)

        if support_count > 0 and refute_count == 0:
            final_verdict = "SUPPORTED"
            reasoning = "Supported by authoritative evidence."
            # Confidence calc
            score = 0.6 + (0.15 * support_count)
            if has_wikidata_support: score += 0.1
            hedging = claim.get("confidence_linguistic", {}).get("hedging", 0.0)
            if hedging > 0.5: score -= 0.2
            confidence = max(0.0, min(1.0, score))

        elif support_count > 0 and refute_count > 0:
            # Conflict case
            if has_wikidata_support:
                final_verdict = "SUPPORTED"
                reasoning = "Authoritative support outweighs conflicting metadata."
                confidence = 0.6  # Conservative confidence
            else:
                final_verdict = "INSUFFICIENT_EVIDENCE"
                reasoning = "Conflicting evidence without dominant authority."
                confidence = 0.0

        elif refute_count > 0 and support_count == 0:
            final_verdict = "REFUTED"
            reasoning = "Authoritative contradiction found."
            confidence = 0.9
            
        else:
             # Check grokipedia fallback
             if not valid_evidence and evidence.get("grokipedia"):
                 reasoning = "Only narrative evidence available (Grokipedia)."
             else:
                 reasoning = "No evidence found."
                 
        # Fix 4: Authority Bleed Prevention
        if final_verdict != "SUPPORTED":
             if self._is_authority_bleed(claim):
                 final_verdict = "REFUTED"
                 reasoning = "Authority Bleed: Influence != Authorship."
                 confidence = 0.9
                 
        claim["verification"] = {
            "verdict": final_verdict,
            "confidence": round(confidence, 2),
            "used_evidence_ids": supporting_ids,
            "contradicted_by": refuting_ids,
            "reasoning": reasoning,
            "nli_summary": nli_stats
        }
        
        return claim
        
    def _is_authority_bleed(self, claim: Dict[str, Any]) -> bool:
        # Subject must be PERSON
        subj = claim.get("subject_entity", {})
        if subj.get("entity_type") != "PERSON": return False
        
        # Predicate Authorship
        pred = claim.get("predicate", "").lower()
        auth_keywords = ["designed", "engineered", "built", "implemented", "coded", "programmed"]
        if not any(k in pred for k in auth_keywords): return False
        
        # Object Technical
        obj_txt = claim.get("object", "").lower()
        tech_keywords = ["processor", "chip", "hardware", "system", "architecture", "kernel"]
        if not any(k in obj_txt for k in tech_keywords): return False
        
        return True
        
    def _temporal_compatible(self, claim_val: str, ev_val: str) -> bool:
        if not ev_val or not ev_val.startswith("+"):
            return False
            
        # Extract 4 digit year from claim
        years = re.findall(r'\d{4}', claim_val)
        if not years:
            return False
            
        # Check if year exists in evidence value
        return years[0] in ev_val

    def _is_eligible(self, item: Dict[str, Any], claim: Dict[str, Any]) -> bool:
        """
        Strict alignment check based on Claim Type.
        """
        align = item.get("alignment", {})
        c_type = claim.get("claim_type")
        
        s_match = align.get("subject_match")
        p_match = align.get("predicate_match")
        o_match = align.get("object_match")
        t_match = align.get("temporal_match")
        
        # Base Requirement: S + P
        if not (s_match and p_match):
            return False
            
        if c_type == "TEMPORAL":
            # Must have temporal match (True or False, NOT None)
            if t_match is None: return False
            
        return True
