"""``breast_cancer.diagnosis`` pipeline component.

Thin wrapper around ``eds.contextual_matcher``. As with the other pipes,
negation/hedging is left to ``eds.negation`` / ``eds.hypothesis`` composed on
top (see package README) rather than duplicated here.
"""
from typing import Optional

from spacy.tokens import Doc, Span

from edsnlp.core import PipelineProtocol
from edsnlp.pipes.core.contextual_matcher import ContextualMatcher

from .patterns import PATTERNS


def _normalize_biopsy(assigned: dict) -> Optional[str]:
    subtype = (assigned.get("subtype") or "").strip().lower()
    if "axill" in subtype:
        return "AxillaryBiopsy"
    if "macro" in subtype:
        return "MacroBiopsy"
    if "micro" in subtype:
        return "MicroBiopsy"
    return None


def _normalize_cytoponction(assigned: dict) -> Optional[str]:
    result = (assigned.get("result") or "").strip().lower()
    if "nég" in result or "neg" in result:
        return "Negative"
    if "pos" in result:
        return "Positive"
    return None


_NORMALIZERS = {
    "Biopsy": _normalize_biopsy,
    "Cytoponction": _normalize_cytoponction,
}


class DiagnosisMatcher:
    """Extracts diagnostic / imaging procedure mentions: biopsy (with
    axillary/macro/micro subtype), screening, cytoponction (with
    positive/negative result), ultrasound, MRI (breast-related only — a
    non-breast body site nearby excludes the match), mammography, PET-scan
    and clinical examination.

    Adds spans to ``doc.spans[spans_key]`` (default ``"diagnosis"``), with
    ``span._.source`` (the procedure type) and ``span._.diagnosis_value``
    (subtype/result detail, or ``None`` when not applicable/interpretable).
    """

    def __init__(
        self,
        nlp: Optional[PipelineProtocol],
        name: str = "diagnosis",
        *,
        spans_key: str = "diagnosis",
    ):
        self.spans_key = spans_key
        # One matcher per source (own label), not one shared instance — see
        # breast_cancer.biomarkers for why (spaCy's Span extension storage
        # is keyed by character position; two same-labelled spans on the
        # identical text range would silently overwrite each other's
        # `_.source`/`_.diagnosis_value`). `include_assigned=True` extends
        # each matched span to also cover its assigned detail text.
        self._matchers = [
            ContextualMatcher(
                nlp,
                name=f"{name}_{pattern['source']}_contextual_matcher",
                patterns=[pattern],
                label=pattern["source"],
                attr="NORM",
                span_setter={"ents": False, spans_key: True},
                include_assigned=True,
            )
            for pattern in PATTERNS
        ]
        if not Span.has_extension("diagnosis_value"):
            Span.set_extension("diagnosis_value", default=None)

    def __call__(self, doc: Doc) -> Doc:
        for matcher in self._matchers:
            doc = matcher(doc)
        for span in doc.spans.get(self.spans_key, []):
            normalize = _NORMALIZERS.get(span._.source)
            span._.diagnosis_value = normalize(span._.assigned or {}) if normalize else None
        return doc
