"""``breast_cancer.tnm`` pipeline component.

Wraps the vendored ``_tnm_stager`` module (see that file's docstring) as an
EDS-NLP pipe: runs the ORIGINAL, unmodified TNM regex/parsing logic per
sentence, and exposes each match as a spaCy ``Span`` with a ``tnm`` extension
holding the full parsed code (prefix/code/suffixes/stage/etc. for T, N, M,
plus R/G/L/V/Pn/serum/stage where present).

Unlike the other pipes in this package, this one is NOT a thin wrapper
around ``eds.contextual_matcher`` — the original module is already its own
purpose-built regex parser (named capture groups decoded into a structured
result), so it is wrapped directly rather than re-expressed as anchor+assign
patterns.
"""
import json
from typing import List, Optional

from spacy.tokens import Doc, Span

from edsnlp.core import PipelineProtocol
from edsnlp.pipes.base import BaseNERComponent, SpanSetterArg

from . import _tnm_stager as tnm_stager


class TnmMatcher(BaseNERComponent):
    """Extracts TNM staging codes (e.g. ``pT2 N1a M0``, ``ypT1c(m) N0(sn)``)
    from clinical text, per sentence.

    Adds spans to ``doc.spans[spans_key]`` (default ``"tnm"``), each with a
    ``span._.tnm`` dict holding every field the original parser decodes:
    ``t_prefix``, ``t_code``, ``t_certainty``, ``t_suffixes``, ``t_mult``,
    ``n_prefix``, ``n_code``, ``n_certainty``, ``n_suffixes``,
    ``n_regional_nodes_examined``, ``n_regional_nodes_involved``,
    ``m_prefix``, ``m_code``, ``m_certainty``, ``m_suffixes``,
    ``l_code``, ``g_code``, ``v_code``, ``pn_code``, ``serum_code``,
    ``r_codes``, ``r_suffixes``, ``r_locations``,
    ``stage_prefix``, ``stage_number``, ``stage_letter``. Fields not present
    in a given match are ``None``.

    Requires sentence boundaries (add ``eds.sentences`` before this pipe) —
    falls back to treating the whole document as one sentence otherwise,
    which is slower and more prone to a T from one sentence being
    accidentally combined with an N/M from an unrelated one.

    Examples
    --------
    ```python
    import edsnlp, edsnlp.pipes as eds
    import edsnlp_breast_cancer

    nlp = edsnlp.blank("eds")
    nlp.add_pipe("eds.sentences")
    nlp.add_pipe("breast_cancer.tnm")

    doc = nlp("Classification pT2 N1a M0.")
    span = doc.spans["tnm"][0]
    span._.tnm["t_code"], span._.tnm["n_code"], span._.tnm["m_code"]
    # ('2', '1', '0')
    ```
    """

    def __init__(
        self,
        nlp: Optional[PipelineProtocol],
        name: str = "tnm",
        *,
        spans_key: str = "tnm",
        span_setter: SpanSetterArg = None,
    ):
        self.spans_key = spans_key
        super().__init__(
            nlp=nlp,
            name=name,
            span_setter=span_setter or {"ents": False, spans_key: True},
        )

    def set_extensions(self) -> None:
        super().set_extensions()
        if not Span.has_extension("tnm"):
            Span.set_extension("tnm", default=None)

    def _sentences(self, doc: Doc):
        if doc.has_annotation("SENT_START"):
            return list(doc.sents)
        return [doc[:]]

    def __call__(self, doc: Doc) -> Doc:
        spans: List[Span] = []
        for sent in self._sentences(doc):
            json_string = tnm_stager.run(sent.text)
            for code_dict in json.loads(json_string):
                local_start = code_dict["start"]
                local_end = code_dict["end"]
                char_start = sent.start_char + local_start
                char_end = sent.start_char + local_end
                span = doc.char_span(char_start, char_end, alignment_mode="expand")
                if span is None:
                    continue
                span.label_ = "tnm"
                span._.tnm = code_dict
                spans.append(span)
        self.set_spans(doc, spans)
        return doc
