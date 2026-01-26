import requests
import time
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from .entity_models import ResolvedEntity, EntityCandidate

if TYPE_CHECKING:
    from .entity_context import EntityContext

class EntityLinker:
    def __init__(self):
        self.WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
        self.WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "EpistemicAuditEngine/1.0 (Research Project)"
        })
        # Optional document-level entity context for coreference resolution
        self._context: Optional['EntityContext'] = None

    def set_context(self, context: 'EntityContext') -> None:
        """
        Set document-level entity context for coreference resolution.

        When set, the linker will attempt to resolve generic references
        (e.g., "the company") to previously mentioned named entities.

        Args:
            context: An EntityContext instance tracking document entities
        """
        self._context = context

    def clear_context(self) -> None:
        """Clear the entity context. Call between documents."""
        self._context = None

    def link_claims(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point. Takes Phase 1 output, returns Phase 2 output with groundings.
        """
        claims = input_data.get("claims", [])
        linked_claims = []
        
        for claim in claims:
            # Context for disambiguation
            context = (claim.get("predicate", "") + " " + claim.get("claim_text", "")).lower()
            
            # 1. Resolve Subject
            subj_res = self._resolve_entity(claim["subject"], "SUBJECT", context)
            
            # 2. Resolve Object
            obj_res = self._resolve_entity(claim["object"], "OBJECT", context) if claim["object"] else None
            
            # Construct output
            linked_claim = claim.copy()
            linked_claim["subject_entity"] = subj_res.to_dict()
            if obj_res:
                linked_claim["object_entity"] = obj_res.to_dict()
                
            linked_claims.append(linked_claim)
            
        return {"claims": linked_claims}

    def _resolve_entity(self, text: str, context_type: str, context: str = "") -> ResolvedEntity:
        """
        Resolves a single text mention to a canonical entity.

        Resolution Order:
        1. Direct Wikidata lookup (primary path)
        2. Coreference resolution via EntityContext (if available and direct fails)

        Args:
            text: The mention text to resolve
            context_type: "SUBJECT" or "OBJECT"
            context: Sentence context for disambiguation

        Returns:
            ResolvedEntity with resolution_status indicating outcome
        """
        if not text or len(text.strip()) < 2:
             return self._create_unresolved(text, "Text too short")

        # Check for coreference resolution first for generic references
        # This runs before expensive API calls if the text matches generic patterns
        if self._context and self._is_generic_reference(text):
            coref_result = self._context.resolve_generic(text, context_type)
            if coref_result:
                # Apply confidence discount for indirect resolution (10% reduction)
                discounted_confidence = coref_result.confidence * 0.9
                return ResolvedEntity(
                    text=text,
                    entity_id=coref_result.entity_id,
                    canonical_name=coref_result.canonical_name,
                    entity_type=coref_result.entity_type,
                    sources=coref_result.sources,
                    confidence=discounted_confidence,
                    resolution_status="RESOLVED_COREF",
                    source_status={"wikidata": "VERIFIED", "wikipedia": "VERIFIED" if coref_result.sources.get("wikipedia") else "UNVERIFIED"},
                    decision_reason=f"Coreference: {coref_result.decision_reason}"
                )

        query = self._clean_query(text)
        forced_disambiguation = False
        
        # Hard Disambiguation (Fix 1)
        ambiguous_orgs = {
            "apple": "Apple Inc.",
            "amazon": "Amazon.com",
            "meta": "Meta Platforms",
            "alphabet": "Alphabet Inc."
        }
        org_keywords = ["founded", "company", "ceo", "technology", "released", "product", "smartphone", "processor", "inc", "corp", "innovative"]
        
        t_low = text.lower().strip()
        if t_low in ambiguous_orgs:
            if any(k in context for k in org_keywords):
                query = ambiguous_orgs[t_low]
                forced_disambiguation = True

        # 1. Candidate Generation
        candidates = self._fetch_candidates_wikidata(query)
        
        if not candidates:
            return self._create_unresolved(text, "No candidates found")
            
        # 2. Scoring
        scored_candidates = self._score_candidates(candidates, query)
        
        # Log candidates
        candidates_log = [{"id": c.id, "label": c.label, "score": c.score} for c in scored_candidates[:5]]
        
        # 3. Selection (with Ambiguity Gap)
        best_candidate, decision_reason = self._select_canonical(scored_candidates)
        
        if best_candidate:
             ent_type = self._infer_type(best_candidate)
             
             # Guard: Forced Disambiguation Type Check
             if forced_disambiguation and ent_type != "ORG":
                  return self._create_unresolved(
                      text, 
                      "Forced org disambiguation failed; non-org candidate rejected", 
                      candidates_log
                  )

             requires_binding = (ent_type == "ROLE")
             
             # 4. Source Verification
             source_status, verified_sources = self._verify_sources(best_candidate)
             
             status = "RESOLVED"
             if decision_reason == "High confidence famous entity":
                 status = "RESOLVED_SOFT"
             if forced_disambiguation:
                 status = "RESOLVED_SOFT"
                 decision_reason = "Contextual Hard Disambiguation"

             # Create final object
             return ResolvedEntity(
                 text=text,
                 entity_id=best_candidate.id,
                 canonical_name=best_candidate.label,
                 entity_type=ent_type,
                 sources=verified_sources,
                 confidence=best_candidate.score,
                 resolution_status=status,
                 source_status=source_status,
                 requires_binding=requires_binding,
                 candidates_log=candidates_log,
                 decision_reason=decision_reason
             )
        else:
             # Direct resolution failed - try coreference as fallback
             if self._context and not self._is_generic_reference(text):
                 # For non-generic references that still failed (e.g., ambiguous names),
                 # we don't attempt coreference - it's genuinely unresolved
                 pass
             elif self._context and self._is_generic_reference(text):
                 # Already tried coreference at the start, so this is truly unresolved
                 pass

             return self._create_unresolved(text, decision_reason, candidates_log)

    def _clean_query(self, text: str) -> str:
        """
        Removes linguistic artifacts like 'as', 'the', etc.
        """
        t = text.strip()
        # Common prepositions/articles to strip from start
        prefixes = ["as ", "the ", "a ", "an "]
        for p in prefixes:
            if t.lower().startswith(p):
                t = t[len(p):].strip()
        return t

    def _fetch_candidates_wikidata(self, query: str) -> List[EntityCandidate]:
        """
        Queries Wikidata for candidates.
        """
        params = {
            "action": "wbsearchentities",
            "search": query,
            "language": "en",
            "format": "json",
            "limit": 5
        }
        try:
            resp = self.session.get(self.WIKIDATA_API_URL, params=params, timeout=5)
            data = resp.json()
            
            candidates = []
            for item in data.get("search", []):
                q_id = item.get("id")
                label = item.get("label", "")
                desc = item.get("description", "")
                aliases = item.get("aliases", [])
                
                # Basic source construction
                sources = {
                    "wikidata": q_id,
                    "wikipedia": item.get("url", f"https://www.wikidata.org/wiki/{q_id}"),
                    "grokipedia": f"https://grokipedia.com/page/{label.replace(' ', '_')}"
                }
                
                candidates.append(EntityCandidate(
                    id=q_id,
                    label=label,
                    description=desc,
                    aliases=aliases,
                    sources=sources
                ))
            return candidates
        except Exception as e:
            return []

    def _score_candidates(self, candidates: List[EntityCandidate], query: str) -> List[EntityCandidate]:
        """
        Scores candidates based on name match and description.
        """
        query_lower = query.lower()
        scored = []
        for cand in candidates:
            score = 0.5 # Base score for just appearing in search
            
            label_lower = cand.label.lower()
            
            # Exact match
            if label_lower == query_lower:
                score += 0.4
            # Alias match logic
            elif query_lower in [a.lower() for a in cand.aliases]:
                score += 0.3
            elif query_lower in label_lower:
                 score += 0.2
            
            # Penalty for disambiguation pages
            if "disambiguation page" in cand.description.lower():
                score -= 0.5
            
            # Boost for shorter labels
            if len(label_lower) == len(query_lower):
                score += 0.1
                
            cand.score = min(1.0, score)
            scored.append(cand)
            
        # Sort by score desc
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored

    def _select_canonical(self, candidates: List[EntityCandidate]) -> (Optional[EntityCandidate], str):
        if not candidates:
            return None, "No candidates"
        
        top = candidates[0]
        if top.score < 0.75:
            return None, "Low confidence"
            
        # Ambiguity Gap Check
        is_ambiguous = False
        if len(candidates) > 1:
            second = candidates[1]
            if (top.score - second.score) < 0.15:
                is_ambiguous = True
        
        # Override Ambiguity for Famous Entities (Wikipedia present)
        # Prompt: "If Top score >= 0.7 AND entity is globally famous... Auto-resolve"
        has_wiki = bool(top.sources.get("wikipedia"))
        
        if is_ambiguous:
            if top.score >= 0.7 and has_wiki:
                return top, "High confidence famous entity"
            else:
                return None, "Ambiguity gap too small"
                
        return top, "Verified dominant candidate"

    def _verify_sources(self, candidate: EntityCandidate) -> (Dict[str, str], Dict[str, str]):
        """
        Verifies Wikipedia sitelink presence and Grokipedia existence.
        Returns (source_status, verified_sources)
        """
        status = {"wikidata": "VERIFIED"} # We got it from Wikidata
        sources = candidate.sources.copy()
        
        # 1. Check Wikipedia Sitelink
        sitelink = self._get_wikipedia_sitelink(candidate.id)
        if sitelink:
            status["wikipedia"] = "VERIFIED"
            sources["wikipedia"] = sitelink
        else:
            status["wikipedia"] = "UNVERIFIED"
            # Keep the constructed URL if we want, or remove it?
            # Prompt says "If enwiki exists -> VERIFIED, Else -> UNVERIFIED".
            # Doesn't say to remove logic, but implies "Never assume".
            # So if unverified, maybe we should NOT emit the URL?
            # "Never assume Wikipedia URLs". So we should remove it if not verified.
            sources["wikipedia"] = ""

        # 2. Check Grokipedia
        grok_url = sources.get("grokipedia", "")
        if self._verify_grokipedia(grok_url):
            status["grokipedia"] = "VERIFIED"
        else:
            status["grokipedia"] = "ABSENT"
            sources.pop("grokipedia", None)
            
        return status, sources

    def _get_wikipedia_sitelink(self, q_id: str) -> str:
        """
        Queries Wikidata for 'enwiki' sitelink.
        """
        try:
            params = {
                "action": "wbgetentities",
                "ids": q_id,
                "props": "sitelinks",
                "sitefilter": "enwiki",
                "format": "json"
            }
            resp = self.session.get(self.WIKIDATA_API_URL, params=params, timeout=5)
            data = resp.json()
            entity = data.get("entities", {}).get(q_id, {})
            sitelinks = entity.get("sitelinks", {})
            if "enwiki" in sitelinks:
                title = sitelinks["enwiki"].get("title", "")
                import urllib.parse
                return f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
        except Exception:
            pass
        return ""

    def _verify_grokipedia(self, url: str) -> bool:
        """
        HEAD request to check existence.
        """
        if not url: return False
        try:
            # Short timeout, don't block
            resp = self.session.head(url, timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def _infer_type(self, candidate: EntityCandidate) -> str:
        desc = candidate.description.lower()
        if any(w in desc for w in ["person", "human", "actor", "entrepreneur", "founder"]):
            return "PERSON"
        if any(w in desc for w in ["company", "corporation", "organization", "agency"]):
            return "ORG"
        if any(w in desc for w in ["country", "city", "location", "place", "state", "region"]):
            return "LOC"
        if any(w in desc for w in ["officer", "position", "title", "profession", "role", "job"]):
            return "ROLE" # New type
        if any(w in desc for w in ["film", "book", "album", "song", "work", "game"]):
            return "WORK"
        if any(w in desc for w in ["event", "war", "battle", "election", "incident"]):
            return "EVENT"
        if any(w in desc for w in ["concept", "theory", "ideology", "principle"]):
            return "CONCEPT"
            
        return "UNKNOWN" # Changed from ENTITY

    def _is_generic_reference(self, text: str) -> bool:
        """
        Check if text matches known generic reference patterns.

        This is a fast pre-check to avoid expensive API calls for phrases
        like "the company" that are unlikely to have Wikidata entries.
        """
        text_lower = text.lower().strip()
        generic_patterns = [
            # ORG patterns
            "the company", "the firm", "the corporation", "the organization",
            "the business", "the enterprise", "the tech giant", "the startup",
            # PERSON patterns
            "the founder", "the ceo", "the executive", "the entrepreneur",
            # LOC patterns
            "the city", "the country", "the state", "the region",
        ]
        return text_lower in generic_patterns

    def _create_unresolved(self, text: str, reason: str, log: List = []) -> ResolvedEntity:
        """
        Create an unresolved entity result.

        Note: Before returning UNRESOLVED, the caller should have attempted
        coreference resolution if EntityContext is available.
        """
        return ResolvedEntity(
            text=text,
            entity_id="",
            canonical_name="",
            entity_type="UNKNOWN",
            sources={},
            confidence=0.0,
            resolution_status="UNRESOLVED",
            decision_reason=reason,
            candidates_log=log
        )
