from dataclasses import dataclass

from src.phase4.diagnosis import DiagnosisEngine
from src.phase4.memory import FailureMemoryStore
from src.phase4.recovery import (
    ControlledRuntimeRecoveryExecutor,
    ExecutionResult,
    RecoverySafetyGate,
    RuleBasedRecoveryPlanner,
    SignalRecoveryValidator,
)
from src.recovery.schema import ActionId


def ev(i, t, ts='2026-01-01T00:00:00Z', rid='r1', wid='w1', payload=None):
    return {'event_id': i, 'event_type': t, 'timestamp': ts, 'job_id': rid, 'workload_id': wid, 'environment_id': 'env1', 'payload': payload or {}, 'provenance': {'source': 'test', 'source_record_id': i, 'timestamp_quality': 'EXACT'}}


def failure(cls='PROCESS_NONZERO_EXIT', rid='r1', wid='w1'):
    return {'failure_id': 'f1', 'failure_class': cls, 'run_id': rid, 'workload_id': wid, 'environment_id': 'env1', 'failure_timestamp': '2026-01-01T00:00:02Z', 'evidence_references': ['fobs'], 'provenance': {'source': 'test', 'source_record_id': 'fobs', 'timestamp_quality': 'EXACT'}}


def diagnose(cls='PROCESS_NONZERO_EXIT', rid='r1', wid='w1', memory=None):
    events = [ev('start', 'execution_started', '2026-01-01T00:00:01Z', rid, wid), ev('fobs', 'failure_detected', '2026-01-01T00:00:02Z', rid, wid, {'failure_kind': 'NONZERO_EXIT'})]
    return DiagnosisEngine().diagnose(failure(cls, rid, wid), events, memory=memory)


def test_planner_selects_restart_for_nonzero_exit_with_no_memory():
    action = RuleBasedRecoveryPlanner().plan(diagnose())
    assert action.action_type == 'restart'


def test_planner_avoids_action_with_a_clean_failure_track_record_in_memory():
    memory = FailureMemoryStore()
    for i in range(2):
        memory.add(workload_id='w1', environment_id='env1', failure_class='PROCESS_NONZERO_EXIT', root_cause='PROCESS_EXIT_FAILURE', diagnosis_confidence='HIGH', source_run_id=f'prior-{i}', source_diagnosis_id=f'diagnosis:prior-{i}', action_taken='restart', validated_outcome='NOT_RECOVERED', recorded_at='2026-01-01T00:00:00Z', provenance={})
    d = diagnose(rid='r2', memory=memory)
    action = RuleBasedRecoveryPlanner().plan(d, memory=memory)
    assert action.action_type != 'restart'
    assert action.action_type == 'retry'


def test_safety_gate_rejects_unknown_action_type_fail_closed():
    gate = RecoverySafetyGate()

    @dataclass
    class FakeAction:
        action_type: str
        authorization_required: bool = True

    authorized, reason = gate.authorize(FakeAction(action_type='rm_rf_prod'), diagnose())
    assert authorized is False


def test_safety_gate_rejects_action_not_in_candidate_list_for_this_failure_class():
    from src.phase4.recovery import _provenance
    from src.phase4.architecture import RecoveryAction
    gate = RecoverySafetyGate()
    # ROLLBACK is a real, SAFE action in the frozen vocabulary, but it is not
    # a declared candidate for PROCESS_NONZERO_EXIT -- must still be rejected.
    action = RecoveryAction(action_id='a', action_type=ActionId.ROLLBACK.value, provenance=_provenance('test'))
    authorized, reason = gate.authorize(action, diagnose())
    assert authorized is False


def test_validator_catches_a_lying_executor():
    """The validator must derive its verdict from the new run's own raw
    events, never from what the executor claims. This is the direct test
    for docs/PHASE4_5_AUDIT_AND_PLAN.md section 5.C's requirement: "inject
    an executor that lies about success and confirm the validator still
    catches it."."""
    from src.phase4.controlled_runtime import RunResult

    lying_run_result = RunResult(
        run_id='run-lying', workload_id='w1', environment_id='env1',
        status='COMPLETED',  # the lie: claims success
        exit_code=0,
        events=[
            ev('start', 'execution_started', '2026-01-01T00:00:01Z', 'run-lying'),
            ev('fobs2', 'failure_detected', '2026-01-01T00:00:02Z', 'run-lying', payload={'failure_kind': 'NONZERO_EXIT', 'exit_code': 7}),
            # No workload_completed event -- the actual raw events show a failure.
        ],
        config={}, collection_start='2026-01-01T00:00:00Z', collection_end='2026-01-01T00:00:02Z',
    )
    lying_execution = ExecutionResult(action_type='restart', executed=True, run_result=lying_run_result, note='executor falsely reports success')
    validation = SignalRecoveryValidator().validate(lying_execution)
    assert validation.status == 'NOT_RECOVERED'


def test_validator_reports_recovered_only_when_new_run_actually_completed_cleanly():
    from src.phase4.controlled_runtime import RunResult
    clean_run = RunResult(
        run_id='run-clean', workload_id='w1', environment_id='env1', status='COMPLETED', exit_code=0,
        events=[ev('start', 'execution_started', '2026-01-01T00:00:01Z', 'run-clean'), ev('done', 'workload_completed', '2026-01-01T00:00:02Z', 'run-clean', payload={'exit_code': 0})],
        config={}, collection_start='2026-01-01T00:00:00Z', collection_end='2026-01-01T00:00:02Z',
    )
    execution = ExecutionResult(action_type='retry', executed=True, run_result=clean_run, note='ok')
    validation = SignalRecoveryValidator().validate(execution)
    assert validation.status == 'RECOVERED'


def test_validator_reports_not_executed_when_action_has_no_executor():
    execution = ExecutionResult(action_type='escalate_to_human', executed=False, run_result=None, note='no executor')
    validation = SignalRecoveryValidator().validate(execution)
    assert validation.status == 'NOT_EXECUTED'
