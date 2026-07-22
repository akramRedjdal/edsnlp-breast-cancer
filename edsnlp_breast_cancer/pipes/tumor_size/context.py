"""Context classification for raw size measurements.

A raw measurement (e.g. "23 x 18 mm") found in a clinical note can refer to
a tumour, a lymph node, or be a false positive for this purpose entirely
(a clock-position reference like "à 4h", a nipple-distance measurement, or
a margin/distance-to-resection measurement) — ported from the context
checks in the original ``Tumour_information_extraction.extractTumourSizes``
(the ``mamelon``/clock-position/``distan``/margin exclusions), generalised
into a reusable classifier here instead of being interleaved with parsing.
"""
import re

_TUMOR_KW = [
    "tumeur", "tumoral", "masse", "lésion", "lesion", "nodule",
    "foyer", "carcinome", "opacit", "rehaussement", "plage", "prise de contraste",
]
_NODE_KW = [
    "ganglion", "adenopath", "adénopath", "axillaire", "mammaire interne",
    "chaine", "chaîne", "sus-clav", "sous-clav", "cortex",
]

# not a tumour/lesion size at all — a different kind of measurement that
# happens to share the same numeric format
_CLOCK_POSITION = re.compile(r"\b\d{1,2}\s*h(?:eures?)?\b", re.IGNORECASE)
_NIPPLE_DISTANCE = re.compile(r"mamelon", re.IGNORECASE)
_MARGIN_DISTANCE = re.compile(r"\b(?:distance|marge|berges?)\b", re.IGNORECASE)

_WINDOW_CHARS = 45


def classify(sentence_text: str, start: int, end: int):
    """Returns (context, excluded): context in {"tumor", "node", None},
    excluded is True when the measurement is a clock-position, nipple- or
    margin-distance mention rather than an actual lesion/node size."""
    lo = max(0, start - _WINDOW_CHARS)
    hi = min(len(sentence_text), end + _WINDOW_CHARS)
    window = sentence_text[lo:hi].lower()
    matched_text = sentence_text[start:end].lower()

    if _CLOCK_POSITION.search(matched_text) or _NIPPLE_DISTANCE.search(window) or _MARGIN_DISTANCE.search(window):
        return None, True

    is_node = any(k in window for k in _NODE_KW)
    is_tumor = any(k in window for k in _TUMOR_KW)
    if is_tumor and not is_node:
        return "tumor", False
    if is_node and not is_tumor:
        return "node", False
    return None, False
