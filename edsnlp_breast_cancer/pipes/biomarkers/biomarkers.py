"""``breast_cancer.biomarkers`` pipeline component.

Thin wrapper around ``eds.contextual_matcher``: the matcher spots the
biomarker mention (anchor) and its nearby raw value (assign), this module
adds the domain-specific normalisation on top (contextual_matcher only
returns raw matched text).
"""
from typing import Callable, Optional

from spacy.tokens import Doc, Span

from edsnlp.core import PipelineProtocol
from edsnlp.pipes.core.contextual_matcher import ContextualMatcher

from .patterns import PATTERNS

_HER2_WORD_SCORES = {"zero": 0, "un": 1, "deux": 2, "trois": 3}


def _normalize_percent(raw: Optional[str]) -> Optional[int]:
    """Used for ER, PR and Ki67: returns an int in [0, 100], or None."""
    if raw is None:
        return None
    r = raw.strip().lower()
    if "pos" in r or r == "+":
        return 100
    if "neg" in r or "nég" in r or "nèg" in r or r == "-":
        return 0
    digits = "".join(ch for ch in r if ch.isdigit())
    if digits:
        val = int(digits)
        if 0 <= val <= 100:
            return val
    return None


def _normalize_her2(raw: Optional[str]) -> Optional[str]:
    """Returns one of 'Her2IHC0'..'Her2IHC3Plus', or None if not interpretable.

    A leading digit (e.g. the '3' in '3+') takes priority over counting '+'
    signs — otherwise '3+' would be read as a single '+' (score 1) instead
    of score 3, since the digit and the plus signs are matched together as
    one token but a naive plus-count would only see the trailing '+'.
    """
    if raw is None:
        return None
    r = raw.strip().lower()
    if "non" in r and "amplifi" in r:
        return "Her2IHC0"
    if "amplifi" in r:
        return "Her2IHC3Plus"
    digit = next((ch for ch in r if ch.isdigit()), None)
    if digit in ("0", "1", "2", "3"):
        return "Her2IHC0" if digit == "0" else f"Her2IHC{digit}Plus"
    if "neg" in r or "nég" in r:
        return "Her2IHC0"
    if "pos" in r:
        return "Her2IHC3Plus"
    for word, score in _HER2_WORD_SCORES.items():
        if word in r:
            return "Her2IHC0" if score == 0 else f"Her2IHC{score}Plus"
    plus = r.count("+")
    if plus:
        return f"Her2IHC{min(plus, 3)}Plus"
    return None


def _normalize_fish(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    r = raw.strip().lower()
    if "non" in r and "amplifi" in r:
        return "negative"
    if "amplifi" in r or "pos" in r or r == "+":
        return "positive"
    if "neg" in r or "nég" in r or r == "-":
        return "negative"
    return None


_NORMALIZERS: dict = {
    "ER": _normalize_percent,
    "PR": _normalize_percent,
    "HER2": _normalize_her2,
    "KI67": _normalize_percent,
    "FISH": _normalize_fish,
}


class BreastBiomarkersMatcher:
    """Extracts ER, PR, HER2, Ki67 and FISH results from breast cancer notes.

    Adds spans to ``doc.spans[spans_key]`` (default ``"biomarkers"``), each
    with two extensions:

    - ``span._.source``: which biomarker matched (``"ER"``, ``"PR"``,
      ``"HER2"``, ``"KI67"`` or ``"FISH"``)
    - ``span._.biomarker_value``: the normalised value — an int in [0, 100]
      for ER/PR/Ki67, one of ``Her2IHC0``..``Her2IHC3Plus`` for HER2,
      ``"positive"``/``"negative"`` for FISH, or ``None`` if the nearby
      value could not be interpreted.

    Examples
    --------
    ```python
    import edsnlp
    import edsnlp_breast_cancer  # noqa: F401  (registers the pipe)

    nlp = edsnlp.blank("eds")
    nlp.add_pipe("breast_cancer.biomarkers")

    doc = nlp("RE 100%, RP negatif, HER2 3+, Ki67 20%")
    for span in doc.spans["biomarkers"]:
        print(span, span._.source, span._.biomarker_value)
    ```

    Known simplification (v1 pilot): "triple négatif" as an implicit
    ER/PR/HER2=negative statement (handled specially in the original
    regex-only code) is not yet ported — only direct mentions are detected.

    Parameters
    ----------
    nlp : Optional[PipelineProtocol]
        The pipeline object.
    name : str
        Name of the pipe.
    spans_key : str
        Key under ``doc.spans`` where matches are stored.
    """

    def __init__(
        self,
        nlp: Optional[PipelineProtocol],
        name: str = "biomarkers",
        *,
        spans_key: str = "biomarkers",
    ):
        self.spans_key = spans_key
        self._matcher = ContextualMatcher(
            nlp,
            name=f"{name}_contextual_matcher",
            patterns=PATTERNS,
            label="biomarker",
            attr="NORM",
            span_setter={"ents": False, spans_key: True},
        )
        if not Span.has_extension("biomarker_value"):
            Span.set_extension("biomarker_value", default=None)

    def __call__(self, doc: Doc) -> Doc:
        doc = self._matcher(doc)
        normalize: Callable
        for span in doc.spans.get(self.spans_key, []):
            normalize = _NORMALIZERS.get(span._.source)
            raw = (span._.assigned or {}).get("value")
            span._.biomarker_value = normalize(raw) if normalize else None
        return doc
