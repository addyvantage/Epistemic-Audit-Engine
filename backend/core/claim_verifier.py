from typing import Dict, Any, List, Set, Optional
import re
import logging
import uuid
from .nli_engine import NLIEngine
from .hallucination_detector import HallucinationDetector
from .alignment_scorer import AlignmentScorer
from .hallucination_attributor import HallucinationAttributor
from .property_mapper import PropertyMapper
from .wikidata_retriever import WikidataRetriever

logger = logging.getLogger(__name__)

class ClaimVerifier:
    def __init__(self):
        self.nli = NLIEngine()
        self.detector = HallucinationDetector()
        self.alignment_scorer = AlignmentScorer()
        self.attributor = HallucinationAttributor()
        self.property_mapper = PropertyMapper()
        self.wikidata = WikidataRetriever()
        
        # v1.3.1 Canonical Restoration (Extended v1.6)
        # Temporal predicates -> date properties
        self.CANONICAL_PRED_MAP = {
            "founded": "P571", # inception
            "born": "P569", # date of birth
            "died": "P570", # date of death
            "released": "P577", # publication date
            "established": "P571",
            "incepted": "P571",
            "created": "P571" # sometimes
        }

        # v1.6: Canonical biographical properties that should use relaxed matching
        # These properties represent core identity facts that are well-established
        self.CANONICAL_BIOGRAPHICAL_PROPS = {
            "P569",  # date of birth
            "P570",  # date of death
            "P19",   # place of birth
            "P20",   # place of death
            "P27",   # country of citizenship / nationality
            "P571",  # inception (for organizations)
            "P159",  # headquarters location
        }

        # v1.6: Location predicates -> place properties
        self.CANONICAL_LOCATION_PRED_MAP = {
            "born in": "P19",      # place of birth
            "died in": "P20",      # place of death
            "from": "P27",         # nationality / citizenship
            "citizen of": "P27",
            "nationality": "P27",
            "headquartered": "P159",
            "based in": "P159",
        }

        self.PREDICATE_PROPERTY_HINTS = {
            "headquarters": {"P159", "P131", "P276", "P17"},
            "located in": {"P131", "P276", "P17"},
            "country": {"P17", "P27"},
            "ceo": {"P169", "P488", "P39"},
            "founder": {"P112"},
            "parent organization": {"P749", "P127", "P355", "P361"},
            "subsidiary": {"P355", "P749", "P127", "P361"},
            "acquired": {"P127", "P749", "P355", "P361"},
            "founded": {"P571", "P112"},
            "inception": {"P571"},
            "born": {"P569", "P19"},
            "died": {"P570", "P20"},
        }

        self.PROP_LABELS = {
            "P159": "headquarters location",
            "P131": "located in administrative territory",
            "P276": "location",
            "P17": "country",
            "P169": "chief executive officer",
            "P488": "chairperson",
            "P39": "position held",
            "P112": "founder",
            "P749": "parent organization",
            "P127": "owned by",
            "P355": "subsidiary",
            "P361": "part of",
            "P571": "inception",
            "P569": "date of birth",
            "P570": "date of death",
            "P19": "place of birth",
            "P20": "place of death",
            "P27": "country of citizenship",
            "P577": "publication date",
        }

        self.TEMPORAL_PROPS = {"P569", "P570", "P571", "P577"}
        self.LOCATION_PROPS = {"P159", "P276", "P131", "P17"}
        self.OWNERSHIP_PROPS = {"P127", "P749", "P355", "P361"}

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
        
        # Fix 5: Sanity Rule
        # If neutral text (heuristic: >3 claims), Verified > 0.
        n_verified = sum(1 for c in output_claims if c["verification"]["verdict"] == "SUPPORTED")
        
        if len(output_claims) > 3 and n_verified == 0:
             # Downgrade INSUFFICIENT -> UNCERTAIN
             for c in output_claims:
                 if c["verification"]["verdict"] == "INSUFFICIENT_EVIDENCE":
                     c["verification"]["verdict"] = "UNCERTAIN"
                     c["verification"]["reasoning"] += " [System: Low confidence fallback]"
        
        return {"claims": output_claims}

    def _verify_single_claim(self, claim: Dict[str, Any], config: Dict[str, Any] = {}) -> Dict[str, Any]:
        evidence = claim.get("evidence", {}) # wikidata, wikipedia lists
        disable_nli = config.get("ablation", {}).get("disable_nli", False)
        
        supporting_ids = []
        refuting_ids = []
        authoritative_contradictions: List[Dict[str, Any]] = []

        target_wikidata_props = self._resolve_target_properties(claim)
        wikidata_positive_props = self._collect_positive_wikidata_properties(
            evidence.get("wikidata", []),
            claim
        )
        
        # 1. Evidence Eligibility Filter
        valid_evidence = []
        for source, items in evidence.items():
            if source == "grokipedia": continue # Narrative evidence rule: Unsupported alone
            
            for item in items:
                if self._is_eligible(item, claim):
                    valid_evidence.append(item)

        # 2. Logic Check per Item
        best_support_score = 0.0
        best_refute_score = 0.0
        best_evidence_item = None

        has_direct_support = False
        has_contradiction = False

        # Weak support accumulation (v1.4)
        # Track weak support for evidence that provides partial corroboration
        weak_support_count = 0
        weak_support_total_score = 0.0
        
        for ev in valid_evidence:
            source = ev.get("source")
            alignment = ev.get("alignment", {})
            val = ev.get("value", "") # Wikidata value
            
            # --- SUPERPROMPT: PRIMARY DOCUMENT PRIORITY ---
            if source == "PRIMARY_DOCUMENT":
                 # Strict Contradiction Check?
                 # Assuming PRIMARY_DOCUMENT is structured fact.
                 # Check Temporal or Value logic if available.
                 # Currently we trust alignment from Retriever.
                 
                 # Simulating Check: If Retriever returned it, it matched basic alignment.
                 # Check negative value? 
                 # For now, if present and aligned -> SUPPORTED
                 supporting_ids.append(ev.get("evidence_id"))
                 has_direct_support = True
                 best_evidence_item = ev
                 
                 # Superprompt: Confidence >= 0.95
                 best_support_score = 0.95
                 
                 # If we found primary support, we can stop searching if we trust it absolutely.
                 # But let's collect for transparency, but score is locked.
                 continue

            # A. Wikidata Logic (Structured) - Enhanced v1.4, v1.6
            # Structured Evidence Independence: Wikidata evidence can independently
            # yield SUPPORTED when alignment metadata confirms the match.
            if source == "WIKIDATA":
                # Extract alignment fields
                s_match = alignment.get("subject_match", False)
                p_match = alignment.get("predicate_match", False)
                o_match = alignment.get("object_match")
                t_match = alignment.get("temporal_match")
                prop_id = ev.get("property", "")

                # v1.6: Canonical Biographical Property Override
                # For core identity facts (birth date, birth place, death date, nationality),
                # if subject matches and we have the right property, this is authoritative.
                is_canonical_biographical = prop_id in self.CANONICAL_BIOGRAPHICAL_PROPS

                # v1.6: Skip contradiction marking for canonical biographical properties
                # when the same property has multiple values (e.g., Newton's birth date
                # has both 1642 Julian and 1643 Gregorian). We only mark as refutation
                # if there's no matching value at all.
                is_refutation = False

                # Temporal contradiction: claim says year X, evidence says year Y
                # Only mark as refutation if:
                # 1. It's NOT a canonical biographical property, OR
                # 2. It's canonical but we'll check later if ANY value matches
                if t_match is False and not is_canonical_biographical:
                    c_val = claim.get("object", "")
                    # v1.6: Use relaxed temporal compatibility for year-level claims
                    if not self._temporal_compatible(c_val, val):
                        is_refutation = True
                        refuting_ids.append(ev.get("evidence_id"))

                # NOTE: We do NOT treat object_match=False as a contradiction for
                # entity-valued properties (Qxxx values) because:
                # 1. Entity hierarchies exist (Mountain View is IN California)
                # 2. String matching "California" vs "Q486860" is not semantic
                # 3. False positives are worse than false negatives for refutation
                #
                # object_match=False for entity values is treated as NEUTRAL, not contradiction

                if is_refutation:
                    has_contradiction = True
                    if best_refute_score < 0.9:
                        best_refute_score = 0.9

                # v1.6: Canonical Biographical Override
                # For canonical biographical properties, subject + predicate match is sufficient
                # for SUPPORTED verdict. The property's existence confirms the fact.
                elif (
                    s_match
                    and p_match
                    and is_canonical_biographical
                    and self._is_canonical_support_compatible(claim, ev)
                ):
                    # For canonical facts, we trust the Wikidata property even without
                    # strict object/temporal alignment. The property value IS the truth.
                    supporting_ids.append(ev.get("evidence_id"))
                    has_direct_support = True
                    from config.core_config import CONFIDENCE_CAP_STRUCTURED
                    if CONFIDENCE_CAP_STRUCTURED > best_support_score:
                        best_support_score = CONFIDENCE_CAP_STRUCTURED
                        best_evidence_item = ev
                        best_evidence_item["support_type"] = "CANONICAL_BIOGRAPHICAL"

                # Structured Evidence Independence Rule (v1.4):
                # If subject AND predicate match, and we have positive object/temporal match,
                # this is DIRECT STRUCTURED SUPPORT regardless of narrative evidence.
                elif s_match and p_match:
                    is_positive_match = (o_match is True) or (t_match is True)

                    if is_positive_match:
                        # Full structured support
                        supporting_ids.append(ev.get("evidence_id"))
                        has_direct_support = True
                        # Structured evidence caps at CONFIDENCE_CAP_STRUCTURED (0.85)
                        from config.core_config import CONFIDENCE_CAP_STRUCTURED
                        if CONFIDENCE_CAP_STRUCTURED > best_support_score:
                            best_support_score = CONFIDENCE_CAP_STRUCTURED
                            best_evidence_item = ev
                            best_evidence_item["support_type"] = "STRUCTURED_INDEPENDENT"

                    elif o_match is None and t_match is None:
                        # Subject and predicate match, but can't verify object/temporal
                        # This is still supportive for general facts
                        supporting_ids.append(ev.get("evidence_id"))
                        has_direct_support = True
                        if 0.75 > best_support_score:
                            best_support_score = 0.75
                            best_evidence_item = ev
                            best_evidence_item["support_type"] = "STRUCTURED_PARTIAL"

                    # o_match=False with entity values: treat as neutral, not contradiction
                    # The claim may still be true but we can't verify it from this property

            # B. Wikipedia Logic (Textual -> NLI)
            elif source == "WIKIPEDIA":
                sent_text = ev.get("sentence", "") or ev.get("snippet", "")
                claim_text = claim.get("claim_text", "")
                
                if not sent_text: continue

                nli_result = {"entailment": 0.0, "contradiction": 0.0, "neutral": 1.0}
                if not disable_nli:
                    nli_result = self.nli.classify(sent_text, claim_text)
                else:
                    # Fallback only on high similarity
                    similarity_score = ev.get("score", 0.0)
                    if similarity_score > 0.8:
                        nli_result["entailment"] = 0.8
                
                # Use AlignmentScorer (Strict)
                alignment = self.alignment_scorer.score_alignment(claim_text, ev, nli_result)
                signal = alignment["signal"]
                score = alignment["score"]
                
                if signal == "SUPPORT":
                    supporting_ids.append(ev.get("evidence_id"))
                    has_direct_support = True
                    if score > best_support_score:
                        best_support_score = score
                        best_evidence_item = ev
                        
                elif signal == "CONTRADICTION":
                    refuting_ids.append(ev.get("evidence_id"))
                    has_contradiction = True
                    if score > best_refute_score:
                        best_refute_score = score
                        
                    # Attribute Hallucination
                    h_flag = self.attributor.attribute(alignment, ev)
                    if h_flag:
                        # Append to claim hallucinations immediately or later? 
                        # We need a list to collect them. 'hallucinations' is overwritten later.
                        # Let's add to a temporary list 'textual_hallucinations' to merge later.
                        if "textual_hallucinations" not in claim: claim["textual_hallucinations"] = []
                        claim["textual_hallucinations"].append(h_flag)
                        
                elif signal == "WEAK_SUPPORT":
                    # Weak Support Accumulation (v1.4)
                    # Track weak support for claims with multiple partial corroborations
                    # Multiple weak supports may upgrade INSUFFICIENT to UNCERTAIN
                    weak_support_count += 1
                    weak_support_total_score += score

        # Predicate-aware structured contradiction pass over all Wikidata evidence
        # (including object-centric retrieval records that may fail strict S+P eligibility).
        for ev in evidence.get("wikidata", []):
            contradiction = self._evaluate_structured_contradiction(
                claim=claim,
                evidence_item=ev,
                target_properties=target_wikidata_props,
                positive_properties=wikidata_positive_props,
            )
            if not contradiction:
                continue

            evidence_id = contradiction.get("evidence_id") or ev.get("evidence_id")
            if not evidence_id:
                evidence_id = self._generate_wikidata_evidence_id(ev)
                ev["evidence_id"] = evidence_id

            contradiction["evidence_id"] = evidence_id
            authoritative_contradictions.append(contradiction)
            refuting_ids.append(evidence_id)
            has_contradiction = True
            if contradiction.get("confidence", 0.0) > best_refute_score:
                best_refute_score = contradiction["confidence"]

        # v1.3.1 KG FALLBACK VERIFICATION (Rule C1/C2) - Extended v1.6
        # If no narrative evidence and no direct support yet, check Wikidata Canonical Properties explicitly.
        if not has_direct_support and not has_contradiction:
            claim_pred = claim.get("predicate", "").lower()
            claim_text = claim.get("claim_text", "").lower()
            target_prop = None

            # 1. Match Canonical Temporal Predicate
            for key, pid in self.CANONICAL_PRED_MAP.items():
                if key in claim_pred:
                    target_prop = pid
                    break

            # v1.6: Also check location predicates (birth place, nationality)
            if not target_prop:
                for key, pid in self.CANONICAL_LOCATION_PRED_MAP.items():
                    if key in claim_pred or key in claim_text:
                        target_prop = pid
                        break

            # 2. Asserted & Resolved Check
            is_asserted = claim.get("epistemic_status", "ASSERTED") == "ASSERTED"
            is_resolved = claim.get("subject_entity", {}).get("resolution_status") in ["RESOLVED", "RESOLVED_SOFT", "RESOLVED_COREF"]

            if target_prop and is_asserted and is_resolved:
                # 3. Scan Wikidata Evidence for Property Match
                # Even if alignment failed previously, if we find the property, we trust it for Canonical facts.
                for ev in evidence.get("wikidata", []):
                    if ev.get("property") == target_prop:
                         # Attach Record
                         supporting_ids.append(ev.get("evidence_id"))
                         has_direct_support = True
                         best_support_score = 0.95 # Guaranteed high confidence
                         best_evidence_item = ev
                         best_evidence_item["source_type"] = "STRUCTURED_KG" # Mark for reasoning
                         break
        confidence = 0.0
        reasoning = "No authoritative evidence found."
        
        # --- HALLUCINATION DETECTION (PHASE 8) ---
        hallucinations = self.detector.detect(claim, evidence)
        
        # Merge Textual Hallucinations (Phase 4.2)
        if "textual_hallucinations" in claim:
            hallucinations.extend(claim.pop("textual_hallucinations"))

        critical_hallucinations = [h for h in hallucinations if h.get("severity") == "CRITICAL"]
        non_critical_hallucinations = [h for h in hallucinations if h.get("severity") == "NON_CRITICAL"]
        
        # --- VERDICT RESOLUTION (STRICT PRECEDENCE v1.2) ---
        # 1. CRITICAL Hallucination -> REFUTED (Always)
        # 2. Authoritative Contradiction -> REFUTED
        # 3. Non-Critical Hallucination -> UNCERTAIN (Blocks Support)
        # 4. Direct Support -> SUPPORTED
        # 5. Weak/Narrative -> INSUFFICIENT
        
        # 1. Critical
        if critical_hallucinations:
            final_verdict = "REFUTED"
            # Pick highest score
            best_h = max(critical_hallucinations, key=lambda x: x.get("score", 0))
            confidence = best_h.get("score", 0.95)
            reasoning = f"Critical Hallucination: {best_h.get('reason')}"
            
        # 2. Contradiction
        elif has_contradiction:
            if refuting_ids:
                final_verdict = "REFUTED"
                confidence = min(0.95, max(0.7, best_refute_score))
            else:
                final_verdict = "UNCERTAIN"
                confidence = 0.5

            if authoritative_contradictions:
                best_kg = max(authoritative_contradictions, key=lambda x: x.get("confidence", 0.0))
                reasoning = best_kg.get("reasoning", "Contradicted by Wikidata.")
            else:
                reasoning = "Contradicted by textual evidence."
            
        # 3. Non-Critical (e.g. Specificity, Bleed) - BLOCKS SUPPORT
        elif non_critical_hallucinations:
             # Default to UNCERTAIN
             final_verdict = "UNCERTAIN"
             best_h = max(non_critical_hallucinations, key=lambda x: x.get("score", 0))
             reasoning = f"Uncertain: {best_h.get('reason')}"
             confidence = 0.5
             
             # Special Case: AUTHORITY_BLEED (Refute if no support found)
             if any(h["hallucination_type"] == "AUTHORITY_BLEED" for h in non_critical_hallucinations):
                 final_verdict = "REFUTED"
                 reasoning = f"Refuted by Hallucination: {best_h.get('reason')}"
                 confidence = 0.9

        # 4. Support
        elif has_direct_support:
            final_verdict = "SUPPORTED"
            
            # --- CONFIDENCE CAPPING (Modality-Based) ---
            from config.core_config import CONFIDENCE_CAP_STRUCTURED, CONFIDENCE_CAP_PRIMARY
            
            raw_confidence = min(0.99, best_support_score)
            modality = best_evidence_item.get("modality", "TEXTUAL")
            source = best_evidence_item.get("source")
            
            # Apply Caps
            if source == "PRIMARY_DOCUMENT":
                confidence = min(raw_confidence, CONFIDENCE_CAP_PRIMARY)
            elif source == "WIKIDATA" or modality == "STRUCTURED":
                confidence = min(raw_confidence, CONFIDENCE_CAP_STRUCTURED)
            else:
                # Textual Wikipedia
                confidence = raw_confidence

            # Dynamic Reasoning
            src = best_evidence_item.get("source")
            if src == "PRIMARY_DOCUMENT":
                 auth = best_evidence_item.get("authority", "SEC")
                 doc_type = best_evidence_item.get("document_type", "Filing")
                 year = best_evidence_item.get("filing_year", "")
                 reasoning = f"Verified by Primary Document: {auth} {doc_type} ({year})"
            elif src == "WIKIDATA":
                prop = best_evidence_item.get("property", "")
                val = best_evidence_item.get("value", "") 
                reasoning = f"Verified by Wikidata property {prop} ({val})."
            elif src == "WIKIPEDIA":
                snippet = best_evidence_item.get("snippet", "")
                snippet_preview = (snippet[:100] + '...') if len(snippet) > 100 else snippet
                reasoning = f"Verified by Wikipedia: \"{snippet_preview}\""
        
        # 5. Insufficient - with Weak Support Accumulation (v1.4)
        else:
            final_verdict = "INSUFFICIENT_EVIDENCE"
            if not valid_evidence and evidence.get("grokipedia"):
                reasoning = "Only narrative evidence available (Grokipedia)."
            else:
                has_weak = any(ev.get("score", 0) > 0.6 for ev in evidence.get("wikipedia", []))
                if has_weak:
                    reasoning = "Evidence found but insufficient for verification."
                else:
                    reasoning = "No relevant evidence found."

            # Weak Support Accumulation Rule (v1.4):
            # If we have multiple weak supports converging AND no contradictions,
            # upgrade INSUFFICIENT_EVIDENCE to UNCERTAIN (not SUPPORTED).
            # This represents "suggestive but not conclusive" evidence.
            #
            # Epistemic Note: This does NOT inflate support rates - it honestly
            # represents cases where evidence exists but doesn't meet SUPPORTED thresholds.
            if weak_support_count >= 2 and not has_contradiction:
                avg_weak_score = weak_support_total_score / weak_support_count
                if avg_weak_score >= 0.68:  # Slightly above WEAK threshold
                    final_verdict = "UNCERTAIN"
                    confidence = 0.5
                    reasoning = (
                        f"Multiple weak corroborations ({weak_support_count} sources, "
                        f"avg score {avg_weak_score:.2f}). Suggestive but not conclusive."
                    )
        
        # FIX 2: Verdict-Hallucination Consistency (Normalization)
        # If verdict is SUPPORTED, ensure no hallucinations remain.
        if final_verdict == "SUPPORTED" and hallucinations:
             hallucinations = [] # Force clear

        # Evidence Sufficiency Classification (v1.5)
        # Computes explicit categorization for frontend messaging
        evidence_sufficiency = self._classify_evidence_sufficiency(evidence, supporting_ids)
        evidence_summary = self._build_evidence_summary(evidence, supporting_ids)

        supporting_ids = [eid for eid in dict.fromkeys(supporting_ids) if eid]
        refuting_ids = [eid for eid in dict.fromkeys(refuting_ids) if eid]

        claim["hallucinations"] = hallucinations
        claim["verification"] = {
            "verdict": final_verdict,
            "confidence": round(confidence, 2),
            "used_evidence_ids": supporting_ids,
            "contradicted_by": refuting_ids,
            "reasoning": reasoning,
            # Evidence Sufficiency (v1.5) - Enables accurate frontend messaging
            "evidence_sufficiency": evidence_sufficiency,
            "evidence_summary": evidence_summary,
            "authoritative_contradictions": authoritative_contradictions,
        }

        return claim

    def _resolve_target_properties(self, claim: Dict[str, Any]) -> Set[str]:
        predicate = (claim.get("predicate", "") or "").lower()
        claim_text = (claim.get("claim_text", "") or "").lower()
        combined = f"{predicate} {claim_text}".strip()

        target_properties: Set[str] = set(self.property_mapper.get_potential_properties(predicate))
        for key, props in self.PREDICATE_PROPERTY_HINTS.items():
            if key in combined:
                target_properties.update(props)

        return target_properties

    def _collect_positive_wikidata_properties(
        self,
        wikidata_evidence: List[Dict[str, Any]],
        claim: Dict[str, Any]
    ) -> Set[str]:
        positive_props: Set[str] = set()
        claim_object = self._extract_claim_object(claim)

        for ev in wikidata_evidence:
            prop = ev.get("property")
            if not prop:
                continue

            alignment = ev.get("alignment", {})
            o_match = alignment.get("object_match")
            t_match = alignment.get("temporal_match")
            value = str(ev.get("value", "") or "")

            if o_match is True or t_match is True:
                positive_props.add(prop)
                continue

            if prop in self.TEMPORAL_PROPS and claim_object and self._temporal_compatible(claim_object, value):
                positive_props.add(prop)
                continue

            if prop in {"P19", "P20", "P159"} and self._is_place_compatible_with_evidence(claim, ev):
                positive_props.add(prop)

        return positive_props

    def _is_canonical_support_compatible(self, claim: Dict[str, Any], evidence_item: Dict[str, Any]) -> bool:
        prop = evidence_item.get("property", "")
        claim_object = self._extract_claim_object(claim)
        evidence_value = str(evidence_item.get("value", "") or "")
        alignment = evidence_item.get("alignment", {})

        if not claim_object:
            return False

        if prop in self.TEMPORAL_PROPS:
            return self._temporal_compatible(claim_object, evidence_value)

        if prop in {"P19", "P20", "P159"}:
            return self._is_place_compatible_with_evidence(claim, evidence_item)

        if alignment.get("object_match") is True:
            return True

        claim_norm = self._normalize_text(claim_object)
        if evidence_value.startswith("Q"):
            evidence_label = self._normalize_text(self._resolve_qid_label(evidence_value))
            if evidence_label and (
                claim_norm == evidence_label
                or claim_norm in evidence_label
                or evidence_label in claim_norm
            ):
                return True

        value_norm = self._normalize_text(evidence_value)
        return bool(
            claim_norm
            and value_norm
            and (claim_norm == value_norm or claim_norm in value_norm or value_norm in claim_norm)
        )

    def _evaluate_structured_contradiction(
        self,
        claim: Dict[str, Any],
        evidence_item: Dict[str, Any],
        target_properties: Set[str],
        positive_properties: Set[str],
    ) -> Optional[Dict[str, Any]]:
        resolution_status = claim.get("subject_entity", {}).get("resolution_status")
        if resolution_status not in {"RESOLVED", "RESOLVED_SOFT", "RESOLVED_COREF"}:
            return None

        prop = evidence_item.get("property")
        if not prop:
            return None

        if target_properties and prop not in target_properties:
            return None

        if prop in positive_properties:
            return None

        claim_object = self._extract_claim_object(claim)
        if not claim_object:
            return None

        alignment = evidence_item.get("alignment", {})
        evidence_value = str(evidence_item.get("value", "") or "")
        evidence_id = evidence_item.get("evidence_id")
        prop_label = self.PROP_LABELS.get(prop, prop)

        if prop in self.TEMPORAL_PROPS:
            claim_years = self._extract_years(claim_object)
            evidence_years = self._extract_years(evidence_value)
            if claim_years and evidence_years and not self._temporal_compatible(claim_object, evidence_value):
                return {
                    "reasoning": f"Contradicted by Wikidata {prop_label}: claim year does not match authoritative record.",
                    "confidence": 0.92,
                    "property": prop,
                    "evidence_id": evidence_id,
                }
            return None

        if prop in self.LOCATION_PROPS:
            is_contradiction, detail = self._evaluate_location_contradiction(claim, evidence_item)
            if is_contradiction:
                return {
                    "reasoning": f"Contradicted by Wikidata {prop_label}: {detail}",
                    "confidence": 0.9,
                    "property": prop,
                    "evidence_id": evidence_id,
                }

        if prop in self.OWNERSHIP_PROPS:
            is_contradiction, detail = self._evaluate_ownership_contradiction(claim, evidence_item)
            if is_contradiction:
                return {
                    "reasoning": f"Contradicted by Wikidata {prop_label}: {detail}",
                    "confidence": 0.88,
                    "property": prop,
                    "evidence_id": evidence_id,
                }

        if alignment.get("temporal_match") is False and prop in self.TEMPORAL_PROPS:
            return {
                "reasoning": f"Contradicted by Wikidata {prop_label}.",
                "confidence": 0.9,
                "property": prop,
                "evidence_id": evidence_id,
            }

        return None

    def _evaluate_location_contradiction(
        self,
        claim: Dict[str, Any],
        evidence_item: Dict[str, Any],
    ) -> (bool, str):
        claim_qids, claim_labels = self._extract_claim_place_candidates(claim)
        if not claim_qids and not claim_labels:
            return False, ""

        evidence_qid = str(evidence_item.get("value", "") or "")
        if not evidence_qid.startswith("Q"):
            return False, ""

        containment = self.wikidata.get_place_containment(evidence_qid)
        containment_qids = set(containment.get("qids", []))
        containment_labels = {self._normalize_text(x) for x in containment.get("labels", []) if x}

        # If we cannot build a containment context, avoid false refutations.
        if not containment_qids and not containment_labels:
            return False, ""

        if self._is_place_compatible_with_evidence(claim, evidence_item):
            return False, ""

        matched_labels = ", ".join(containment.get("labels", [])[:3]) or evidence_qid
        return True, f"authoritative location is {matched_labels}, not '{claim.get('object', '')}'."

    def _is_place_compatible_with_evidence(self, claim: Dict[str, Any], evidence_item: Dict[str, Any]) -> bool:
        claim_qids, claim_labels = self._extract_claim_place_candidates(claim)
        if not claim_qids and not claim_labels:
            return False

        evidence_qid = str(evidence_item.get("value", "") or "")
        if not evidence_qid.startswith("Q"):
            value_norm = self._normalize_text(evidence_qid)
            return any(
                label == value_norm or label in value_norm or value_norm in label
                for label in claim_labels
                if label and value_norm
            )

        containment = self.wikidata.get_place_containment(evidence_qid)
        containment_qids = set(containment.get("qids", []))
        containment_labels = {self._normalize_text(x) for x in containment.get("labels", []) if x}

        if claim_qids.intersection(containment_qids):
            return True

        for label in claim_labels:
            if label in containment_labels:
                return True
            if any(label in candidate or candidate in label for candidate in containment_labels if candidate):
                return True

        return False

    def _evaluate_ownership_contradiction(
        self,
        claim: Dict[str, Any],
        evidence_item: Dict[str, Any],
    ) -> (bool, str):
        predicate_text = f"{claim.get('predicate', '')} {claim.get('claim_text', '')}".lower()
        is_acquisition_claim = any(
            token in predicate_text for token in ["acquired", "acquire", "bought", "purchased", "takeover"]
        )
        if not is_acquisition_claim:
            return False, ""

        # Use explicit ownership/parent properties only for acquisition contradiction.
        if evidence_item.get("property") not in {"P127", "P749"}:
            return False, ""

        subject_qid = claim.get("subject_entity", {}).get("entity_id", "")
        object_qid = claim.get("object_entity", {}).get("entity_id", "")
        if not (subject_qid.startswith("Q") and object_qid.startswith("Q")):
            return False, ""

        # For acquisition contradictions, evidence must be about the claimed target entity.
        evidence_entity_qid = evidence_item.get("entity_id", "")
        if evidence_entity_qid != object_qid:
            return False, ""

        evidence_owner_qid = str(evidence_item.get("value", "") or "")
        if not evidence_owner_qid.startswith("Q"):
            return False, ""

        accepted_owners = {subject_qid}
        accepted_owners.update(self.wikidata.get_entity_property_qids(subject_qid, ["P127", "P749"]))

        if evidence_owner_qid in accepted_owners:
            return False, ""

        owner_label = self._resolve_qid_label(evidence_owner_qid)
        return True, f"target entity owner/parent is {owner_label} ({evidence_owner_qid}), not the claim subject."

    def _extract_claim_place_candidates(self, claim: Dict[str, Any]) -> (Set[str], Set[str]):
        qids: Set[str] = set()
        labels: Set[str] = set()

        object_entity = claim.get("object_entity", {}) or {}
        object_qid = object_entity.get("entity_id")
        if object_qid and object_qid.startswith("Q"):
            qids.add(object_qid)

        raw_candidates = [
            claim.get("object", ""),
            object_entity.get("canonical_name", ""),
            object_entity.get("text", ""),
        ]

        for candidate in raw_candidates:
            normalized = self._normalize_text(candidate)
            if normalized:
                labels.add(normalized)

        return qids, labels

    def _resolve_qid_label(self, qid: str) -> str:
        containment = self.wikidata.get_place_containment(qid, max_hops=0)
        labels = containment.get("labels", [])
        if labels:
            return labels[0]
        return qid

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"[^a-z0-9\s]", "", (text or "").lower()).strip()

    def _extract_claim_object(self, claim: Dict[str, Any]) -> str:
        obj = (claim.get("object", "") or "").strip()
        if obj:
            return obj

        claim_text = claim.get("claim_text", "") or ""
        return claim_text.strip()

    def _extract_years(self, text: str) -> List[str]:
        return re.findall(r"\b(\d{4})\b", str(text))

    def _generate_wikidata_evidence_id(self, evidence_item: Dict[str, Any]) -> str:
        entity_id = evidence_item.get("entity_id", "")
        prop = evidence_item.get("property", "")
        value = evidence_item.get("value", "")
        unique_str = f"WIKIDATA:{entity_id}:{prop}:{value}"
        return str(uuid.uuid5(uuid.NAMESPACE_OID, unique_str))
        
    def _temporal_compatible(self, claim_val: str, ev_val: str) -> bool:
        """
        Check if claim's temporal value is compatible with evidence value.

        v1.6: Relaxed temporal granularity matching.
        - Year-level claims (e.g., "1643") match full dates (e.g., "1643-01-04")
        - Exact day matching is NOT required unless claim specifies a day
        - Handles both ISO format (+1643-01-04) and plain year strings (1643)
        """
        if not ev_val:
            return False

        # Extract years from both claim and evidence
        claim_years = re.findall(r'\b(\d{4})\b', str(claim_val))
        ev_years = re.findall(r'\b(\d{4})\b', str(ev_val))

        if not claim_years:
            return False

        # If evidence has no parseable year but starts with + (ISO format),
        # try to extract from the ISO prefix
        if not ev_years and ev_val.startswith("+"):
            match = re.search(r'\+(\d{4})', ev_val)
            if match:
                ev_years = [match.group(1)]

        if not ev_years:
            return False

        # Year-level matching: claim year must match evidence year
        # This allows "1643" to match "+1643-01-04T00:00:00Z"
        return any(cy in ev_years for cy in claim_years)

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

    def _classify_evidence_sufficiency(
        self,
        evidence: Dict[str, Any],
        used_evidence_ids: List[str]
    ) -> str:
        """
        Classify overall evidence sufficiency for frontend messaging (v1.5).

        Distinguishes:
        - ES_VERIFIED: Structured evidence directly supports claim
        - ES_CORROBORATED: Textual evidence contributes to verdict
        - ES_EVALUATED: Evidence found but insufficient for verdict
        - ES_ABSENT: No evidence retrieved

        Args:
            evidence: Dict with wikidata, wikipedia, primary_document lists
            used_evidence_ids: List of evidence IDs that contributed to verdict

        Returns:
            One of: ES_VERIFIED, ES_CORROBORATED, ES_EVALUATED, ES_ABSENT
        """
        from config.core_config import (
            EVIDENCE_SUFFICIENCY_VERIFIED,
            EVIDENCE_SUFFICIENCY_CORROBORATED,
            EVIDENCE_SUFFICIENCY_EVALUATED,
            EVIDENCE_SUFFICIENCY_ABSENT
        )

        # Check for any retrieved evidence
        wikidata_items = evidence.get("wikidata", [])
        wikipedia_items = evidence.get("wikipedia", [])
        primary_items = evidence.get("primary_document", [])

        has_any_evidence = bool(wikidata_items or wikipedia_items or primary_items)

        if not has_any_evidence:
            return EVIDENCE_SUFFICIENCY_ABSENT

        # Check if structured evidence was used (highest authority)
        used_ids_set = set(used_evidence_ids)

        for ev in primary_items:
            if ev.get("evidence_id") in used_ids_set:
                return EVIDENCE_SUFFICIENCY_VERIFIED

        for ev in wikidata_items:
            if ev.get("evidence_id") in used_ids_set:
                return EVIDENCE_SUFFICIENCY_VERIFIED

        # Check if textual evidence was used
        for ev in wikipedia_items:
            if ev.get("evidence_id") in used_ids_set:
                return EVIDENCE_SUFFICIENCY_CORROBORATED

        # Evidence was retrieved but not sufficient for verdict
        return EVIDENCE_SUFFICIENCY_EVALUATED

    def _build_evidence_summary(
        self,
        evidence: Dict[str, Any],
        used_evidence_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Build a summary of evidence for frontend display (v1.5).

        Returns structured counts and used evidence items for each source type,
        enabling the frontend to display appropriate messaging and evidence chips.

        Args:
            evidence: Dict with wikidata, wikipedia, primary_document lists
            used_evidence_ids: List of evidence IDs that contributed to verdict

        Returns:
            Dict with total/used counts and used_items for each source type
        """
        used_ids_set = set(used_evidence_ids)

        summary = {
            "wikidata": {
                "total": 0,
                "used": 0,
                "used_items": []
            },
            "wikipedia": {
                "total": 0,
                "used": 0,
                "used_items": []
            },
            "primary_document": {
                "total": 0,
                "used": 0,
                "used_items": []
            }
        }

        # Process Wikidata evidence
        for ev in evidence.get("wikidata", []):
            summary["wikidata"]["total"] += 1
            if ev.get("evidence_id") in used_ids_set:
                summary["wikidata"]["used"] += 1
                summary["wikidata"]["used_items"].append({
                    "evidence_id": ev.get("evidence_id"),
                    "source": "WIKIDATA",
                    "property": ev.get("property", ""),
                    "value": str(ev.get("value", "")),
                    "snippet": (ev.get("snippet", "") or "")[:150],
                    "url": ev.get("url", "")
                })

        # Process Wikipedia evidence
        for ev in evidence.get("wikipedia", []):
            summary["wikipedia"]["total"] += 1
            if ev.get("evidence_id") in used_ids_set:
                summary["wikipedia"]["used"] += 1
                snippet = ev.get("snippet", "") or ev.get("sentence", "") or ""
                summary["wikipedia"]["used_items"].append({
                    "evidence_id": ev.get("evidence_id"),
                    "source": "WIKIPEDIA",
                    "snippet": snippet[:150],
                    "url": ev.get("url", "")
                })

        # Process Primary Document evidence
        for ev in evidence.get("primary_document", []):
            summary["primary_document"]["total"] += 1
            if ev.get("evidence_id") in used_ids_set:
                summary["primary_document"]["used"] += 1
                summary["primary_document"]["used_items"].append({
                    "evidence_id": ev.get("evidence_id"),
                    "source": "PRIMARY_DOCUMENT",
                    "authority": ev.get("authority", "SEC"),
                    "document_type": ev.get("document_type", "Filing"),
                    "filing_year": ev.get("filing_year", ""),
                    "snippet": (ev.get("snippet", "") or ev.get("value", "") or "")[:150]
                })

        return summary
