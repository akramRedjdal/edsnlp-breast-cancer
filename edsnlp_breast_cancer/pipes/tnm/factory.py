from edsnlp.core import registry

from .tnm import TnmMatcher

create_component = registry.factory.register(
    "breast_cancer.tnm",
    assigns=["doc.spans"],
)(TnmMatcher)
