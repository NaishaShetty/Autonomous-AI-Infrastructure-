"""Phase 4.10 -- unit coverage for the ablation helpers."""
from src.phase4.ablations import NullUncertaintyPredictor, RetryDisabledCalibrationProfile
from src.phase4.agent_calibration import AgentDecisionCalibrationProfile, BucketStats, AGREEMENT_BUCKETS
from src.phase4.architecture import AutonomyState, Prediction
from src.data_foundation.foundation import Provenance, TimestampQuality


def _prediction(score: float) -> Prediction:
    return Prediction(
        prediction_id="p", job_id="j", snapshot_id="s", decision_time="2020-01-01T00:00:00Z", score=score,
        provenance=Provenance(source="test", source_version="v", extraction_method="m", transformation="t",
                               transformation_version="v", timestamp_source="s", timestamp_quality=TimestampQuality.EXACT),
    )


def test_null_predictor_always_returns_the_fixed_score_regardless_of_events():
    predictor = NullUncertaintyPredictor(fixed_score=0.5)
    p1 = predictor.predict_from_events("j1", [], None, "2020-01-01T00:00:00Z", "2020-01-01T00:00:00Z")
    p2 = predictor.predict_from_events("j2", [{"event_type": "telemetry_observed"}] * 50, None, "2020-01-01T00:00:00Z", "2020-01-01T00:00:01Z")
    assert p1.score == p2.score == 0.5


def test_null_predictor_score_is_clipped_to_unit_interval():
    predictor = NullUncertaintyPredictor(fixed_score=5.0)
    p = predictor.predict_from_events("j", [], None, "t", "t")
    assert p.score == 1.0


def test_retry_disabled_wrapper_remaps_retry_to_review():
    stats = {b: BucketStats(bucket=b, n_observed=100, n_correct=30, n_retry_observed=100, n_retry_correct=95) for b in AGREEMENT_BUCKETS}
    base = AgentDecisionCalibrationProfile(bucket_stats=stats, calibration_seed_range=(0, 100))
    wrapped = RetryDisabledCalibrationProfile(base_profile=base)

    base_decision = base.decide(_prediction(0.5), current_n_samples=5)
    assert base_decision.decision == "RETRY"  # sanity: this bucket really does prefer RETRY

    wrapped_decision = wrapped.decide(_prediction(0.5), current_n_samples=5)
    assert wrapped_decision.decision == "REVIEW"
    assert wrapped_decision.next_state == AutonomyState.ESCALATED.value
    assert "retry-disabled" in wrapped_decision.rationale


def test_retry_disabled_wrapper_also_remaps_answer_since_it_reaches_the_same_planner_path():
    """ANSWER and RETRY both let AutonomyPipeline reach the planner, which
    picks RETRY as its top candidate for AGENT_INCORRECT_ANSWER regardless
    of which label produced the decision -- a real ablation must block
    both, not just literal "RETRY" decisions."""
    stats = {b: BucketStats(bucket=b, n_observed=100, n_correct=100, n_retry_observed=100, n_retry_correct=100) for b in AGREEMENT_BUCKETS}
    base = AgentDecisionCalibrationProfile(bucket_stats=stats, calibration_seed_range=(0, 100))
    wrapped = RetryDisabledCalibrationProfile(base_profile=base)

    base_decision = base.decide(_prediction(0.0), current_n_samples=5)
    assert base_decision.decision in ("ANSWER", "RETRY")

    wrapped_decision = wrapped.decide(_prediction(0.0), current_n_samples=5)
    assert wrapped_decision.decision == "REVIEW"


def test_retry_disabled_wrapper_passes_through_non_retry_decisions_unchanged():
    stats = {b: BucketStats(bucket=b, n_observed=100, n_correct=0, n_retry_observed=100, n_retry_correct=0) for b in AGREEMENT_BUCKETS}
    base = AgentDecisionCalibrationProfile(bucket_stats=stats, calibration_seed_range=(0, 100))
    wrapped = RetryDisabledCalibrationProfile(base_profile=base)

    base_decision = base.decide(_prediction(1.0), current_n_samples=5)
    wrapped_decision = wrapped.decide(_prediction(1.0), current_n_samples=5)
    assert wrapped_decision.decision == base_decision.decision
    assert wrapped_decision.decision != "RETRY"
