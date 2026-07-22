"""Regex patterns for the ``breast_cancer.biomarkers`` pipe.

Each entry follows the ``eds.contextual_matcher`` pattern format: an anchor
(``regex``/``terms``) that spots a biomarker mention, and one ``assign`` rule
that captures the nearby value in a window after the anchor. The ``assign``
regex must have exactly one capturing group (enforced by edsnlp).

Ported from the project's original ``BiomarkersExtraction.py`` regex, split
into "mention" (anchor) and "value" (assign) instead of one monolithic
pattern — the anchor no longer needs to also capture the value, which is
what made the original regex hard to bound (e.g. matching a 4-digit year as
if it were a percentage).
"""

# --- anchors (mention only, no value) --------------------------------------

_ER_MENTION = (
    r"r[eéè]c[eéè]pteurs?\s*(?:aux\s*)?oestrog[eè]nes?"
    r"|\bre\b|\bro\b|\br0\b"
)
_PR_MENTION = (
    r"r[eéè]c[eéè]pteurs?\s*(?:[àa]\s*la\s*)?prog[eéè]st[eéè]rones?"
    r"|\brp\b"
)
# "RH" ("Récepteurs Hormonaux") and the spelled-out "récepteurs hormonaux"
# cover BOTH estrogen and progesterone receptors at once — kept as its own
# source (not folded into _ER_MENTION/_PR_MENTION) because spaCy's Span
# extension storage is keyed by character position alone: two spans landing
# on the exact same range cannot independently hold different `_.source`/
# `_.biomarker_value` values, so ER and PR can never both anchor on the
# literal same "RH" text. Downstream (this pipe's own normalizer, and any
# consumer reading biomarker spans) must treat source == "RH_COMBINED" as
# evidence for BOTH ER and PR with the same value.
_RH_COMBINED_MENTION = r"r[eéè]c[eéè]pteurs?\s*hormonaux|\brh\b"
_HER2_MENTION = r"\bher\s*-?\s*2\b|\bc[-\s]?erbb?[-\s]?2\b"
_KI67_MENTION = r"\bki\s*-?\s*67\b"
_FISH_MENTION = r"\bfish\b"

# --- assign (value, exactly one capturing group each) -----------------------

# ER/PR/Ki67: percentage bounded to [0, 100] (as 1-2 digits or literal 100) or
# a qualitative pos/neg — this bound is what keeps 4-digit years out.
# NB: the assign window always includes the anchor's own span (edsnlp's
# WordContextWindow computes it as doc[span.start+before : span.end+after],
# so "words[0:N]" starts at the anchor's START, not its end). Since some
# anchors embed a digit in their own name ("Ki67", "HER2"), the numeric
# branch requires a non-alnum lookbehind so it can't re-match that digit as
# if it were the value (e.g. the "67" glued inside "Ki67").
_NOT_GLUED = r"(?<![A-Za-z0-9])"
_PERCENT_VALUE = (
    r"(\+|-|pos(?:itif|itive)?|n[eéè]g(?:atif|ative)?"
    rf"|{_NOT_GLUED}(?:100|\d{{1,2}})(?!\d)\s*%?)"
)

_HER2_VALUE = (
    r"(non\s*amplifi[ée]e?|amplifi[ée]e?"
    r"|z[ée]ro\b|un\b|deux\b|trois\b"
    rf"|{_NOT_GLUED}[0-3]\+{{0,2}}(?!\d)|\+{{1,3}}"
    r"|n[eéè]g(?:atif|ative)?|pos(?:itif|itive)?)"
)

_FISH_VALUE = (
    r"(non\s*amplifi[ée]e?|amplifi[ée]e?"
    r"|pos(?:itif|itive)?|n[eéè]g(?:atif|ative)?|\+|-)"
)

# Guards against the anchor's value being confused with a nearby date
# (the original bug: "RE 2019" being read as ER=2019). Kept as a tight
# window so it only blocks dates immediately next to the anchor, not
# unrelated dates elsewhere in the same sentence.
_YEAR_EXCLUDE = [{"regex": r"\b(?:19|20)\d{2}\b", "window": 4}]

PATTERNS = [
    {
        "source": "ER",
        "regex": [_ER_MENTION],
        "regex_attr": "NORM",
        "exclude": _YEAR_EXCLUDE,
        "assign": [
            {"name": "value", "regex": _PERCENT_VALUE, "window": "words[0:6]", "reduce_mode": "keep_first"},
        ],
    },
    {
        "source": "PR",
        "regex": [_PR_MENTION],
        "regex_attr": "NORM",
        "exclude": _YEAR_EXCLUDE,
        "assign": [
            {"name": "value", "regex": _PERCENT_VALUE, "window": "words[0:6]", "reduce_mode": "keep_first"},
        ],
    },
    {
        "source": "RH_COMBINED",
        "regex": [_RH_COMBINED_MENTION],
        "regex_attr": "NORM",
        "exclude": _YEAR_EXCLUDE,
        "assign": [
            {"name": "value", "regex": _PERCENT_VALUE, "window": "words[0:6]", "reduce_mode": "keep_first"},
        ],
    },
    {
        "source": "HER2",
        "regex": [_HER2_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "value", "regex": _HER2_VALUE, "window": "words[0:6]", "reduce_mode": "keep_first"},
        ],
    },
    {
        "source": "KI67",
        "regex": [_KI67_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "value", "regex": _PERCENT_VALUE, "window": "words[0:6]", "reduce_mode": "keep_first"},
        ],
    },
    {
        "source": "FISH",
        "regex": [_FISH_MENTION],
        "regex_attr": "NORM",
        "assign": [
            {"name": "value", "regex": _FISH_VALUE, "window": "words[0:6]", "reduce_mode": "keep_first"},
        ],
    },
]
