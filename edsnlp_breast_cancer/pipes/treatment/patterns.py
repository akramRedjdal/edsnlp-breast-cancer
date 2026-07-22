"""Regex patterns for the ``breast_cancer.treatment`` pipe.

Ported from ``Treatment_extraction.py`` (the bilingual FR/EN version — richer
than a later refactor found in a separate copy of this project, which had
dropped the English terms). As with the other pipes, negation is left to
``eds.negation`` (see package README) instead of the original's inline
``"sans"/"pas"/"aucun"/"absenc"`` checks duplicated in every branch.

Known restructuring vs. the original (documented, not silent):
- The original had a second, near-duplicate regex
  (``Traitement_chirurgical_premier``) that matched the same bare
  "chirurgie"/"surgery" mentions as part of the ``Surgery`` pattern's own
  alternation — folded here into a single ``SURGERY_UNSPECIFIED`` source
  instead of running two overlapping passes.
- ``antiher2`` was one regex serving two unrelated concepts (HER2-targeted
  therapy AND anti-hormonal/endocrine therapy, distinguished after the fact
  by checking for "her" in the match) — split here into ``ANTI_HER2`` and
  folded the anti-hormonal wording into ``ENDOCRINE_THERAPY`` instead.
"""

# --- surgery: one anchor per concrete procedure type ------------------------

_MASTECTOMY = r"mast[eéè]ctomies?|mastectom(?:y|ies)"
_CONSERVATIVE_SURGERY = (
    r"tume?o?r[eéè]ctomies?|tumorectom(?:y|ies)"
    r"|zon[eéè]ctom(?:ies?|[yi]e?s?)|pam[eéè]ctomies?|pamectom(?:y|ies)"
    r"|conservati(?:ve|on)\s*surgery"
)
_ONCOPLASTY = r"oncoplasties?|oncoplast(?:y|ies)|(?:onco)?[\s.]?plasties?"
_ANNEXECTOMY = r"ann[eéè]xectomies?"
_BREAST_RECONSTRUCTION = r"(?:reconstructions?|r[eéè]ductions?)\s*mammaires?|breast\s*plastic\s*surgery"
_AXILLARY_DISSECTION = r"curage(?:\s*ganglionnaire)?(?:\s*axill?aire?)?|dissection|lymph\s*node\s*dissection"
_SENTINEL_NODE = r"ganglions?\s*(?:non\s*)?sentinelles?|sentinel\s*lymph\s*nodes?|\bgs\b"
# a count right before "ganglion(s)" (e.g. "3 ganglions non sentinelles")
# means it's a lymph-node-COUNT report, not the sentinel-node PROCEDURE
# itself — exclude those. `exclude` ignores matches that fall *inside* the
# anchor span (edsnlp semantics), so the count must NOT be part of the
# anchor regex itself — it is checked in the word(s) just before it instead.
_SENTINEL_NODE_EXCLUDE = [
    {"regex": r"\b(?:\d+|un|deux|trois|quatre|cinq|one|two|three|four|five)\b", "window": "words[-2:0]"},
]
_BREAST_REEXCISION = r"reprise\s*de\s*berges?|re-excision\s*of\s*margins"
_SURGERY_UNSPECIFIED = r"chirurgies?|surgery|surgical\s*treatments?"

# --- systemic / radiation therapy -------------------------------------------

_CHEMOTHERAPY_MENTION = r"chimio(?:th[eéè]rapies?)?|chemio?th[eéè]rapies?|chemotherapy|\bct\b"
_ENDOCRINE_MENTION = (
    r"hormonoth[eéè]rapies?|endocrine\s*therapy"
    r"|anti[\s-]?hormonale?s?|anti[\s-]?hormonal"
)
_ANTI_HER2_MENTION = r"anti[\s-]?her\s*-?\s*2|double\s*blocages?|double\s*blockade"
_THERAPY_PHASE = r"(n[eéè]oadjuvante?|neoadjuvant|adjuvante?)"

_RADIOTHERAPY_MENTION = r"radioth[eéè]rapies?|radiotherapy"
_RADIOTHERAPY_SITE = r"(boost|parois?|sus[\s-]?claviculaires?|creux\s*axillaire|lit\s*tumoral|tumor\s*bed)"

_IMMUNOTHERAPY_MENTION = r"immunoth[eéè]rapies?|immunotherapy"

PATTERNS = [
    {"source": "MASTECTOMY", "regex": [_MASTECTOMY], "regex_attr": "NORM"},
    {"source": "CONSERVATIVE_SURGERY", "regex": [_CONSERVATIVE_SURGERY], "regex_attr": "NORM"},
    {"source": "ONCOPLASTY", "regex": [_ONCOPLASTY], "regex_attr": "NORM"},
    {"source": "ANNEXECTOMY", "regex": [_ANNEXECTOMY], "regex_attr": "NORM"},
    {"source": "BREAST_RECONSTRUCTION", "regex": [_BREAST_RECONSTRUCTION], "regex_attr": "NORM"},
    {"source": "AXILLARY_DISSECTION", "regex": [_AXILLARY_DISSECTION], "regex_attr": "NORM"},
    {
        "source": "SENTINEL_NODE",
        "regex": [_SENTINEL_NODE],
        "regex_attr": "NORM",
        "exclude": _SENTINEL_NODE_EXCLUDE,
    },
    {"source": "BREAST_REEXCISION", "regex": [_BREAST_REEXCISION], "regex_attr": "NORM"},
    {"source": "SURGERY_UNSPECIFIED", "regex": [_SURGERY_UNSPECIFIED], "regex_attr": "NORM"},
    {
        "source": "CHEMOTHERAPY",
        "regex": [_CHEMOTHERAPY_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "phase", "regex": _THERAPY_PHASE, "window": "words[0:4]", "reduce_mode": "keep_first"},
        ],
    },
    {
        "source": "ENDOCRINE_THERAPY",
        "regex": [_ENDOCRINE_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "phase", "regex": _THERAPY_PHASE, "window": "words[0:4]", "reduce_mode": "keep_first"},
        ],
    },
    {"source": "ANTI_HER2", "regex": [_ANTI_HER2_MENTION], "regex_attr": "NORM"},
    {
        "source": "RADIOTHERAPY",
        "regex": [_RADIOTHERAPY_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "site", "regex": _RADIOTHERAPY_SITE, "window": "words[0:6]", "reduce_mode": "keep_first"},
        ],
    },
    {"source": "IMMUNOTHERAPY", "regex": [_IMMUNOTHERAPY_MENTION], "regex_attr": "NORM"},
]
