from src.phase4.diagnosis import DiagnosisEngine, Confidence, CausalStatus, EvidenceKind
from src.phase4.memory import FailureMemoryStore


def ev(i, t, ts='2026-01-01T00:00:00Z', rid='r1', wid='w1', payload=None):
    return {'event_id': i, 'event_type': t, 'timestamp': ts, 'job_id': rid, 'workload_id': wid, 'environment_id': 'controlled-runtime-local-environment', 'payload': payload or {}, 'provenance': {'source': 'project-owned-controlled-runtime', 'source_record_id': i, 'timestamp_quality': 'EXACT'}}


def failure(i='f1', cls='PROCESS_NONZERO_EXIT', rid='r1', wid='w1', ts='2026-01-01T00:00:02Z'):
    return {'failure_id': i, 'failure_class': cls, 'run_id': rid, 'workload_id': wid, 'environment_id': 'controlled-runtime-local-environment', 'failure_timestamp': ts, 'evidence_references': ['fobs'], 'provenance': {'source': 'project-owned-controlled-runtime', 'source_record_id': 'fobs', 'timestamp_quality': 'EXACT'}}


def basic_events(rid='r1', wid='w1'):
    return [ev('start', 'execution_started', '2026-01-01T00:00:01Z', rid, wid), ev('fobs', 'failure_detected', '2026-01-01T00:00:02Z', rid, wid, {'failure_kind': 'NONZERO_EXIT'})]


def test_no_memory_argument_leaves_behavior_unchanged():
    without = DiagnosisEngine().diagnose(failure(), basic_events())
    with_none = DiagnosisEngine().diagnose(failure(), basic_events(), memory=None)
    assert without == with_none
    assert without.foundation_references['memory_used'] is False
    assert without.foundation_references['evidence_scope'] == 'CURRENT_RUN_ONLY'


def test_memory_hit_from_different_run_same_workload_adds_historical_evidence():
    memory = FailureMemoryStore()
    memory.add(workload_id='w1', environment_id='controlled-runtime-local-environment', failure_class='PROCESS_NONZERO_EXIT', root_cause='PROCESS_EXIT_FAILURE', diagnosis_confidence='HIGH', source_run_id='r-prior', source_diagnosis_id='diagnosis:r-prior', action_taken='restart', validated_outcome='RECOVERED', recorded_at='2026-01-01T00:00:00Z', provenance={'source': 'test'})
    d = DiagnosisEngine().diagnose(failure(rid='r2'), basic_events(rid='r2'), memory=memory)
    assert d.foundation_references['memory_used'] is True
    assert d.foundation_references['memory_version'] == 1
    historical = [e for e in d.evidence if e.kind == EvidenceKind.HISTORICAL.value]
    assert len(historical) == 1
    # A corroborating RECOVERED prior promotes HIGH... but HIGH has no
    # further promotion tier (see _CONFIDENCE_PROMOTION); confidence stays
    # HIGH and only causal_status moves toward SUPPORTED.
    assert d.confidence == Confidence.HIGH.value
    assert d.causal_status == CausalStatus.SUPPORTED.value


def test_memory_never_eligible_from_the_same_run_id():
    memory = FailureMemoryStore()
    memory.add(workload_id='w1', environment_id='controlled-runtime-local-environment', failure_class='PROCESS_NONZERO_EXIT', root_cause='PROCESS_EXIT_FAILURE', diagnosis_confidence='HIGH', source_run_id='r1', source_diagnosis_id='diagnosis:r1', action_taken='restart', validated_outcome='RECOVERED', recorded_at='2026-01-01T00:00:00Z', provenance={'source': 'test'})
    d = DiagnosisEngine().diagnose(failure(rid='r1'), basic_events(rid='r1'), memory=memory)
    assert d.foundation_references['memory_used'] is False
    assert all(e.kind != EvidenceKind.HISTORICAL.value for e in d.evidence)


def test_memory_scoped_to_workload_does_not_leak_across_workloads():
    memory = FailureMemoryStore()
    memory.add(workload_id='w-OTHER', environment_id='controlled-runtime-local-environment', failure_class='PROCESS_NONZERO_EXIT', root_cause='PROCESS_EXIT_FAILURE', diagnosis_confidence='HIGH', source_run_id='r-prior', source_diagnosis_id='diagnosis:r-prior', action_taken='restart', validated_outcome='RECOVERED', recorded_at='2026-01-01T00:00:00Z', provenance={'source': 'test'})
    d = DiagnosisEngine().diagnose(failure(rid='r2', wid='w1'), basic_events(rid='r2', wid='w1'), memory=memory)
    assert d.foundation_references['memory_used'] is False


def test_network_failure_class_is_now_diagnosable():
    f = failure('fnet', 'NETWORK_FAILURE', 'r3', ts='2026-01-01T00:00:02Z')
    events = [ev('start', 'execution_started', '2026-01-01T00:00:01Z', 'r3'), ev('fobs', 'failure_detected', '2026-01-01T00:00:02Z', 'r3', payload={'failure_kind': 'NETWORK_ERROR', 'exit_code': 9})]
    d = DiagnosisEngine().diagnose(f, events)
    assert d.primary_hypothesis.name == 'NETWORK_CONNECTIVITY_FAILURE'
    assert d.confidence == Confidence.HIGH.value
