import edsnlp
import pytest

import edsnlp_breast_cancer  # noqa: F401  (registers the pipes)


@pytest.fixture
def blank_nlp():
    return edsnlp.blank("eds")


@pytest.fixture
def nlp_patient_info():
    nlp = edsnlp.blank("eds")
    nlp.add_pipe("breast_cancer.patient_info")
    return nlp


@pytest.fixture
def nlp_diagnosis():
    nlp = edsnlp.blank("eds")
    nlp.add_pipe("breast_cancer.diagnosis")
    return nlp


@pytest.fixture
def nlp_treatment():
    nlp = edsnlp.blank("eds")
    nlp.add_pipe("breast_cancer.treatment")
    return nlp


@pytest.fixture
def nlp_side_findings():
    nlp = edsnlp.blank("eds")
    nlp.add_pipe("breast_cancer.side_findings")
    return nlp


@pytest.fixture
def nlp_tnm():
    nlp = edsnlp.blank("eds")
    nlp.add_pipe("eds.sentences")
    nlp.add_pipe("breast_cancer.tnm")
    return nlp


@pytest.fixture
def nlp_tumor_size():
    nlp = edsnlp.blank("eds")
    nlp.add_pipe("eds.sentences")
    nlp.add_pipe("breast_cancer.tumor_size")
    return nlp


@pytest.fixture
def nlp_tumor_info():
    nlp = edsnlp.blank("eds")
    nlp.add_pipe("breast_cancer.tumor_info")
    return nlp
