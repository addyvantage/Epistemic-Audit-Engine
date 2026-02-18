import requests
import uuid
from typing import List, Dict, Any, Optional, Set
from config.core_config import EVIDENCE_MODALITY_STRUCTURED

class WikidataRetriever:
    """
    Tier 1 Evidence Source: Structured Knowledge Graph.
    Extracts (Subject, Predicate, Object) triples and converts them to 
    declarative sentences for verification.
    """
    
    def __init__(self):
        self.WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
        self.session = requests.Session()
        self.session.headers.update({
             "User-Agent": "EpistemicAuditEngine/1.0 (Research Project)"
        })
        self.entity_cache = {}
        self.place_containment_cache: Dict[str, Dict[str, List[str]]] = {}
        self.request_timeout_s = 5.0

    def retrieve_structured_evidence(self, q_id: str, p_ids: List[str], claim: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetches structured claims from Wikidata for a specific entity and property list.
        Returns formatted evidence items with "STRUCTURED" modality and alignment metadata.

        Args:
            q_id: Wikidata entity ID (e.g., "Q95" for Google)
            p_ids: List of property IDs to query (e.g., ["P571", "P159"])
            claim: The claim being verified, used for alignment computation

        Returns:
            List of evidence items with alignment metadata for verdict eligibility
        """
        if not q_id or not p_ids:
            return []

        # Prepare Props
        props = "|".join(p_ids)
        params = {
            "action": "wbgetentities",
            "ids": q_id,
            "props": "claims|labels",
            "languages": "en",
            "format": "json"
        }

        found_evidence = []
        try:
            entity = self._get_entity(q_id)

            claims_data = entity.get("claims", {})
            entity_label = entity.get("labels", {}).get("en", {}).get("value", "Entity")

            for pid in p_ids:
                if pid in claims_data:
                    stmts = claims_data[pid]
                    for stmt in stmts:
                        # Pass claim for alignment computation
                        evidence_item = self._process_statement(stmt, q_id, pid, entity_label, claim)
                        if evidence_item:
                            found_evidence.append(evidence_item)

            return found_evidence

        except Exception as e:
            # Silent fail for resilience
            return []

    def get_entity_property_qids(self, q_id: str, properties: List[str]) -> Set[str]:
        """
        Fetch QID-valued property targets for an entity.
        """
        if not q_id or not properties:
            return set()

        try:
            entity = self._get_entity(q_id)
            claims_data = entity.get("claims", {})
            values: Set[str] = set()
            for pid in properties:
                values.update(self._extract_entity_ids(claims_data.get(pid, [])))
            return values
        except Exception:
            return set()

    def get_place_containment(self, q_id: str, max_hops: int = 3) -> Dict[str, List[str]]:
        """
        Return place self/parents/country containment labels and qids.
        Includes:
        - self QID + label
        - P131 chain up to max_hops
        - P17 country at each hop
        """
        if not q_id or not q_id.startswith("Q"):
            return {"qids": [], "labels": []}

        if q_id in self.place_containment_cache:
            return self.place_containment_cache[q_id]

        visited: Set[str] = set()
        collected_qids: Set[str] = set()
        collected_labels: Set[str] = set()

        frontier: Set[str] = {q_id}
        hops = 0

        while frontier and hops <= max_hops:
            next_frontier: Set[str] = set()
            for node_qid in frontier:
                if node_qid in visited:
                    continue
                visited.add(node_qid)
                collected_qids.add(node_qid)

                entity = self._get_entity(node_qid)
                label = self._extract_label(entity, node_qid)
                if label:
                    collected_labels.add(label)

                claims_data = entity.get("claims", {})
                parents = self._extract_entity_ids(claims_data.get("P131", []))
                countries = self._extract_entity_ids(claims_data.get("P17", []))

                for parent_qid in parents + countries:
                    if parent_qid not in visited:
                        next_frontier.add(parent_qid)

            frontier = next_frontier
            hops += 1

        # Ensure labels are collected for all discovered qids.
        for discovered_qid in list(collected_qids):
            entity = self._get_entity(discovered_qid)
            label = self._extract_label(entity, discovered_qid)
            if label:
                collected_labels.add(label)

        payload = {
            "qids": sorted(collected_qids),
            "labels": sorted(collected_labels),
        }
        self.place_containment_cache[q_id] = payload
        return payload

    def _get_entity(self, q_id: str) -> Dict[str, Any]:
        if q_id in self.entity_cache:
            return self.entity_cache[q_id]

        params = {
            "action": "wbgetentities",
            "ids": q_id,
            "props": "claims|labels",
            "languages": "en",
            "format": "json"
        }
        resp = self.session.get(self.WIKIDATA_API_URL, params=params, timeout=self.request_timeout_s)
        data = resp.json()
        entity = data.get("entities", {}).get(q_id, {})
        self.entity_cache[q_id] = entity
        return entity

    def _extract_entity_ids(self, statements: List[Dict[str, Any]]) -> List[str]:
        values: List[str] = []
        for stmt in statements or []:
            mainsnak = stmt.get("mainsnak", {})
            if mainsnak.get("snaktype") != "value":
                continue
            datavalue = mainsnak.get("datavalue", {})
            val = datavalue.get("value")
            val_type = datavalue.get("type")
            if val_type == "wikibase-entityid" and isinstance(val, dict):
                qid = val.get("id")
                if qid and qid.startswith("Q"):
                    values.append(qid)
        return values

    def _extract_label(self, entity: Dict[str, Any], fallback_qid: str = "") -> str:
        return entity.get("labels", {}).get("en", {}).get("value", fallback_qid)

    def _process_statement(
        self, stmt: Dict[str, Any], q_id: str, pid: str, entity_label: str,
        claim: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Converts a Wikidata statement into a usable evidence item with alignment metadata.

        Args:
            stmt: Wikidata statement object
            q_id: Entity ID
            pid: Property ID
            entity_label: Human-readable entity name
            claim: The claim being verified (for alignment computation)

        Returns:
            Evidence item dict with alignment metadata, or None if invalid
        """
        mainsnak = stmt.get("mainsnak", {})
        if mainsnak.get("snaktype") != "value":
            return None

        datavalue = mainsnak.get("datavalue", {})
        val = datavalue.get("value")
        val_type = datavalue.get("type")

        parsed_value = self._parse_value(val, val_type)
        if not parsed_value:
            return None

        # Template Generation
        declarative_sentence = f"{entity_label} [{pid}] is {parsed_value}."

        # Compute alignment metadata for verdict eligibility
        alignment = self._compute_structured_alignment(
            entity_label=entity_label,
            property_id=pid,
            value=parsed_value,
            claim=claim
        )

        ev_item = {
            "source": "WIKIDATA",
            "modality": EVIDENCE_MODALITY_STRUCTURED,
            "entity_id": q_id,
            "property": pid,
            "value": parsed_value,
            "snippet": declarative_sentence,
            "textual_evidence": False,
            "url": f"https://www.wikidata.org/wiki/{q_id}#{pid}",
            "evidence_id": self._generate_evidence_id(q_id, pid, parsed_value),
            "alignment": alignment  # NEW: Alignment metadata for verdict eligibility
        }
        return ev_item

    def _compute_structured_alignment(
        self, entity_label: str, property_id: str, value: str, claim: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Compute alignment metadata for structured evidence.

        Epistemic Contract:
        -------------------
        - subject_match: True if entity_label matches claim subject
        - predicate_match: True by design (we queried for this property based on predicate)
        - object_match: True/False/None based on value comparison
        - temporal_match: For date values, True/False based on year comparison

        This alignment enables structured evidence to independently yield SUPPORTED
        verdicts when all relevant fields match, without requiring narrative confirmation.
        """
        import re

        if not claim:
            # Default alignment when no claim context
            return {
                "subject_match": True,
                "predicate_match": True,
                "object_match": None,
                "temporal_match": None
            }

        # Extract claim components
        claim_subject = claim.get("subject_entity", {}).get("canonical_name", "")
        if not claim_subject:
            claim_subject = claim.get("subject", "")
        claim_object = claim.get("object", "")
        claim_text = claim.get("claim_text", "")

        # Subject match: entity label matches claim subject
        s_match = False
        if entity_label and claim_subject:
            entity_lower = entity_label.lower()
            subject_lower = claim_subject.lower()
            s_match = (
                entity_lower in subject_lower or
                subject_lower in entity_lower or
                entity_lower == subject_lower
            )

        # Predicate match: True by design (property was selected based on predicate mapping)
        p_match = True

        # Object and temporal matching
        o_match = None
        t_match = None

        if value and claim_object:
            value_str = str(value).lower()
            claim_obj_lower = claim_object.lower()

            # Temporal comparison: Extract years and compare
            claim_years = re.findall(r'\b(\d{4})\b', claim_object)
            value_years = re.findall(r'\b(\d{4})\b', str(value))

            if claim_years and value_years:
                # Check if any claim year matches any evidence year
                t_match = any(cy in value_years for cy in claim_years)

            # Entity/string comparison for non-temporal values
            if not (claim_years or value_years):
                # Only do string match for non-date values
                if claim_obj_lower in value_str or value_str in claim_obj_lower:
                    o_match = True
                elif claim_obj_lower and value_str:
                    # No match
                    o_match = False

        return {
            "subject_match": s_match,
            "predicate_match": p_match,
            "object_match": o_match,
            "temporal_match": t_match
        }

    def _parse_value(self, val: Any, val_type: str) -> Optional[str]:
        if val_type == "string":
            return val
        elif val_type == "wikibase-entityid":
            return val.get("id")
        elif val_type == "time":
            # Extract year from ISO format +1999-01-01T00:00:00Z
            time_str = val.get("time", "")
            if time_str.startswith("+") or time_str.startswith("-"):
                 import re
                 m = re.search(r'([+\-]\d{4})', time_str)
                 if m: return m.group(1).lstrip("+")
            return time_str
        elif val_type == "quantity":
            return str(val.get("amount", ""))
        return str(val)

    def _generate_evidence_id(self, qid: str, pid: str, val: str) -> str:
        unique_str = f"WIKIDATA:{qid}:{pid}:{val}"
        return str(uuid.uuid5(uuid.NAMESPACE_OID, unique_str))
