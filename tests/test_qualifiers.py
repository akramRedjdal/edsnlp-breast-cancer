"""Regression test for the long-document qualifier-drop workaround.

See edsnlp_breast_cancer/qualifiers.py docstring: eds.negation/eds.hypothesis
can silently drop some entities (extension stays None) when run on the whole
document at once, on real multi-paragraph clinical notes. This is not
reproducible on short single-sentence text (already covered by
test_patient_info.py's negation spot-checks) — it requires enough preceding
text/sentences, which is why this test builds a long synthetic note instead
of a short string.
"""
import os

import edsnlp

from edsnlp_breast_cancer.qualifiers import apply_qualifiers_by_sentence

# This is the real excerpt that reproduced the drop during manual
# investigation (a short synthetic filler-sentence text was tried first and
# did NOT reproduce it — the trigger is specific to real note structure, not
# just raw sentence count). Kept verbatim rather than re-guessed.
_FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "long_note.txt")
with open(_FIXTURE_PATH, encoding="utf-8") as _f:
    _LONG_NOTE = _f.read()


def _nlp_with_qualifiers():
    nlp = edsnlp.blank("eds")
    nlp.add_pipe("eds.sentences")
    nlp.add_pipe("breast_cancer.biomarkers")
    nlp.add_pipe("breast_cancer.patient_info")
    neg = nlp.add_pipe("eds.negation", config={"span_getter": ["biomarkers", "patient_info"]})
    hyp = nlp.add_pipe("eds.hypothesis", config={"span_getter": ["biomarkers", "patient_info"]})
    return nlp, neg, hyp


def test_whole_document_can_drop_entities():
    """Documents the failure mode this workaround exists for (not a bug in
    our pipes — see module docstring). If EDS-NLP fixes this upstream, this
    assertion may start failing; that would be good news, not a regression."""
    nlp, neg, hyp = _nlp_with_qualifiers()
    doc = nlp(_LONG_NOTE)
    # run negation the "naive" way (whole doc, as eds.negation.process does
    # internally) to show the gap — note this is DIFFERENT from just calling
    # nlp(text), which already ran it once via add_pipe; process() again here
    # is idempotent-ish for inspection purposes (re-derives the same result).
    results = neg.process(doc)
    processed_starts = {er.ent.start_char for er in results.ents}
    all_starts = {s.start_char for s in doc.spans["biomarkers"]}
    assert not all_starts.issubset(processed_starts), (
        "if this now passes, eds.negation's whole-document drop bug seems "
        "fixed upstream — the per-sentence workaround may no longer be needed"
    )


def test_apply_qualifiers_by_sentence_fixes_the_drop():
    nlp, neg, hyp = _nlp_with_qualifiers()
    doc = nlp(_LONG_NOTE)
    apply_qualifiers_by_sentence(doc, [neg, hyp])

    biomarker_spans = doc.spans["biomarkers"]
    assert len(biomarker_spans) > 0
    for span in biomarker_spans:
        assert span._.negation is not None, f"{span.text!r} still has negation=None"
        assert span._.hypothesis is not None

    patient_info_spans = doc.spans["patient_info"]
    recidive = [s for s in patient_info_spans if s._.source == "RECIDIVE"]
    assert recidive, "expected a RECIDIVE span"
    assert recidive[0]._.negation is True


def test_requires_sentence_boundaries():
    # deliberately no eds.sentences in this pipeline, and no qualifier pipe
    # either (eds.negation.__call__ would itself require sentence boundaries
    # and run automatically via add_pipe, which would mask what we want to
    # test here: our OWN guard clause, checked before touching any qualifier).
    nlp = edsnlp.blank("eds")
    nlp.add_pipe("breast_cancer.biomarkers")
    doc = nlp("RE 90%.")
    try:
        apply_qualifiers_by_sentence(doc, [])
        assert False, "expected ValueError without eds.sentences"
    except ValueError:
        pass
