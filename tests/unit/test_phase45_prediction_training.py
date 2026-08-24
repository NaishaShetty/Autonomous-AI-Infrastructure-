"""Phase 4.5 gap 1 -- unit coverage for the ML training/persistence path.

Uses a small corpus (fast, seconds not minutes) purely to prove the
mechanism works end to end: real subprocess-generated features, a real
fitted scikit-learn model, a real precision-recall-curve-calibrated
threshold, a real persisted-and-reloaded artifact. The large-scale, real
reported numbers live in ``experiments/results/phase4_5_prediction/`` via
``scripts/run_phase4_5_evidence_at_scale.py`` -- this test file is not where
performance claims are made.
"""
import tempfile
from pathlib import Path

from src.phase4.prediction import DECISION_THRESHOLD, DecisionThresholdCalibrator, FEATURE_NAMES, TrainedRiskPredictor
from src.phase4.prediction_training import SplitSeeds, calibrate_threshold, generate_corpus_rows, train_and_persist
from src.reliability.artifacts import ArtifactValidationError


def test_generate_corpus_rows_produces_both_labels_and_valid_feature_vectors():
    rows = generate_corpus_rows(list(range(0, 25)), split="unit-test", timeout_seconds=0.15)
    assert rows, "expected at least one rolling checkpoint row"
    labels = {r.label for r in rows}
    assert labels == {0, 1}, f"expected both healthy and failing runs in a 25-seed corpus, got labels={labels}"
    for row in rows:
        assert len(row.features) == len(FEATURE_NAMES)
        assert all(0.0 <= f <= 1.0 for f in row.features)
        assert row.split == "unit-test"


def test_rolling_checkpoints_never_include_the_runs_own_failure_event():
    rows = generate_corpus_rows(list(range(0, 25)), split="unit-test-2", timeout_seconds=0.15)
    failing_runs = {r.run_id for r in rows if r.label == 1}
    for row in rows:
        if row.run_id in failing_runs:
            assert row.time_to_failure_seconds is None or row.time_to_failure_seconds > 0


def test_train_and_persist_round_trips_through_a_real_artifact(tmp_path):
    seeds = SplitSeeds(train=range(0, 30), validation=range(500, 510), test=range(900, 910))
    result = train_and_persist(seeds, tmp_path, timeout_seconds=0.15)

    assert (tmp_path / "manifest.json").is_file()
    assert (tmp_path / "model.pkl").is_file()
    assert (tmp_path / "calibrator.pkl").is_file()
    assert (tmp_path / "metrics.json").is_file()

    metrics = result["test_metrics"]["per_checkpoint"]
    for key in ("precision", "recall", "f1", "brier_score", "true_positives", "false_positives", "false_negatives", "true_negatives"):
        assert key in metrics

    predictor = TrainedRiskPredictor.load(tmp_path)
    assert isinstance(predictor.calibrator, DecisionThresholdCalibrator)
    assert 0.0 <= predictor.calibrator.threshold <= 1.0

    prediction = predictor.predict_from_events(
        job_id="j1", events_prefix=[], configured_timeout_seconds=1.0,
        run_start_iso="2026-01-01T00:00:00Z", at_time_iso="2026-01-01T00:00:00Z",
    )
    assert 0.0 <= prediction.score <= 1.0


def test_loading_an_artifact_with_the_wrong_feature_schema_fails_closed(tmp_path):
    seeds = SplitSeeds(train=range(0, 30), validation=range(500, 510), test=range(900, 910))
    train_and_persist(seeds, tmp_path, timeout_seconds=0.15)
    try:
        TrainedRiskPredictor.load(tmp_path.__class__(tmp_path), baseline=None)  # sanity: correct schema loads
    except ArtifactValidationError:
        raise AssertionError("correct feature schema should load without error")

    import json
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["feature_names"] = ["totally", "different", "schema"]
    manifest_path.write_text(json.dumps(manifest))
    try:
        TrainedRiskPredictor.load(tmp_path)
        raise AssertionError("expected ArtifactValidationError for a mismatched feature schema")
    except ArtifactValidationError:
        pass


def test_calibrate_threshold_falls_back_to_default_when_validation_set_has_one_class():
    from src.phase4.prediction_training import CorpusRow

    single_class_rows = [CorpusRow(seed=1, split="validation", run_id="r1", workload_id="w1", failure_class=None, label=0, checkpoint_index=0, checkpoint_time="2026-01-01T00:00:00Z", time_to_failure_seconds=None, features=(0.0, 0.0, 0.0, 0.0))]

    class _StubModel:
        def predict_proba(self, x):
            return [[0.9, 0.1] for _ in x]

    assert calibrate_threshold(_StubModel(), single_class_rows) == 0.5
    assert calibrate_threshold(_StubModel(), []) == 0.5
