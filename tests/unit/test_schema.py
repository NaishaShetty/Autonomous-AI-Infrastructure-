"""Regression tests for the Phase 1 confidence-scale bug
(global_reliability_score: 189.61 caused by mixing 0-1 and 0-100 scales,
PHASE1_AUDIT_REPORT.md section 5) and for schema-level invariants."""
import json

import pytest
from pydantic import ValidationError

from src.schema.events import Decision, EventSource, Outcome, ReliabilityEvent, confidence_to_percent


def _event(confidence: float, decision: Decision = Decision.ANSWER, abstained: bool = False) -> ReliabilityEvent:
    return ReliabilityEvent(
        workload_id="w",
        source=EventSource.RELIABILITY_ENGINE,
        context={"f1": 1.0},
        confidence=confidence,
        decision=decision,
        abstained=abstained,
    )


def test_confidence_must_be_in_unit_interval():
    _event(0.0)
    _event(1.0)
    with pytest.raises(ValidationError):
        _event(1.5)
    with pytest.raises(ValidationError):
        _event(-0.1)


def test_confidence_over_100_scale_is_rejected():
    """The literal regression case: a value like 189.61 (a 0-100-scale
    number accidentally used where 0-1 was expected) must fail validation,
    not silently propagate into an aggregate metric."""
    with pytest.raises(ValidationError):
        _event(189.61)


def test_confidence_to_percent_conversion():
    assert confidence_to_percent(0.0) == 0.0
    assert confidence_to_percent(1.0) == 100.0
    assert confidence_to_percent(0.5) == 50.0
    with pytest.raises(ValueError):
        confidence_to_percent(1.8961)  # the exact bad value from Phase 1, on the wrong scale


def test_abstained_must_match_decision():
    _event(0.9, decision=Decision.ANSWER, abstained=False)
    with pytest.raises(ValidationError):
        _event(0.9, decision=Decision.ANSWER, abstained=True)
    _event(0.1, decision=Decision.ABSTAIN, abstained=True)
    with pytest.raises(ValidationError):
        _event(0.1, decision=Decision.ABSTAIN, abstained=False)


def test_failure_risk_and_raw_confidence_also_bounded():
    ReliabilityEvent(
        workload_id="w",
        source=EventSource.RELIABILITY_ENGINE,
        context={},
        confidence=0.5,
        raw_confidence=0.4,
        failure_risk=0.3,
        decision=Decision.ANSWER,
        abstained=False,
    )
    with pytest.raises(ValidationError):
        ReliabilityEvent(
            workload_id="w",
            source=EventSource.RELIABILITY_ENGINE,
            context={},
            confidence=0.5,
            failure_risk=1.2,
            decision=Decision.ANSWER,
            abstained=False,
        )


def test_event_is_json_serializable_without_numpy_leakage():
    """Regression test for the Phase 1 numpy-scalar serialization 500 error
    (Introspective-Failure-Memory-Model POST /api/control,
    PHASE1_AUDIT_REPORT.md section 4). Simulates a producer accidentally
    handing numpy scalar types to the model constructor -- pydantic should
    coerce them to native Python types, and the result must round-trip
    through stdlib json without error."""
    import numpy as np

    event = ReliabilityEvent(
        workload_id="w",
        source=EventSource.RELIABILITY_ENGINE,
        context={"f1": np.float32(1.5), "f2": np.float64(2.0)},
        confidence=float(np.float32(0.83)),
        failure_risk=float(np.float64(0.2)),
        decision=Decision.ANSWER,
        abstained=False,
        metadata={"predicted_label": int(np.int64(1))},
    )
    payload = event.model_dump(mode="json")
    serialized = json.dumps(payload)  # must not raise
    assert isinstance(serialized, str)
    assert json.loads(serialized)["confidence"] == pytest.approx(0.83, abs=1e-4)


def test_outcome_defaults_unknown():
    event = _event(0.9)
    assert event.outcome == Outcome.UNKNOWN
