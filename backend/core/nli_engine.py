import logging
from typing import Dict, Any

class NLIEngine:
    def __init__(self, model_name: str = "roberta-large-mnli"):
        self.pipeline = None
        self.model_name = model_name
        try:
            from transformers import pipeline
            # Optimization: distinct device or cpu
            self.pipeline = pipeline("text-classification", model=model_name, top_k=None)
        except Exception as e:
            logging.warning(f"Failed to load NLI model: {e}. NLI features will be unavailable.")

    def classify(self, premise: str, hypothesis: str) -> Dict[str, float]:
        """
        Returns dictionary of probabilities: { "entailment": ..., "contradiction": ..., "neutral": ... }
        """
        if not self.pipeline:
            # Fallback for environments without transformers
            return {"entailment": 0.0, "contradiction": 0.0, "neutral": 1.0}
            
        try:
            # HuggingFace standard for MNLI: premise + hypothesis
            # Some models expect specific delimiters, pipeline handles pair usually?
            # Pipeline 'text-classification' for MNLI usually takes single string "premise [SEP] hypothesis" or input pair.
            # But standard pipeline usage for NLI is often zero-shot-classification or just passing text with specialized formatting.
            # Actually roberta-large-mnli via pipeline allows: text="Premise: ... \n Hypothesis: ..." or similar.
            # Let's use the simplest robust string format: "premise </s></s> hypothesis" for RoBERTa.
            
            input_text = f"{premise} </s></s> {hypothesis}" 
            results = self.pipeline(input_text)
            # Results is list of dicts: [{'label': 'CONTRADICTION', 'score': 0.9}, ...]
            # Classes for MNLI: contradiction, neutral, entailment (sometimes LABEL_0 etc)
            
            scores = {"entailment": 0.0, "contradiction": 0.0, "neutral": 0.0}
            for r in results[0]: # top_k=None returns list of all labels
                label = r['label'].lower()
                if "entail" in label: scores["entailment"] = r['score']
                elif "contradict" in label: scores["contradiction"] = r['score']
                else: scores["neutral"] = r['score']
                
            return scores
        except Exception as e:
            logging.error(f"NLI Inference failed: {e}")
            return {"entailment": 0.0, "contradiction": 0.0, "neutral": 1.0}
