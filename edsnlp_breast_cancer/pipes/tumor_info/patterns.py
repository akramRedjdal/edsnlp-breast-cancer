"""Regex patterns for the ``breast_cancer.tumor_info`` pipe.

Ported from ``Tumour_information_extraction.py`` (histologic type, SBR/
Elston-Ellis grade, in-situ grade, tumour site/quadrant, associated in-situ
component, widespread microcalcifications, surgical margin status) and
``Patient_information_extraction.py`` (embolus/embole — conceptually
tumour-level per the project's own BCKM entity taxonomy, even though the
original code extracted it in the patient-info module).

The original's histologic-type classifier was ONE monolithic regex whose
match text was then re-inspected for a dozen overlapping keyword
combinations (ductal/lobular x invasive/in-situ x negation) to pick a
category. Here each concrete category gets its OWN anchor instead — the
same restructuring already used for ``breast_cancer.treatment``'s surgery
types, for the same reason: mutually-exclusive categorical outcomes read
more clearly as separate small patterns than as one giant one classified
after the fact.

As with the other pipes, GENERIC negation ("pas de", "absence de"...) is
left to ``eds.negation``. Domain-specific antonym vocabulary ("indemne",
"réactionnelle", "radiaire" = clear/negative, not caught by a generic
negation qualifier) is kept explicit in ``assign`` where relevant.
"""

# --- histologic type ---------------------------------------------------

_INVASIVE_DUCTAL = r"(?:carcinome\s*)?canalaire\s*(?:infiltrant|invasif|invasive)s?|\bcci\b"
_INVASIVE_LOBULAR = r"(?:carcinome\s*)?lobulaire\s*(?:infiltrant|invasif|invasive)s?|\bcli\b(?!s)"
_INVASIVE_DUCTAL_AND_LOBULAR = (
    r"canalaire\s*(?:et|\+)\s*lobulaire|lobulaire\s*(?:et|\+)\s*canalaire"
)
_DCIS = r"\bccis\b|canalaire\s*in\s*situ|\bcc\s*in\s*situ\b"
_LOBULAR_IS = r"\bclis\b|lobulaire\s*in\s*situ"
_IN_SITU_OTHER = r"carcinome\s*in\s*situ|\bcis\b"
_PAGET_DISEASE = r"pag[eé]to[iï]de|maladie\s*de\s*paget"
_BREAST_SARCOMA = r"sarcomes?"
_NON_CANCER = r"hyperplasies?|papillomes?|m[eé]taplasies?"
_INVASIVE_OTHER = (
    # "carcinome"/"adénocarcinome" + infiltrant/invasif, tolerating up to 2
    # descriptive words in between (e.g. "carcinome épidermoïde infiltrant")
    r"(?:ad[eé]no)?carcinome(?:\s+(?!canalaire|lobulaire)\w+){0,2}\s*(?:infiltrant|invasif|invasive)s?(?!\s*(?:canalaire|lobulaire))"
    # named subtypes that are inherently invasive carcinoma even without the
    # word "infiltrant"/"invasif" being stated (colloid/mucinous/medullary/
    # tubular/squamous adenocarcinoma)
    r"|(?:ad[eé]no)?carcinome\s+(?:collo[iï]de|muqueux|m[eé]dullaire|tubuleux|[eé]pidermo[iï]de)"
    r"|(?:ad[eé]no)?carcinome(?!\s*(?:in\s*situ|canalaire|lobulaire))"
)

# --- grade ---------------------------------------------------------------

_GRADE_INV_MENTION = r"\bsbr\b|grade\s*histopronostique|elston\s*(?:et|&)?\s*ellis|\bgrade\b"
_GRADE_INV_VALUE = r"([1-3]|i{1,3})(?![a-zA-Z])"

_GRADE_INSITU_HAUT = r"haut\s*grade"
_GRADE_INSITU_BAS = r"bas\s*grade"
_GRADE_INSITU_INTERMEDIAIRE = r"grades?\s*interm[eé]diaires?"

