"""Regex patterns for the ``breast_cancer.patient_info`` pipe.

Ported from the project's original ``Patient_information_extraction.py``,
where each field was one large regex baking together the anchor term AND
every possible negation/hedge phrasing ("pas de", "absence de", "sans",
"non"...) — classified afterwards by checking which keyword ended up inside
the match. Negation/hedging is a generic, already-solved problem in EDS-NLP
(``eds.negation``, ``eds.hypothesis``), so here the anchors only spot the
*mention*; the categorical detail (which type of response, which gene...) is
captured via ``assign``, and Negated/Hypothetic state is left to the
qualifier pipes the user composes on top (see package README).
"""

_MENOPAUSE_MENTION = r"m[eéè]nopaus[eéè]e?s?|am[eéè]n{1,2}or{1,2}h[eéè]{1,2}e?s?"
# peri/post/non modifier just before the mention, e.g. "non ménopausée"
_MENOPAUSE_MODIFIER = r"(p[eéè]ri|post|non)"

_RECIDIVE_MENTION = r"r[eéè]cidiv\w*"

_RESPONSE_MENTION = r"r[eéè]ponses?|r[eéè]gressions?"
_RESPONSE_DEGREE = (
    r"(partielle|compl[eè]te|incompl[eè]te|mod[eé]r[eé]e|faible|mauvaise|\d{1,2}\s*%)"
)

_MUTATION_MENTION = r"mutations?|variants?|mut[eé]{2}"
_MUTATION_GENE = r"(brca\s*[12]?|palb2|rad51[cd]|stk11|egfr|met|t?p53|cdh1)"

_ONCOTYPE_MENTION = r"oncotype"
_ONCOTYPE_SCORE = r"(\d{1,3})"

_CANCER_COMORBIDITY_MENTION = r"cancers?|carcinomes?|lymphomes?|leuc[eé]mies?"
_CANCER_SITE = (
    r"(sein|cerveau|r[eé]nal?e?|rein|testicule|vessie|thyro[iï]dien?ne?"
    r"|colique|colorectal|prostate|ovarien?ne?|pulmonaire|poumons?|peau"
    r"|pancr[eé]as|ovaire|foie|c[oô]lon|rectum|estomac|endom[eè]tre|ut[eé]rus)"
)

_BRA_CUP_MENTION = r"bonnet"
_BRA_CUP_LETTER = r"(?<![A-Za-z])([a-f])(?![a-zA-Z])"

# Fixed-list comorbidities (no assign needed — presence alone is the fact)
NAMED_DISEASES = [
    "maladie cardiaque ischémique",
    "cardiomyopathie",
    "insuffisance cardiaque congestive",
    "insuffisance cardiaque",
    "hypertension artérielle",
    "hypertension",
    "sclérodermie systémique",
    "sclérodermie cutanée",
    "xeroderma pigmentosum",
    "anémie falciforme",
    "leucémie myéloïde chronique",
    "thalassémie",
    "myélodysplasie",
    "lupus érythémateux disséminé",
    "polyarthrite rhumatoïde",
    "sclérose en plaques",
    "maladie de crohn",
    "immunodépression",
    "insuffisance rénale aiguë",
    "insuffisance rénale chronique",
]

PATTERNS = [
    {
        "source": "MENOPAUSE",
        "regex": [_MENOPAUSE_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "modifier", "regex": _MENOPAUSE_MODIFIER, "window": "words[-3:0]", "reduce_mode": "keep_first"},
        ],
    },
    {
        "source": "RECIDIVE",
        "regex": [_RECIDIVE_MENTION],
        "regex_attr": "NORM",
    },
    {
        "source": "RESPONSE",
        "regex": [_RESPONSE_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "degree", "regex": _RESPONSE_DEGREE, "window": "words[0:6]", "reduce_mode": "keep_first", "required": True},
        ],
    },
    {
        "source": "MUTATION",
        "regex": [_MUTATION_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "gene", "regex": _MUTATION_GENE, "window": "words[0:8]", "reduce_mode": "keep_first"},
        ],
    },
    {
        "source": "ONCOTYPE",
        "regex": [_ONCOTYPE_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "score", "regex": _ONCOTYPE_SCORE, "window": "words[0:10]", "reduce_mode": "keep_first", "required": True},
        ],
    },
    {
        "source": "CANCER_COMORBIDITY",
        "regex": [_CANCER_COMORBIDITY_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "site", "regex": _CANCER_SITE, "window": "words[0:5]", "reduce_mode": "keep_first", "required": True},
        ],
    },
    {
        "source": "BRA_CUP",
        "regex": [_BRA_CUP_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "cup", "regex": _BRA_CUP_LETTER, "window": "words[-3:3]", "reduce_mode": "keep_first", "required": True},
        ],
    },
    {
        "source": "NAMED_DISEASE",
        "terms": NAMED_DISEASES,
        "regex_attr": "NORM",
    },
]
