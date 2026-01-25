"""
Calibration Analysis Module

Computes:
- Expected Calibration Error (ECE)
- Confidence vs correctness bins
- Reliability diagrams data

Epistemic Rationale:
Calibration measures whether confidence scores are meaningful predictors
of correctness. A well-calibrated system with 80% confidence should be
correct 80% of the time. Poor calibration indicates the confidence scores
are not trustworthy.

ECE Formula:
ECE = Σ (|B_m| / n) * |acc(B_m) - conf(B_m)|

Where:
- B_m is the set of predictions in bin m
- acc(B_m) is the accuracy of predictions in bin m
- conf(B_m) is the average confidence of predictions in bin m
- n is the total number of predictions
"""

import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field


@dataclass
class CalibrationBin:
    """Single calibration bin."""
    bin_lower: float
    bin_upper: float
    bin_center: float
    count: int
    accuracy: float
    avg_confidence: float
    gap: float  # |accuracy - avg_confidence|

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CalibrationReport:
    """Complete calibration analysis report."""
    ece: float                           # Expected Calibration Error
    mce: float                           # Maximum Calibration Error
    overconfidence_rate: float           # % of bins where conf > accuracy
    underconfidence_rate: float          # % of bins where conf < accuracy
    bins: List[CalibrationBin]           # Detailed bin data
    total_samples: int
    reliability_data: Dict[str, List[float]]  # For plotting

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ece": self.ece,
            "mce": self.mce,
            "overconfidence_rate": self.overconfidence_rate,
            "underconfidence_rate": self.underconfidence_rate,
            "bins": [b.to_dict() for b in self.bins],
            "total_samples": self.total_samples,
            "reliability_data": self.reliability_data
        }


@dataclass
class VerdictCalibration:
    """Calibration analysis for a specific verdict type."""
    verdict: str
    calibration: CalibrationReport

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict,
            "calibration": self.calibration.to_dict()
        }