# --- tumour site / quadrant ------------------------------------------------

_QUADRANT_UPPER_OUTER = r"quadrants?\s*sup[eé]ro?\s*-?\s*ext[eé]rne?s?|\bqse\b"
_QUADRANT_UPPER_INNER = r"quadrants?\s*sup[eé]ro?\s*-?\s*int[eé]rne?s?|\bqsi(?:nf)?\b"
_QUADRANT_LOWER_OUTER = r"quadrants?\s*inf[eé]ro?\s*-?\s*ext[eé]rne?s?|\bqie\b"
_QUADRANT_LOWER_INNER = r"quadrants?\s*inf[eé]ro?\s*-?\s*int[eé]rne?s?|\bqii(?:nf)?\b"
_UNION_UPPER_QUADRANT = r"unions?\s*des?\s*quadrants?\s*sup[eé]rieurs?|\buqs\b"
_UNION_LOWER_QUADRANT = r"unions?\s*des?\s*quadrants?\s*inf[eé]rieurs?|\buqinf\b"
_UNION_INNER_QUADRANT = r"unions?\s*des?\s*quadrants?\s*int[eé]rnes?|\buqi\b"
_UNION_OUTER_QUADRANT = r"unions?\s*des?\s*quadrants?\s*ext[eé]rnes?|\buqe(?:xt)?\b"
_AXILLARY_REGION = r"prolongements?\s*axillaires?|\bpam\b"
_UNDER_MAMMARY_FOLD = r"sillons?\s*sous\s*-?\s*mammaires?|\bssm\b"
_AREOLAR_REGION = r"(?:p[eé]ri|para|r[eé]tro)?-?\s*ar[eé]olo?(?:aires?)?(?:-mamelonnaire)?"

# --- associated findings ---------------------------------------------------

# Real corpus phrasing is "composante [carcinomateuse/de carcinome/canalaire/
# lobulaire] in situ" — "associé(e)" (when present) comes BEFORE "composante"
# ("associé à une composante..."), never after "in situ", so it is not part
# of the anchor itself. Descriptor words between "composante" and "in situ"
# are a closed, explicit vocabulary (not a generic word-gap) since this
# anchor otherwise has no boundary to stop a runaway match.
_ASSOCIATED_INSITU_MENTION = (
    r"composantes?"
    r"(?:\s+(?:carcinomateuses?|de\s+carcinome|canalaires?|lobulaires?))*"
    r"\s*in\s*situ"
)
_MICROCALCIFICATIONS_MENTION = r"(?:foyers?\s*de\s*)?(?:micro)?calcifications?"
_DOMAIN_NEGATIVE_QUALIFIER = r"(indemnes?|r[eé]actionnelles?|radiaires?|absentes?|n[eé]gatives?)"

_EMBOLE_MENTION = r"emboles?"
_EMBOLE_TYPE = r"(sanguins?|lymphatiques?)"

# --- surgical margins -------------------------------------------------------

_MARGIN_MENTION = r"berges?|marges?|recoupes?|limites?\s*d.ex[eé]r[eè]se"
_MARGIN_QUALIFIER = r"(saines?|indemnes?|libres?|envahies?|atteintes?)"

