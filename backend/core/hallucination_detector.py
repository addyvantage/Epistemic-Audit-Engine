from typing import Dict, Any, List, Optional
import re

class HallucinationDetector:
    """
    Detects specific hallucination patterns as defined in Epistemic Audit Engine v1.1 Phase 8.
    """
    
    def __init__(self):
        # Phase 5: Mutually Exclusive Creator Rule Trigger Predicates
        # Phase 5: Mutually Exclusive Creator Rule Trigger Predicates
        self.ORG_CREATION_PREDICATES = {"founded", "established", "incorporated"}
        self.ARTIFACT_CREATION_PREDICATES = {
            "created", "released", "built", "invented", "launched", 
            "designed", "developed", "manufactured"
        }
        
        self.CRITICAL_HALLUCINATIONS = {"ENTITY_ROLE_CONFLICT", "TEMPORAL_FABRICATION", "COURT_AUTHORITY_MISATTRIBUTION", "IMPOSSIBLE_DOSAGE", "SCOPE_OVERGENERALIZATION"}
        self.NON_CRITICAL_HALLUCINATIONS = {"UNSUPPORTED_SPECIFICITY", "AUTHORITY_BLEED"}

        # Scope Keywords
        self.SCOPE_AUTHORITIES = {"government", "supreme court", "high court", "who", "cdc", "fda", "agency", "federal"}
        self.SCOPE_FORCE_PREDICATES = {"mandated", "required", "forced", "banned", "prohibited", "compelled", "ordered"}
        self.SCOPE_UNIVERSAL_OBJECTS = {"everyone", "all citizens", "population", "nationwide", "all people", "vaccine", "mask"}
        self.SCOPE_LIMITERS = {
            "federal employees", "contractors", "healthcare workers", "specific states", 
            "emergency", "conditional", "recommended",
            "funding", "research", "development", "trials", "distribution", "access"
        }
        
        # Extended Universality Markers
        self.UNIVERSAL_MARKERS = {"everyone", "all", "nationwide", "entire population", "mandatory for all", "universal"}

    def detect_structural(self, claim: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fast pre-filter for structural hallucinations that don't require external evidence.
        Returns the first detected hallucination, or None.
        """
        # 1. SCOPE_OVERGENERALIZATION (Critical)
        scope = self._check_scope_overgeneralization(claim)
        if scope:
            self._enrich(scope)
            return scope
            
        # 2. IMPOSSIBLE_DOSAGE (Critical)
        dosage = self._check_impossible_dosage(claim)
        if dosage:
            self._enrich(dosage)
            return dosage
            
        # 3. AUTHORITY_BLEED (Non-Critical -> But we can REFUTE immediately if logic allows)
        # Note: Previous logic allowed Bleed to be Non-Critical but verified as Refuted.
        # If we pre-filter, we avoid evidence. Safe to Refute?
        # Bleed is "Attributed technical authorship to influencer". 
        # Without evidence proving they DIDN'T do it, we rely on the structural heuristic.
        # The heuristic is strong (high score 0.9).
        # We will treat it as pre-filterable.
        bleed = self._check_authority_bleed(claim)
        if bleed:
            self._enrich(bleed)
            return bleed
            
        return None

    def detect(self, claim: Dict[str, Any], evidence: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Returns a list of detected hallucinations.
        """
        flags = []
        
        # 1. ENTITY_ROLE_CONFLICT (Phase 5 Hard Refutation)
        conflict = self._check_entity_role_conflict(claim, evidence)
        if conflict:
            self._enrich(conflict)
            flags.append(conflict)
            
        # 2. TEMPORAL_FABRICATION (Phase 6)
        temp_fab = self._check_temporal_fabrication(claim, evidence)
        if temp_fab:
            self._enrich(temp_fab)
            flags.append(temp_fab)
            
        # 3. UNSUPPORTED_SPECIFICITY (Phase 8)
        # Checks for numbers in claim not present in evidence
        spec_fab = self._check_unsupported_specificity(claim, evidence)
        if spec_fab:
            self._enrich(spec_fab)
            flags.append(spec_fab)
            
        # 4. AUTHORITY_BLEED (Phase 8/Fix 4)
        auth_bleed = self._check_authority_bleed(claim)
        if auth_bleed:
             self._enrich(auth_bleed)
             flags.append(auth_bleed)

        # 5. COURT_AUTHORITY_MISATTRIBUTION (Stress Test)
        court = self._check_court_authority(claim, evidence)
        if court:
             self._enrich(court)
             flags.append(court)
             
        # 6. IMPOSSIBLE_DOSAGE (Stress Test)
        dosage = self._check_impossible_dosage(claim)
        if dosage:
             self._enrich(dosage)
             flags.append(dosage)

        # 7. SCOPE_OVERGENERALIZATION (v1.1 Patch)
        scope = self._check_scope_overgeneralization(claim)
        if scope:
             self._enrich(scope)
             flags.append(scope)
            
        return flags

    def _enrich(self, h: Dict[str, Any]):
        h_type = h.get("hallucination_type")
        if h_type in self.CRITICAL_HALLUCINATIONS:
            h["severity"] = "CRITICAL"
        else:
            h["severity"] = "NON_CRITICAL"

    def _check_entity_role_conflict(self, claim: Dict[str, Any], evidence: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Detects if a creation claim is attributed to the wrong entity.
        Rule: If Object has a known Creator (P170/P176/P178) that != Subject -> REFUTED.
        """
        pred = claim.get("predicate", "").lower()
        pred_tokens = set(pred.split())
        
        # Check if predicate involves creation
        
        # Skip organizational founding — not a role conflict (v1.1 Fix)
        if any(p in pred_tokens for p in self.ORG_CREATION_PREDICATES):
            return None

        # Only artifact creation predicates are eligible
        if pred_tokens.isdisjoint(self.ARTIFACT_CREATION_PREDICATES):
            return None
            
        subj_ent = claim.get("subject_entity", {})
        subj_qid = subj_ent.get("entity_id")
        
        # Check Wikidata Evidence for Creator Properties
        # P170 (creator), P176 (manufacturer), P178 (developer)
        # REMOVED P112 (founder) as it apples to Orgs, not Artifacts.
        CREATOR_PROPS = {"P170", "P176", "P178"}
        
        wikidata_ev = evidence.get("wikidata", [])
        
        for ev in wikidata_ev:
            prop = ev.get("property")
            if prop in CREATOR_PROPS:
                val_qid = ev.get("value") # Expecting QID of actual creator
                
                # If the evidence value (Real Creator) is NOT the Claim Subject
                if val_qid and val_qid.startswith("Q") and val_qid != subj_qid:
                    # Double check: Is it just an alias? 
                    # Simulating check: If IDs mismatch, it's likely a conflict.
                    # Strict v1.1: Mismatching ID on Creator Property is a Conflict.
                    
                    # Exception: If the claim subject is a Subsidiary of the Creator?
                    # For "Google released iPhone" (Google Q95 vs Apple Q312) -> Conflict.
                    
                    return {
                        "hallucination_type": "ENTITY_ROLE_CONFLICT",
                        "reason": f"Entity Role Conflict: Object created by {val_qid}, not {subj_qid}.",
                        "score": 0.95 # High confidence refutation
                    }
        return None

    def _check_temporal_fabrication(self, claim: Dict[str, Any], evidence: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Detects mismatching dates.
        """
        claim_type = claim.get("claim_type")
        if claim_type != "TEMPORAL":
            return None
            
        # Extract claim year
        c_text = claim.get("claim_text", "")
        c_years = re.findall(r'\b(1\d{3}|20\d{2})\b', c_text)
        if not c_years:
            return None
        c_year = int(c_years[0])
        
        # Check Wikidata time properties
        wikidata_ev = evidence.get("wikidata", [])
        if not wikidata_ev:
            return None
            
        # If we have time evidence, check for match
        has_time_ev = False
        for ev in wikidata_ev:
            val = str(ev.get("value", ""))
            if val.startswith("+"): # ISO Time
                has_time_ev = True
                ev_year = int(val[1:5])
                if ev_year != c_year:
                    return {
                        "hallucination_type": "TEMPORAL_FABRICATION",
                        "reason": f"Temporal Mismatch: Evidence indicates {ev_year}, claim asserts {c_year}.",
                        "score": 0.90
                    }
                    
        return None

        return None

    def _check_unsupported_specificity(self, claim: Dict[str, Any], evidence: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Checks for precise numbers in claim that are absent in evidence.
        Now supports Semantic Numeric Intents: LOWER_BOUND, UPPER_BOUND, APPROXIMATE.
        """
        c_text = claim.get("claim_text", "").lower()

        # v1.6: Skip specificity check for canonical biographical claims
        # Birth dates/places are verified through structured evidence, not number matching
        claim_type = claim.get("claim_type", "")
        predicate = claim.get("predicate", "").lower()
        CANONICAL_BIOGRAPHICAL_PREDICATES = {"born", "died", "birth", "death", "founded", "established"}
        if any(p in predicate for p in CANONICAL_BIOGRAPHICAL_PREDICATES):
            return None

        # 1. Regex for numbers (simple integers/floats/formatted)
        # Filter out years: any 4-digit number between 1000-2099 (covers historical dates)
        nums = re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', c_text)

        def is_likely_year(n: str) -> bool:
            """Check if a 4-digit number is likely a year (1000-2099)."""
            if len(n) != 4:
                return False
            try:
                year = int(n)
                return 1000 <= year <= 2099
            except ValueError:
                return False

        non_year_nums = [n for n in nums if not is_likely_year(n)]
        
        if not non_year_nums:
            return None
            
        # 2. Extract Evidence Text
        all_text = ""
        for src in evidence.values():
            for item in src:
                all_text += " " + str(item.get("value", "")) + " " + item.get("snippet", "") + " " + item.get("sentence", "")
        all_text_lower = all_text.lower()
        
        # 3. Numeric Intent Analysis
        LOWER_BOUND = {"over", "more than", "above", "at least", "exceeding", "exceeds"}
        UPPER_BOUND = {"under", "less than", "below", "at most"}
        APPROXIMATE = {"about", "around", "approximately", "roughly", "approx"}
        
        for n in non_year_nums:
            # Clean number for value comparison
            try:
                val_c = float(n.replace(",", ""))
            except:
                continue
                
            # Check context window (prev 3 words)
            # Find index of n in c_text
            idx = c_text.find(n)
            context = c_text[max(0, idx-20):idx] if idx != -1 else ""
            
            intent = "EXACT"
            if any(k in context for k in LOWER_BOUND): intent = "LOWER"
            elif any(k in context for k in UPPER_BOUND): intent = "UPPER"
            elif any(k in context for k in APPROXIMATE): intent = "APPROX"
            
            # 4. Check against Evidence
            # We need to extract Numbers from Evidence to compare values!
            ev_nums = re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', all_text_lower)
            
            satisfied = False
            
            # First: Exact Match Check (Legacy) - Fast Path
            clean_n_str = n.replace(",", "")
            if clean_n_str in all_text_lower or n in all_text_lower:
                satisfied = True
            else:
                # Value Comparison Logic
                for en in ev_nums:
                    try:
                        val_e = float(en.replace(",", ""))
                    except:
                        continue
                        
                    if intent == "LOWER":
                        # Claim: > X. Evidence: Y. Satisfied if Y >= X.
                        if val_e >= val_c:
                            satisfied = True
                            break
                    elif intent == "UPPER":
                        # Claim: < X. Evidence: Y. Satisfied if Y <= X.
                        if val_e <= val_c:
                            satisfied = True
                            break
                    elif intent == "APPROX": # APPROX
                         # Claim: ~X. Evidence: Y. Satisfied if Y within +/- 5% of X.
                        if 0.95 * val_c <= val_e <= 1.05 * val_c:
                            satisfied = True
                            break
                    elif intent == "EXACT":
                        # Strict match (fallback to text or precise value match)
                        if val_e == val_c:
                            satisfied = True
                            break
                            
            if not satisfied:
                 # If explicit quantity is missing/unsatisfied in evidence
                 return {
                        "hallucination_type": "UNSUPPORTED_SPECIFICITY",
                        "reason": f"Specific figure '{n}' ({intent} intent) not supported by evidence.",
                        "score": 0.5 
                    }
        return None

    def _check_authority_bleed(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detects if authorship is attributed based on influence/leadership rather than technical execution.
        """
        # Subject must be PERSON
        subj = claim.get("subject_entity", {})
        if subj.get("entity_type") != "PERSON": return None
        
        # Predicate Authorship
        pred = claim.get("predicate", "").lower()
        auth_keywords = ["designed", "engineered", "built", "implemented", "coded", "programmed", "developed"]
        if not any(k in pred for k in auth_keywords): return None
        
        # Object Technical
        obj_txt = claim.get("object", "").lower()
        tech_keywords = ["processor", "chip", "hardware", "system", "architecture", "kernel", "quantum", "algorithm", "equation"]
        if not any(k in obj_txt for k in tech_keywords): return None
        
        return {
            "hallucination_type": "AUTHORITY_BLEED",
            "reason": "Authority Bleed: Attributed technical authorship to influencer/leader.",
            "score": 0.9
        }

    def _check_court_authority(self, claim: Dict[str, Any], evidence: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Detects misattribution of court rulings (e.g. Supreme Court vs Lower Court).
        """
        # Subject must be a Court
        subj_txt = claim.get("subject", "").lower() 
        c_text = claim.get("claim_text", "").lower()
        subj_ent = claim.get("subject_entity", {})
        
        # Keywords for high courts
        high_courts = ["supreme court", "high court", "scotus"]
        
        # Check explicit subject text OR claim text context (e.g. "The Supreme Court ruled...")
        is_high_court = any(k in subj_txt or k in c_text for k in high_courts)
        
        if not is_high_court:
            return None
            
        # Predicate involves ruling
        pred = claim.get("predicate", "").lower()
        if "ruled" not in pred and "decided" not in pred:
            return None
            
        # Check evidence for contradiction of court level
        # If evidence mentions "district court", "lower court", "judge" (singular) without "supreme"
        # Logic: If claim says Supreme Court, but evidence says District Court -> Conflict.
        
        # Flatten evidence
        all_text = ""
        for src in evidence.values():
            for item in src:
                all_text += " " + item.get("snippet", "") + " " + item.get("sentence", "")
        all_text = all_text.lower()
        
        if "district court" in all_text or "federal judge" in all_text or "lower court" in all_text:
            if "supreme court" not in all_text:
                return {
                    "hallucination_type": "COURT_AUTHORITY_MISATTRIBUTION",
                    "reason": "Court Misattribution: Evidence cites lower court, not Supreme Court.",
                    "score": 0.95
                }
        return None

    def _check_impossible_dosage(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detects dangerous medical dosages.
        """
        # Heuristic: "ibuprofen" + > 800mg/dose or > 3200mg/day
        c_text = claim.get("claim_text", "").lower()
        
        if "ibuprofen" in c_text or "advil" in c_text or "motrin" in c_text:
            # Extract dosage stats
            # Look for number + mg
            mgs = re.findall(r'(\d+(?:,\d{3})?)\s*mg', c_text)
            for m in mgs:
                val = int(m.replace(",", ""))
                # High dose check (800mg is Rx max usually, 1200 is definitely high per dose)
                if val >= 1000:
                    return {
                        "hallucination_type": "IMPOSSIBLE_DOSAGE",
                        "reason": f"Safety Alert: Dosage {val}mg exceeds standard medical limits.",
                        "score": 1.0
                    }
        return None

    def _check_scope_overgeneralization(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detects structural impossibility of universal mandates (Scope Hallucination).
        """
        c_text = claim.get("claim_text", "").lower()
        subj_txt = claim.get("subject", "").lower()
        pred_txt = claim.get("predicate", "").lower()
        obj_txt = claim.get("object", "").lower()
        
        # 1. Check Authority Subject
        if not any(a in subj_txt or a in c_text for a in self.SCOPE_AUTHORITIES):
            return None
            
        # 2. Check Force Predicate
        if not any(p in pred_txt or p in c_text for p in self.SCOPE_FORCE_PREDICATES):
            return None
            
        # 3. Check Universal Object/Target
        # "Vaccine" or "Mask" in singular context usually implies universal policy in these hallucinations.
        # Or explicit "everyone", "all"
        found_target = None
        for o in self.SCOPE_UNIVERSAL_OBJECTS:
             # Check distinct word boundaries for short words like "all"
             if o in ["all", "mask"]:
                  # Allow plural for mask
                  pattern = r'\b' + re.escape(o) + r'(?:s)?\b' if o == "mask" else r'\b' + re.escape(o) + r'\b'
                  if re.search(pattern, c_text):
                       found_target = o
                       break
             elif o in obj_txt or o in c_text:
                found_target = o
                break
        
        if not found_target:
            return None
            
        # Refinement: If target is generic ("vaccine", "mask"), REQUIRE explicit universal marker
        # to ensure we don't flag "mandated a vaccine requirement for entry" (scoped by context implied).
        # We only refute if it explicitly claims universality.
        if found_target in {"vaccine", "mask"}:
            if not any(u in c_text for u in self.UNIVERSAL_MARKERS):
                 return None
            
        # 4. Check for Limiters (Absence of)
        if any(l in c_text for l in self.SCOPE_LIMITERS):
            return None
            
        return {
            "hallucination_type": "SCOPE_OVERGENERALIZATION",
            "reason": "Scope Hallucination: Claim asserts universal coercive authority without specifying a legally valid scope.",
            "score": 0.95
        }
