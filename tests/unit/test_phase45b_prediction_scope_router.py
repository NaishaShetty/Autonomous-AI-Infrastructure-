"""Phase 4.5b -- honest fix for "recognize when it's likely wrong".

Verifies the actual mechanism, not just that classes import: a model
trained/evaluated ONLY on the predictable scope (real telemetry precursor)
has real discriminative skill, a router built from it routes correctly by
workload mode, and the fallback path for non-predictable modes is honestly
labeled rather than pretending to be a genuine prediction.
"""
import tempfile
from pathlib import Path

from src.phase4.prediction import (
    PREDICTABLE_FAILURE_CLASSES,
    PREDICTABLE_MODES,
    PredictionScopeRouter,
    TrainedRiskPredictor,
)
from src.phase4.prediction_training import (
    SplitSeeds,
    compute_fallback_priors,
    generate_corpus_rows,
    restrict_to_predictable_scope,
    train_and_persist_scope_router,
)


def test_predictable_taxonomy_matches_the_class_with_a_measured_real_precursor():
    # PROCESS_OOM was originally assumed to belong here too, but measured
    # in isolation it has no more precursor than the instant-failing
    # classes (AUC ~0.46, no better than chance) -- see prediction.py's
    # module-level comment for the real measurement that corrected this.
    assert PREDICTABLE_FAILURE_CLASSES == frozenset({"PROCESS_TIMEOUT"})
    assert PREDICTABLE_MODES == frozenset({"cpu"})


def test_restrict_to_predictable_scope_keeps_only_cpu_and_oom_mode_rows():
    rows = generate_corpus_rows(list(range(0, 40)), split="unit-scope", timeout_seconds=0.15)
    assert rows, "expected rows from a 40-seed corpus"
    modes_present = {r.mode for r in rows}
    assert modes_present, "CorpusRow.mode must be populated"

    scoped = restrict_to_predictable_scope(rows)
    assert scoped, "expected at least some cpu/oom-mode rows in a 40-seed corpus"
    assert all(r.mode in PREDICTABLE_MODES for r in scoped)
    # Sanity: some rows must have been excluded (this corpus covers every family)
    assert len(scoped) < len(rows)


def test_compute_fallback_priors_uses_run_level_labels_not_checkpoint_level():
    from src.phase4.prediction_training import CorpusRow

    # Two runs of the same mode, one failing (3 checkpoints), one healthy
    # (1 checkpoint) -- a naive per-row average would skew toward the
    # failing run just because it has more checkpoints; per-run must not.
    rows = [
        CorpusRow(seed=1, split="train", run_id="r-fail", workload_id="w1", failure_class="GPU_DEVICE_FAILURE", label=1, checkpoint_index=0, checkpoint_time="t0", time_to_failure_seconds=0.01, features=(0, 0, 0, 0), mode="gpu"),
        CorpusRow(seed=1, split="train", run_id="r-fail", workload_id="w1", failure_class="GPU_DEVICE_FAILURE", label=1, checkpoint_index=1, checkpoint_time="t1", time_to_failure_seconds=0.005, features=(0, 0, 0, 0), mode="gpu"),
        CorpusRow(seed=1, split="train", run_id="r-fail", workload_id="w1", failure_class="GPU_DEVICE_FAILURE", label=1, checkpoint_index=2, checkpoint_time="t2", time_to_failure_seconds=0.001, features=(0, 0, 0, 0), mode="gpu"),
        CorpusRow(seed=2, split="train", run_id="r-ok", workload_id="w2", failure_class=None, label=0, checkpoint_index=0, checkpoint_time="t0", time_to_failure_seconds=None, features=(0, 0, 0, 0), mode="gpu"),
    ]
    priors = compute_fallback_priors(rows)
    assert priors["gpu"] == 0.5  # one failing run, one healthy run -> 0.5, not 0.75


