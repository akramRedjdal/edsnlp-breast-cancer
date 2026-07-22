"""Regex patterns for the ``breast_cancer.diagnosis`` pipe.

Diagnostic / imaging procedures mentioned in the note. Ported from
``Diagnosis_extraction.py``.
"""

_BIOPSY_MENTION = r"(?:macro|micro)?[\s-]?bio[ps]{1,2}ies?"
_BIOPSY_SUBTYPE = r"(axillaire|macro|micro)"

_SCREENING_MENTION = r"d[eé]pistage"

_CYTOPONCTION_MENTION = r"cyto[\s-]?(?:ponctions?|logies?)"
_CYTOPONCTION_RESULT = r"(n[eéè]gative?|positive?)"

_ULTRASOUND_MENTION = r"[eéè]chographies?|[eéè]cho\b"

_MRI_MENTION = r"\birm\b"
# non-breast body sites — if the MRI mention is qualified with one of these,
# it is not a breast-related exam (mirrors the original code's site check)
_MRI_NON_BREAST_SITE = [
    {"regex": r"abdominale?|c[eé]r[eé]brale?|cervicale?|thorax|\bcou\b|ost[eé]o[\s-]?articulaires?", "window": "words[0:4]"},
]

_MAMMOGRAPHY_MENTION = r"(?:angio[\s-]?)?mammo(?:graphies?)?"

_PET_SCAN_MENTION = r"pet[\s-]?scan(?:ner)?|tep[\s-]?(?:tdm\s*)?(?:tep)?[\s-]?(?:scanne?r)?"

_CLINICAL_EXAM_MENTION = r"examen\s*(?:clinique|mammaire)s?|cliniquement|(?:auto[\s-]?)?palpations?"

PATTERNS = [
    {
        "source": "Biopsy",
        "regex": [_BIOPSY_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "subtype", "regex": _BIOPSY_SUBTYPE, "window": "words[-2:1]", "reduce_mode": "keep_first"},
        ],
    },
    {"source": "Screening", "regex": [_SCREENING_MENTION], "regex_attr": "NORM"},
    {
        "source": "Cytoponction",
        "regex": [_CYTOPONCTION_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "result", "regex": _CYTOPONCTION_RESULT, "window": "words[0:10]", "reduce_mode": "keep_first"},
        ],
    },
    {"source": "Ultra_sound", "regex": [_ULTRASOUND_MENTION], "regex_attr": "NORM"},
    {
        "source": "MRI",
        "regex": [_MRI_MENTION],
        "regex_attr": "NORM",
        "exclude": _MRI_NON_BREAST_SITE,
    },
    {"source": "Mammography", "regex": [_MAMMOGRAPHY_MENTION], "regex_attr": "NORM"},
    {"source": "Pet_scan", "regex": [_PET_SCAN_MENTION], "regex_attr": "NORM"},
    {"source": "Clinical_examination", "regex": [_CLINICAL_EXAM_MENTION], "regex_attr": "NORM"},
]
