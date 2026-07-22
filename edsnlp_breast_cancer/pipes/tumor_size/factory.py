from edsnlp.core import registry

from .tumor_size import TumorSizeMatcher

create_component = registry.factory.register(
    "breast_cancer.tumor_size",
    assigns=["doc.spans"],
)(TumorSizeMatcher)
