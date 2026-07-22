"""Regression test: apply_qualifiers_by_sentence's _RESULT_ATTR mapping also
covers eds.family / eds.history / eds.reported_speech, not just
eds.negation/eds.hypothesis (added when a downstream project needed the
dual antecedent/family signal — section-name-based AND qualifier-based)."""
import edsnlp

from edsnlp_breast_cancer.qualifiers import apply_qualifiers_by_sentence


def test_family_and_history_qualifiers_supported():
    nlp = edsnlp.blank("eds")
    nlp.add_pipe("eds.sentences")
    nlp.add_pipe("breast_cancer.patient_info")
    fam = nlp.add_pipe("eds.family", config={"span_getter": ["patient_info"]})
    hist = nlp.add_pipe("eds.history", config={"span_getter": ["patient_info"]})

    doc = nlp("Antecedent familial de cancer du poumon chez la mere.")
    apply_qualifiers_by_sentence(doc, [fam, hist])

    spans = doc.spans["patient_info"]
    assert spans
    for span in spans:
        assert span._.family is not None
        assert span._.history is not None
