"""``breast_cancer.tumor_size`` pipeline component.

Wraps the vendored ``_size_finder`` module (see that file's docstring) — a
general-purpose 1D/2D/3D size-measurement parser (handles "23x18mm",
"2.3-4.5cm" ranges, lists, area/volume units, views) that already converts
everything to millimetres correctly. Note: in the original project this
module's ``run()`` was called but its own ``_to_json()`` normalisation step
was NEVER actually invoked downstream (a real gap — the raw regex match
list was re-processed by a separate, cruder function instead) — this pipe
fixes that by calling ``run()`` + ``_to_json()`` together as the module's
docstring always said to.

As with ``breast_cancer.tnm``, this is not a thin ``eds.contextual_matcher``
wrapper: the vendored parser is its own purpose-built engine.

Binding a given measurement to a *specific* lesion/side (the "which size
goes with which tumour" question) is deliberately NOT decided here — that
is a relation/aggregation concern for the consuming (project-specific)
pipeline. This pipe only extracts every plausible measurement and tags it
with a context hint (tumor/node/excluded) to make that downstream decision
easier.
"""
import json
from typing import List, Optional

from spacy.tokens import Doc, Span

from edsnlp.core import PipelineProtocol
from edsnlp.pipes.base import BaseNERComponent, SpanSetterArg

from . import _size_finder as size_finder
from . import context as size_context


class TumorSizeMatcher(BaseNERComponent):
    """Extracts size measurements (1D/2D/3D, ranges, lists, area/volume)
    from clinical text, per sentence, normalised to millimetres.

    Adds spans to ``doc.spans[spans_key]`` (default ``"tumor_size"``), each
    with extensions:

    - ``span._.size``: the full parsed measurement dict (``units``,
      ``condition``, ``x``/``y``/``z`` or ``values``, ``minValue``,
      ``maxValue`` — see ``_size_finder``'s module docstring)
    - ``span._.size_context``: ``"tumor"``, ``"node"``, or ``None``
      (ambiguous — no nearby keyword decided it)
    - ``span._.size_excluded``: ``True`` when the match is a clock-position
      reference ("à 4h"), a nipple-distance, or a margin/resection-distance
      measurement rather than an actual lesion/node size

    Requires sentence boundaries (add ``eds.sentences`` before this pipe) —
    falls back to treating the whole document as one sentence otherwise.
    """

    def __init__(
        self,
        nlp: Optional[PipelineProtocol],
        name: str = "tumor_size",
        *,
        spans_key: str = "tumor_size",
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
        for ext in ("size", "size_context", "size_excluded"):
            if not Span.has_extension(ext):
                Span.set_extension(ext, default=None)

    def _sentences(self, doc: Doc):
        if doc.has_annotation("SENT_START"):
            return list(doc.sents)
        return [doc[:]]

    def __call__(self, doc: Doc) -> Doc:
        spans: List[Span] = []
        for sent in self._sentences(doc):
            raw_measurements = size_finder.run(sent.text)
            if not raw_measurements:
                continue
            parsed = json.loads(size_finder._to_json(raw_measurements))
            for m in parsed:
                char_start = sent.start_char + m["start"]
                char_end = sent.start_char + m["end"]
                span = doc.char_span(char_start, char_end, alignment_mode="expand")
                if span is None:
                    continue
                ctx, excluded = size_context.classify(sent.text, m["start"], m["end"])
                span.label_ = "tumor_size"
                span._.size = m
                span._.size_context = ctx
                span._.size_excluded = excluded
                spans.append(span)
        self.set_spans(doc, spans)
        return doc
