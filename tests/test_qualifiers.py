"""Regression test for the long-document qualifier-drop workaround.

See edsnlp_breast_cancer/qualifiers.py docstring: eds.negation/eds.hypothesis
can silently drop some entities (extension stays None) when run on the whole
document at once, on real multi-paragraph clinical notes. This is not
reproducible on short single-sentence text (already covered by
test_patient_info.py's negation spot-checks) — it requires enough preceding
text/sentences, which is why this test builds a long synthetic note instead
of a short string.
"""
import edsnlp

from edsnlp_breast_cancer.qualifiers import apply_qualifiers_by_sentence

# Synthetic (fabricated, no real patient data) multi-paragraph note, long
# enough to reproduce the drop during manual investigation (a short
# filler-sentence text was tried first and did NOT reproduce it — the
# trigger is specific to real note structure, not just raw sentence count).
# Kept inline (not a separate .txt file) by policy: no text-file fixtures
# in this repo, even synthetic ones.
_LONG_NOTE = (
    "Antécédents : patiente ménopausée depuis 8 ans. Antécédent de cancer du "
    "poumon traité. Suivie pour hypertension artérielle et diabète. Bonnet C. "
    "Pas de mutation BRCA connue dans la famille.\n\n"
    "Bilan initial : mammographie et échographie mammaire bilatérale réalisées "
    "le 12/01/2023. Masse tumorale de 23 x 18 mm du quadrant supero-externe du "
    "sein droit, Bi-rads 5. Ganglion axillaire droit de 15 mm suspect, "
    "Bi-rads 4c. IRM mammaire complémentaire confirmant la lésion. Examen "
    "clinique retrouve une masse palpable. PET-scan au FDG montrant un "
    "hypermétabolisme axillaire.\n\n"
    "Microbiopsie du 15/01/2023 : carcinome canalaire infiltrant, grade "
    "histopronostique 2, SBR grade 2. RE 90%, RP 60%, HER2 score 0, Ki67 20%. "
    "Cytoponction ganglionnaire axillaire positive, en faveur d'une métastase "
    "ganglionnaire axillaire. Composante in situ associée étendue. Présence "
    "de microcalcifications associées. Emboles vasculaires sanguins "
    "présents.\n\n"
    "Bilan d'extension : classification cTNM : cT2 N1a M0. Oncotype DX score "
    "22. Réponse partielle après la première cure. Pas de récidive à ce "
    "jour.\n\n"
    "Proposition thérapeutique : chimiothérapie néoadjuvante puis "
    "tumorectomie avec ganglion sentinelle et curage axillaire. "
    "Radiothérapie du lit tumoral prévue. Hormonothérapie adjuvante à "
    "discuter selon les récepteurs. Traitement anti-HER2 non indiqué "
    "(HER2 négatif).\n"
)


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
