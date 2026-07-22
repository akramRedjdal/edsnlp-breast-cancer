def test_basic_measurement_mm(nlp_tumor_size):
    doc = nlp_tumor_size("Masse tumorale de 23 x 18 mm du sein droit.")
    spans = doc.spans["tumor_size"]
    assert len(spans) == 1
    s = spans[0]
    assert s._.size["minValue"] == 18.0
    assert s._.size["maxValue"] == 23.0
    assert s._.size["units"] == "MILLIMETERS"
    assert s._.size_context == "tumor"
    assert s._.size_excluded is False


def test_cm_converted_to_mm(nlp_tumor_size):
    doc = nlp_tumor_size("Nodule mesurant 2.3 cm dans son grand axe.")
    s = doc.spans["tumor_size"][0]
    assert s._.size["maxValue"] == 23.0
    assert s._.size["units"] == "MILLIMETERS"


def test_node_context(nlp_tumor_size):
    doc = nlp_tumor_size("Ganglion axillaire de 15 mm suspect.")
    s = doc.spans["tumor_size"][0]
    assert s._.size_context == "node"


def test_clock_position_excluded(nlp_tumor_size):
    doc = nlp_tumor_size("Lesion situee a 4h a 3 cm du mamelon.")
    spans = doc.spans["tumor_size"]
    # both the clock-position "4h" (if captured as a measurement) and the
    # nipple-distance "3 cm du mamelon" must be flagged excluded
    assert len(spans) >= 1
    assert all(s._.size_excluded for s in spans), [
        (s.text, s._.size_excluded) for s in spans
    ]


def test_multiple_measurements_multiple_sentences(nlp_tumor_size):
    text = "Tumeur de 12 mm du sein gauche. Ganglion de 8 mm dans le creux axillaire."
    doc = nlp_tumor_size(text)
    spans = doc.spans["tumor_size"]
    assert len(spans) == 2
    contexts = {s._.size_context for s in spans}
    assert contexts == {"tumor", "node"}
