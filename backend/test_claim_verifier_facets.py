import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.claim_verifier import ClaimVerifier


class _DummyDetector:
    def detect(self, claim, evidence):
        return []


class _DummyPropertyMapper:
    def get_potential_properties(self, predicate):
        return []


class _DummyWikidata:
    def __init__(self, containment_map=None):
        self._containment = containment_map or {}

    def get_place_containment(self, qid, max_hops=3):
        return self._containment.get(qid, {"qids": [qid], "labels": []})

    def get_entity_property_qids(self, qid, properties):
        return set()


class _DummyNLI:
    def classify(self, premise, hypothesis):
        return {"entailment": 0.0, "contradiction": 0.0, "neutral": 1.0}


class _DummyAlignmentScorer:
    def score_alignment(self, claim_text, evidence, nli_result):
        return {"signal": "NEUTRAL", "score": 0.0}


class _DummyAttributor:
    def attribute(self, alignment, evidence):
        return None


class LightweightClaimVerifier(ClaimVerifier):
    def __init__(self, containment_map=None):
        self.nli = _DummyNLI()
        self.detector = _DummyDetector()
        self.alignment_scorer = _DummyAlignmentScorer()
        self.attributor = _DummyAttributor()
        self.property_mapper = _DummyPropertyMapper()
        self.wikidata = _DummyWikidata(containment_map=containment_map)

        self.CANONICAL_PRED_MAP = {
            "founded": "P571",
            "born": "P569",
            "died": "P570",
            "released": "P577",
            "established": "P571",
            "incepted": "P571",
            "created": "P571",
        }
        self.CANONICAL_BIOGRAPHICAL_PROPS = {
            "P569",
            "P570",
            "P19",
            "P20",
            "P27",
            "P571",
            "P159",
        }
        self.CANONICAL_LOCATION_PRED_MAP = {
            "born in": "P19",
            "died in": "P20",
            "from": "P27",
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
        self.INCEPTION_KEYWORDS = ("founded", "inception", "established", "created")
        self.HQ_KEYWORDS = ("headquartered", "headquarters", "based in", "head office")
        self.NATIONALITY_KEYWORDS = ("nationality", "citizen of", "citizenship", "from")
        self.NONPROFIT_KEYWORDS = ("non-profit", "nonprofit", "not-for-profit", "not for profit")
        self.OWNERSHIP_KEYWORDS = ("acquired", "owned by", "subsidiary", "parent organization", "parent company")
        self.FACET_TO_PROPS = {
            "INCEPTION": {"P571"},
            "HQ": {"P159", "P276", "P131", "P17"},
            "NATIONALITY": {"P27"},
            "OWNERSHIP": {"P127", "P749", "P355", "P361"},
        }


def _base_claim(claim_text, predicate, obj, claim_type="RELATION"):
    return {
        "claim_id": "c1",
        "claim_text": claim_text,
        "predicate": predicate,
        "object": obj,
        "claim_type": claim_type,
        "epistemic_status": "ASSERTED",
        "epistemic_polarity": "ASSERTED",
        "subject_entity": {
            "resolution_status": "RESOLVED",
            "entity_id": "Q_OPENAI",
            "canonical_name": "OpenAI",
        },
        "object_entity": {
            "resolution_status": "RESOLVED_SOFT",
            "entity_id": "",
            "canonical_name": obj,
            "text": obj,
        },
        "evidence": {
            "primary_document": [],
            "wikidata": [],
            "wikipedia": [],
            "grokipedia": [],
        },
    }


class TestClaimVerifierFacetReliability(unittest.TestCase):
    def test_non_temporal_claim_is_not_supported_by_p571_only(self):
        verifier = LightweightClaimVerifier()
        claim = _base_claim(
            "OpenAI is a non-profit AI research organization headquartered in San Francisco.",
            "is",
            "a non-profit AI research organization headquartered in San Francisco",
            claim_type="RELATION",
        )
        claim["evidence"]["wikidata"] = [
            {
                "source": "WIKIDATA",
                "entity_id": "Q_OPENAI",
                "property": "P571",
                "value": "2015",
                "evidence_id": "wd-p571-2015",
                "alignment": {
                    "subject_match": True,
                    "predicate_match": True,
                    "object_match": None,
                    "temporal_match": True,
                },
            }
        ]

        out = verifier._verify_single_claim(claim)
        self.assertNotEqual(out["verification"]["verdict"], "SUPPORTED")
        self.assertIn(out["verification"]["verdict"], {"UNCERTAIN", "INSUFFICIENT_EVIDENCE", "PARTIALLY_SUPPORTED"})

    def test_temporal_founded_year_mismatch_refutes(self):
        verifier = LightweightClaimVerifier()
        claim = _base_claim("OpenAI was founded in 2017.", "founded", "2017", claim_type="TEMPORAL")
        claim["evidence"]["wikidata"] = [
            {
                "source": "WIKIDATA",
                "entity_id": "Q_OPENAI",
                "property": "P571",
                "value": "2015",
                "evidence_id": "wd-p571-2015",
                "alignment": {
                    "subject_match": True,
                    "predicate_match": True,
                    "object_match": False,
                    "temporal_match": False,
                },
            }
        ]

        out = verifier._verify_single_claim(claim)
        self.assertEqual(out["verification"]["verdict"], "REFUTED")
        self.assertIn("year", out["verification"]["reasoning"].lower())
        self.assertIn("wd-p571-2015", out["verification"]["contradicted_by"])

    def test_hq_claim_supported_with_location_containment(self):
        verifier = LightweightClaimVerifier(
            containment_map={
                "Q_SF": {
                    "qids": ["Q_SF", "Q_CA", "Q_US"],
                    "labels": ["San Francisco", "California", "United States"],
                }
            }
        )
        claim = _base_claim(
            "OpenAI is headquartered in San Francisco.",
            "headquartered in",
            "San Francisco",
            claim_type="RELATION",
        )
        claim["evidence"]["wikidata"] = [
            {
                "source": "WIKIDATA",
                "entity_id": "Q_OPENAI",
                "property": "P159",
                "value": "Q_SF",
                "evidence_id": "wd-p159-sf",
                "alignment": {
                    "subject_match": True,
                    "predicate_match": True,
                    "object_match": False,
                    "temporal_match": None,
                },
            }
        ]

        out = verifier._verify_single_claim(claim)
        self.assertEqual(out["verification"]["verdict"], "SUPPORTED")
        self.assertEqual(out["verification"]["facet_status"]["HQ"], "SUPPORTED")

    def test_evidence_summary_deduplicates_same_evidence_id(self):
        verifier = LightweightClaimVerifier()
        evidence = {
            "wikidata": [
                {"evidence_id": "dup-eid", "property": "P571", "value": "2015", "snippet": "OpenAI [P571] is 2015.", "url": "x"},
                {"evidence_id": "dup-eid", "property": "P571", "value": "2015", "snippet": "OpenAI [P571] is 2015.", "url": "x"},
            ],
            "wikipedia": [],
            "primary_document": [],
        }
        summary = verifier._build_evidence_summary(evidence, ["dup-eid"])
        self.assertEqual(summary["wikidata"]["used"], 1)
        self.assertEqual(len(summary["wikidata"]["used_items"]), 1)
        self.assertEqual(summary["wikidata"]["used_items"][0]["evidence_id"], "dup-eid")


if __name__ == "__main__":
    unittest.main()
