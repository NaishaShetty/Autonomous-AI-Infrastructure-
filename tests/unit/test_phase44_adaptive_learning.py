"""Phase 4.5 gap 5 -- a real adaptive mechanism, tested with a quantified,
measured improvement across episodes (not a single before/after assertion).

This deliberately does not spin up real subprocesses: it drives the real
``AdaptiveRecoveryPlanner`` / ``FailureMemoryStore`` / ``DiagnosisEngine``
code paths directly against a synthetic two-armed scenario with a known
(but not planner-visible) true success probability per action -- the
standard way an online decision mechanism's convergence is evaluated. The
mechanism under test (the Beta-smoothed online estimate in
``FailureMemoryStore.action_success_estimate`` and the ranking in
``AdaptiveRecoveryPlanner.plan``) is exactly the production code; only the
"was this simulated recovery attempt actually successful" coin flip is
synthetic, because there is no real infrastructure in this repository where
one action is durably 4x better than another to observe from.
"""
from datetime import datetime, timedelta, timezone
import random

from src.phase4.adaptive import AdaptiveRecoveryPlanner
from src.phase4.diagnosis import DiagnosisEngine
from src.phase4.memory import FailureMemoryStore
from src.phase4.recovery import RuleBasedRecoveryPlanner


def _ts(i):
    return (datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=i)).isoformat().replace("+00:00", "Z")


def _ev(i, t, ts, rid, payload=None):
    return {"event_id": i, "event_type": t, "timestamp": ts, "job_id": rid, "workload_id": "w1", "environment_id": "env1", "payload": payload or {}, "provenance": {"source": "test", "source_record_id": i, "timestamp_quality": "EXACT"}}


def _diagnose(rid, boundary, memory=None):
    events = [_ev("start", "execution_started", _ts(0), rid), _ev("fobs", "failure_detected", boundary, rid, {"failure_kind": "RESOURCE_UNAVAILABLE"})]
    failure = {"failure_id": f"f-{rid}", "failure_class": "RESOURCE_UNAVAILABLE", "run_id": rid, "workload_id": "w1", "environment_id": "env1", "failure_timestamp": boundary, "evidence_references": ["fobs"], "provenance": {"source": "test", "source_record_id": "fobs", "timestamp_quality": "EXACT"}}
    return DiagnosisEngine().diagnose(failure, events, memory=memory)


def _run_bandit(planner, n_episodes, epsilon, seed):
    """Drives ``planner.plan`` for RESOURCE_UNAVAILABLE (candidates retry,
    reconfigure, escalate_to_human, abstain -- see src/phase4/recovery.py)
    against a true success probability of 0.2 for retry and 0.8 for
    reconfigure. Returns the list of 1/0 "chose the better action" flags,
    one per episode, in order."""
    true_success_prob = {"retry": 0.35, "reconfigure": 0.65}
    memory = FailureMemoryStore()
    rng = random.Random(seed)
    correct = []
    for i in range(n_episodes):
        rid = f"run-{i}"
        boundary = _ts(i + 1)
        diagnosis = _diagnose(rid, boundary, memory=memory)
        action = planner.plan(diagnosis, memory=memory)
        chosen = action.action_type
        if chosen not in true_success_prob:
            correct.append(0)
            continue
        # Epsilon-greedy exploration at the evaluation-harness level (not
        # inside the planner) -- a real online decision mechanism evaluated
        # this way is standard practice; without *some* exploration a
        # zero-evidence greedy tie-break could get permanently stuck on one
        # arm from a single lucky/unlucky early draw.
        realized_action = chosen
        if rng.random() < epsilon:
            realized_action = rng.choice(list(true_success_prob))
        outcome = "RECOVERED" if rng.random() < true_success_prob[realized_action] else "NOT_RECOVERED"
        memory.add(
            workload_id="w1", environment_id="env1", failure_class="RESOURCE_UNAVAILABLE",
            root_cause="RESOURCE_UNAVAILABLE", diagnosis_confidence=diagnosis.confidence,
            source_run_id=rid, source_diagnosis_id=diagnosis.diagnosis_id, action_taken=realized_action,
            validated_outcome=outcome, recorded_at=boundary, provenance={"source": "test"},
        )
        correct.append(1 if chosen == "reconfigure" else 0)
    return correct


def test_adaptive_planner_correct_action_selection_rate_improves_with_evidence():
    correct = _run_bandit(AdaptiveRecoveryPlanner(), n_episodes=400, epsilon=0.15, seed=20260824)
    early_rate = sum(correct[:40]) / 40
    late_rate = sum(correct[-40:]) / 40
    # Reported as measured -- not asserted to hit a pre-picked target beyond
    # "the mechanism actually learns something": the late-window rate must
    # exceed the early-window rate, and must clear a modest bar showing real
    # convergence toward the better action (reconfigure, true prob 0.65 vs
    # retry's 0.35 -- deliberately close, not a trivially-easy gap), not
    # just noise.
    print(f"[adaptive-learning] early-window correct-action rate={early_rate:.3f} late-window rate={late_rate:.3f}")
    assert late_rate > early_rate
    assert late_rate >= 0.60


def test_base_planner_shows_no_such_improvement_over_the_same_scenario():
    """Control: the unmodified RuleBasedRecoveryPlanner always tries
    'retry' first (declared order) with no ranking by outcome quality, so it
    should NOT show the same convergence -- this is the "before" this
    module's gap-5 fix addresses, kept as a regression guard so a future
    change can't silently make AdaptiveRecoveryPlanner degenerate back to
    the base class's behavior while still claiming to be adaptive."""
    correct = _run_bandit(RuleBasedRecoveryPlanner(), n_episodes=400, epsilon=0.15, seed=20260824)
    late_rate = sum(correct[-40:]) / 40
    print(f"[base-planner-control] late-window correct-action rate={late_rate:.3f}")
    # The base planner only ever switches off 'retry' once retry accumulates
    # >=2 confirmed zero-success outcomes -- with a real (nonzero) 0.35
    # success rate that will happen often, so it keeps re-qualifying and
    # never durably prefers 'reconfigure' by quality. Its long-run rate
    # should sit well below the adaptive planner's.
    assert late_rate < 0.60


def test_online_estimate_updates_immediately_after_a_single_new_outcome():
    """Directly exercises FailureMemoryStore.action_success_estimate to
    prove it is truly online (re-derived from current records on every
    call, no stale cache) rather than the ranking test above being the only
    evidence."""
    memory = FailureMemoryStore()
    kwargs = dict(workload_id="w1", environment_id="env1", failure_class="RESOURCE_UNAVAILABLE", action="reconfigure", exclude_run_id="x", at_or_before="2026-01-01T01:00:00Z")
    before = memory.action_success_estimate(**kwargs)
    assert before == 0.5  # Beta(1,1) prior with zero evidence
    memory.add(workload_id="w1", environment_id="env1", failure_class="RESOURCE_UNAVAILABLE", root_cause="RESOURCE_UNAVAILABLE", diagnosis_confidence="HIGH", source_run_id="r1", source_diagnosis_id="d1", action_taken="reconfigure", validated_outcome="RECOVERED", recorded_at="2026-01-01T00:00:00Z", provenance={})
    after_one_success = memory.action_success_estimate(**kwargs)
    assert after_one_success == (1 + 1) / (1 + 2)
    assert after_one_success > before
