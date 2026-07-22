"""Workaround for a long-document limitation of EDS-NLP's qualifier pipes.

``eds.negation``/``eds.hypothesis`` (and likely other qualifiers built on the
same base class) compute sentence-like "boundaries" from termination cues
and then match each entity to a boundary via an internal consume/second-chance
mechanism. On short text this works as expected, but on real multi-paragraph
clinical notes we observed entities being silently DROPPED from processing
entirely — not set to "not negated", just never visited, leaving the
extension at its default ``None``. Confirmed via direct inspection of
``qualifier.process(doc).ents``: on an 8-paragraph, ~9-biomarker test note,
only 2/9 entities got a negation result when run on the whole document; all
9/9 got one when the SAME qualifier was instead run per sentence.

Since real clinical notes in this project are long by nature (not a corner
case), this module makes per-sentence qualifier application the easy,
default path instead of leaving every caller to rediscover the workaround.
"""
from typing import Iterable

from spacy.tokens import Doc

# results-object attribute name holding the boolean value, per qualifier
# factory name — extend this mapping if you compose other eds.* qualifiers
# (eds.family, eds.reported_speech, eds.history...) through this helper.
_RESULT_ATTR = {
    "eds.negation": "negation",
    "eds.hypothesis": "hypothesis",
    "eds.family": "family",
    "eds.history": "history",
    "eds.reported_speech": "reported_speech",
}


def apply_qualifiers_by_sentence(doc: Doc, qualifier_pipes: Iterable) -> Doc:
    """Apply one or more qualifier pipes (e.g. ``nlp.get_pipe("eds.negation")``)
    sentence-by-sentence instead of on the whole document at once, working
    around the entity-dropping issue described in this module's docstring.

    Requires sentence boundaries (``eds.sentences``) to already be set on
    ``doc``. Call this AFTER your NER pipes have populated their spans, and
    instead of adding the qualifier pipes via ``nlp.add_pipe`` (or in
    addition to adding them — ``add_pipe`` still works for config validation
    at pipeline-build time; this function does the actual span-qualifying).

    Parameters
    ----------
    doc : Doc
        The document to qualify, with sentence boundaries already set.
    qualifier_pipes : Iterable
        The qualifier pipe instances to apply (e.g. results of
        ``nlp.get_pipe("eds.negation")``).

    Returns
    -------
    Doc
        The same document, with qualifier extensions set on every entity
        returned by each pipe's configured ``span_getter``.

    Examples
    --------
    ```python
    import edsnlp
    import edsnlp_breast_cancer
    from edsnlp_breast_cancer.qualifiers import apply_qualifiers_by_sentence

    nlp = edsnlp.blank("eds")
    nlp.add_pipe("eds.sentences")
    nlp.add_pipe("breast_cancer.biomarkers")
    negation = nlp.add_pipe(
        "eds.negation", config={"span_getter": ["biomarkers"]}
    )

    doc = nlp(long_clinical_note)
    apply_qualifiers_by_sentence(doc, [negation])
    ```
    """
    if not doc.has_annotation("SENT_START"):
        raise ValueError(
            "apply_qualifiers_by_sentence requires sentence boundaries — "
            "add eds.sentences to the pipeline before calling this."
        )

    for qualifier in qualifier_pipes:
        factory_name = getattr(qualifier, "name", None) or ""
        attr = None
        for key, value in _RESULT_ATTR.items():
            if key in factory_name or key.split(".")[-1] in factory_name:
                attr = value
                break
        if attr is None:
            raise ValueError(
                f"Don't know the result attribute for qualifier {qualifier!r} — "
                f"add it to edsnlp_breast_cancer.qualifiers._RESULT_ATTR."
            )
        for sent in doc.sents:
            results = qualifier.process(sent)
            for ent_result in results.ents:
                current = getattr(ent_result.ent._, attr)
                setattr(ent_result.ent._, attr, current or getattr(ent_result, attr))

    return doc
