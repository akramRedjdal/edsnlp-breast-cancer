from edsnlp.core import registry

from .biomarkers import BreastBiomarkersMatcher

create_component = registry.factory.register(
    "breast_cancer.biomarkers",
    assigns=["doc.spans"],
)(BreastBiomarkersMatcher)
