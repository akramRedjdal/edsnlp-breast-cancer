"""``breast_cancer.side_findings`` pipeline component.

Thin wrapper around ``eds.contextual_matcher``. Generic negation/hedging is
left to ``eds.negation``/``eds.hypothesis`` composed on top (see package
README); domain-specific antonym vocabulary ("indemne", "libre"...) that a
generic negation qualifier cannot know about is captured explicitly here.
"""
from typing import Optional, Union

from spacy.tokens import Doc, Span

from edsnlp.core import PipelineProtocol
from edsnlp.pipes.core.contextual_matcher import ContextualMatcher

from .patterns import PATTERNS

_NEGATIVE_QUALIFIERS = {"indemne", "indemnes", "libre", "libres", "négatif", "negatif", "négatifs", "negatifs"}
_POSITIVE_QUALIFIERS = {"envahi", "envahis", "positif", "positifs", "suspect", "suspects"}


def _normalize_birads(assigned: dict) -> Optional[str]:
    grade = (assigned.get("grade") or "").strip().lower().replace(" ", "")
    return f"Birads{grade}" if grade else None


def _normalize_node_metastasis(assigned: dict) -> bool:
    return True


def _normalize_node_involvement(assigned: dict) -> Union[bool, None]:
    qualifier = (assigned.get("qualifier") or "").strip().lower()
    if qualifier in _NEGATIVE_QUALIFIERS:
        return False
    if qualifier in _POSITIVE_QUALIFIERS:
        return True
    return True  # bare mention: presence — eds.negation/hypothesis refine further


_NORMALIZERS = {
    "BIRADS": _normalize_birads,
    "NODE_METASTASIS": _normalize_node_metastasis,
    "NODE_INVOLVEMENT": _normalize_node_involvement,
}


class SideFindingsMatcher:
    """Extracts BIRADS classification and lymph node involvement mentions
    (pathologically-confirmed metastatic nodes vs. a more generic clinical
    node/adenopathy mention).

    Adds spans to ``doc.spans[spans_key]`` (default ``"side_findings"``),
    with ``span._.source`` (``"BIRADS"``, ``"NODE_METASTASIS"`` or
    ``"NODE_INVOLVEMENT"``) and ``span._.side_finding_value`` (e.g.
    ``"Birads4b"`` for BIRADS, a bool for node sources).

    Generic negation/hedging ("pas de", "doute"...) is intentionally not
    handled here — compose ``eds.negation``/``eds.hypothesis`` on top (see
    the package README). The ``qualifier`` vocabulary captured for
    ``NODE_INVOLVEMENT`` ("indemne", "libre", "envahi"...) is domain-specific
    and would not be recognised by a generic negation qualifier.
    """

    def __init__(
        self,
        nlp: Optional[PipelineProtocol],
        name: str = "side_findings",
        *,
        spans_key: str = "side_findings",
    ):
        self.spans_key = spans_key
        # One matcher per source (own label), not one shared instance — see
        # breast_cancer.biomarkers for why (spaCy's Span extension storage
        # is keyed by character position; two same-labelled spans on the
        # identical text range would silently overwrite each other's
        # `_.source`/`_.side_finding_value`). `include_assigned=True`
        # extends each matched span to also cover its assigned detail text.
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
        if not Span.has_extension("side_finding_value"):
            Span.set_extension("side_finding_value", default=None)

    def __call__(self, doc: Doc) -> Doc:
        for matcher in self._matchers:
            doc = matcher(doc)
        for span in doc.spans.get(self.spans_key, []):
            normalize = _NORMALIZERS.get(span._.source)
            span._.side_finding_value = normalize(span._.assigned or {}) if normalize else None
        return doc
