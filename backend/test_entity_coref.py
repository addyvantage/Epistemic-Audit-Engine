import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.claim_extractor import ClaimExtractor
from core.entity_context import EntityContext
from core.entity_linker import EntityLinker


class TestEntityCoreference(unittest.TestCase):
    def setUp(self):
        self.extractor = ClaimExtractor()
        self.linker = EntityLinker()
        self.context = EntityContext()
        self.linker.set_context(self.context)

    def _link_document(self, text):
        extracted = self.extractor.extract(text)
        linked_claims = []
        for claim in extracted["claims"]:
            linked = self.linker.link_claims({"claims": [claim], "pipeline_config": {"performance": {}}})["claims"][0]
            linked_claims.append(linked)
            subj = linked.get("subject_entity", {})
            if subj.get("resolution_status") in {"RESOLVED", "RESOLVED_SOFT", "RESOLVED_COREF"}:
                self.context.register_entity(subj, claim.get("sentence_id", 0))
            obj = linked.get("object_entity", {})
            if obj.get("resolution_status") in {"RESOLVED", "RESOLVED_SOFT", "RESOLVED_COREF"}:
                self.context.register_entity(obj, claim.get("sentence_id", 0))
        return linked_claims

    def test_pronoun_and_nominal_references_resolve_to_prior_entity(self):
        claims = self._link_document(
            "The Eiffel Tower is a famous landmark in Europe. "
            "It was built in 1889 by Gustave Eiffel. "
            "The tower stands in the city of Brussels."
        )
        texts = [claim["claim_text"] for claim in claims]
        self.assertIn("Eiffel Tower was built by Gustave Eiffel", texts)
        self.assertIn("Eiffel Tower was built in 1889", texts)
        self.assertIn("Eiffel Tower stands in the city of Brussels", texts)

    def test_possessive_reference_rewrites_to_readable_claim(self):
        claims = self._link_document("India is a country in Asia and its capital city is New Delhi.")
        texts = [claim["claim_text"] for claim in claims]
        self.assertIn("capital city of India is New Delhi", texts)


if __name__ == "__main__":
    unittest.main()
