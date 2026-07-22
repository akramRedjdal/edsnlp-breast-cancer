def _by_source(doc):
    out = {}
    for span in doc.spans["treatment"]:
        out.setdefault(span._.source, []).append((span.text, span._.treatment_value))
    return out


def test_surgery_types_fr_and_en(nlp_treatment):
    for text, source, expected in [
        ("mastectomie totale realisee", "MASTECTOMY", "Mastectomy"),
        ("mastectomy performed", "MASTECTOMY", "Mastectomy"),
        ("tumorectomie du sein droit", "CONSERVATIVE_SURGERY", "Conservative_surgery"),
        ("tumorectomy of the right breast", "CONSERVATIVE_SURGERY", "Conservative_surgery"),
        ("oncoplastie realisee", "ONCOPLASTY", "Oncoplasty"),
        ("annexectomie bilaterale", "ANNEXECTOMY", "Annexectomy"),
        ("reconstruction mammaire immediate", "BREAST_RECONSTRUCTION", "Breast_reconstruction"),
        ("curage ganglionnaire axillaire", "AXILLARY_DISSECTION", "Axillary_dissection"),
        ("reprise de berges", "BREAST_REEXCISION", "BreastReExcision"),
        ("indication de chirurgie", "SURGERY_UNSPECIFIED", "Surgery"),
    ]:
        doc = nlp_treatment(text)
        v = _by_source(doc)
        assert source in v, f"{text!r} -> no {source} span, got {list(v)}"
        assert v[source][0][1] == expected, f"{text!r} -> {v[source]}"


def test_sentinel_node_vs_node_count(nlp_treatment):
    doc = nlp_treatment("ganglion sentinelle realise")
    v = _by_source(doc)
    assert v["SENTINEL_NODE"][0][1] == "Sentinel_lymph_node_Biopsy"

    # "3 ganglions non sentinelles" = a lymph-node count report, not the
    # sentinel-node procedure itself — must be excluded
    doc2 = nlp_treatment("3 ganglions non sentinelles envahis")
    assert "SENTINEL_NODE" not in _by_source(doc2)


def test_chemotherapy_phase(nlp_treatment):
    for text, expected in [
        ("chimiotherapie neoadjuvante", "Neoadjuvant_chemotherapy"),
        ("chimiotherapie adjuvante", "Adjuvant_chemotherapy"),
        ("chimiotherapie en cours", "chemotherapy"),
        # hyphenated accented spelling, very common in the real corpus —
        # regression test for a bug where the hyphen broke the néo-
        # alternatives and fell through to bare "adjuvante", dropping the
        # néo- prefix and misreading this as Adjuvant instead of Neoadjuvant
        ("Chimiothérapie néo-adjuvante", "Neoadjuvant_chemotherapy"),
    ]:
        doc = nlp_treatment(text)
        v = _by_source(doc)
        assert v["CHEMOTHERAPY"][0][1] == expected, f"{text!r} -> {v.get('CHEMOTHERAPY')}"


def test_endocrine_therapy_and_antihormonal_folded_in(nlp_treatment):
    doc = nlp_treatment("hormonotherapie adjuvante")
    assert _by_source(doc)["ENDOCRINE_THERAPY"][0][1] == "Adjuvant_endocrine_therapy"

    doc2 = nlp_treatment("traitement anti-hormonal en cours")
    assert "ENDOCRINE_THERAPY" in _by_source(doc2)


def test_anti_her2(nlp_treatment):
    doc = nlp_treatment("traitement anti-HER2 par trastuzumab")
    assert _by_source(doc)["ANTI_HER2"][0][1] == "Anti_HER2_therapy"


def test_radiotherapy_site(nlp_treatment):
    for text, expected in [
        ("radiotherapie du lit tumoral", "LitTumoral"),
        ("radiotherapie boost", "Boost"),
        ("radiotherapie de la paroi", "Paroi"),
        ("radiotherapie sans precision", "Radiotherapy"),
    ]:
        doc = nlp_treatment(text)
        v = _by_source(doc)
        assert v["RADIOTHERAPY"][0][1] == expected, f"{text!r} -> {v.get('RADIOTHERAPY')}"


def test_immunotherapy(nlp_treatment):
    doc = nlp_treatment("immunotherapie par pembrolizumab")
    assert _by_source(doc)["IMMUNOTHERAPY"][0][1] == "Immunotherapy"
