from edsnlp.core import registry

from .tumor_info import TumorInfoMatcher

create_component = registry.factory.register(
    "breast_cancer.tumor_info",
    assigns=["doc.spans"],
)(TumorInfoMatcher)
