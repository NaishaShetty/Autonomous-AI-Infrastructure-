import dataclasses

import pytest

from src.failure_patterns.schema import (
    DescriptiveAssociation,
    EvidenceTier,
    PatternCandidate,
    PatternQuery,
    AlibabaTestOutcome,
)


def test_evidence_tier_has_exactly_four_values():
    assert {t.value for t in EvidenceTier} == {"OBSERVED", "INFERRED", "CONFIRMED", "UNCERTAIN"}


def test_pattern_query_only_has_decision_time_fields():
    fields = {f.name for f in dataclasses.fields(PatternQuery)}
    assert fields == {"task_name", "gpu_type"}


def test_pattern_query_is_frozen():
    q = PatternQuery(task_name="tensorflow", gpu_type="MISC")
    with pytest.raises(dataclasses.FrozenInstanceError):
        q.task_name = "worker"


def test_pattern_query_cannot_be_constructed_with_extra_leakage_fields():
    with pytest.raises(TypeError):
        PatternQuery(task_name="tensorflow", gpu_type="MISC", train_rate=0.9)  # type: ignore[call-arg]


def test_pattern_candidate_query_roundtrip_excludes_evidence():
    cand = PatternCandidate(
        task_name="tensorflow", gpu_type="MISC", n_train=100, train_rate=0.3,
        train_baseline_rate=0.17, n_validation=20, validation_rate=0.28,
        validation_baseline_rate=0.17, tier=EvidenceTier.CONFIRMED,
        protocol_version="test", dataset_content_hash="abc123", split_name="temporal",
    )
    q = cand.query()
    assert q == PatternQuery(task_name="tensorflow", gpu_type="MISC")
    assert not hasattr(q, "train_rate")


def test_pattern_candidate_elevation_properties():
    cand = PatternCandidate(
        task_name="a", gpu_type="b", n_train=50, train_rate=0.4, train_baseline_rate=0.2,
        n_validation=10, validation_rate=0.3, validation_baseline_rate=0.15,
        tier=EvidenceTier.INFERRED, protocol_version="t", dataset_content_hash="h", split_name="temporal",
    )
    assert cand.train_elevation == pytest.approx(0.2)
    assert cand.validation_elevation == pytest.approx(0.15)


def test_pattern_candidate_elevation_none_when_rate_missing():
    cand = PatternCandidate(
        task_name="a", gpu_type="b", n_train=0, train_rate=None, train_baseline_rate=0.2,
        n_validation=0, validation_rate=None, validation_baseline_rate=None,
        tier=EvidenceTier.UNCERTAIN, protocol_version="t", dataset_content_hash="h", split_name="temporal",
    )
    assert cand.train_elevation is None
    assert cand.validation_elevation is None


def test_test_candidate_outcome_test_elevated_none_when_missing():
    outcome = AlibabaTestOutcome(task_name="a", gpu_type="b", n_test=0, test_rate=None, test_baseline_rate=0.2)
    assert outcome.test_elevated is None


def test_descriptive_association_is_candidate_flag():
    assoc = DescriptiveAssociation(dataset="aiops_kpi_2020", key=("docker_001", "CPU fault"), count=3, is_candidate=True)
    assert assoc.is_candidate is True
    assert assoc.count == 3
