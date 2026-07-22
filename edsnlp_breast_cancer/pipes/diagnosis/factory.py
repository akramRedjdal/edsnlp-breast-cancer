from edsnlp.core import registry

from .diagnosis import DiagnosisMatcher

create_component = registry.factory.register(
    "breast_cancer.diagnosis",
    assigns=["doc.spans"],
)(DiagnosisMatcher)
