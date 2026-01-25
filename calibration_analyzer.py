import numpy as np
from typing import List, Dict, Any

class CalibrationAnalyzer:
    """
    Computes calibration metrics (ECE) and reliability buckets.
    No plotting.
    """
    
    def __init__(self, n_bins: int = 10):
        self.n_bins = n_bins
        
    def analyze(self, predictions: List[Dict[str, Any]], gold_labels: List[str]) -> Dict[str, Any]:
        """
        Computes ECE for the SUPPORTED class (Positive Class).
        """
        confidences = []
        accuracies = []
        
        # Filter for alignment
        limit = min(len(predictions), len(gold_labels))
        
        for i in range(limit):
            p = predictions[i]
            verdict = p.get("verification", {}).get("verdict", "INSUFFICIENT_EVIDENCE")
            conf = p.get("verification", {}).get("confidence", 0.0)
            
            gold = gold_labels[i]
            
            # Map to Binary (SUPPORTED vs NOT)
            is_supported_pred = (verdict == "SUPPORTED")
            is_supported_gold = (gold == "SUPPORTED")
            
            # We only calibrate the Confidence of the Model relative to its correctness?
            # ECE typically measures: If model says score X, is it correct X% of the time?
            # If verdict is REFUTED with 0.9 confidence, it means 90% chance of REFUTED.
            # Here we simplify: Calibrate "Correctness" given Confidence.
            
            is_correct = (verdict == gold)
            confidences.append(conf)
            accuracies.append(1 if is_correct else 0)
            
        return self._compute_ece(confidences, accuracies)
            
    def _compute_ece(self, confidences: List[float], accuracies: List[int]) -> Dict[str, Any]:
        bin_boundaries = np.linspace(0, 1, self.n_bins + 1)
        
        ece = 0.0
        bins_data = []
        
        conf = np.array(confidences)
        acc = np.array(accuracies)
        
        total = len(conf)
        if total == 0:
            return {"ece": 0.0, "bins": []}
            
        for i in range(self.n_bins):
            # Bin Indices
            ix = np.where((conf > bin_boundaries[i]) & (conf <= bin_boundaries[i+1]))[0]
            
            n_bin = len(ix)
            if n_bin > 0:
                avg_conf = np.mean(conf[ix])
                avg_acc = np.mean(acc[ix])
                
                # ECE Component
                diff = np.abs(avg_acc - avg_conf)
                ece += (n_bin / total) * diff
                
                bins_data.append({
                    "lower": float(bin_boundaries[i]),
                    "upper": float(bin_boundaries[i+1]),
                    "count": int(n_bin),
                    "avg_confidence": float(avg_conf),
                    "avg_accuracy": float(avg_acc)
                })
            else:
                bins_data.append({
                    "lower": float(bin_boundaries[i]),
                    "upper": float(bin_boundaries[i+1]),
                    "count": 0,
                    "avg_confidence": 0.0,
                    "avg_accuracy": 0.0
                })
                
        return {
            "ece": float(ece),
            "bins": bins_data
        }