PATTERNS = [
    {"source": "INVASIVE_DUCTAL_AND_LOBULAR", "regex": [_INVASIVE_DUCTAL_AND_LOBULAR], "regex_attr": "NORM"},
    {"source": "INVASIVE_DUCTAL", "regex": [_INVASIVE_DUCTAL], "regex_attr": "NORM"},
    {"source": "INVASIVE_LOBULAR", "regex": [_INVASIVE_LOBULAR], "regex_attr": "NORM"},
    {"source": "DCIS", "regex": [_DCIS], "regex_attr": "NORM"},
    {"source": "LOBULAR_IS", "regex": [_LOBULAR_IS], "regex_attr": "NORM"},
    {"source": "IN_SITU_OTHER", "regex": [_IN_SITU_OTHER], "regex_attr": "NORM"},
    {"source": "PAGET_DISEASE", "regex": [_PAGET_DISEASE], "regex_attr": "NORM"},
    {"source": "BREAST_SARCOMA", "regex": [_BREAST_SARCOMA], "regex_attr": "NORM"},
    {"source": "NON_CANCER", "regex": [_NON_CANCER], "regex_attr": "NORM"},
    {"source": "INVASIVE_OTHER", "regex": [_INVASIVE_OTHER], "regex_attr": "NORM"},
    {
        "source": "TUMOR_GRADE_INV",
        "regex": [_GRADE_INV_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "grade", "regex": _GRADE_INV_VALUE, "window": "words[0:4]", "reduce_mode": "keep_first", "required": True},
        ],
    },
    {"source": "GRADE_INSITU_HAUT", "regex": [_GRADE_INSITU_HAUT], "regex_attr": "NORM"},
    {"source": "GRADE_INSITU_BAS", "regex": [_GRADE_INSITU_BAS], "regex_attr": "NORM"},
    {"source": "GRADE_INSITU_INTERMEDIAIRE", "regex": [_GRADE_INSITU_INTERMEDIAIRE], "regex_attr": "NORM"},
    {"source": "QUADRANT_UPPER_OUTER", "regex": [_QUADRANT_UPPER_OUTER], "regex_attr": "NORM"},
    {"source": "QUADRANT_UPPER_INNER", "regex": [_QUADRANT_UPPER_INNER], "regex_attr": "NORM"},
    {"source": "QUADRANT_LOWER_OUTER", "regex": [_QUADRANT_LOWER_OUTER], "regex_attr": "NORM"},
    {"source": "QUADRANT_LOWER_INNER", "regex": [_QUADRANT_LOWER_INNER], "regex_attr": "NORM"},
    {"source": "UNION_UPPER_QUADRANT", "regex": [_UNION_UPPER_QUADRANT], "regex_attr": "NORM"},
    {"source": "UNION_LOWER_QUADRANT", "regex": [_UNION_LOWER_QUADRANT], "regex_attr": "NORM"},
    {"source": "UNION_INNER_QUADRANT", "regex": [_UNION_INNER_QUADRANT], "regex_attr": "NORM"},
    {"source": "UNION_OUTER_QUADRANT", "regex": [_UNION_OUTER_QUADRANT], "regex_attr": "NORM"},
    {"source": "AXILLARY_REGION", "regex": [_AXILLARY_REGION], "regex_attr": "NORM"},
    {"source": "UNDER_MAMMARY_FOLD", "regex": [_UNDER_MAMMARY_FOLD], "regex_attr": "NORM"},
    {"source": "AREOLAR_REGION", "regex": [_AREOLAR_REGION], "regex_attr": "NORM"},
    {
        "source": "ASSOCIATED_INSITU",
        "regex": [_ASSOCIATED_INSITU_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "qualifier", "regex": _DOMAIN_NEGATIVE_QUALIFIER, "window": "words[-2:4]", "reduce_mode": "keep_first"},
        ],
    },
    {
        "source": "WIDESPREAD_MICROCALCIFICATIONS",
        "regex": [_MICROCALCIFICATIONS_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "qualifier", "regex": _DOMAIN_NEGATIVE_QUALIFIER, "window": "words[-2:4]", "reduce_mode": "keep_first"},
        ],
    },
    {
        "source": "PRESENCE_EMBOLE",
        "regex": [_EMBOLE_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "type", "regex": _EMBOLE_TYPE, "window": "words[-2:2]", "reduce_mode": "keep_first"},
        ],
    },
    {
        "source": "MARGIN_STATUS",
        "regex": [_MARGIN_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "qualifier", "regex": _MARGIN_QUALIFIER, "window": "words[0:6]", "reduce_mode": "keep_first"},
        ],
    },
]
