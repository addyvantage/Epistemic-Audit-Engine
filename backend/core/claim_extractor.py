import spacy
import uuid
import re
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ClaimExtractor:
    def __init__(self):
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise OSError("Model 'en_core_web_sm' not found. Please download it using `python3 -m spacy download en_core_web_sm`.")
            
        # Lists for filtering and scoring
        self.HEDGING_TERMS = {"may", "might", "possibly", "possible", "likely", "reportedly", "could", "perhaps", "seem", "suggest"}
        self.ABSOLUTISM_TERMS = {"definitely", "always", "never", "undeniably", "proven", "indisputable", "certainly"}
        self.TEMPORAL_SPECIFICITY_REGEX = r"\b(1\d{3}|20\d{2})\b|January|February|March|April|May|June|July|August|September|October|November|December"
        self.WEAK_MODALS = {"could", "might", "may", "seem", "appear"}
        self.STRONG_MODALS = {"was", "is", "are", "were", "will", "must", "definitely"}
        
        # Phase 1 Epistemic Hardening
        self.EVALUATIVE_ADJECTIVES = {
            "innovative", "influential", "important", "significant", 
            "famous", "notable", "successful", "great", "best", "worst", 
            "amazing", "terrible", "beautiful", "ugly", "fantastic"
        }
        
        # v1.3: Reported Speech & Hedging
        self.REPORTED_SPEECH_LEMMAS = {"state", "report", "claim", "argue", "suggest", "say", "announce", "warn", "predict", "speculate"}
        self.HEDGING_PHRASES = {"some sources", "according to", "it is claimed", "rumors", "allegedly"}
        self.LOCATION_PREPOSITIONS = {"in", "at", "on", "inside", "within", "near"}
        self.RELATION_PREPOSITIONS = {"in", "at", "on", "inside", "within", "near", "by", "during", "across", "from", "of"}
        self.ALLOWED_FACTUAL_PRONOUNS = {"it", "he", "she", "they", "this", "these", "those"}
        
    def extract(self, text: str) -> Dict[str, Any]:
        """
        Main entry point for claim extraction.
        """
        doc = self.nlp(text)
        sentences = self._segment_sentences(doc)
        
        all_claims = []
        excluded_sentences_count = 0
        
        for sent_obj in sentences:
            if not sent_obj["is_declarative"]:
                excluded_sentences_count += 1
                continue
                
            # Parse the sentence to extract claims
            claims = self._decompose_claims(sent_obj)
            all_claims.extend(claims)
            
        return {
            "sentences": [
                {k: v for k, v in s.items() if k != "spacy_sent"}
                for s in sentences
            ],
            "claims": all_claims,
            "metadata": {
                "total_sentences": len(sentences),
                "total_claims": len(all_claims),
                "excluded_sentences": excluded_sentences_count,
                "pipeline_phase": "PHASE_1_CLAIM_EXTRACTION",
                "version": "1.1.0"
            }
        }

    def _segment_sentences(self, doc) -> List[Dict[str, Any]]:
        """
        Splits text into atomic, ordered sentences and filters non-declarative ones.
        """
        sentences = []
        for i, sent in enumerate(doc.sents):
            formatted_sent = sent.text.strip()
            if not formatted_sent:
                continue
                
            is_decl = self._is_declarative(sent)
            
            sentences.append({
                "sentence_id": i,
                "text": formatted_sent,
                "start": sent.start_char,
                "end": sent.end_char,
                "is_declarative": is_decl,
                "spacy_sent": sent
            })
        return sentences

    def _is_declarative(self, sent) -> bool:
        """
        Filters out questions, instructions, opinions, etc.
        """
        text = sent.text.strip()
        text_lower = text.lower()
        
        # 1. Questions
        if text.endswith("?"):
            return False
            
        # 2. Instructions (Imperatives) - heuristic: starts with verb
        if sent.root.tag_ == "VB" and sent[0].pos_ == "VERB":
            return False
            
        # 3. Meta commentary
        meta_starts = ["This answer", "Here is", "I can explain", "Note that"]
        if any(text.startswith(m) for m in meta_starts):
            return False
            
        # 4. Opinions / Subjective (Refined)
        # We handle specific claim-level filtering in _is_valid_claim, but we can filter whole sentences here if they are purely opinion info.
        # However, "Apple is innovative and founded in 1976" has one valid claim.
        # So we should be less aggressive here and more aggressive in _is_valid_claim.
        # But for strictly subjective sentences:
        
        # If the sentence is SHORT and purely evaluative, drop it.
        # "Apple is innovative."
        # If it contains factual clauses (dates, numbers, extensive text), let it pass to decomposition.
        
        return True

    def _decompose_claims(self, sent_obj: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extracts claims from a single sentence using dependency parsing.
        """
        sent = sent_obj["spacy_sent"]
        claims = []
        
        verbs = [token for token in sent if token.pos_ == "VERB" or token.pos_ == "AUX"]
        
        extracted_tuples = []
        
        for verb in verbs:
            if verb.dep_ not in ("ROOT", "conj", "advcl", "ccomp", "xcomp"):
                 continue
            
            # v1.3: Prune Content Clauses of Reported Speech (Double-check parent)
            # If "sources state [that X is Y]", we drop X is Y if parent is reporting verb.
            if verb.dep_ == "ccomp" and verb.head.lemma_ in self.REPORTED_SPEECH_LEMMAS:
                 continue
            
            subj = None
            for child in verb.children:
                if child.dep_ in ("nsubj", "nsubjpass", "csubj", "csubjpass"):
                    subj = child
                    break
            
            if not subj and verb.dep_ == "conj":
                 head = verb.head
                 current = verb
                 while current.dep_ == "conj" and not subj:
                     current = current.head
                     for child in current.children:
                        if child.dep_ in ("nsubj", "nsubjpass", "csubj", "csubjpass"):
                            subj = child
                            break
            obj = None
            for child in verb.children:
                if child.dep_ in ("dobj", "attr", "acomp", "xcomp"):
                    obj = child
                    break
            if not obj:
                prep_candidates = []
                for child in verb.children:
                    if child.dep_ in ("prep", "agent"):
                        prep_candidates.append(child)
                prep_candidates.sort(
                    key=lambda token: (
                        0 if token.dep_ == "agent" or token.text.lower() == "by" else 1,
                        token.i,
                    )
                )
                for child in prep_candidates:
                    for grandchild in child.children:
                        if grandchild.dep_ == "pobj":
                            obj = child
                            break
                    if obj:
                        break
            
            if subj:
                extracted_tuples.append((subj, verb, obj))

        unique_claim_ids = set()
        
        for subj, verb, obj in extracted_tuples:
            
            if not self._is_valid_claim(subj, verb, obj, sent):
                continue
                
            # v1.3 Fragment Suppression: Drop if starts with 'that' or 'which'
            # Note: valid claim check is better place? But we have tokens here.
            # We will filter later after string formation.
            pass
            
            # --- ATOMIC TOKEN & SPAN CALCULATION (Fix 1) ---
            subj_tokens = self._get_atomic_tokens(subj)
            verb_tokens = self._get_verb_tokens(verb)
            obj_tokens = self._get_atomic_tokens(obj) if obj else []
            
            all_claim_tokens = subj_tokens + verb_tokens + obj_tokens
            if not all_claim_tokens: continue
            
            # Filter hedging from span (Fix 1: Clean Highlights)
            filtered_tokens = [t for t in all_claim_tokens if t.text.lower() not in self.HEDGING_TERMS]
            if not filtered_tokens: filtered_tokens = all_claim_tokens

            min_idx = min(t.idx for t in filtered_tokens)
            max_idx = max(t.idx + len(t) for t in filtered_tokens)
            
            subj_text = self._clean_component_text("".join([t.text_with_ws for t in subj_tokens]).strip())
            verb_text = self._clean_predicate_text("".join([t.text_with_ws for t in verb_tokens]).strip())
            obj_text = self._clean_component_text("".join([t.text_with_ws for t in obj_tokens]).strip())

            claim_type = "RELATION"
            temporal_predicates = ["launched", "founded", "born", "died"]
            if any(tp in verb_text.lower() for tp in temporal_predicates):
                claim_type = "TEMPORAL"
            elif verb.lemma_ == "be":
                if obj and obj.dep_ in ("attr", "acomp"):
                    claim_type = "FACTUAL_ATTRIBUTE"
                else:
                    claim_type = "EXISTENTIAL"

            predicate_text, object_text, claim_type = self._normalize_relation_components(
                verb=verb,
                verb_text=verb_text,
                obj=obj,
                obj_text=obj_text,
                claim_type=claim_type,
            )
            object_variants = self._split_coordinate_objects(obj) or [object_text]

            parent_claim_id: Optional[str] = None
            for object_variant in object_variants:
                object_variant = self._clean_component_text(object_variant)
                claim_entry = self._build_claim_entry(
                    subj_text=subj_text,
                    predicate_text=predicate_text,
                    object_text=object_variant,
                    claim_type=claim_type,
                    verb=verb,
                    sent=sent,
                    sent_obj=sent_obj,
                    min_idx=min_idx,
                    max_idx=max_idx,
                )
                if not claim_entry:
                    continue
                if claim_entry["claim_text"] in unique_claim_ids:
                    continue
                unique_claim_ids.add(claim_entry["claim_text"])
                if parent_claim_id is None:
                    parent_claim_id = claim_entry["claim_id"]
                claims.append(claim_entry)

            if parent_claim_id is None:
                parent_basis = f"{sent_obj['sentence_id']}::{subj_text}::{predicate_text}::{object_text}"
                parent_claim_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, parent_basis))

            temporal_claim = self._create_temporal_claim(subj, verb, obj, sent, parent_claim_id, sent_obj["sentence_id"], sent_obj["text"])
            if temporal_claim:
                 claims.append(temporal_claim)

            # v1.6: Compound Claim Decomposition - Location Claims
            # For "born in YEAR in PLACE" patterns, also extract the location claim
            location_claim = self._create_location_claim(subj, verb, obj, sent, parent_claim_id, sent_obj["sentence_id"], sent_obj["text"])
            if location_claim:
                 claims.append(location_claim)

            agent_claim = None
            if not obj or obj.dep_ != "agent":
                agent_claim = self._create_agent_claim(subj, verb, sent, parent_claim_id, sent_obj["sentence_id"], sent_obj["text"])
            if agent_claim:
                 claims.append(agent_claim)

        return claims

    def _build_claim_entry(
        self,
        subj_text: str,
        predicate_text: str,
        object_text: str,
        claim_type: str,
        verb,
        sent,
        sent_obj: Dict[str, Any],
        min_idx: int,
        max_idx: int,
    ) -> Optional[Dict[str, Any]]:
        predicate_text = self._clean_predicate_text(predicate_text)
        object_text = self._clean_component_text(object_text)
        claim_str = f"{subj_text} {predicate_text} {object_text}".strip()
        claim_str = self._clean_claim_text(claim_str)
        object_text = self._extract_object_from_claim_text(claim_str, subj_text, predicate_text)

        if not claim_str or not object_text:
            return None

        lower_claim = claim_str.lower()
        if lower_claim.startswith(("that ", "which ", "who ")):
            return None

        signals = self._compute_linguistic_signals(claim_str, sent.text)
        id_str = f"{sent_obj['sentence_id']}_{claim_str}"
        claim_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, id_str))

        epistemic_status = "ASSERTED"
        is_hedged = False
        if verb.lemma_ in self.REPORTED_SPEECH_LEMMAS:
            claim_type = "META_REPORTED"
            epistemic_status = "NON_ASSERTIVE"
            is_hedged = True

        if any(h in subj_text.lower() for h in ["some sources", "critics", "commentators", "rumors"]):
            claim_type = "META_REPORTED"
            epistemic_status = "NON_ASSERTIVE"
            is_hedged = True

        if self._is_contested(subj_text, verb.lemma_):
            epistemic_status = "CONTESTED"

        if is_hedged:
            epistemic_status = "NON_ASSERTIVE"

        return {
            "claim_id": claim_id,
            "sentence_id": sent_obj["sentence_id"],
            "claim_text": claim_str,
            "subject": subj_text,
            "predicate": predicate_text,
            "object": object_text,
            "confidence_linguistic": signals,
            "claim_type": claim_type,
            "epistemic_status": epistemic_status,
            "raw_sentence": sent_obj["text"],
            "is_derived": False,
            "start_char": min_idx,
            "end_char": max_idx,
            "sentence_index": sent_obj["sentence_id"],
            "span": {
                "start": min_idx,
                "end": max_idx,
                "sentence_index": sent_obj["sentence_id"]
            }
        }

    def _normalize_relation_components(
        self,
        verb,
        verb_text: str,
        obj,
        obj_text: str,
        claim_type: str,
    ) -> (str, str, str):
        """
        Normalize prepositional claims so the relation is preserved in the
        predicate while the object is reduced to the entity text.

        Example:
        - predicate "is", object "in Belgium" -> predicate "is in", object "Belgium"
        """
        predicate_text = verb_text
        object_text = obj_text
        normalized_type = claim_type

        if not obj or obj.dep_ not in {"prep", "agent"}:
            return predicate_text, object_text, normalized_type

        prep = obj.text.lower().strip()
        if prep not in self.RELATION_PREPOSITIONS:
            return predicate_text, object_text, normalized_type

        if prep == "of":
            material_match = re.match(r"^(?:(primarily|mostly|mainly)\s+)?of\s+(.+)$", obj_text, flags=re.IGNORECASE)
            if material_match:
                intensifier = (material_match.group(1) or "").strip()
                object_text = material_match.group(2).strip()
                predicate_text = f"{verb_text} {intensifier + ' ' if intensifier else ''}of".strip()
            else:
                object_text = re.sub(rf"^{re.escape(prep)}\s+", "", obj_text, flags=re.IGNORECASE).strip()
                predicate_text = f"{verb_text} {prep}".strip()
        else:
            object_text = re.sub(rf"^{re.escape(prep)}\s+", "", obj_text, flags=re.IGNORECASE).strip()
            predicate_text = f"{verb_text} {prep}".strip()
        if not object_text:
            return predicate_text, obj_text, normalized_type
        if normalized_type == "EXISTENTIAL":
            normalized_type = "RELATION"
        return predicate_text, object_text, normalized_type

    def _split_coordinate_objects(self, obj) -> List[str]:
        if not obj or obj.dep_ == "prep":
            return []

        conjuncts = [obj] + [child for child in obj.children if child.dep_ == "conj"]
        if len(conjuncts) <= 1:
            return []

        variants: List[str] = []
        for node in conjuncts:
            text = self._clean_component_text(self._get_coordinate_phrase(node))
            if text:
                variants.append(text)
        return variants

    def _get_coordinate_phrase(self, token) -> str:
        tokens = []
        pruned = {"cc", "conj", "punct", "relcl", "advcl", "parataxis"}

        def recurse(tok):
            tokens.append(tok)
            for child in tok.children:
                if child.dep_ not in pruned:
                    recurse(child)

        recurse(token)
        tokens.sort(key=lambda t: t.i)
        return "".join(t.text_with_ws for t in tokens).strip()

    def _is_contested(self, subj_text: str, verb_lemma: str) -> bool:
        """Fix 2: Detect explicitly contested claims"""
        critics = ["critics", "commentators", "experts", "regulators", "some"]
        contest_verbs = ["argue", "claim", "allege", "suggest", "contend"]
        
        subj_lower = subj_text.lower()
        if any(c in subj_lower for c in critics) and verb_lemma in contest_verbs:
            return True
        return False

    def _get_atomic_tokens(self, head_token) -> List[Any]:
        """
        Recursively retrieves tokens in subtree, pruning 'relcl', 'appos', 'advcl' 
        to ensure atomicity of the component.
        """
        tokens = []
        PRUNE_DEPS = {"relcl", "appos", "advcl", "parataxis"}
        
        def recurse(tok):
            tokens.append(tok)
            for child in tok.children:
                if child.dep_ not in PRUNE_DEPS:
                    recurse(child)
        
        recurse(head_token)
        tokens.sort(key=lambda t: t.i)
        return tokens

    def _get_verb_tokens(self, verb) -> List[Any]:
        """
        Get verb phrase tokens (aux, neg, verb).
        """
        parts = [verb]
        for child in verb.children:
            if child.dep_ in ("aux", "auxpass", "neg", "prt"):
                parts.append(child)
        parts.sort(key=lambda t: t.i)
        return parts

    def _is_valid_claim(self, subj, verb, obj, sent) -> bool:
        """
        Validates claim candidates to reject pronouns, modals, and non-falsifiable statements.
        Also implements strict evaluative filtering.
        """
        # 1. Subject Constraint: Allow concrete anaphora, reject vague expletive-only claims.
        if subj.pos_ == "PRON":
            pronoun = subj.text.lower().strip()
            if pronoun not in self.ALLOWED_FACTUAL_PRONOUNS:
                return False
            if verb.lemma_.lower() == "be" and obj:
                obj_text = self._get_full_subtree_text(obj).lower()
                has_concrete_anchor = any(
                    tok.ent_type_ in {"DATE", "TIME", "CARDINAL", "GPE", "LOC", "ORG", "PERSON"}
                    for tok in obj.subtree
                ) or bool(re.search(r"\b(1\d{3}|20\d{2}|\d+)\b", obj_text))
                if not has_concrete_anchor:
                    return False
            
        # 2. Predicate Constraint: No empty modals or scaffolding
        verb_lemma = verb.lemma_.lower()
        if verb_lemma in ["seem", "appear", "suggest", "indicate", "imply"]:
            return False
        
        # Check for "be possible", "be likely"
        if verb_lemma == "be" and obj:
            obj_text = obj.text.lower()
            if obj_text in ["possible", "likely", "unlikely", "probable", "certain", "clear"]:
                return False
        
        # 3. Evaluative / Attribute Constraints
        # Replaces and tightens the previous subjective filter
        if verb_lemma == "be" and obj:
             # Check if the object subtree contains evaluative adjectives
             obj_subtree_text = self._get_full_subtree_text(obj).lower()
             
             # If strictly evaluative without measurable data, reject.
             has_evaluative = any(adj in obj_subtree_text.split() for adj in self.EVALUATIVE_ADJECTIVES)
             
             if has_evaluative:
                 # Check for measurable anchors in the OBJECT phrase primarily, or sentence context
                 measurable = False
                 # Check entities in object subtree
                 for t in obj.subtree:
                     if t.ent_type_ in ("DATE", "MONEY", "QUANTITY", "PERCENT"):
                         measurable = True
                         break
                     if t.ent_type_ == "CARDINAL":
                         # Ignore "one" as in "one of the"
                         if t.text.lower() not in ("one", "1"):
                             measurable = True
                             break
                 
                 if not measurable:
                     # Check keywords
                     measurable_keywords = ["revenue", "market cap", "sales", "profit", "valuation", "worth", "ranked"]
                     if any(k in obj_subtree_text for k in measurable_keywords):
                         measurable = True
                     # Check for explicit rank pattern "rank 1", "top 10"
                     if "rank" in obj_subtree_text and any(c.isdigit() for c in obj_subtree_text):
                          measurable = True
                 
                 if not measurable:
                     has_entity_anchor = any(
                         t.ent_type_ in ("GPE", "LOC", "FAC", "ORG", "PERSON", "DATE")
                         for t in obj.subtree
                     )
                     if has_entity_anchor:
                         measurable = True
                 if not measurable:
                     return False

        return True

    def _clean_component_text(self, text: str) -> str:
        cleaned = re.sub(r"\s+", " ", (text or "")).strip(" \t\n\r,;:")
        while True:
            updated = re.sub(r"(?:\s|,)+(and|or|but)$", "", cleaned, flags=re.IGNORECASE).strip(" \t\n\r,;:")
            updated = re.sub(r"(?:\s|,)+(of|in|at|to|for|with|by|during|across|from)$", "", updated, flags=re.IGNORECASE).strip(" \t\n\r,;:")
            if updated == cleaned:
                break
            cleaned = updated
        return cleaned

    def _clean_predicate_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", (text or "")).strip(" \t\n\r,;:")

    def _clean_claim_text(self, text: str) -> str:
        return self._clean_component_text(re.sub(r"\s+", " ", text or "").strip())

    def _extract_object_from_claim_text(self, claim_text: str, subject_text: str, predicate_text: str) -> str:
        prefix = f"{subject_text} {predicate_text}".strip()
        if claim_text.startswith(prefix):
            return self._clean_component_text(claim_text[len(prefix):].strip())
        return ""

    def _get_verb_phrase(self, verb) -> str:
        """
        Reconstructs verb phrase including auxiliaries and negations.
        """
        parts = [verb]
        for child in verb.children:
            if child.dep_ in ("aux", "auxpass", "neg", "prt"):
                parts.append(child)
        parts.sort(key=lambda t: t.i)
        return " ".join(t.text for t in parts)

    def _get_full_subtree_text(self, token) -> str:
        """
        Enhanced subtree text extraction.
        """
        return "".join([t.text_with_ws for t in token.subtree]).strip()

    def _create_temporal_claim(self, subj, verb, obj, sent, parent_claim_id, sent_id, raw_sent) -> Optional[Dict[str, Any]]:
        """
        Extracts a derived temporal claim if a date is present in the verb's modifiers.
        Ensures passive voice if subject is switched.
        """
        target_date = None
        
        # 1. Look for explicit prep dates attached to verb
        for child in verb.children:
            if child.dep_ == "prep" and child.text.lower() in ["in", "on", "during", "at", "since"]:
                 for grand in child.children:
                     if grand.dep_ == "pobj":
                         if grand.ent_type_ == "DATE" or re.match(r"(1\d{3}|20\d{2})", grand.text):
                             target_date = self._get_full_subtree_text(child) # "in 1976"
                             break
            if child.dep_ in ["npadvmod", "tmod"] and (child.ent_type_ == "DATE" or re.match(r"(1\d{3}|20\d{2})", child.text)):
                target_date = self._get_full_subtree_text(child)
                break
        
        if not target_date:
            return None
            
        # Determine Subject
        new_subj_text = self._get_full_subtree_text(subj)
        subject_was_switched = False
        
        if obj and obj.dep_ not in ("prep", "agent"):
             # Switch to object
             new_subj_text = self._get_full_subtree_text(obj)
             subject_was_switched = True
        
        # Determine Predicate
        verb_phrase = self._get_verb_phrase(verb)
        
        # FIX 2: Passive Voice Normalization
        is_passive = any(c.dep_ == "auxpass" for c in verb.children)
        
        if subject_was_switched and not is_passive:
            if verb.tag_ == "VBD": 
                 # "founded" -> "was founded"
                 verb_phrase = "was " + verb_phrase
        
        claim_str = f"{new_subj_text} {verb_phrase} {target_date}".strip()
        
        id_str = f"{sent_id}_{claim_str}_derived"
        claim_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, id_str))
        
        return {
            "claim_id": claim_id,
            "sentence_id": sent_id,
            "claim_text": claim_str,
            "subject": new_subj_text,
            "predicate": verb_phrase,
            "object": target_date,
            "confidence_linguistic": {"hedging": 0.0, "absolutism": 0.0, "temporal_specificity": 1.0, "modal_strength": 1.0},
            "claim_type": "TEMPORAL",
            "raw_sentence": raw_sent,
            "is_derived": True,
            "source_claim_id": parent_claim_id,
            "highlight_type": "IMPLICIT_FACT", # Fix 3
            "start_char": sent.start_char,
            "end_char": sent.end_char,
            "sentence_index": sent_id,
            "span": {
                "start": sent.start_char,
                "end": sent.end_char,
                "sentence_index": sent_id
            }
        }

    def _create_agent_claim(self, subj, verb, sent, parent_claim_id, sent_id, raw_sent) -> Optional[Dict[str, Any]]:
        agent_phrase = None
        for child in verb.children:
            if child.dep_ == "agent" or child.text.lower() == "by":
                for grand in child.children:
                    if grand.dep_ == "pobj":
                        agent_phrase = self._get_full_subtree_text(child)
                        break
            if agent_phrase:
                break

        if not agent_phrase:
            return None

        subj_text = self._clean_component_text(self._get_full_subtree_text(subj))
        predicate = self._clean_predicate_text(f"{self._get_verb_phrase(verb)} by")
        obj_text = self._clean_component_text(re.sub(r"^by\s+", "", agent_phrase, flags=re.IGNORECASE))
        claim_text = self._clean_claim_text(f"{subj_text} {predicate} {obj_text}")
        if not subj_text or not obj_text:
            return None

        id_str = f"{sent_id}_{claim_text}_agent_derived"
        claim_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, id_str))
        return {
            "claim_id": claim_id,
            "sentence_id": sent_id,
            "claim_text": claim_text,
            "subject": subj_text,
            "predicate": predicate,
            "object": obj_text,
            "confidence_linguistic": {"hedging": 0.0, "absolutism": 0.0, "temporal_specificity": 0.0, "modal_strength": 1.0},
            "claim_type": "RELATION",
            "epistemic_status": "ASSERTED",
            "raw_sentence": raw_sent,
            "is_derived": True,
            "source_claim_id": parent_claim_id,
            "highlight_type": "IMPLICIT_FACT",
            "start_char": sent.start_char,
            "end_char": sent.end_char,
            "sentence_index": sent_id,
            "span": {
                "start": sent.start_char,
                "end": sent.end_char,
                "sentence_index": sent_id
            }
        }

    def _create_location_claim(self, subj, verb, obj, sent, parent_claim_id, sent_id, raw_sent) -> Optional[Dict[str, Any]]:
        """
        v1.6: Extracts a derived location claim from compound biographical statements.
        For "born in 1643 in England", this extracts "born in England".
        """
        # Only process biographical predicates that can have location components
        verb_lemma = verb.lemma_.lower()
        if verb_lemma not in ["bear", "die", "live", "reside", "base"]:
            return None

        target_location = None
        location_prep = None

        # Look for location prepositional phrases attached to verb
        # Need to find a prep phrase that contains a GPE/LOC entity, not a DATE
        for child in verb.children:
            if child.dep_ == "prep" and child.text.lower() == "in":
                for grand in child.children:
                    if grand.dep_ == "pobj":
                        # Check if this is a location, not a date
                        if grand.ent_type_ in ("GPE", "LOC", "FAC", "ORG"):
                            target_location = self._get_full_subtree_text(child)  # "in England"
                            location_prep = child
                            break
                        # Also check by content - if it doesn't look like a year/date
                        elif grand.ent_type_ not in ("DATE", "TIME", "CARDINAL"):
                            text = grand.text
                            # Heuristic: if it's not a 4-digit number, might be a location
                            if not re.match(r'^\d{4}$', text):
                                # Check if any child is a GPE/LOC
                                has_date_child = any(t.ent_type_ == "DATE" for t in grand.subtree)
                                if not has_date_child:
                                    target_location = self._get_full_subtree_text(child)
                                    location_prep = child
                                    break

        if not target_location:
            return None

        # Determine Subject
        new_subj_text = self._get_full_subtree_text(subj)

        # Determine Predicate (passive form for "born")
        verb_phrase = self._get_verb_phrase(verb)
        is_passive = any(c.dep_ == "auxpass" for c in verb.children)
        if verb_lemma == "bear" and not is_passive:
            verb_phrase = "was born"

        claim_str = f"{new_subj_text} {verb_phrase} {target_location}".strip()

        id_str = f"{sent_id}_{claim_str}_location_derived"
        claim_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, id_str))

        return {
            "claim_id": claim_id,
            "sentence_id": sent_id,
            "claim_text": claim_str,
            "subject": new_subj_text,
            "predicate": verb_phrase,
            "object": target_location.replace("in ", "").strip(),  # "England" not "in England"
            "confidence_linguistic": {"hedging": 0.0, "absolutism": 0.0, "temporal_specificity": 0.0, "modal_strength": 1.0},
            "claim_type": "RELATION",  # Location claims are RELATION type
            "epistemic_status": "ASSERTED",
            "raw_sentence": raw_sent,
            "is_derived": True,
            "source_claim_id": parent_claim_id,
            "highlight_type": "IMPLICIT_FACT",
            "start_char": sent.start_char,
            "end_char": sent.end_char,
            "sentence_index": sent_id,
            "span": {
                "start": sent.start_char,
                "end": sent.end_char,
                "sentence_index": sent_id
            }
        }

    def _get_subtree_text(self, token) -> str:
        """Helper to get the full text of a token's subtree (e.g. 'Steve Jobs' from 'Steve')"""
        return "".join([t.text_with_ws for t in token.subtree]).strip()

    def _compute_linguistic_signals(self, claim_text: str, sentence_text: str) -> Dict[str, float]:
        """
        Computes hedging, absolutism, specificity, and modal strength.
        """
        text_lower = sentence_text.lower()
        
        # 1. Hedging
        hedging_count = sum(1 for term in self.HEDGING_TERMS if term in text_lower.split())
        hedging_score = min(1.0, hedging_count * 0.5) # Simple heuristic mapping
        
        # 2. Absolutism
        absolutism_count = sum(1 for term in self.ABSOLUTISM_TERMS if term in text_lower.split())
        absolutism_score = min(1.0, absolutism_count * 0.5)
        
        # 3. Temporal Specificity
        # Check for dates
        matches = re.findall(self.TEMPORAL_SPECIFICITY_REGEX, sentence_text)
        temporal_score = 1.0 if matches else 0.0
        if "recently" in text_lower or "long ago" in text_lower:
            temporal_score = 0.2
            
        # 4. Modal Strength
        # Check verbs in the sentence
        modal_score = 1.0 # Default strong
        if any(w in text_lower.split() for w in self.WEAK_MODALS):
            modal_score = 0.5
        
        return {
            "hedging": hedging_score,
            "absolutism": absolutism_score,
            "temporal_specificity": temporal_score,
            "modal_strength": modal_score
        }

if __name__ == "__main__":
    extractor = ClaimExtractor()
    text = "Steve Jobs founded Apple in 1976 and later served as CEO. It is possible that he was a genius. Apple is one of the most innovative companies ever."
    result = extractor.extract(text)
    import json
    print(json.dumps(result, indent=2))