class CalibrationAnalyzer:
    """
    Calibration analysis for epistemic audit engine.

    Determinism: Uses fixed bin boundaries and deterministic aggregation.
    """

    # Fixed bin boundaries for reproducibility
    DEFAULT_N_BINS = 10

    def __init__(self, n_bins: int = DEFAULT_N_BINS):
        """
        Initialize analyzer with fixed number of bins.

        Args:
            n_bins: Number of calibration bins (default: 10)
        """
        self.n_bins = n_bins
        self.bin_boundaries = [i / n_bins for i in range(n_bins + 1)]

    def compute_calibration(
        self,
        predictions: List[Dict[str, Any]],
        gold_labels: Optional[List[str]] = None
    ) -> CalibrationReport:
        """
        Compute calibration metrics for a set of predictions.

        Args:
            predictions: List of dicts with 'confidence' and 'verdict' (and optionally 'correct')
            gold_labels: Optional list of gold verdicts for computing correctness

        Returns:
            CalibrationReport with ECE, MCE, and bin details
        """
        # Extract confidence-correctness pairs
        pairs = []

        for i, pred in enumerate(predictions):
            confidence = pred.get("confidence", 0.0)

            # Determine correctness
            if "correct" in pred:
                correct = pred["correct"]
            elif gold_labels and i < len(gold_labels):
                correct = pred.get("verdict") == gold_labels[i]
            else:
                # Assume verdict implies correctness for calibration
                # (SUPPORTED with high confidence should be correct)
                correct = pred.get("verdict") == "SUPPORTED"

            pairs.append((confidence, 1 if correct else 0))

        return self._compute_from_pairs(pairs)

    def compute_verdict_calibration(
        self,
        claims: List[Dict[str, Any]],
        gold_verdicts: Optional[List[str]] = None
    ) -> Dict[str, VerdictCalibration]:
        """
        Compute separate calibration for each verdict type.

        Args:
            claims: List of claims with verification data
            gold_verdicts: Optional list of gold verdicts

        Returns:
            Dict mapping verdict type to CalibrationReport
        """
        # Group by verdict
        by_verdict: Dict[str, List[Tuple[float, int]]] = {
            "SUPPORTED": [],
            "REFUTED": [],
            "INSUFFICIENT_EVIDENCE": [],
            "UNCERTAIN": []
        }

        for i, claim in enumerate(claims):
            verification = claim.get("verification", {})
            verdict = verification.get("verdict", "UNKNOWN")
            confidence = verification.get("confidence", 0.0)

            if verdict not in by_verdict:
                continue

            # Determine correctness
            if gold_verdicts and i < len(gold_verdicts):
                correct = verdict == gold_verdicts[i]
            else:
                # Without gold, assume all predictions are "intended"
                # This measures self-consistency rather than accuracy
                correct = True

            by_verdict[verdict].append((confidence, 1 if correct else 0))

        # Compute calibration for each verdict
        results = {}
        for verdict, pairs in by_verdict.items():
            if pairs:
                calibration = self._compute_from_pairs(pairs)
                results[verdict] = VerdictCalibration(verdict=verdict, calibration=calibration)

        return results

    def _compute_from_pairs(
        self,
        pairs: List[Tuple[float, int]]
    ) -> CalibrationReport:
        """
        Compute calibration from confidence-correctness pairs.

        Args:
            pairs: List of (confidence, correct) tuples

        Returns:
            CalibrationReport
        """
        if not pairs:
            return CalibrationReport(
                ece=0.0,
                mce=0.0,
                overconfidence_rate=0.0,
                underconfidence_rate=0.0,
                bins=[],
                total_samples=0,
                reliability_data={"confidence": [], "accuracy": [], "count": []}
            )

        n = len(pairs)
        bins_data: List[CalibrationBin] = []
        ece = 0.0
        mce = 0.0
        overconf_count = 0
        underconf_count = 0

        reliability_conf = []
        reliability_acc = []
        reliability_count = []

        for bin_idx in range(self.n_bins):
            lower = self.bin_boundaries[bin_idx]
            upper = self.bin_boundaries[bin_idx + 1]
            center = (lower + upper) / 2

            # Get predictions in this bin
            bin_pairs = [p for p in pairs if lower <= p[0] < upper or (bin_idx == self.n_bins - 1 and p[0] == 1.0)]

            if not bin_pairs:
                bins_data.append(CalibrationBin(
                    bin_lower=lower,
                    bin_upper=upper,
                    bin_center=center,
                    count=0,
                    accuracy=0.0,
                    avg_confidence=0.0,
                    gap=0.0
                ))
                continue

            count = len(bin_pairs)
            avg_conf = sum(p[0] for p in bin_pairs) / count
            accuracy = sum(p[1] for p in bin_pairs) / count
            gap = abs(accuracy - avg_conf)

            # Update ECE and MCE
            ece += (count / n) * gap
            mce = max(mce, gap)

            # Track over/underconfidence
            if avg_conf > accuracy:
                overconf_count += 1
            elif avg_conf < accuracy:
                underconf_count += 1

            bins_data.append(CalibrationBin(
                bin_lower=round(lower, 4),
                bin_upper=round(upper, 4),
                bin_center=round(center, 4),
                count=count,
                accuracy=round(accuracy, 4),
                avg_confidence=round(avg_conf, 4),
                gap=round(gap, 4)
            ))

            # For reliability diagram
            reliability_conf.append(round(avg_conf, 4))
            reliability_acc.append(round(accuracy, 4))
            reliability_count.append(count)

        # Compute rates
        non_empty_bins = sum(1 for b in bins_data if b.count > 0)
        overconf_rate = overconf_count / non_empty_bins if non_empty_bins > 0 else 0.0
        underconf_rate = underconf_count / non_empty_bins if non_empty_bins > 0 else 0.0

        return CalibrationReport(
            ece=round(ece, 4),
            mce=round(mce, 4),
            overconfidence_rate=round(overconf_rate, 4),
            underconfidence_rate=round(underconf_rate, 4),
            bins=bins_data,
            total_samples=n,
            reliability_data={
                "confidence": reliability_conf,
                "accuracy": reliability_acc,
                "count": reliability_count
            }
        )

    def compute_from_audit_results(
        self,
        audit_results: List[Dict[str, Any]],
        gold_data: Optional[List[Dict[str, Any]]] = None
    ) -> CalibrationReport:
        """
        Compute calibration from full audit pipeline results.

        Args:
            audit_results: List of pipeline output dicts (each with 'claims')
            gold_data: Optional list of dicts with gold verdicts

        Returns:
            CalibrationReport
        """
        pairs = []

        for result_idx, result in enumerate(audit_results):
            claims = result.get("claims", [])

            for claim_idx, claim in enumerate(claims):
                verification = claim.get("verification", {})
                confidence = verification.get("confidence", 0.0)
                verdict = verification.get("verdict", "UNKNOWN")

                # Determine correctness
                correct = False
                if gold_data and result_idx < len(gold_data):
                    gold_verdicts = gold_data[result_idx].get("gold_verdicts", [])
                    for gv in gold_verdicts:
                        if gv.get("claim_index") == claim_idx:
                            correct = verdict == gv.get("verdict")
                            break
                else:
                    # Without gold, use heuristic: high confidence SUPPORTED = correct
                    correct = verdict == "SUPPORTED" and confidence > 0.8

                pairs.append((confidence, 1 if correct else 0))

        return self._compute_from_pairs(pairs)


def analyze_calibration(
    claims: List[Dict[str, Any]],
    gold_verdicts: Optional[List[str]] = None,
    n_bins: int = 10
) -> Dict[str, Any]:
    """
    Convenience function for calibration analysis.

    Args:
        claims: List of claims with verification data
        gold_verdicts: Optional list of gold verdicts
        n_bins: Number of calibration bins

    Returns:
        Calibration report as dict
    """
    analyzer = CalibrationAnalyzer(n_bins=n_bins)

    # Overall calibration
    predictions = []
    for i, claim in enumerate(claims):
        verification = claim.get("verification", {})
        pred = {
            "confidence": verification.get("confidence", 0.0),
            "verdict": verification.get("verdict", "UNKNOWN")
        }
        if gold_verdicts and i < len(gold_verdicts):
            pred["correct"] = verification.get("verdict") == gold_verdicts[i]
        predictions.append(pred)

    overall = analyzer.compute_calibration(predictions, gold_verdicts)

    # Per-verdict calibration
    per_verdict = analyzer.compute_verdict_calibration(claims, gold_verdicts)

    return {
        "overall": overall.to_dict(),
        "per_verdict": {k: v.to_dict() for k, v in per_verdict.items()}
    }
