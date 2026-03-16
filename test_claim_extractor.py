import unittest
import json
from claim_extractor import ClaimExtractor

class TestClaimExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = ClaimExtractor()

    def test_sentence_segmentation(self):
        text = "Steve Jobs founded Apple. He was strictly a genius!"
        result = self.extractor.extract(text)
        self.assertEqual(len(result["sentences"]), 2)
        self.assertEqual(result["sentences"][0]["text"], "Steve Jobs founded Apple.")
        self.assertEqual(result["sentences"][1]["text"], "He was strictly a genius!")

    def test_claim_decomposition_complex(self):
        text = "Steve Jobs founded Apple in 1976."
        result = self.extractor.extract(text)
        claims = result["claims"]
        
        texts = [c["claim_text"] for c in claims]
        # Core claim
        self.assertIn("Steve Jobs founded Apple", texts)
        
        # Temporal derived claim
        # Subject should be Apple (Object) -> "Apple was founded in 1976"
        self.assertIn("Apple was founded in 1976", texts)
        
        derived = next(c for c in claims if c["is_derived"])
        self.assertEqual(derived["claim_type"], "TEMPORAL")

    def test_validity_gate(self):
        # 1. "It is possible" -> Invalid predicate/subject combo
        text = "It is possible that Steve Jobs founded Apple."
        # Should extract "Steve Jobs founded Apple" but NOT "It is possible"
        result = self.extractor.extract(text)
        texts = [c["claim_text"] for c in result["claims"]]
        self.assertNotIn("It is possible", texts)
        self.assertIn("Steve Jobs founded Apple", texts)
        
        # 2. Pronoun subject validation
        text2 = "He was a genius."
        result2 = self.extractor.extract(text2)
        # Should still be empty because the pronoun claim is vague/evaluative.
        self.assertEqual(len(result2["claims"]), 0)

        text3 = "It was built in 1889 by Gustave Eiffel."
        result3 = self.extractor.extract(text3)
        texts3 = [c["claim_text"] for c in result3["claims"]]
        self.assertIn("It was built by Gustave Eiffel", texts3)
        self.assertIn("It was built in 1889", texts3)

    def test_subtree_reconstruction(self):
        text = "Steve Jobs did not invent the iPhone."
        result = self.extractor.extract(text)
        claims = result["claims"]
        # Expect "Steve Jobs did not invent the iPhone"
        self.assertTrue(any("did not invent" in c["claim_text"] for c in claims))
        self.assertTrue(any("did not invent" in c["predicate"] for c in claims))

    def test_epistemic_hardening(self):
        # 1. Reject purely evaluative attribute
        text_eval = "Apple is innovative."
        res_eval = self.extractor.extract(text_eval)
        # Should be empty claims because "innovative" is in EVALUATIVE_ADJECTIVES and no measurable data
        self.assertEqual(len(res_eval["claims"]), 0)
        
        # 2. Reject superlative evaluative without numbers
        text_super = "Apple is the most innovative company ever."
        res_super = self.extractor.extract(text_super)
        self.assertEqual(len(res_super["claims"]), 0)
        
        # 3. Accept factual attribute (numeric/measurable)
        text_fact = "Apple was the most valuable company in 2020."
        res_fact = self.extractor.extract(text_fact)
        # Claim should exist
        self.assertGreater(len(res_fact["claims"]), 0)
        claim = res_fact["claims"][0]
        self.assertEqual(claim["claim_type"], "FACTUAL_ATTRIBUTE")

    def test_temporal_passive_normalization(self):
        text = "Steve Jobs founded Apple in 1976."
        result = self.extractor.extract(text)
        claims = result["claims"]
        
        # Check derived temporal claim
        derived = next(c for c in claims if c["is_derived"])
        # Should be "Apple was founded in 1976"
        self.assertIn("Apple was founded", derived["claim_text"])
        self.assertEqual(derived["subject"], "Apple")

    def test_copular_location_claim_normalization(self):
        text = "Eiffel Tower is in Belgium."
        result = self.extractor.extract(text)
        self.assertGreater(len(result["claims"]), 0)

        claim = result["claims"][0]
        self.assertEqual(claim["claim_text"], "Eiffel Tower is in Belgium")
        self.assertEqual(claim["predicate"], "is in")
        self.assertEqual(claim["object"], "Belgium")
        self.assertEqual(claim["claim_type"], "RELATION")

    def test_prepositional_birth_claim_normalization(self):
        text = "Albert Einstein was born in Germany."
        result = self.extractor.extract(text)
        self.assertGreater(len(result["claims"]), 0)

        claim = result["claims"][0]
        self.assertIn("born in", claim["predicate"])
        self.assertEqual(claim["object"], "Germany")

    def test_coordinate_object_claims_are_split_cleanly(self):
        text = "Octopuses have three hearts and blue blood, which helps them survive in deep ocean environments."
        result = self.extractor.extract(text)
        texts = [c["claim_text"] for c in result["claims"]]
        self.assertEqual(texts, ["Octopuses have three hearts", "Octopuses have blue blood"])
        self.assertTrue(all(not text.endswith(",") for text in texts))

    def test_compound_sentence_claims_drop_dangling_conjunctions(self):
        text = "India is a country in Asia and its capital city is New Delhi."
        result = self.extractor.extract(text)
        texts = [c["claim_text"] for c in result["claims"]]
        self.assertIn("India is a country in Asia", texts)
        self.assertIn("its capital city is New Delhi", texts)
        self.assertTrue(all(not text.endswith(" and") for text in texts))

    def test_material_claim_normalization_keeps_material_object_clean(self):
        text = "The tower is made primarily of wood."
        result = self.extractor.extract(text)
        self.assertEqual(result["claims"][0]["predicate"], "is made primarily of")
        self.assertEqual(result["claims"][0]["object"], "wood")

    def test_determinism(self):
        text = "The earth rotates around the sun."
        res1 = self.extractor.extract(text)
        res2 = self.extractor.extract(text)
        import json
        self.assertEqual(json.dumps(res1, sort_keys=True), json.dumps(res2, sort_keys=True))

if __name__ == "__main__":
    unittest.main()
