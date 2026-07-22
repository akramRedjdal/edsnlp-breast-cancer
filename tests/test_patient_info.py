def _by_source(doc):
    out = {}
    for span in doc.spans["patient_info"]:
        out.setdefault(span._.source, []).append((span.text, span._.patient_value))
    return out


def test_menopause_variants(nlp_patient_info):
    for text, expected in [
        ("patiente ménopausée depuis 10 ans", "Postmenopausal"),
        ("patiente non ménopausée", "Premenopausal"),
        ("patiente péri-ménopausée", "Perimenopausal"),
    ]:
        doc = nlp_patient_info(text)
        v = _by_source(doc)
        assert v["MENOPAUSE"][0][1] == expected, f"{text!r} -> {v['MENOPAUSE']}"


def test_recidive_detected(nlp_patient_info):
    doc = nlp_patient_info("récidive locale du sein droit")
    v = _by_source(doc)
    assert v["RECIDIVE"][0][1] is True


def test_recidive_word_forms(nlp_patient_info):
    # stem-based anchor must catch inflected forms, not just the bare noun
    for text in ["tumeur récidivante", "cancer non récidivant"]:
        doc = nlp_patient_info(text)
        assert "RECIDIVE" in _by_source(doc), f"{text!r} -> no RECIDIVE span"


def test_response_degree(nlp_patient_info):
    for text, expected in [
        ("bonne réponse partielle clinique", "PartialResponse"),
        ("réponse complète", "CompleteResponse"),
        ("réponse modérée", "StableDisease"),
    ]:
        doc = nlp_patient_info(text)
        v = _by_source(doc)
        assert v["RESPONSE"][0][1] == expected, f"{text!r} -> {v.get('RESPONSE')}"


def test_mutation_brca_vs_other(nlp_patient_info):
    doc = nlp_patient_info("mutation BRCA1 identifiee")
    assert _by_source(doc)["MUTATION"][0][1] == "BRCA"

    doc2 = nlp_patient_info("mutation PALB2 retrouvee")
    assert _by_source(doc2)["MUTATION"][0][1] == "Other"


def test_oncotype_score(nlp_patient_info):
    doc = nlp_patient_info("oncotype DX score 25")
    assert _by_source(doc)["ONCOTYPE"][0][1] == 25


def test_cancer_comorbidity_requires_site(nlp_patient_info):
    # bare "cancer" with no site should not produce an entity (assign required)
    doc = nlp_patient_info("antecedent de cancer non precise")
    assert "CANCER_COMORBIDITY" not in _by_source(doc)

    doc2 = nlp_patient_info("cancer du poumon dans les antecedents")
    v = _by_source(doc2)
    assert v["CANCER_COMORBIDITY"][0][1] == "OtherCancer"

    doc3 = nlp_patient_info("cancer du sein controlateral")
    assert _by_source(doc3)["CANCER_COMORBIDITY"][0][1] == "BreastCancer"


def test_bra_cup(nlp_patient_info):
    doc = nlp_patient_info("bonnet C")
    assert _by_source(doc)["BRA_CUP"][0][1] == "C"


def test_named_disease(nlp_patient_info):
    doc = nlp_patient_info("antecedent d'hypertension arterielle et de diabete")
    v = _by_source(doc)
    assert any("hypertension" in text.lower() for text, _ in v["NAMED_DISEASE"])
