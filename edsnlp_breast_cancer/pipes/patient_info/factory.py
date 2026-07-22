from edsnlp.core import registry

from .patient_info import PatientInfoMatcher

create_component = registry.factory.register(
    "breast_cancer.patient_info",
    assigns=["doc.spans"],
)(PatientInfoMatcher)
