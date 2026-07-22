def _by_source(doc):
    out = {}
    for span in doc.spans["diagnosis"]:
        out.setdefault(span._.source, []).append((span.text, span._.diagnosis_value))
    return out


def test_biopsy_subtypes(nlp_diagnosis):
    for text, expected in [
        ("biopsie axillaire realisee", "AxillaryBiopsy"),
        ("macrobiopsie du sein droit", "MacroBiopsy"),
        ("microbiopsie echoguidee", "MicroBiopsy"),
    ]:
        doc = nlp_diagnosis(text)
        v = _by_source(doc)
        assert v["Biopsy"][0][1] == expected, f"{text!r} -> {v.get('Biopsy')}"


def test_screening(nlp_diagnosis):
    doc = nlp_diagnosis("dans le cadre du depistage organise")
    assert "Screening" in _by_source(doc)


def test_cytoponction_result(nlp_diagnosis):
    doc = nlp_diagnosis("cytoponction ganglionnaire negative")
    assert _by_source(doc)["Cytoponction"][0][1] == "Negative"

    doc2 = nlp_diagnosis("cytoponction axillaire positive")
    assert _by_source(doc2)["Cytoponction"][0][1] == "Positive"


def test_ultrasound(nlp_diagnosis):
    doc = nlp_diagnosis("echographie mammaire bilaterale")
    assert "Ultra_sound" in _by_source(doc)


def test_mri_breast_kept_nonbreast_excluded(nlp_diagnosis):
    doc = nlp_diagnosis("IRM mammaire realisee ce jour")
    assert "MRI" in _by_source(doc)

    doc2 = nlp_diagnosis("IRM cerebrale sans anomalie")
    assert "MRI" not in _by_source(doc2)


def test_mammography(nlp_diagnosis):
    doc = nlp_diagnosis("mammographie de depistage")
    assert "Mammography" in _by_source(doc)


def test_pet_scan(nlp_diagnosis):
    doc = nlp_diagnosis("pet-scan au fdg realise")
    assert "Pet_scan" in _by_source(doc)


def test_clinical_examination(nlp_diagnosis):
    doc = nlp_diagnosis("examen clinique mammaire normal")
    assert "Clinical_examination" in _by_source(doc)
