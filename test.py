import edsnlp
import edsnlp_breast_cancer  # noqa: F401 — registers the pipes

nlp = edsnlp.blank("eds")
nlp.add_pipe("eds.sentences")  # required by breast_cancer.tnm and .tumor_size

for name in ("biomarkers", "patient_info", "diagnosis", "treatment",
             "side_findings", "tnm", "tumor_size", "tumor_info"):
    nlp.add_pipe(f"breast_cancer.{name}")

# recommended: compose generic negation/hedging qualifiers on top instead of
# reimplementing "pas de"/"absence de"/"suspicion de" per field (see Design)
qualified_keys = ["biomarkers", "patient_info", "diagnosis", "treatment",
                  "side_findings", "tumor_info"]
nlp.add_pipe("eds.negation", config={"span_getter": qualified_keys})
nlp.add_pipe("eds.hypothesis", config={"span_getter": qualified_keys})

doc = nlp("RE 100%, RP negatif, HER2 3+, Ki67 20%. Pas de récidive.")
for span in doc.spans["biomarkers"]:
    print(span, span._.source, span._.biomarker_value)
for span in doc.spans["patient_info"]:
    print(span, span._.source, span._.patient_value, "negated:", span._.negation)