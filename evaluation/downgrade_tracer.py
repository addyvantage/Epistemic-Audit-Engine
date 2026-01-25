"""
Downgrade Tracer for Epistemic Audit Engine

Provides detailed tracing of why claims fail to receive SUPPORTED verdicts.
Traces through all 5 pipeline phases to identify the exact failure point.

Usage:
    python -m evaluation.downgrade_tracer "Apple was founded in 1980."
"""

import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.pipeline.run_full_audit import AuditPipeline


@dataclass
class PhaseTrace:
    """Trace for a single pipeline phase."""
    phase: str
    status: str  # PASS, FAIL, WARN
    details: dict = field(default_factory=dict)
    blocking: bool = False  # Did this phase block SUPPORTED?


@dataclass
class ClaimTrace:
    """Complete trace for a single claim through all phases."""
    claim_text: str
    claim_type: str
    final_verdict: str
    confidence: float
    phases: list = field(default_factory=list)
    blocking_phase: Optional[str] = None
    hallucinations: list = field(default_factory=list)

    def to_dict(self):
        return {
            "claim_text": self.claim_text,
            "claim_type": self.claim_type,
            "final_verdict": self.final_verdict,
            "confidence": self.confidence,
            "blocking_phase": self.blocking_phase,
            "hallucinations": self.hallucinations,
            "phases": [
                {
                    "phase": p.phase,
                    "status": p.status,
                    "blocking": p.blocking,
                    "details": p.details
                }
                for p in self.phases
            ]
        }


def trace_claim(claim: dict) -> ClaimTrace:
    """
    Trace a claim through all pipeline phases.
    Identifies where and why the claim was downgraded from potential SUPPORTED.
    """
    claim_text = claim.get("claim_text", "")
    claim_type = claim.get("claim_type", "UNKNOWN")
    verification = claim.get("verification", {})
    final_verdict = verification.get("verdict", "UNKNOWN")
    confidence = verification.get("confidence", 0.0)

    trace = ClaimTrace(
        claim_text=claim_text,
        claim_type=claim_type,
        final_verdict=final_verdict,
        confidence=confidence,
        hallucinations=[h.get("hallucination_type") for h in claim.get("hallucinations", [])]
    )

    # Phase 1: Extraction
    extraction_trace = PhaseTrace(
        phase="1_extraction",
        status="PASS",  # If we have the claim, extraction succeeded
        details={
            "subject": claim.get("subject"),
            "predicate": claim.get("predicate"),
            "object": claim.get("object"),
            "epistemic_status": claim.get("epistemic_status"),
            "linguistic_confidence": claim.get("confidence_linguistic", {})
        }
    )
    trace.phases.append(extraction_trace)

    # Phase 2: Entity Linking
    subject_entity = claim.get("subject_entity", {})
    object_entity = claim.get("object_entity", {})

    subject_resolved = subject_entity.get("resolution_status") == "RESOLVED"
    subject_soft = subject_entity.get("resolution_status") == "RESOLVED_SOFT"

    linking_status = "PASS" if subject_resolved else ("WARN" if subject_soft else "FAIL")
    linking_blocking = not subject_resolved and not subject_soft

    linking_trace = PhaseTrace(
        phase="2_entity_linking",
        status=linking_status,
        blocking=linking_blocking,
        details={
            "subject": {
                "text": subject_entity.get("text"),
                "entity_id": subject_entity.get("entity_id"),
                "canonical_name": subject_entity.get("canonical_name"),
                "resolution_status": subject_entity.get("resolution_status"),
                "decision_reason": subject_entity.get("decision_reason"),
                "candidates_count": len(subject_entity.get("candidates_log", []))
            },
            "object": {
                "text": object_entity.get("text"),
                "entity_id": object_entity.get("entity_id"),
                "resolution_status": object_entity.get("resolution_status")
            }
        }
    )
    trace.phases.append(linking_trace)

    if linking_blocking:
        trace.blocking_phase = "2_entity_linking"

    # Phase 3: Evidence Retrieval
    evidence = claim.get("evidence", {})
    evidence_status = claim.get("evidence_status", {})

    wd_evidence = evidence.get("wikidata", [])
    wp_evidence = evidence.get("wikipedia", [])
    pd_evidence = evidence.get("primary_document", [])

    has_evidence = bool(wd_evidence or wp_evidence or pd_evidence)

    evidence_trace = PhaseTrace(
        phase="3_evidence_retrieval",
        status="PASS" if has_evidence else "FAIL",
        blocking=not has_evidence and not linking_blocking,
        details={
            "sources": {
                "wikidata": {
                    "status": evidence_status.get("wikidata", "ABSENT"),
                    "count": len(wd_evidence),
                    "properties": [e.get("property") for e in wd_evidence]
                },
                "wikipedia": {
                    "status": evidence_status.get("wikipedia", "ABSENT"),
                    "count": len(wp_evidence),
                    "scores": [e.get("score") for e in wp_evidence[:3]]  # Top 3
                },
                "primary_document": {
                    "status": evidence_status.get("primary_document", "ABSENT"),
                    "count": len(pd_evidence)
                }
            }
        }
    )
    trace.phases.append(evidence_trace)

    if not has_evidence and not trace.blocking_phase:
        trace.blocking_phase = "3_evidence_retrieval"

    # Phase 4: Verification
    used_evidence = verification.get("used_evidence_ids", [])
    contradicted_by = verification.get("contradicted_by", [])
    reasoning = verification.get("reasoning", "")

    # Check evidence eligibility
    eligible_evidence = []
    ineligible_reasons = []

    for source in ["wikidata", "wikipedia"]:
        for ev in evidence.get(source, []):
            alignment = ev.get("alignment", {})
            ev_id = ev.get("evidence_id", "?")

            subject_match = alignment.get("subject_match", False)
            predicate_match = alignment.get("predicate_match", False)
            object_match = alignment.get("object_match")
            temporal_match = alignment.get("temporal_match")

            if subject_match and predicate_match:
                if claim_type == "TEMPORAL" and temporal_match is None:
                    ineligible_reasons.append(f"{ev_id}: TEMPORAL claim but temporal_match=None")
                else:
                    eligible_evidence.append(ev_id)
            else:
                reasons = []
                if not subject_match:
                    reasons.append("subject_match=False")
                if not predicate_match:
                    reasons.append("predicate_match=False")
                ineligible_reasons.append(f"{ev_id}: {', '.join(reasons)}")

    verification_status = "PASS" if final_verdict == "SUPPORTED" else "FAIL"
    verification_blocking = final_verdict != "SUPPORTED" and not trace.blocking_phase

    verification_trace = PhaseTrace(
        phase="4_verification",
        status=verification_status,
        blocking=verification_blocking and final_verdict in ["REFUTED", "INSUFFICIENT_EVIDENCE"],
        details={
            "verdict": final_verdict,
            "confidence": confidence,
            "used_evidence_ids": used_evidence,
            "contradicted_by": contradicted_by,
            "reasoning": reasoning,
            "nli_summary": verification.get("nli_summary", {}),
            "evidence_eligibility": {
                "eligible": eligible_evidence,
                "ineligible": ineligible_reasons
            }
        }
    )
    trace.phases.append(verification_trace)

    if verification_trace.blocking and not trace.blocking_phase:
        trace.blocking_phase = "4_verification"

    # Phase 5: Hallucination Detection
    hallucinations = claim.get("hallucinations", [])
    critical_halluc = [h for h in hallucinations if h.get("severity") == "CRITICAL"]
    non_critical_halluc = [h for h in hallucinations if h.get("severity") != "CRITICAL"]

    halluc_status = "FAIL" if critical_halluc else ("WARN" if non_critical_halluc else "PASS")
    halluc_blocking = (
        (bool(critical_halluc) or bool(non_critical_halluc))
        and final_verdict in ["REFUTED", "UNCERTAIN"]
        and not trace.blocking_phase
    )

    halluc_trace = PhaseTrace(
        phase="5_hallucination_detection",
        status=halluc_status,
        blocking=halluc_blocking,
        details={
            "critical": [
                {
                    "type": h.get("hallucination_type"),
                    "reason": h.get("reason"),
                    "score": h.get("score")
                }
                for h in critical_halluc
            ],
            "non_critical": [
                {
                    "type": h.get("hallucination_type"),
                    "reason": h.get("reason"),
                    "score": h.get("score")
                }
                for h in non_critical_halluc
            ]
        }
    )
    trace.phases.append(halluc_trace)

    if halluc_blocking:
        trace.blocking_phase = "5_hallucination_detection"

    return trace


