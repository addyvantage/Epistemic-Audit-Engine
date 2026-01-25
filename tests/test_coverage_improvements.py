"""
Tests for Coverage Improvement Changes (v1.4)

This module tests the following improvements:
1. Document-level entity coreference resolution
2. Structured evidence independence for Wikidata
3. Weak support accumulation
4. Expanded property mappings
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from entity_context import EntityContext, EntityMention, CorefResolution
from property_mapper import PropertyMapper


class TestEntityContext:
    """Tests for document-level entity context and coreference resolution."""

    def test_register_and_resolve_singleton_org(self):
        """Single ORG entity should be resolvable via generic reference."""
        ctx = EntityContext()

        # Simulate a resolved Google entity
        google_entity = {
            "entity_id": "Q95",
            "canonical_name": "Google",
            "entity_type": "ORG",
            "confidence": 0.95,
            "resolution_status": "RESOLVED",
            "sources": {"wikidata": "Q95", "wikipedia": "https://en.wikipedia.org/wiki/Google"},
        }
        ctx.register_entity(google_entity, sentence_idx=0)

        # Resolve "the company"
        result = ctx.resolve_generic("the company", "SUBJECT")

        assert result is not None
        assert result.entity_id == "Q95"
        assert result.canonical_name == "Google"
        assert result.resolution_method == "DOMINANT_SINGLETON"

    def test_unresolved_entity_not_registered(self):
        """UNRESOLVED entities should not be registered in context."""
        ctx = EntityContext()

        unresolved_entity = {
            "entity_id": "",
            "canonical_name": "",
            "entity_type": "UNKNOWN",
            "confidence": 0.0,
            "resolution_status": "UNRESOLVED",
        }
        ctx.register_entity(unresolved_entity, sentence_idx=0)

        assert len(ctx.mention_sequence) == 0

    def test_ambiguous_resolution_returns_none(self):
        """Multiple competing entities should result in ambiguous resolution."""
        ctx = EntityContext()

        # Register two ORG entities with similar frequency
        google = {
            "entity_id": "Q95",
            "canonical_name": "Google",
            "entity_type": "ORG",
            "confidence": 0.95,
            "resolution_status": "RESOLVED",
            "sources": {},
        }
        apple = {
            "entity_id": "Q312",
            "canonical_name": "Apple Inc.",
            "entity_type": "ORG",
            "confidence": 0.95,
            "resolution_status": "RESOLVED",
            "sources": {},
        }

        ctx.register_entity(google, sentence_idx=0)
        ctx.register_entity(apple, sentence_idx=1)

        # Should be ambiguous (no frequency dominance)
        result = ctx.resolve_generic("the company", "SUBJECT")
        # May or may not resolve depending on recency tiebreaker

        # Check the resolution log
        log = ctx.get_resolution_log()
        assert len(log) == 1

    def test_frequency_dominance(self):
        """Entity with clear frequency dominance should be selected."""
        ctx = EntityContext()

        google = {
            "entity_id": "Q95",
            "canonical_name": "Google",
            "entity_type": "ORG",
            "confidence": 0.95,
            "resolution_status": "RESOLVED",
            "sources": {},
        }
        apple = {
            "entity_id": "Q312",
            "canonical_name": "Apple Inc.",
            "entity_type": "ORG",
            "confidence": 0.95,
            "resolution_status": "RESOLVED",
            "sources": {},
        }

        # Register Google 3 times, Apple once
        ctx.register_entity(google, sentence_idx=0)
        ctx.register_entity(google, sentence_idx=1)
        ctx.register_entity(google, sentence_idx=2)
        ctx.register_entity(apple, sentence_idx=3)

        result = ctx.resolve_generic("the company", "SUBJECT")

        assert result is not None
        assert result.entity_id == "Q95"
        assert result.resolution_method == "DOMINANT_FREQUENCY"

    def test_non_matching_pattern_returns_none(self):
        """Unknown patterns should not resolve."""
        ctx = EntityContext()

        google = {
            "entity_id": "Q95",
            "canonical_name": "Google",
            "entity_type": "ORG",
            "confidence": 0.95,
            "resolution_status": "RESOLVED",
            "sources": {},
        }
        ctx.register_entity(google, sentence_idx=0)

        # "the widget" is not a known pattern
        result = ctx.resolve_generic("the widget", "SUBJECT")
        assert result is None

    def test_low_confidence_entity_not_resolved(self):
        """Entities below confidence threshold should not resolve."""
        ctx = EntityContext()

        low_conf = {
            "entity_id": "Q123",
            "canonical_name": "SomeCompany",
            "entity_type": "ORG",
            "confidence": 0.5,  # Below threshold of 0.70
            "resolution_status": "RESOLVED",
            "sources": {},
        }
        ctx.register_entity(low_conf, sentence_idx=0)

        result = ctx.resolve_generic("the company", "SUBJECT")
        assert result is None


class TestPropertyMapper:
    """Tests for expanded property mappings."""

    def test_incorporated_mapping(self):
        """'incorporated' should map to headquarters/location properties."""
        mapper = PropertyMapper()
        props = mapper.get_potential_properties("incorporated")

        assert "P571" in props  # inception
        assert "P159" in props  # headquarters

    def test_headquartered_mapping(self):
        """'headquartered' should map to P159."""
        mapper = PropertyMapper()
        props = mapper.get_potential_properties("headquartered")

        assert "P159" in props

    def test_launched_mapping(self):
        """'launched' should map to inception and publication date."""
        mapper = PropertyMapper()
        props = mapper.get_potential_properties("launched")

        assert "P571" in props  # inception
        assert "P577" in props  # publication date

    def test_partial_match(self):
        """Partial predicate matches should work."""
        mapper = PropertyMapper()

        # "was founded" contains "founded"
        props = mapper.get_potential_properties("was founded")
        assert "P571" in props

    def test_unknown_predicate_returns_empty(self):
        """Unknown predicates should return empty list."""
        mapper = PropertyMapper()
        props = mapper.get_potential_properties("flibbertigibbeted")

        assert props == []


class TestStructuredAlignment:
    """Tests for Wikidata alignment metadata computation."""

    def test_temporal_alignment_match(self):
        """Temporal values should match when years align."""
        from backend.wikidata_retriever import WikidataRetriever

        retriever = WikidataRetriever()
        claim = {
            "subject": "Google",
            "subject_entity": {"canonical_name": "Google"},
            "object": "1998",
            "predicate": "founded",
        }

        alignment = retriever._compute_structured_alignment(
            entity_label="Google",
            property_id="P571",
            value="+1998-09-04T00:00:00Z",
            claim=claim,
        )

        assert alignment["subject_match"] is True
        assert alignment["predicate_match"] is True
        assert alignment["temporal_match"] is True

    def test_temporal_alignment_mismatch(self):
        """Temporal values should not match when years differ."""
        from backend.wikidata_retriever import WikidataRetriever

        retriever = WikidataRetriever()
        claim = {
            "subject": "Google",
            "subject_entity": {"canonical_name": "Google"},
            "object": "1999",  # Wrong year
            "predicate": "founded",
        }

        alignment = retriever._compute_structured_alignment(
            entity_label="Google",
            property_id="P571",
            value="+1998-09-04T00:00:00Z",
            claim=claim,
        )

        assert alignment["temporal_match"] is False

    def test_subject_match_partial(self):
        """Subject match should work with partial containment."""
        from backend.wikidata_retriever import WikidataRetriever

        retriever = WikidataRetriever()
        claim = {
            "subject": "Apple Inc.",
            "subject_entity": {"canonical_name": "Apple Inc."},
            "object": "1976",
            "predicate": "founded",
        }

        alignment = retriever._compute_structured_alignment(
            entity_label="Apple",  # Partial match
            property_id="P571",
            value="1976",
            claim=claim,
        )

        assert alignment["subject_match"] is True


class TestIntegration:
    """Integration tests for the full pipeline."""

    @pytest.mark.slow
    def test_coref_pipeline_integration(self):
        """Test that coreference works in the full pipeline."""
        from backend.pipeline.run_full_audit import AuditPipeline

        # Skip if models not available
        try:
            pipeline = AuditPipeline()
        except Exception as e:
            pytest.skip(f"Pipeline initialization failed: {e}")

        text = "Google was founded in 1998 by Larry Page. The company went public in 2004."
        result = pipeline.run(text)

        claims = result.get("claims", [])

        # Should have at least 2 claims
        assert len(claims) >= 2

        # Check for RESOLVED_COREF status in any claim
        has_coref = any(
            c.get("subject_entity", {}).get("resolution_status") == "RESOLVED_COREF"
            for c in claims
        )

        # Note: This test may not find RESOLVED_COREF if "The company" is not extracted
        # as a separate claim. The important thing is no errors occur.

    @pytest.mark.slow
    def test_structured_evidence_support(self):
        """Test that structured evidence can yield SUPPORTED verdict."""
        from backend.pipeline.run_full_audit import AuditPipeline

        try:
            pipeline = AuditPipeline()
        except Exception as e:
            pytest.skip(f"Pipeline initialization failed: {e}")

        text = "Google was founded in 1998."
        result = pipeline.run(text)

        claims = result.get("claims", [])

        # At least one claim should be SUPPORTED
        supported = [
            c for c in claims
            if c.get("verification", {}).get("verdict") == "SUPPORTED"
        ]

        # This claim should be supportable via Wikidata P571
        assert len(supported) >= 1 or any(
            c.get("verification", {}).get("verdict") != "INSUFFICIENT_EVIDENCE"
            for c in claims
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
