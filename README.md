# edsnlp-breast-cancer

[EDS-NLP](https://aphp.github.io/edsnlp/) pipes for extracting structured data
from breast cancer clinical notes (tumour board reports / FRCP): TNM staging,
tumour size, biomarkers, histology, treatments, diagnostic procedures, and
patient-level facts.

This is a clean-room port of domain-specific regex rules — developed and
refined against a real hospital corpus — into the EDS-NLP pipe architecture,
so they compose with the rest of the EDS-NLP ecosystem (`eds.negation`,
`eds.family`, `eds.sections`...) instead of living as standalone scripts.

## Status

8 pipes implemented and tested (55 tests, all passing):

| Pipe | Extracts | Spans key |
|---|---|---|
| `breast_cancer.biomarkers` | ER, PR, HER2, Ki67, FISH | `biomarkers` |
| `breast_cancer.patient_info` | Menopausal status, genetic mutation (BRCA/Other), OncotypeDX score, prior relapse, response to neoadjuvant therapy, other-cancer comorbidity, bra cup size, named comorbid diseases | `patient_info` |
| `breast_cancer.diagnosis` | Biopsy (+ axillary/macro/micro subtype), screening, cytoponction (+ result), ultrasound, MRI (breast-only), mammography, PET-scan, clinical exam | `diagnosis` |
| `breast_cancer.treatment` | Surgery (mastectomy/conservative/oncoplasty/annexectomy/reconstruction/axillary dissection/sentinel node/re-excision/unspecified), chemotherapy & endocrine therapy (± neoadjuvant/adjuvant), anti-HER2, radiotherapy (± site), immunotherapy | `treatment` |
| `breast_cancer.side_findings` | BIRADS classification, lymph node involvement (clinical vs. pathologically-confirmed metastatic) | `side_findings` |
| `breast_cancer.tnm` | Full TNM staging codes (T/N/M prefix, code, suffixes, stage, R/G/L/V/Pn/serum) | `tnm` |
| `breast_cancer.tumor_size` | Every 1D/2D/3D size measurement (mm), tagged tumor/node/excluded (clock-position, nipple- or margin-distance false positives) | `tumor_size` |
| `breast_cancer.tumor_info` | Histologic type, SBR/Elston-Ellis invasive grade, in-situ (DCIS) grade, tumour site/quadrant, associated in-situ component, widespread microcalcifications, lymphovascular embolus (± type), surgical margin status | `tumor_info` |

## Install

```bash
pip install -e ".[test]"
```

## Usage

```python
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
```

**On real (long) notes**, apply the qualifiers per sentence instead of on the
whole document at once — see "Known limitations" below for why:

```python
from edsnlp_breast_cancer.qualifiers import apply_qualifiers_by_sentence

doc = nlp(a_long_multi_paragraph_note)
apply_qualifiers_by_sentence(doc, [nlp.get_pipe("eds.negation"), nlp.get_pipe("eds.hypothesis")])
```

## Design

Each pipe follows the same layout as EDS-NLP's own pipes
(`pipes/<name>/{<name>.py, patterns.py, factory.py}`), and is registered
under the `edsnlp_factories` entry-point namespace so it is auto-discovered
by `nlp.add_pipe("breast_cancer.xxx")` once the package is installed —
no explicit import required.

**Anchor + assign, not monolithic regex.** Most pipes are thin wrappers
composing `eds.contextual_matcher` (anchor + context window + capture group)
rather than reimplementing context-window scanning by hand. Domain-specific
normalisation (e.g. mapping a raw matched string to a `Her2IHC0`..`Her2IHC3Plus`
value) is added on top, since `contextual_matcher` only returns raw matched
text. `breast_cancer.tnm` and `breast_cancer.tumor_size` are the exception:
they wrap purpose-built, vendored parsers (`_tnm_stager.py`,
`_size_finder.py`) directly, since those are already their own structured
engines rather than a simple anchor+value pattern.

**Negation is not reimplemented per field.** Here, each pipe only detects the *mention* and any
*categorical* detail (which biomarker value, which gene, which subtype...);
generic negation/hedging is left to `eds.negation`/`eds.hypothesis` composed
on top, pointed at the relevant `spans_key`s (see Usage). Domain-specific ANTONYM vocabulary that a generic negation
qualifier has no way to know about ("indemne", "libre", "réactionnelle" =
clear/negative; "envahie", "atteinte" = positive) is kept explicit in each
pipe's own `assign` patterns instead.


## Known limitations

- **`eds.negation`/`eds.hypothesis` can silently drop entities on long
  documents.** These qualifiers compute sentence-like "boundaries" from
  termination cues and match each entity to one via an internal
  consume/second-chance mechanism. On short text (our own test suite, one
  or two sentences per test) this works perfectly. On a real multi-paragraph
  clinical note, we observed some entities simply never appearing in the
  qualifier's results — not set to "not negated", left at the extension's
  default `None` — while neighbouring entities in the very same sentence
  were qualified correctly. Confirmed by calling
  `qualifier.process(doc).ents` directly: on an 8-paragraph synthetic note
  with 9 biomarker mentions, only 2 got a result when run on the whole
  document; running the exact same qualifier **per sentence** instead
  qualified all 9/9. Since real clinical notes in this project are long by
  nature (not a corner case), don't call `eds.negation`/`eds.hypothesis` on
  the whole document — use `edsnlp_breast_cancer.qualifiers
  .apply_qualifiers_by_sentence()` instead (see Usage above), and treat a
  remaining `None` on `span._.negation`/`span._.hypothesis` as "unknown",
  never as "not negated". This looks like an EDS-NLP-internal behaviour
  (root cause not fully diagnosed — the drop happens inside the qualifier's
  own boundary/consume logic, not in anything this package controls), worth
  reporting upstream; not something we've patched here.
- **Site ambiguity in `tumor_info`'s `INVASIVE_OTHER`**: the generic
  "carcinome"/"adénocarcinome" + invasive-subtype anchor has no breast-site
  filter, so it can also match a carcinoma mention from unrelated patient
  history (e.g. a prior bladder/urothelial carcinoma). Validated against a
  40-patient sample: acceptable trade-off for coverage, but a real residual
  risk worth knowing about before relying on it for cohort-level statistics.
- **`breast_cancer.tnm`'s T→N connector** was widened to skip up to 2 free
  words between T and N codes (e.g. "T2 multifocal N+"), and the T-suffix
  list now also accepts bare `mi` and generic parenthesized descriptors
  (e.g. "Tis(DCIS)") — found and fixed via a 40-patient old-vs-new
  comparison. `get_suffixes` (inherited from the original code) does plain
  substring search for suffix letters, so a parenthesized descriptor
  containing e.g. "c" or "d" can spuriously appear in `t_suffixes`/
  `n_suffixes` — pre-existing quirk, not introduced by this port.
- **Genetic mutation** only distinguishes BRCA vs. Other (matching the
  original code's granularity, not a full gene panel).
- Several categories only exist in this package and were never wired into
  the source project's final DESIREE CSV output (treatment, diagnosis,
  mutation, oncotype, relapse, embolus, margin status, tumour
  site/quadrant) — the extraction logic existed but was dropped before the
  final mapping step. This package surfaces them; using them downstream is
  up to the consuming project.


## Tests

```bash
pytest
```

## Citing

This package builds on [EDS-NLP](https://aphp.github.io/edsnlp/latest/):

```bibtex
@misc{edsnlp,
  author = {Wajsburt, Perceval and Petit-Jean, Thomas and Dura, Basile and Cohen, Ariel and Jean, Charline and Bey, Romain},
  doi    = {10.5281/zenodo.6424993},
  title  = {EDS-NLP: efficient information extraction from French clinical notes},
  url    = {https://aphp.github.io/edsnlp}
}
```

The extraction rules ported here were originally developed for, and are
described in:

> Redjdal A, Novikava N, Kempf E, Bouaud J, Seroussi B. Leveraging Rule-Based
> NLP to Translate Textual Reports as Structured Inputs Automatically
> Processed by a Clinical Decision Support System. Stud Health Technol
> Inform. 2024 Aug 22;316:1861-1865. doi: 10.3233/SHTI240794. PMID: 39176854.

Further background: [PhD thesis (HAL)](https://theses.hal.science/THESES-SU/tel-04330919v1).

## License

BSD-3-Clause — same license as EDS-NLP, to keep the door open for upstream
contribution.
