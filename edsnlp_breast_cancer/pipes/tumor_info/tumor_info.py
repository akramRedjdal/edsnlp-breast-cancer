"""``breast_cancer.tumor_info`` pipeline component.

Thin wrapper around ``eds.contextual_matcher``. Generic negation is left to
``eds.negation``/``eds.hypothesis`` composed on top (see package README);
domain-specific antonym vocabulary is captured explicitly where relevant.
"""
from typing import Optional

from spacy.tokens import Doc, Span

from edsnlp.core import PipelineProtocol
from edsnlp.pipes.core.contextual_matcher import ContextualMatcher

from .patterns import PATTERNS

# sources that are a fully-specified categorical value on their own
_HISTOLOGIC_TYPE = {
    "INVASIVE_DUCTAL_AND_LOBULAR": "InvasiveDuctalAndLobularCarcinoma",
    "INVASIVE_DUCTAL": "InvasiveDuctalBreastCarcinoma",
    "INVASIVE_LOBULAR": "InvasiveLobularBreastCarcinoma",
    "DCIS": "DCISBreastCarcinoma",
    "LOBULAR_IS": "LobularISBreastCarcinoma",
    "IN_SITU_OTHER": "InSituBreastCarcinoma",
    "PAGET_DISEASE": "PagetDisease",
    "BREAST_SARCOMA": "BreastSarcoma",
    "NON_CANCER": "NonCancer",
    "INVASIVE_OTHER": "InvasiveBreastCarcinoma",
}
_GRADE_INSITU = {
    "GRADE_INSITU_HAUT": "Haut_Grade",
    "GRADE_INSITU_BAS": "Bas_Grade",
    "GRADE_INSITU_INTERMEDIAIRE": "Grade_intermediaire",
}
_TUMOR_SITE = {
    "QUADRANT_UPPER_OUTER": "upper_outer_quadrant",
    "QUADRANT_UPPER_INNER": "upper_inner_quadrant",
    "QUADRANT_LOWER_OUTER": "lower_outer_quadrant",
    "QUADRANT_LOWER_INNER": "lower_inner_quadrant",
    "UNION_UPPER_QUADRANT": "union_upper_quadrant",
    "UNION_LOWER_QUADRANT": "union_lower_quadrant",
    "UNION_INNER_QUADRANT": "union_inner_quadrant",
    "UNION_OUTER_QUADRANT": "union_outer_quadrant",
    "AXILLARY_REGION": "axillary_region",
    "UNDER_MAMMARY_FOLD": "under_mammary_fold",
    "AREOLAR_REGION": "areolar_region",
}
_ROMAN_TO_ARABIC = {"i": "1", "ii": "2", "iii": "3"}
_NEGATIVE_QUALIFIER_WORDS = {"indemne", "indemnes", "réactionnelle", "réactionnelles",
                             "reactionnelle", "reactionnelles", "radiaire", "radiaires",
                             "absente", "absentes", "négative", "négatives", "negative", "negatives"}
_MARGIN_NEGATIVE = {"envahie", "envahies", "atteinte", "atteintes"}
_MARGIN_POSITIVE = {"saine", "saines", "indemne", "indemnes", "libre", "libres"}


def _normalize_grade_inv(assigned: dict) -> Optional[str]:
    grade = (assigned.get("grade") or "").strip().lower()
    grade = _ROMAN_TO_ARABIC.get(grade, grade)
    return f"Grade{grade}" if grade else None


def _normalize_binary_with_domain_qualifier(assigned: dict) -> bool:
    qualifier = (assigned.get("qualifier") or "").strip().lower()
    if qualifier in _NEGATIVE_QUALIFIER_WORDS:
        return False
    return True  # bare mention: presence — eds.negation/hypothesis refine further


def _normalize_embole(assigned: dict) -> str:
    kind = (assigned.get("type") or "").strip().lower()
    if "sanguin" in kind:
        return "Sanguins"
    if "lymphatique" in kind:
        return "Lymphatiques"
    return "NotSpecified"


def _normalize_margin_status(assigned: dict) -> Optional[bool]:
    qualifier = (assigned.get("qualifier") or "").strip().lower()
    if qualifier in _MARGIN_NEGATIVE:
        return False
    if qualifier in _MARGIN_POSITIVE:
        return True
    return None  # bare mention without a qualifier: not interpretable alone


class TumorInfoMatcher:
    """Extracts tumour-level histopathology facts: histologic type, SBR /
    Elston-Ellis invasive grade, in-situ (DCIS) grade, tumour
    site/quadrant, associated in-situ component, widespread
    microcalcifications, lymphovascular embolus (with sanguine/lymphatic
    type), and surgical margin status.

    Adds spans to ``doc.spans[spans_key]`` (default ``"tumor_info"``), with
    ``span._.source`` and ``span._.tumor_info_value`` (type depends on
    ``source`` — see the ``_normalize_*`` functions).

    Generic negation is intentionally not handled here — compose
    ``eds.negation``/``eds.hypothesis`` on top (see the package README).
    Domain-specific antonym vocabulary (e.g. "indemne", "réactionnelle" for
    microcalcifications; "saine"/"envahie" for margins) is captured
    explicitly since a generic negation qualifier has no way to know these
    are negative/positive.

    Known simplification (v1): histologic-type detection uses one anchor
    per concrete category (mirroring ``breast_cancer.treatment``) rather
    than reproducing every keyword combination of the original monolithic
    regex; rare phrasings not covered by these anchors are not yet ported.
    """

    def __init__(
        self,
        nlp: Optional[PipelineProtocol],
        name: str = "tumor_info",
        *,
        spans_key: str = "tumor_info",
    ):
        self.spans_key = spans_key
        self._matcher = ContextualMatcher(
            nlp,
            name=f"{name}_contextual_matcher",
            patterns=PATTERNS,
            label="tumor_info",
            attr="NORM",
            span_setter={"ents": False, spans_key: True},
        )
        if not Span.has_extension("tumor_info_value"):
            Span.set_extension("tumor_info_value", default=None)

    def __call__(self, doc: Doc) -> Doc:
        doc = self._matcher(doc)
        for span in doc.spans.get(self.spans_key, []):
            source = span._.source
            assigned = span._.assigned or {}
            if source in _HISTOLOGIC_TYPE:
                span._.tumor_info_value = _HISTOLOGIC_TYPE[source]
            elif source in _GRADE_INSITU:
                span._.tumor_info_value = _GRADE_INSITU[source]
            elif source in _TUMOR_SITE:
                span._.tumor_info_value = _TUMOR_SITE[source]
            elif source == "TUMOR_GRADE_INV":
                span._.tumor_info_value = _normalize_grade_inv(assigned)
            elif source in ("ASSOCIATED_INSITU", "WIDESPREAD_MICROCALCIFICATIONS"):
                span._.tumor_info_value = _normalize_binary_with_domain_qualifier(assigned)
            elif source == "PRESENCE_EMBOLE":
                span._.tumor_info_value = _normalize_embole(assigned)
            elif source == "MARGIN_STATUS":
                span._.tumor_info_value = _normalize_margin_status(assigned)
        return doc
