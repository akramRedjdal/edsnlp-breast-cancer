from edsnlp.core import registry

from .side_findings import SideFindingsMatcher

create_component = registry.factory.register(
    "breast_cancer.side_findings",
    assigns=["doc.spans"],
)(SideFindingsMatcher)
