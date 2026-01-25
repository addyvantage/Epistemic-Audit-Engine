import json
import argparse
from typing import List, Dict, Any
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

class EvaluationPipeline:
    """
    Computes strict Classification Metrics (P/R/F1, Confusion Matrix) given Gold Labels.
    Does NOT interpret results.
    """
    
    def __init__(self):
        self.LABELS = ["SUPPORTED", "REFUTED", "UNCERTAIN", "INSUFFICIENT_EVIDENCE"]

    def evaluate_file(self, gold_file_path: str, predictions_file_path: str) -> Dict[str, Any]:
        """
        Loads gold labels and predictions (aligned by index or ID) and computes metrics.
        Assumes strictly aligned JSONL or JSON lists.
        """
        gold_data = self._load_data(gold_file_path)
        pred_data = self._load_data(predictions_file_path)
        
        return self.evaluate_predictions(pred_data, gold_data)

    def evaluate_predictions(self, predictions: List[Dict[str, Any]], gold: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Computes metrics comparing prediction verdicts to gold verdicts.
        Uses simplistic alignment (matching index or claim text exact match).
        For strict eval, we assume claims are 1:1 aligned or use Claim ID if available.
        """
        y_true = []
        y_pred = []
        
        limit = min(len(predictions), len(gold))
        for i in range(limit):
            p = predictions[i]
            g = gold[i]
            
            # Extract Verdicts
            p_v = p.get("verification", {}).get("verdict", "INSUFFICIENT_EVIDENCE")
            g_v = g.get("verification", {}).get("verdict", "INSUFFICIENT_EVIDENCE")
            
            y_true.append(g_v)
            y_pred.append(p_v)
            
        # Metrics
        precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='macro', zero_division=0)
        cm = confusion_matrix(y_true, y_pred, labels=self.LABELS)
        
        return {
            "metrics": {
                "precision_macro": float(precision),
                "recall_macro": float(recall),
                "f1_macro": float(f1)
            },
            "confusion_matrix": {
                "labels": self.LABELS,
                "matrix": cm.tolist()
            }
        }

    def _load_data(self, path: str) -> List[Dict[str, Any]]:
        with open(path, 'r') as f:
            if path.endswith(".jsonl"):
                return [json.loads(line) for line in f]
            return json.load(f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True, help="Path to gold labels JSON/JSONL")
    parser.add_argument("--pred", required=True, help="Path to predictions JSON/JSONL")
    args = parser.parse_args()
    
    pipeline = EvaluationPipeline()
    results = pipeline.evaluate_file(args.gold, args.pred)
    print(json.dumps(results, indent=2))
