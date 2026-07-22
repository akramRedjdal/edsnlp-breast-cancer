"""``breast_cancer.patient_info`` pipeline component.

Thin wrapper around ``eds.contextual_matcher`` (see ``patterns.py`` for the
rationale). Negation/hedging is intentionally NOT handled here: compose
``eds.negation`` / ``eds.hypothesis`` on top (pointed at this pipe's
``spans_key``) to get ``span._.negation`` / ``span._.hypothesis`` for free —
see the package README for the recommended pipeline recipe.
"""
from typing import Optional

from spacy.tokens import Doc, Span

from edsnlp.core import PipelineProtocol
from edsnlp.pipes.core.contextual_matcher import ContextualMatcher

from .patterns import PATTERNS


def _normalize_menopause(assigned: dict) -> Optional[str]:
    modifier = (assigned.get("modifier") or "").strip().lower()
    if "non" in modifier:
        return "Premenopausal"
    if modifier.startswith(("peri", "péri", "péri")):
        return "Perimenopausal"
    return "Postmenopausal"


def _normalize_recidive(assigned: dict) -> bool:
    return True


def _normalize_response(assigned: dict) -> Optional[str]:
    degree = (assigned.get("degree") or "").strip().lower()
    if not degree:
        return None
    if "partielle" in degree or "%" in degree:
        return "PartialResponse"
    if "compl" in degree and "in" not in degree:
        return "CompleteResponse"
    if "incompl" in degree or "mod" in degree or "faible" in degree or "mauvaise" in degree:
        return "StableDisease"
    return None


def _normalize_mutation(assigned: dict) -> str:
    gene = (assigned.get("gene") or "").strip().lower()
    return "BRCA" if "brca" in gene else "Other"


def _normalize_oncotype(assigned: dict) -> Optional[int]:
    score = assigned.get("score")
    if score is None:
        return None
    val = int(score)
    return val if 0 <= val <= 100 else None


def _normalize_cancer_comorbidity(assigned: dict) -> str:
    site = (assigned.get("site") or "").strip().lower()
    return "BreastCancer" if "sein" in site else "OtherCancer"


def _normalize_bra_cup(assigned: dict) -> Optional[str]:
    cup = assigned.get("cup")
    return cup.upper() if cup else None


def _normalize_named_disease(assigned: dict) -> None:
    return None  # the span text itself (span.text) is the value


_NORMALIZERS = {
    "MENOPAUSE": _normalize_menopause,
    "RECIDIVE": _normalize_recidive,
    "RESPONSE": _normalize_response,
    "MUTATION": _normalize_mutation,
    "ONCOTYPE": _normalize_oncotype,
    "CANCER_COMORBIDITY": _normalize_cancer_comorbidity,
    "BRA_CUP": _normalize_bra_cup,
    "NAMED_DISEASE": _normalize_named_disease,
}


class PatientInfoMatcher:
    """Extracts patient-level facts: menopausal status, prior breast cancer
    relapse, response to neoadjuvant therapy, genetic mutation, OncotypeDX
    score, other-cancer comorbidities, bra cup size and a fixed list of named
    comorbid diseases.

    Adds spans to ``doc.spans[spans_key]`` (default ``"patient_info"``), each
    with two extensions:

    - ``span._.source``: which field matched (``"MENOPAUSE"``, ``"RECIDIVE"``,
      ``"RESPONSE"``, ``"MUTATION"``, ``"ONCOTYPE"``, ``"CANCER_COMORBIDITY"``,
      ``"BRA_CUP"`` or ``"NAMED_DISEASE"``)
    - ``span._.patient_value``: the normalised value (type depends on
      ``source`` — see each ``_normalize_*`` function), or ``None`` if the
      nearby detail could not be interpreted. For ``NAMED_DISEASE``, use
      ``span.text`` directly (the matched disease name).

    Negation / hedging is intentionally not handled here — compose
    ``eds.negation`` / ``eds.hypothesis`` on top (see the package README).

    Known simplification (v1): ``Genetic_mutation`` only distinguishes BRCA
    vs. Other (matching the original code's granularity); the assay/technique
    mentions (NGS, Archer...) are not yet captured as separate fields.
    """

    def __init__(
        self,
        nlp: Optional[PipelineProtocol],
        name: str = "patient_info",
        *,
        spans_key: str = "patient_info",
    ):
        self.spans_key = spans_key
        # One matcher per source (own label), not one shared instance — see
        # breast_cancer.biomarkers for why (spaCy's Span extension storage
        # is keyed by character position; two same-labelled spans on the
        # identical text range would silently overwrite each other's
        # `_.source`/`_.patient_value`). `include_assigned=True` extends
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
        if not Span.has_extension("patient_value"):
            Span.set_extension("patient_value", default=None)

    def __call__(self, doc: Doc) -> Doc:
        for matcher in self._matchers:
            doc = matcher(doc)
        for span in doc.spans.get(self.spans_key, []):
            normalize = _NORMALIZERS.get(span._.source)
            span._.patient_value = normalize(span._.assigned or {}) if normalize else None
        return doc
