from typing import List

class PropertyMapper:
    """
    Maps linguistic predicates to Wikidata Property IDs.

    Property Selection Criteria:
    ----------------------------
    Properties are selected based on:
    1. Direct semantic match to the predicate
    2. Common alternative representations in Wikidata
    3. Inverse properties when applicable

    Epistemic Note:
    ---------------
    Multiple properties per predicate increase recall at the cost of precision.
    The verification layer applies alignment checks to filter false matches.
    """
    def __init__(self):
        # Static mapping for research prototype
        # Expanded in v1.4 to improve coverage for common corporate/biographical facts
        self.PREDICATE_MAP = {
            # === ORGANIZATIONAL FACTS ===
            "founded": ["P112", "P571"],           # founded by, inception
            "established": ["P571", "P112"],       # inception, founded by
            "incorporated": ["P571", "P159", "P17", "P131"],  # inception, HQ, country, admin
            "headquartered": ["P159", "P131"],     # headquarters, admin territory
            "based": ["P159", "P131", "P17"],      # headquarters, admin territory, country
            "created": ["P571", "P170", "P112"],   # inception, creator, founded by
            "launched": ["P571", "P577", "P1056"],   # inception, publication date, product produced
            "acquired": ["P127", "P749", "P1365"], # owned by, parent org, replaces
            "merged": ["P156", "P155"],            # followed by, follows
            "owns": ["P127", "P749"],              # owned by (query inverse)
            "publishes": ["P123"],                 # publisher
            "employs": ["P1128"],                  # employees
            "operates": ["P159", "P276"],          # headquarters, location

            # === BIOGRAPHICAL FACTS ===
            "born": ["P569", "P19"],     # date of birth, place of birth
            "died": ["P570", "P20"],     # date of death, place of death
            "spouse": ["P26"],           # spouse
            "married": ["P26"],          # spouse
            "educated": ["P69"],         # educated at
            "studied": ["P69"],          # educated at
            "graduated": ["P69"],        # educated at
            "works": ["P108"],           # employer
            "worked": ["P108"],          # employer
            "employed": ["P108"],        # employer

            # === POSITION/ROLE FACTS ===
            "ceo": ["P39", "P488", "P169"],        # position held, chairperson, CEO
            "chief": ["P39", "P488", "P169"],      # position held, chairperson, CEO
            "served": ["P39"],                     # position held
            "appointed": ["P39"],                  # position held
            "elected": ["P39"],                    # position held
            "leads": ["P39", "P488"],              # position held, chairperson
            "chairs": ["P488"],                    # chairperson

            # === CREATIVE WORKS ===
            "wrote": ["P50"],            # author
            "authored": ["P50"],         # author
            "directed": ["P57"],         # director
            "produced": ["P162"],        # producer
            "composed": ["P86"],         # composer
            "invented": ["P61"],         # discoverer/inventor
            "discovered": ["P61"],       # discoverer/inventor
            "designed": ["P170"],        # creator
            "developed": ["P178"],       # developer
            "released": ["P577"],        # publication date
            "published": ["P577", "P123"],  # publication date, publisher

            # === LOCATION/GEOGRAPHY ===
            "located": ["P131", "P276", "P17"],  # admin terr, location, country
            "situated": ["P131", "P276"],        # admin terr, location
            "capital": ["P36"],                  # capital

            # === IDENTITY/CLASSIFICATION ===
            "is": ["P31", "P279"],       # instance of, subclass of
            "was": ["P31", "P279"],      # instance of, subclass of

            # === FINANCIAL FACTS ===
            "revenue": ["P2139"],        # revenue
            "profit": ["P2295"],         # net profit
            "valued": ["P2226"],         # market capitalization
            "worth": ["P2226"],          # market capitalization
            "traded": ["P414"],          # stock exchange
            "listed": ["P414"],          # stock exchange
            "public": ["P414", "P576"],  # stock exchange, dissolved (IPO-related)
            "ipo": ["P414", "P576"],     # stock exchange
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
