from edsnlp.core import registry

from .treatment import TreatmentMatcher

create_component = registry.factory.register(
    "breast_cancer.treatment",
    assigns=["doc.spans"],
)(TreatmentMatcher)
