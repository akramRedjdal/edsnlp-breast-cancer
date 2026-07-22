"""Regex patterns for the ``breast_cancer.side_findings`` pipe.

Ported from ``Breast_Information_extraction.py`` — scoped to BIRADS
classification and lymph node involvement (``positive_nodes``/``nbrgg``
regex in the original). Two things from that file are intentionally NOT
re-implemented here:

- ``extractSide`` (left/right/bilateral assignment): a structural/routing
  concern of the original pipeline (which side an entity belongs to), not a
  clinical fact worth its own span — left to the project-specific
  BCKM-mapping layer that composes this package's output.
- ``extractTNMs`` (TNM mentions re-derived from raw text): superseded by the
  dedicated ``breast_cancer.tnm`` pipe.

As with the other pipes, GENERIC negation/hedging ("pas de", "absence de",
"doute", "possible"...) is left to ``eds.negation`` / ``eds.hypothesis``.
What IS kept explicit here are DOMAIN-SPECIFIC antonym words ("indemne",
"libre" = clear/negative for involvement) that a generic negation qualifier
has no way to know are negative — those are real vocabulary, not negation.
"""

_BIRADS_MENTION = r"bi[\s-]?rads|acr"
_BIRADS_GRADE = r"(\d\s*[abc]?)"

_NODE_METASTASIS_MENTION = (
    r"(?:ganglions?|ad[eé]nopathies?)\s*(?:axillaires?|ganglionnaires?)?\s*m[eé]tastatiques?"
    r"|m[eé]tastases?\s*(?:ganglionnaires?|axillaires?)"
    r"|microm[eé]tastase\s*(?:ganglionnaires?|axillaires?)"
)

_NODE_INVOLVEMENT_MENTION = (
    r"ad[eé]nopathies?|ad[eé]nom[eé]galies?"
    r"|aires?\s*ganglionnaires?"
    r"|ganglions?(?:\s*(?:axillaires?|ganglionnaires?|intra\s*-?\s*mammaires?|sus\s*-?\s*claviculaires?))?"
)
_NODE_QUALIFIER = (
    r"(envahis?|positifs?|indemnes?|libres?|n[eé]gatifs?|suspects?)"
)

PATTERNS = [
    {
        "source": "BIRADS",
        "regex": [_BIRADS_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "grade", "regex": _BIRADS_GRADE, "window": "words[0:3]", "reduce_mode": "keep_first", "required": True},
        ],
    },
    {
        "source": "NODE_METASTASIS",
        "regex": [_NODE_METASTASIS_MENTION],
        "regex_attr": "NORM",
    },
    {
        "source": "NODE_INVOLVEMENT",
        "regex": [_NODE_INVOLVEMENT_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "qualifier", "regex": _NODE_QUALIFIER, "window": "words[0:4]", "reduce_mode": "keep_first"},
        ],
    },
]
