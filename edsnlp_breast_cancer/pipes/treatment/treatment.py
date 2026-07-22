"""``breast_cancer.treatment`` pipeline component.

Thin wrapper around ``eds.contextual_matcher``. Negation is left to
``eds.negation`` composed on top (see package README), not duplicated here.
"""
from typing import Optional

from spacy.tokens import Doc, Span

from edsnlp.core import PipelineProtocol
from edsnlp.pipes.core.contextual_matcher import ContextualMatcher

from .patterns import PATTERNS

# sources that are already a fully-specified treatment value on their own
# (no further phase/site qualification needed)
_DIRECT_VALUE = {
    "MASTECTOMY": "Mastectomy",
    "CONSERVATIVE_SURGERY": "Conservative_surgery",
    "ONCOPLASTY": "Oncoplasty",
    "ANNEXECTOMY": "Annexectomy",
    "BREAST_RECONSTRUCTION": "Breast_reconstruction",
    "AXILLARY_DISSECTION": "Axillary_dissection",
    "SENTINEL_NODE": "Sentinel_lymph_node_Biopsy",
    "BREAST_REEXCISION": "BreastReExcision",
    "SURGERY_UNSPECIFIED": "Surgery",
    "ANTI_HER2": "Anti_HER2_therapy",
    "IMMUNOTHERAPY": "Immunotherapy",
}


def _normalize_phased_therapy(base_name: str):
    def normalize(assigned: dict) -> str:
        phase = (assigned.get("phase") or "").strip().lower()
        # check neo/néo FIRST: "néoadjuvante" also contains "adjuvante"
        if "neo" in phase or "néo" in phase:
            return f"Neoadjuvant_{base_name}"
        if "adj" in phase:
            return f"Adjuvant_{base_name}"
        return base_name

    return normalize


def _normalize_radiotherapy(assigned: dict) -> str:
    site = (assigned.get("site") or "").strip().lower()
    if "lit" in site or "tumor bed" in site:
        return "LitTumoral"
    if "boost" in site:
        return "Boost"
    if "paroi" in site:
        return "Paroi"
    if "claviculaire" in site:
        return "SusClaviculaire"
    return "Radiotherapy"


_PHASED_NORMALIZERS = {
    "CHEMOTHERAPY": _normalize_phased_therapy("chemotherapy"),
    "ENDOCRINE_THERAPY": _normalize_phased_therapy("endocrine_therapy"),
}


class TreatmentMatcher:
    """Extracts treatment mentions: surgery (mastectomy, conservative
    surgery/tumorectomy, oncoplasty, annexectomy, breast reconstruction,
    axillary dissection, sentinel lymph node biopsy, breast re-excision, or
    unspecified surgery), chemotherapy and endocrine therapy (each optionally
    qualified as neoadjuvant/adjuvant), anti-HER2 therapy, radiotherapy (with
    an optional site: boost/paroi/sus-claviculaire/lit tumoral) and
    immunotherapy.

    Adds spans to ``doc.spans[spans_key]`` (default ``"treatment"``), with
    ``span._.source`` (the matched category) and ``span._.treatment_value``
    (the final normalised treatment label — see ``_DIRECT_VALUE`` and the
    phase/site normalisers).

    Negation is intentionally not handled here — compose ``eds.negation`` /
    ``eds.hypothesis`` on top (see the package README).
    """

    def __init__(
        self,
        nlp: Optional[PipelineProtocol],
        name: str = "treatment",
        *,
        spans_key: str = "treatment",
    ):
        self.spans_key = spans_key
        self._matcher = ContextualMatcher(
            nlp,
            name=f"{name}_contextual_matcher",
            patterns=PATTERNS,
            label="treatment",
            attr="NORM",
            span_setter={"ents": False, spans_key: True},
        )
        if not Span.has_extension("treatment_value"):
            Span.set_extension("treatment_value", default=None)

    def __call__(self, doc: Doc) -> Doc:
        doc = self._matcher(doc)
        for span in doc.spans.get(self.spans_key, []):
            source = span._.source
            if source in _DIRECT_VALUE:
                span._.treatment_value = _DIRECT_VALUE[source]
            elif source == "RADIOTHERAPY":
                span._.treatment_value = _normalize_radiotherapy(span._.assigned or {})
            elif source in _PHASED_NORMALIZERS:
                span._.treatment_value = _PHASED_NORMALIZERS[source](span._.assigned or {})
        return doc
