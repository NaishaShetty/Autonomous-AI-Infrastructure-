"""Phase 4.5b -- PredictionScopeRouter wired through the real AutonomyPipeline,
end to end, on real ControlledRuntime executions (not stubbed events).
"""
import pathlib
import tempfile

from src.phase4.controlled_runtime import ControlledRuntime, RuntimeConfig
from src.phase4.observability import PersistentEventStore
from src.phase4.pipeline import AutonomyPipeline
from src.phase4.prediction import PredictionScopeRouter
from src.phase4.prediction_training import SplitSeeds, train_and_persist_scope_router


def _pipeline(predictor, rolling_prediction=True):
    tmp = tempfile.TemporaryDirectory()
    store = PersistentEventStore(pathlib.Path(tmp.name) / "events.sqlite")
    config = RuntimeConfig(timeout_seconds=0.15, telemetry_interval_seconds=0.01)
    runtime = ControlledRuntime(store, config)
    pipeline = AutonomyPipeline(runtime, predictor=predictor, rolling_prediction=rolling_prediction)
    return pipeline, tmp


def test_router_produces_a_real_prediction_score_for_a_predictable_mode_run():
    seeds = SplitSeeds(train=range(0, 60), validation=range(1000, 1010), test=range(2000, 2010))
    with tempfile.TemporaryDirectory() as artifact_dir:
        train_and_persist_scope_router(seeds, artifact_dir, timeout_seconds=0.15)
        router = PredictionScopeRouter.load(artifact_dir)

        pipeline, tmp = _pipeline(router)
        try:
            # duration well past the configured timeout -- a genuine PROCESS_TIMEOUT
            result = pipeline.run_workload("timeout_via_cpu", {"mode": "cpu", "duration_seconds": 0.4})
        finally:
            tmp.cleanup()

        assert result.prediction_score is not None
        assert 0.0 <= result.prediction_score <= 1.0
        assert result.diagnosis is not None
        assert result.diagnosis.primary_hypothesis.name != "UNKNOWN"


def test_router_uses_the_honest_fallback_for_a_detectable_only_mode_run():
    seeds = SplitSeeds(train=range(0, 60), validation=range(1000, 1010), test=range(2000, 2010))
    with tempfile.TemporaryDirectory() as artifact_dir:
        train_and_persist_scope_router(seeds, artifact_dir, timeout_seconds=0.15)
        router = PredictionScopeRouter.load(artifact_dir)

        pipeline, tmp = _pipeline(router)
        try:
            result = pipeline.run_workload("gpu", {"mode": "gpu"})
        finally:
            tmp.cleanup()

        # gpu is real hardware-absence detection, always fails in this sandbox
        assert result.prediction_score is not None
        expected_fallback = router.fallback_priors.get("gpu", router.default_fallback)
        assert result.prediction_score == expected_fallback


def test_router_threshold_delegates_to_the_predictable_scope_models_calibrator():
    seeds = SplitSeeds(train=range(0, 60), validation=range(1000, 1010), test=range(2000, 2010))
    with tempfile.TemporaryDirectory() as artifact_dir:
        train_and_persist_scope_router(seeds, artifact_dir, timeout_seconds=0.15)
        router = PredictionScopeRouter.load(artifact_dir)
        assert router.calibrator is router.predictable_model.calibrator
        assert 0.0 <= router.calibrator.threshold <= 1.0
