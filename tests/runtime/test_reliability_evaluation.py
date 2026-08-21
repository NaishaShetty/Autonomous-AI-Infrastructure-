from __future__ import annotations

import pytest

from src.reliability.evaluation import (
    EvaluationProtocolError,
    abstention_metrics,
    calibration_metrics,
    evaluate_predictions,
    validate_feature_availability,
    validate_group_disjointness,
)


def test_group_disjointness_rejects_cross_split_entity() -> None:
    records = [
        {"group_id": "g1", "split": "train"},
        {"group_id": "g1", "split": "evaluation"},
    ]
    with pytest.raises(EvaluationProtocolError):
        validate_group_disjointness(records)


def test_feature_availability_rejects_post_outcome_feature() -> None:
    records = [{"features": {"latency": 1.0, "outcome": 1}, "label": 1}]
    with pytest.raises(EvaluationProtocolError):
        validate_feature_availability(records, feature_keys=["latency"])


def test_metrics_report_calibration_and_abstention() -> None:
    labels = [0, 1, 1, 0]
    risks = [0.1, 0.8, 0.7, 0.2]
    evaluated = evaluate_predictions(labels, risks)
    calibrated = calibration_metrics(labels, risks, bins=2)
    abstained = abstention_metrics(labels, risks, accept_risk_threshold=0.5)
    assert evaluated["auroc"] == 1.0
    assert calibrated["brier_score"] < 0.1
    assert abstained["coverage"] == 0.5
    assert abstained["abstained_failure_rate"] == 1.0
