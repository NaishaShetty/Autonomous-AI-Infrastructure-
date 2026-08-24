"""Phase 4.5b -- unit coverage for the taxonomy/diagnosis wiring of the
three agent-runtime failure classes (monitoring.py + diagnosis.py).
"""
from src.phase4.diagnosis import DiagnosisEngine
from src.phase4.monitoring import FailureDetector, MonitoringEngine


def _failure_detected_event(kind, run_id="r1", wid="w1", env="e1"):
    return {
        "event_id": "ev1", "event_type": "failure_detected", "job_id": run_id,
        "workload_id": wid, "environment_id": env, "timestamp": "2026-01-01T00:00:01Z",
        "payload": {"failure_kind": kind}, "provenance": {"source": "test"},
    }


def _execution_started(run_id="r1", wid="w1", env="e1"):
    return {
        "event_id": "ev0", "event_type": "execution_started", "job_id": run_id,
        "workload_id": wid, "environment_id": env, "timestamp": "2026-01-01T00:00:00Z",
        "payload": {}, "provenance": {"source": "test"},
    }


def test_failure_detector_classifies_all_three_new_agent_kinds():
    detector = FailureDetector()
    expectations = {
        "AGENT_INCORRECT_ANSWER": "AGENT_INCORRECT_ANSWER",
        "AGENT_TASK_TIMEOUT": "AGENT_TASK_TIMEOUT",
        "AGENT_WORKER_ERROR": "AGENT_WORKER_ERROR",
    }
    for kind, expected_class in expectations.items():
        event = _failure_detected_event(kind)
        failure = detector.detect(event)
        assert failure is not None
        assert failure.failure_class == expected_class


def test_diagnosis_engine_produces_a_real_hypothesis_for_each_agent_failure_class():
    events = [_execution_started(), _failure_detected_event("AGENT_INCORRECT_ANSWER")]
    engine = MonitoringEngine(); engine.process(events)
    failure = engine.failures[0]
    diagnosis = DiagnosisEngine().diagnose(failure, events)
    assert diagnosis.primary_hypothesis.name == "AGENT_INCORRECT_OUTPUT"
    assert diagnosis.primary_hypothesis.confidence == "HIGH"
    assert diagnosis.causal_status == "OBSERVED"
    assert diagnosis.primary_hypothesis.name != "UNKNOWN"


def test_diagnosis_engine_handles_agent_timeout_and_worker_error():
    for kind, expected_name in (("AGENT_TASK_TIMEOUT", "AGENT_RUNTIME_TIMEOUT"), ("AGENT_WORKER_ERROR", "AGENT_WORKER_CRASH")):
        events = [_execution_started(), _failure_detected_event(kind)]
        engine = MonitoringEngine(); engine.process(events)
        failure = engine.failures[0]
        diagnosis = DiagnosisEngine().diagnose(failure, events)
        assert diagnosis.primary_hypothesis.name == expected_name
