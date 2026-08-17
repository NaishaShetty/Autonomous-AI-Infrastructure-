"""Integration tests for Phase 3.6.5/3.6.6 recovery: max-retry enforcement,
rollback safety (rollback never fails, never fabricates a retry when
there is nothing to retry), deterministic recovery policy, and no
infinite loops."""
from __future__ import annotations

from src.data.synthetic import FEATURE_NAMES, StreamSample
from src.evaluation.decision_policy import RiskTier, TierThresholds
from src.evaluation.recovery import MAX_RETRIES, RecoveryOutcome, attempt_recovery


def _make_thresholds(low=True) -> TierThresholds:
    # low=True -> any score recovers to LOW/MEDIUM; low=False -> nothing recovers
    if low:
        return TierThresholds(t_50=1.1, t_80=1.2, t_95=1.3)  # unreachable -> everything scores LOW
    return TierThresholds(t_50=-1.0, t_80=-0.9, t_95=-0.8)  # everything scores CRITICAL


def test_max_retries_is_exactly_one():
    assert MAX_RETRIES == 1


def test_clean_diagnosis_never_retries_deterministic_model():
    """A sample whose context looks 'clean' to the diagnosis rule must
    roll back immediately -- retrying a deterministic model on an
    unchanged input cannot help, and the policy must not pretend it can."""
    sample = StreamSample(context={"f1": 0.1, "f2": 0.1, "f3": 0.1, "f4": 0.1, "f5": 0.1}, label=1, regime=3)
    result = attempt_recovery(
        sample, None, original_ordinal=None, seed=1, feature_names=FEATURE_NAMES,
        workload_predict=lambda s: 1, score_fn=lambda ctx: 0.0, b_score_fn=lambda ctx: 0.0,
        thresholds=_make_thresholds(low=True), b_thresholds=_make_thresholds(low=True), condition_id="clean",
    )
    assert result.outcome == RecoveryOutcome.ROLLED_BACK
    assert result.action_taken == "none_clean"


def test_feature_noise_diagnosis_without_ordinal_rolls_back_not_crashes():
    """A misdiagnosed 'feature_noise' sample with no attack_ordinal (e.g.
    a clean-condition sample that happened to look noisy) must roll back
    safely, not raise or fabricate a retry."""
    sample = StreamSample(context={"f1": 3.0, "f2": -2.5, "f3": 2.8, "f4": -3.1, "f5": 2.6}, label=1, regime=3)
    result = attempt_recovery(
        sample, None, original_ordinal=None, seed=1, feature_names=FEATURE_NAMES,
        workload_predict=lambda s: 1, score_fn=lambda ctx: 0.0, b_score_fn=lambda ctx: 0.0,
        thresholds=_make_thresholds(low=True), b_thresholds=_make_thresholds(low=True), condition_id="clean",
    )
    assert result.outcome == RecoveryOutcome.ROLLED_BACK
    assert result.action_taken == "misdiagnosed_no_ordinal"


def test_feature_noise_retry_recovers_when_new_tier_is_low():
    sample = StreamSample(context={"f1": 3.0, "f2": -2.5, "f3": 2.8, "f4": -3.1, "f5": 2.6}, label=1, regime=3)
    result = attempt_recovery(
        sample, None, original_ordinal=1, seed=1, feature_names=FEATURE_NAMES,
        workload_predict=lambda s: 1, score_fn=lambda ctx: 0.0, b_score_fn=lambda ctx: 0.0,
        thresholds=_make_thresholds(low=True), b_thresholds=_make_thresholds(low=True), condition_id="feature_noise_mild",
    )
    assert result.outcome == RecoveryOutcome.RECOVERED
    assert result.action_taken == "retry"
    assert result.recovered_correct is True  # workload_predict always returns 1 == label


def test_feature_noise_retry_rolls_back_when_still_critical():
    sample = StreamSample(context={"f1": 3.0, "f2": -2.5, "f3": 2.8, "f4": -3.1, "f5": 2.6}, label=1, regime=3)
    result = attempt_recovery(
        sample, None, original_ordinal=2, seed=1, feature_names=FEATURE_NAMES,
        workload_predict=lambda s: 1, score_fn=lambda ctx: 0.0, b_score_fn=lambda ctx: 0.0,
        thresholds=_make_thresholds(low=False), b_thresholds=_make_thresholds(low=False), condition_id="feature_noise_severe",
    )
    assert result.outcome == RecoveryOutcome.ROLLED_BACK
    assert result.action_taken == "retry"


def test_feature_dropout_reconfigure_recovers_when_b_alone_is_low():
    sample = StreamSample(context={"f1": 1.0, "f2": 0.0, "f3": -1.0, "f4": 0.0, "f5": 0.5}, label=0, regime=3)
    result = attempt_recovery(
        sample, None, original_ordinal=None, seed=1, feature_names=FEATURE_NAMES,
        workload_predict=lambda s: 0, score_fn=lambda ctx: 0.0, b_score_fn=lambda ctx: 0.0,
        thresholds=_make_thresholds(low=False), b_thresholds=_make_thresholds(low=True), condition_id="feature_dropout",
    )
    assert result.outcome == RecoveryOutcome.RECOVERED
    assert result.action_taken == "reconfigure"


def test_feature_dropout_reconfigure_rolls_back_when_b_alone_still_critical():
    """Matches the empirical Phase 3.6 finding: reconfiguring to B alone
    frequently does not help because B is computed from the SAME
    corrupted context."""
    sample = StreamSample(context={"f1": 1.0, "f2": 0.0, "f3": -1.0, "f4": 0.0, "f5": 0.5}, label=0, regime=3)
    result = attempt_recovery(
        sample, None, original_ordinal=None, seed=1, feature_names=FEATURE_NAMES,
        workload_predict=lambda s: 0, score_fn=lambda ctx: 0.0, b_score_fn=lambda ctx: 0.0,
        thresholds=_make_thresholds(low=False), b_thresholds=_make_thresholds(low=False), condition_id="feature_dropout",
    )
    assert result.outcome == RecoveryOutcome.ROLLED_BACK
    assert result.action_taken == "reconfigure"


def test_recovery_deterministic_given_same_inputs():
    sample = StreamSample(context={"f1": 3.0, "f2": -2.5, "f3": 2.8, "f4": -3.1, "f5": 2.6}, label=1, regime=3)
    kwargs = dict(
        original_score=None, original_ordinal=1, seed=7, feature_names=FEATURE_NAMES,
        workload_predict=lambda s: 1, score_fn=lambda ctx: 0.0, b_score_fn=lambda ctx: 0.0,
        thresholds=_make_thresholds(low=True), b_thresholds=_make_thresholds(low=True), condition_id="feature_noise_mild",
    )
    a = attempt_recovery(sample, **kwargs)
    b = attempt_recovery(sample, **kwargs)
    assert a == b


def test_recovery_never_loops_single_call_terminates():
    """attempt_recovery is a single, non-recursive, bounded function call
    -- no while-loop and no self-recursion, so an infinite recovery loop
    is structurally impossible."""
    import inspect
    from src.evaluation import recovery
    src = inspect.getsource(recovery.attempt_recovery)
    assert "while " not in src
    assert "attempt_recovery(" not in src.split("def attempt_recovery", 1)[1]  # no self-recursive call