def test_a_model_trained_only_on_predictable_scope_has_real_discriminative_skill():
    """The whole point of the fix: restricted to the population with a
    genuine precursor, the model's AUC must be meaningfully above chance --
    not asserted to hit a specific cherry-picked number, just clearly
    better than the ~0.5 blended aggregate this is fixing."""
    seeds = SplitSeeds(train=range(0, 400), validation=range(2000, 2100), test=range(4000, 4100))
    with tempfile.TemporaryDirectory() as tmp:
        result = train_and_persist_scope_router(seeds, tmp, timeout_seconds=0.15)

        predictable = result["scoped_test_metrics"]["predictable_scope"]
        assert predictable["n"] > 0
        assert predictable["auc"] is not None
        # Report exactly what was measured; only assert the direction the
        # architectural fix claims to produce (real, clearly-above-chance
        # skill in-scope, not a specific cherry-picked decimal -- separate
        # isolated measurement put timeout-only AUC at ~0.63).
        assert predictable["auc"] > 0.55, f"expected real discriminative skill in predictable scope, measured AUC={predictable['auc']}"

        detectable_only = result["scoped_test_metrics"]["detectable_only_scope"]
        assert detectable_only["n"] > 0  # the corpus does include these classes

        router = PredictionScopeRouter.load(tmp)
        assert 0.0 <= router.calibrator.threshold <= 1.0


def test_router_delegates_to_the_trained_model_for_predictable_modes():
    seeds = SplitSeeds(train=range(0, 60), validation=range(1000, 1010), test=range(2000, 2010))
    with tempfile.TemporaryDirectory() as tmp:
        train_and_persist_scope_router(seeds, tmp, timeout_seconds=0.15)
        router = PredictionScopeRouter.load(tmp)

    prediction = router.predict_from_events(
        job_id="j1", events_prefix=[], configured_timeout_seconds=1.0,
        run_start_iso="2026-01-01T00:00:00Z", at_time_iso="2026-01-01T00:00:00Z",
        workload_type="timeout_via_cpu", parameters={"mode": "cpu"},
    )
    assert prediction.provenance.extraction_method == "engineered_feature_rule"
    assert "sklearn_model" in prediction.provenance.transformation


def test_router_returns_an_honestly_labeled_fallback_for_non_predictable_modes():
    router = PredictionScopeRouter(
        predictable_model=None,  # never touched for a non-predictable mode
        fallback_priors={"gpu": 0.83},
        default_fallback=0.5,
    )
    prediction = router.predict_from_events(
        job_id="j1", events_prefix=[], configured_timeout_seconds=1.0,
        run_start_iso="2026-01-01T00:00:00Z", at_time_iso="2026-01-01T00:00:00Z",
        workload_type="gpu", parameters={"mode": "gpu"},
    )
    assert prediction.score == 0.83
    assert prediction.provenance.extraction_method == "no_precursor_available_fallback_prior"

    # An unrecognized mode with no specific prior falls back to the
    # explicit default, not a silently guessed model score.
    unknown = router.predict_from_events(
        job_id="j2", events_prefix=[], configured_timeout_seconds=1.0,
        run_start_iso="2026-01-01T00:00:00Z", at_time_iso="2026-01-01T00:00:00Z",
        workload_type="mystery", parameters={"mode": "mystery"},
    )
    assert unknown.score == 0.5
    assert unknown.provenance.extraction_method == "no_precursor_available_fallback_prior"


def test_evaluate_by_scope_reports_blended_aggregate_alongside_the_split_metrics():
    """The old misleading blended number must still be visible for direct
    comparison, not hidden -- the fix is honesty about scope, not deletion
    of the inconvenient number."""
    seeds = SplitSeeds(train=range(0, 60), validation=range(1000, 1010), test=range(2000, 2010))
    result = train_and_persist_scope_router(seeds, tempfile.mkdtemp(), timeout_seconds=0.15)
    scoped = result["scoped_test_metrics"]
    assert "router_combined_output_all_scopes" in scoped
    assert "predictable_scope" in scoped
    assert "detectable_only_scope" in scoped
