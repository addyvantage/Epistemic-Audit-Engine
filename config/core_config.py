# Epistemic Audit Engine - Core Configuration
# Strict Constants - Do NOT modify without Regression Testing

# --- Alignment Thresholds ---
ALIGN_THRESH_SIM_HIGH = 0.85
ALIGN_THRESH_SIM_MED = 0.75
ALIGN_THRESH_SIM_ULTRA = 0.92
ALIGN_THRESH_SIM_WEAK = 0.65

ALIGN_THRESH_ENT_HIGH = 0.8
ALIGN_THRESH_ENT_MED = 0.5

ALIGN_THRESH_CON_HIGH = 0.75

# --- Hallucination Types ---
HALLUCINATION_TYPE_CONTRADICTION = "TEXTUAL_CONTRADICTION"
HALLUCINATION_TYPE_UNSUPPORTED = "UNSUPPORTED_CLAIMS"
HALLUCINATION_TYPE_ROLE_CONFLICT = "ENTITY_ROLE_CONFLICT"
HALLUCINATION_TYPE_TEMPORAL = "TEMPORAL_FABRICATION"
HALLUCINATION_TYPE_DOSAGE = "IMPOSSIBLE_DOSAGE"
HALLUCINATION_TYPE_SCOPE = "SCOPE_OVERGENERALIZATION"
HALLUCINATION_TYPE_BLEED = "AUTHORITY_BLEED"

# --- Verdicts ---
VERDICT_SUPPORTED = "SUPPORTED"
VERDICT_REFUTED = "REFUTED"
VERDICT_UNCERTAIN = "UNCERTAIN"
VERDICT_INSUFFICIENT = "INSUFFICIENT_EVIDENCE"

# --- Evidence Modalities ---
EVIDENCE_MODALITY_TEXTUAL = "TEXTUAL"
EVIDENCE_MODALITY_STRUCTURED = "STRUCTURED"

# --- Confidence Caps ---
CONFIDENCE_CAP_STRUCTURED = 0.85
CONFIDENCE_CAP_PRIMARY = 0.95

# --- Retrieval Tiers ---
TIER_1_SOURCES = ["Primary Document", "Wikidata"]

# --- Resolution Status (v1.4) ---
# Added RESOLVED_COREF for coreference-based resolution
RESOLUTION_STATUS_RESOLVED = "RESOLVED"
RESOLUTION_STATUS_RESOLVED_SOFT = "RESOLVED_SOFT"
RESOLUTION_STATUS_RESOLVED_COREF = "RESOLVED_COREF"  # NEW: Coreference resolution
RESOLUTION_STATUS_UNRESOLVED = "UNRESOLVED"

# --- Feature Flags (v1.4) ---
# These flags allow incremental rollout and rollback of coverage improvements
ENABLE_COREFERENCE = True              # Document-level entity coreference
ENABLE_STRUCTURED_INDEPENDENCE = True  # Wikidata evidence can independently yield SUPPORTED
ENABLE_WEAK_ACCUMULATION = True        # Multiple weak supports upgrade to UNCERTAIN

# --- Coreference Thresholds (v1.4) ---
COREF_CONFIDENCE_DISCOUNT = 0.9        # Applied to coreference-resolved entities
COREF_MIN_CONFIDENCE = 0.70            # Minimum confidence for coreference source
COREF_DOMINANCE_GAP = 0.3              # Required frequency gap for dominance
