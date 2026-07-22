def test_basic_tnm(nlp_tnm):
    doc = nlp_tnm("Classification pT2 N1a M0.")
    spans = doc.spans["tnm"]
    assert len(spans) == 1
    tnm = spans[0]._.tnm
    assert tnm["t_prefix"] == "p"
    assert tnm["t_code"] == "2"
    assert tnm["n_code"] == "1"
    assert tnm["n_suffixes"] == ["a"]
    assert tnm["m_code"] == "0"


def test_span_offsets_are_doc_relative(nlp_tnm):
    text = "Antecedents sans particularite. Classification pT2 N1a M0 retenue."
    doc = nlp_tnm(text)
    span = doc.spans["tnm"][0]
    # the span's own text (sliced via doc-relative offsets) must match
    # what the parser actually found, not be shifted by the first sentence
    assert "pT2" in span.text
    assert text[span.start_char:span.end_char] == span.text


def test_t_only_when_no_n_present(nlp_tnm):
    doc = nlp_tnm("Tumeur classee cT1c.")
    spans = doc.spans["tnm"]
    assert len(spans) == 1
    assert spans[0]._.tnm["t_code"] == "1"
    assert spans[0]._.tnm["t_suffixes"] == ["c"]
    assert spans[0]._.tnm["n_code"] is None


def test_stage_and_multiple_sentences(nlp_tnm):
    text = "Premier examen: cT1 N0 M0. Bilan ulterieur: ypT2 N1 M0 (stage IIB)."
    doc = nlp_tnm(text)
    spans = doc.spans["tnm"]
    assert len(spans) == 2
    second = spans[1]._.tnm
    assert second["t_prefix"] == "yp"
    assert second["stage_number"] == "2"
    assert second["stage_letter"] == "b"