def trace_text(text: str) -> list:
    """Trace all claims extracted from input text."""
    pipeline = AuditPipeline()
    result = pipeline.run(text)

    traces = []
    for claim in result.get("claims", []):
        traces.append(trace_claim(claim))

    return traces


def print_trace(trace: ClaimTrace, verbose: bool = False):
    """Print a claim trace in human-readable format."""
    print(f"\n{'='*60}")
    print(f"CLAIM: {trace.claim_text}")
    print(f"TYPE:  {trace.claim_type}")
    print(f"{'='*60}")

    for pt in trace.phases:
        status_icon = {"PASS": "[OK]", "FAIL": "[X]", "WARN": "[!]"}.get(pt.status, "[?]")
        blocking = " <-- BLOCKING" if pt.blocking else ""
        print(f"\n{status_icon} {pt.phase}{blocking}")

        if verbose or pt.status != "PASS":
            for key, value in pt.details.items():
                if isinstance(value, dict):
                    print(f"    {key}:")
                    for k2, v2 in value.items():
                        print(f"      {k2}: {v2}")
                else:
                    print(f"    {key}: {value}")

    print(f"\n{'─'*60}")
    print(f"VERDICT:        {trace.final_verdict}")
    print(f"CONFIDENCE:     {trace.confidence:.2f}")
    print(f"BLOCKING PHASE: {trace.blocking_phase or 'None (SUPPORTED)'}")

    if trace.hallucinations:
        print(f"HALLUCINATIONS: {trace.hallucinations}")

    print()


def main():
    parser = argparse.ArgumentParser(description="Trace claim downgrade reasons")
    parser.add_argument("text", type=str, help="Input text to analyze")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all phase details")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    traces = trace_text(args.text)

    if args.json:
        output = [t.to_dict() for t in traces]
        print(json.dumps(output, indent=2))
    else:
        for trace in traces:
            print_trace(trace, args.verbose)


if __name__ == "__main__":
    main()
