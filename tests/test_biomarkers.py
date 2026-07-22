def _values(doc):
    return {span._.source: span._.biomarker_value for span in doc.spans["biomarkers"]}


def test_er_pr_basic(blank_nlp):
    blank_nlp.add_pipe("breast_cancer.biomarkers")
    doc = blank_nlp("RE 100%, RP negatif")
    v = _values(doc)
    assert v["ER"] == 100
    assert v["PR"] == 0


def test_her2_scores(blank_nlp):
    blank_nlp.add_pipe("breast_cancer.biomarkers")
    for text, expected in [
        ("HER2 3+", "Her2IHC3Plus"),
        ("HER2 0", "Her2IHC0"),
        ("HER2 negatif", "Her2IHC0"),
        ("HER2 amplifie", "Her2IHC3Plus"),
        ("HER2 non amplifie", "Her2IHC0"),
    ]:
        doc = blank_nlp(text)
        v = _values(doc)
        assert v.get("HER2") == expected, f"{text!r} -> {v.get('HER2')!r}, expected {expected!r}"


def test_ki67(blank_nlp):
    blank_nlp.add_pipe("breast_cancer.biomarkers")
    doc = blank_nlp("Ki67 20%")
    assert _values(doc)["KI67"] == 20


def test_fish(blank_nlp):
    blank_nlp.add_pipe("breast_cancer.biomarkers")
    for text, expected in [
        ("FISH positif", "positive"),
        ("FISH negatif", "negative"),
        ("FISH non amplifie", "negative"),
        ("FISH amplifie", "positive"),
    ]:
        doc = blank_nlp(text)
        assert _values(doc)["FISH"] == expected


def test_year_not_read_as_er_value(blank_nlp):
    """Regression test for the original bug: 'RE 2019' being read as ER=2019
    (the anchor mention 're' immediately followed by a 4-digit year, e.g. a
    dictation/exam date, must not produce a fake percentage value)."""
    blank_nlp.add_pipe("breast_cancer.biomarkers")
    doc = blank_nlp("re 2019")
    # exclude window drops the whole mention when a year sits right next to it
    assert "ER" not in _values(doc)


def test_er_value_far_from_date_still_extracted(blank_nlp):
    """A date elsewhere in the sentence (outside the exclude window) should
    not prevent a genuine nearby value from being read."""
    blank_nlp.add_pipe("breast_cancer.biomarkers")
    doc = blank_nlp("RE 90% mesure realisee bien avant la consultation de 2019")
    v = _values(doc)
    assert v.get("ER") == 90


def test_multiple_biomarkers_in_one_note(blank_nlp):
    blank_nlp.add_pipe("breast_cancer.biomarkers")
    doc = blank_nlp("RE 80%, RP 60%, HER2 1+, Ki67 15%, FISH negatif")
    v = _values(doc)
    assert v == {
        "ER": 80,
        "PR": 60,
        "HER2": "Her2IHC1Plus",
        "KI67": 15,
        "FISH": "negative",
    }
