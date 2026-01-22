from typing import List

class PropertyMapper:
    """
    Maps linguistic predicates to Wikidata Property IDs.
    """
    def __init__(self):
        # Static mapping for research prototype
        self.PREDICATE_MAP = {
            "founded": ["P112", "P571"], # founded by, inception
            "born": ["P569", "P19"],     # date of birth, place of birth
            "died": ["P570", "P20"],     # date of death, place of death
            "spouse": ["P26"],
            "educated": ["P69"],         # educated at
            "ceo": ["P39", "P488"],      # position held, chairperson
            "served": ["P39"],           # position held
            "wrote": ["P50"],            # author
            "directed": ["P57"],         # director
            "invented": ["P61"],         # discoverer/inventor
            "located": ["P131", "P276"], # admin terr, location
            "is": ["P31", "P279"]        # instance of, subclass of
        }

    def get_potential_properties(self, predicate: str) -> List[str]:
        """
        Returns list of P-IDs for a given predicate lemma.
        """
        pred_lower = predicate.lower().strip()
        
        # Direct match
        if pred_lower in self.PREDICATE_MAP:
            return self.PREDICATE_MAP[pred_lower]
            
        # Partial match / Keyword search
        for key, pids in self.PREDICATE_MAP.items():
            if key in pred_lower:
                return pids
                
        return []
