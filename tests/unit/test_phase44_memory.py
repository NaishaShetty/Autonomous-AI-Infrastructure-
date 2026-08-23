from src.phase4.memory import FailureMemoryStore


def add(store, *, run_id, ts, workload_id='w1', environment_id='env1', failure_class='PROCESS_TIMEOUT', action='retry', outcome='RECOVERED'):
    return store.add(workload_id=workload_id, environment_id=environment_id, failure_class=failure_class, root_cause='RUNTIME_TIMEOUT', diagnosis_confidence='HIGH', source_run_id=run_id, source_diagnosis_id=f'diagnosis:{run_id}', action_taken=action, validated_outcome=outcome, recorded_at=ts, provenance={'source': 'test'})


def test_retrieval_excludes_same_run_id_even_when_everything_else_matches():
    store = FailureMemoryStore()
    add(store, run_id='run-1', ts='2026-01-01T00:00:00Z')
    matches = store.retrieve(workload_id='w1', environment_id='env1', failure_class='PROCESS_TIMEOUT', exclude_run_id='run-1', at_or_before='2026-01-01T01:00:00Z')
    assert matches == ()


def test_retrieval_is_scoped_by_workload_and_environment():
    store = FailureMemoryStore()
    add(store, run_id='run-1', ts='2026-01-01T00:00:00Z', workload_id='w1')
    add(store, run_id='run-2', ts='2026-01-01T00:00:00Z', workload_id='w2')
    matches = store.retrieve(workload_id='w1', environment_id='env1', failure_class='PROCESS_TIMEOUT', exclude_run_id='run-999', at_or_before='2026-01-01T01:00:00Z')
    assert [m.record.source_run_id for m in matches] == ['run-1']


def test_retrieval_respects_temporal_boundary():
    store = FailureMemoryStore()
    add(store, run_id='run-1', ts='2026-01-02T00:00:00Z')
    matches = store.retrieve(workload_id='w1', environment_id='env1', failure_class='PROCESS_TIMEOUT', exclude_run_id='run-999', at_or_before='2026-01-01T00:00:00Z')
    assert matches == ()


def test_retrieval_fails_closed_on_missing_scope():
    store = FailureMemoryStore()
    add(store, run_id='run-1', ts='2026-01-01T00:00:00Z')
    assert store.retrieve(workload_id=None, environment_id='env1', failure_class='PROCESS_TIMEOUT', exclude_run_id='x', at_or_before='2026-01-02T00:00:00Z') == ()
    assert store.retrieve(workload_id='w1', environment_id=None, failure_class='PROCESS_TIMEOUT', exclude_run_id='x', at_or_before='2026-01-02T00:00:00Z') == ()


def test_memory_version_increments_atomically_and_is_reported_on_records():
    store = FailureMemoryStore()
    assert store.memory_version == 0
    r1 = add(store, run_id='run-1', ts='2026-01-01T00:00:00Z')
    r2 = add(store, run_id='run-2', ts='2026-01-01T00:00:01Z')
    assert r1.memory_version == 1 and r2.memory_version == 2 and store.memory_version == 2


def test_prior_outcome_rate_counts_only_matching_action_and_scope():
    store = FailureMemoryStore()
    add(store, run_id='run-1', ts='2026-01-01T00:00:00Z', action='retry', outcome='NOT_RECOVERED')
    add(store, run_id='run-2', ts='2026-01-01T00:00:01Z', action='retry', outcome='NOT_RECOVERED')
    add(store, run_id='run-3', ts='2026-01-01T00:00:02Z', action='restart', outcome='RECOVERED')
    successes, total = store.prior_outcome_rate(workload_id='w1', environment_id='env1', failure_class='PROCESS_TIMEOUT', action='retry', exclude_run_id='run-999', at_or_before='2026-01-02T00:00:00Z')
    assert (successes, total) == (0, 2)
    successes, total = store.prior_outcome_rate(workload_id='w1', environment_id='env1', failure_class='PROCESS_TIMEOUT', action='restart', exclude_run_id='run-999', at_or_before='2026-01-02T00:00:00Z')
    assert (successes, total) == (1, 1)


def test_relevance_decays_with_age_and_ranks_more_recent_first():
    store = FailureMemoryStore()
    add(store, run_id='old', ts='2026-01-01T00:00:00Z')
    add(store, run_id='new', ts='2026-01-01T02:00:00Z')
    matches = store.retrieve(workload_id='w1', environment_id='env1', failure_class='PROCESS_TIMEOUT', exclude_run_id='x', at_or_before='2026-01-01T02:00:00Z')
    assert [m.record.source_run_id for m in matches] == ['new', 'old']
    assert matches[0].relevance > matches[1].relevance
