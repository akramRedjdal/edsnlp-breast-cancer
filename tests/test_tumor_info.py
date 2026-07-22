def _by_source(doc):
    out = {}
    for span in doc.spans["tumor_info"]:
        out.setdefault(span._.source, []).append((span.text, span._.tumor_info_value))
    return out


def test_histologic_types(nlp_tumor_info):
    for text, source, expected in [
        ("carcinome canalaire infiltrant du sein droit", "INVASIVE_DUCTAL", "InvasiveDuctalBreastCarcinoma"),
        ("carcinome lobulaire infiltrant", "INVASIVE_LOBULAR", "InvasiveLobularBreastCarcinoma"),
        ("CCIS pur", "DCIS", "DCISBreastCarcinoma"),
        ("CLIS associe", "LOBULAR_IS", "LobularISBreastCarcinoma"),
        ("maladie de Paget du mamelon", "PAGET_DISEASE", "PagetDisease"),
        ("sarcome du sein", "BREAST_SARCOMA", "BreastSarcoma"),
        ("hyperplasie canalaire", "NON_CANCER", "NonCancer"),
    ]:
        doc = nlp_tumor_info(text)
        v = _by_source(doc)
        assert source in v, f"{text!r} -> no {source}, got {list(v)}"
        assert v[source][0][1] == expected


def test_grade_inv(nlp_tumor_info):
    for text, expected in [
        ("SBR grade 2", "Grade2"),
        ("grade histopronostique III", "Grade3"),
        ("Elston et Ellis: 1", "Grade1"),
    ]:
        doc = nlp_tumor_info(text)
        v = _by_source(doc)
        assert v["TUMOR_GRADE_INV"][0][1] == expected, f"{text!r} -> {v.get('TUMOR_GRADE_INV')}"


def test_grade_insitu(nlp_tumor_info):
    doc = nlp_tumor_info("DCIS de haut grade")
    assert _by_source(doc)["GRADE_INSITU_HAUT"][0][1] == "Haut_Grade"

    doc2 = nlp_tumor_info("composante in situ de bas grade")
    assert _by_source(doc2)["GRADE_INSITU_BAS"][0][1] == "Bas_Grade"


def test_tumor_site_quadrant(nlp_tumor_info):
    doc = nlp_tumor_info("masse du quadrant supero-externe")
    assert _by_source(doc)["QUADRANT_UPPER_OUTER"][0][1] == "upper_outer_quadrant"

    doc2 = nlp_tumor_info("lesion du PAM")
    assert _by_source(doc2)["AXILLARY_REGION"][0][1] == "axillary_region"


def test_associated_insitu_domain_antonym(nlp_tumor_info):
    doc = nlp_tumor_info("composante in situ associee etendue")
    assert _by_source(doc)["ASSOCIATED_INSITU"][0][1] is True


def test_microcalcifications_domain_antonym(nlp_tumor_info):
    doc = nlp_tumor_info("microcalcifications indemnes")
    assert _by_source(doc)["WIDESPREAD_MICROCALCIFICATIONS"][0][1] is False

    doc2 = nlp_tumor_info("foyer de calcifications suspectes")
    assert _by_source(doc2)["WIDESPREAD_MICROCALCIFICATIONS"][0][1] is True


def test_embole_type(nlp_tumor_info):
    doc = nlp_tumor_info("presence d'emboles vasculaires sanguins")
    assert _by_source(doc)["PRESENCE_EMBOLE"][0][1] == "Sanguins"

    doc2 = nlp_tumor_info("emboles lymphatiques nombreux")
    assert _by_source(doc2)["PRESENCE_EMBOLE"][0][1] == "Lymphatiques"


def test_margin_status(nlp_tumor_info):
    doc = nlp_tumor_info("berges saines")
    assert _by_source(doc)["MARGIN_STATUS"][0][1] is True

    doc2 = nlp_tumor_info("marge envahie")
    assert _by_source(doc2)["MARGIN_STATUS"][0][1] is False
