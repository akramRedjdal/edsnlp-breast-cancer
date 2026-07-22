def _by_source(doc):
    out = {}
    for span in doc.spans["side_findings"]:
        out.setdefault(span._.source, []).append((span.text, span._.side_finding_value))
    return out


def test_birads_grade(nlp_side_findings):
    for text, expected in [
        ("classe ACR 4b", "Birads4b"),
        ("BI-RADS 3", "Birads3"),
        ("acr 5", "Birads5"),
    ]:
        doc = nlp_side_findings(text)
        v = _by_source(doc)
        assert v["BIRADS"][0][1] == expected, f"{text!r} -> {v.get('BIRADS')}"


def test_node_metastasis(nlp_side_findings):
    doc = nlp_side_findings("ganglion axillaire metastatique confirme")
    assert _by_source(doc)["NODE_METASTASIS"][0][1] is True


def test_node_involvement_domain_antonyms(nlp_side_findings):
    doc = nlp_side_findings("ganglion axillaire indemne")
    assert _by_source(doc)["NODE_INVOLVEMENT"][0][1] is False

    doc2 = nlp_side_findings("adenopathie axillaire envahie")
    assert _by_source(doc2)["NODE_INVOLVEMENT"][0][1] is True


def test_node_involvement_bare_mention_defaults_true(nlp_side_findings):
    # generic negation ("pas de ganglion suspect") is deferred to
    # eds.negation (validated against real domain phrasings in
    # test_patient_info.py) — not this pipe's job. A bare mention with no
    # domain-antonym qualifier nearby defaults to True (presence detected).
    doc = nlp_side_findings("ganglion axillaire visualise")
    assert _by_source(doc)["NODE_INVOLVEMENT"][0][1] is True
