"""Phase 4.7 -- unit coverage for AgentDecisionCalibrationProfile: the
train/calibration/test split, per-bucket probability estimation, the
expected-utility decision rule, and drop-in compatibility with
AutonomyDecision's decision/next_state contract.
"""
import pytest

from src.phase4.agent_calibration import (
    AGREEMENT_BUCKETS,
    AgentDecisionCalibrationProfile,
    AgentSplitSeeds,
    BucketStats,
    MAX_RETRY_N_SAMPLES,
    RETRY_SAMPLE_INCREASE_FACTOR,
    _bucket_for,
)
from src.phase4.architecture import AutonomyState, Prediction
from src.data_foundation.foundation import Provenance, TimestampQuality


def _prediction(score: float) -> Prediction:
    return Prediction(
        prediction_id="p", job_id="j", snapshot_id="s", decision_time="2020-01-01T00:00:00Z", score=score,
        provenance=Provenance(source="test", source_version="v", extraction_method="m", transformation="t",
                               transformation_version="v", timestamp_source="s", timestamp_quality=TimestampQuality.EXACT),
    )


def test_split_seeds_rejects_overlapping_ranges():
    with pytest.raises(ValueError):
        AgentSplitSeeds(train=range(0, 100), calibration=range(50, 150), test=range(200, 300))


def test_split_seeds_accepts_disjoint_ranges():
    seeds = AgentSplitSeeds(train=range(0, 100), calibration=range(100, 200), test=range(200, 300))
    assert seeds.train.stop <= seeds.calibration.start
    assert seeds.calibration.stop <= seeds.test.start


def test_bucket_for_covers_full_unit_interval():
    for x in (0.0, 0.2, 0.4, 0.4001, 0.6, 0.8, 0.9999, 1.0):
        bucket = _bucket_for(x)
        assert bucket in AGREEMENT_BUCKETS
        lo, hi = bucket
        assert lo <= x <= hi


def test_bucket_stats_laplace_smoothing_avoids_hard_zero_or_one():
    stats = BucketStats(bucket=(0.8, 1.0), n_observed=10, n_correct=10, n_retry_observed=10, n_retry_correct=0)
    assert 0.0 < stats.p_correct < 1.0
    assert 0.0 < stats.p_retry_success < 1.0


def test_fit_only_touches_the_calibration_split():
    seeds = AgentSplitSeeds(train=range(0, 50), calibration=range(1000, 1150), test=range(5000, 5150))
    profile = AgentDecisionCalibrationProfile.fit(seeds, base_n_samples=5)
    assert profile.calibration_seed_range == (1000, 1150)
    total_observed = sum(s.n_observed for s in profile.bucket_stats.values())
    assert total_observed == 150  # exactly the calibration split size, not train+calibration


def test_all_buckets_populated_after_fit_with_a_large_enough_calibration_range():
    seeds = AgentSplitSeeds(train=range(0, 50), calibration=range(1000, 2000), test=range(5000, 5150))
    profile = AgentDecisionCalibrationProfile.fit(seeds, base_n_samples=5)
    assert set(profile.bucket_stats.keys()) == set(AGREEMENT_BUCKETS)
    assert all(s.n_observed >= 0 for s in profile.bucket_stats.values())


def test_high_agreement_bucket_prefers_answer_or_retry_over_review_or_abstain():
    # Force a profile where the top bucket has near-perfect correctness and
    # near-perfect retry success -- utility calculation should clearly
    # favor autonomous action over REVIEW/ABSTAIN for that bucket.
    stats = {b: BucketStats(bucket=b, n_observed=100, n_correct=100, n_retry_observed=100, n_retry_correct=100) for b in AGREEMENT_BUCKETS}
    profile = AgentDecisionCalibrationProfile(bucket_stats=stats, calibration_seed_range=(0, 100))
    decision = profile.decide(_prediction(score=0.0), current_n_samples=5)  # score=0 -> agreement_rate=1.0
    assert decision.decision in ("ANSWER", "RETRY")
    assert decision.next_state == AutonomyState.DIAGNOSING.value


def test_low_agreement_low_retry_yield_bucket_prefers_review_or_abstain():
    # Bucket where neither answering now nor retrying helps (both near 0%
    # correct) -- utility calculation should never pick autonomous action.
    stats = {b: BucketStats(bucket=b, n_observed=100, n_correct=0, n_retry_observed=100, n_retry_correct=0) for b in AGREEMENT_BUCKETS}
    profile = AgentDecisionCalibrationProfile(bucket_stats=stats, calibration_seed_range=(0, 100))
    decision = profile.decide(_prediction(score=1.0), current_n_samples=5)  # score=1 -> agreement_rate=0.0
    assert decision.decision in ("REVIEW", "ABSTAIN")
    assert decision.next_state in (AutonomyState.ESCALATED.value, AutonomyState.ABSTAINED.value)


def test_retry_is_preferred_over_bare_answer_when_retry_recovers_much_more_often():
    # A bucket where the CURRENT answer is usually wrong but RETRYING
    # (more samples) usually fixes it -- this is exactly the situation the
    # generic policy could never act on (see PHASE4_5B report); the
    # calibrated profile should prefer RETRY here.
    stats = {b: BucketStats(bucket=b, n_observed=100, n_correct=30, n_retry_observed=100, n_retry_correct=95) for b in AGREEMENT_BUCKETS}
    profile = AgentDecisionCalibrationProfile(bucket_stats=stats, calibration_seed_range=(0, 100))
    decision = profile.decide(_prediction(score=0.5), current_n_samples=5)
    assert decision.decision == "RETRY"


def test_max_retry_n_samples_safety_cap_forecloses_retry_when_exceeded():
    stats = {b: BucketStats(bucket=b, n_observed=100, n_correct=30, n_retry_observed=100, n_retry_correct=95) for b in AGREEMENT_BUCKETS}
    profile = AgentDecisionCalibrationProfile(bucket_stats=stats, calibration_seed_range=(0, 100))
    huge_n = MAX_RETRY_N_SAMPLES  # current_n_samples * RETRY_SAMPLE_INCREASE_FACTOR will exceed the cap
    decision = profile.decide(_prediction(score=0.5), current_n_samples=huge_n)
    assert decision.decision != "RETRY"


def test_decide_rationale_and_utilities_are_populated_and_traceable():
    seeds = AgentSplitSeeds(train=range(0, 50), calibration=range(1000, 1400), test=range(5000, 5150))
    profile = AgentDecisionCalibrationProfile.fit(seeds, base_n_samples=5)
    decision = profile.decide(_prediction(score=0.2), current_n_samples=5)
    assert decision.decision in ("ANSWER", "RETRY", "ABSTAIN", "REVIEW")
    assert "agreement_rate=" in decision.rationale
    assert "p_correct=" in decision.rationale
    assert decision.utilities is not None
    assert decision.policy_version.startswith("phase4.7")
