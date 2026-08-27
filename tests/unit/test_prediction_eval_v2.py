"""Phase 4.8 -- unit coverage for the leak-free, per-failure-class
prediction evaluation harness."""
import subprocess
import sys

from src.phase4.prediction_eval_v2 import (
    ALL_EVALUATED_MODES,
    BIMODAL_FAMILY_MODES,
    DETERMINISTIC_MODES,
    _ece,
    _shuffle_labels_by_run,
    _stable_seed,
    evaluate_all_families,
    evaluate_family,
)
from src.phase4.prediction_training import CorpusRow, SplitSeeds, generate_corpus


def test_deterministic_modes_are_reported_not_predictable_not_fabricated():
    # 'gpu' is excluded from the unconditional assertion below -- it is the
    # one DETERMINISTIC_MODES entry whose determinism is an environment fact,
    # not a code fact (see evaluate_all_families's own real-GPU-machine
    # carve-out a few tests down, and src/phase4/gpu_probe.py for the P3-W7
    # background this test used to silently assume away). On a machine with
    # a real GPU probe tool available, 'gpu' can legitimately produce both
    # labels and evaluate as EVALUATED rather than NOT_PREDICTABLE_SINGLE_CLASS.
    always_deterministic = {m: c for m, c in DETERMINISTIC_MODES.items() if m != "gpu"}
    seeds = SplitSeeds(train=range(0, 150), validation=range(2000, 2050), test=range(4000, 4050))
    corpus = generate_corpus(seeds, timeout_seconds=0.15)
    for mode, failure_class in always_deterministic.items():
        result = evaluate_family(mode, failure_class, corpus)
        assert result.status == "NOT_PREDICTABLE_SINGLE_CLASS"
        assert "NOT PREDICTABLE" in result.note
        assert result.metrics is None
    gpu_result = evaluate_family("gpu", DETERMINISTIC_MODES["gpu"], corpus)
    assert gpu_result.status in ("NOT_PREDICTABLE_SINGLE_CLASS", "EVALUATED")


def test_ece_is_zero_for_perfectly_calibrated_scores():
    y = [1] * 10 + [0] * 10
    scores = [1.0] * 10 + [0.0] * 10
    assert _ece(y, scores) == 0.0


def test_shuffle_labels_by_run_preserves_marginal_rate_and_row_count():
    rows = [
        CorpusRow(seed=i, split="train", run_id=f"r{i}", workload_id=f"w{i}", failure_class=None,
                   label=(1 if i % 2 == 0 else 0), checkpoint_index=0, checkpoint_time="t", time_to_failure_seconds=None,
                   features=(0.0, 0.0, 0.0, 0.0), mode="cpu")
        for i in range(20)
    ]
    shuffled = _shuffle_labels_by_run(rows, seed=1)
    assert len(shuffled) == len(rows)
    assert sum(r.label for r in shuffled) == sum(r.label for r in rows)  # same marginal label rate
    # every row for a given run_id still carries the SAME (shuffled) label
    by_run = {}
    for r in shuffled:
        by_run.setdefault(r.run_id, set()).add(r.label)
    assert all(len(v) == 1 for v in by_run.values())


def test_shuffle_preserves_within_run_label_consistency_across_multiple_checkpoints_per_run():
    rows = [
        CorpusRow(seed=1, split="train", run_id="r1", workload_id="w1", failure_class=None, label=1,
                   checkpoint_index=i, checkpoint_time="t", time_to_failure_seconds=None,
                   features=(0.0, 0.0, 0.0, 0.0), mode="cpu")
        for i in range(5)
    ] + [
        CorpusRow(seed=2, split="train", run_id="r2", workload_id="w2", failure_class=None, label=0,
                   checkpoint_index=i, checkpoint_time="t", time_to_failure_seconds=None,
                   features=(0.0, 0.0, 0.0, 0.0), mode="cpu")
        for i in range(5)
    ]
    shuffled = _shuffle_labels_by_run(rows, seed=7)
    r1_labels = {r.label for r in shuffled if r.run_id == "r1"}
    r2_labels = {r.label for r in shuffled if r.run_id == "r2"}
    assert len(r1_labels) == 1
    assert len(r2_labels) == 1


def test_stable_seed_is_deterministic_within_a_process():
    assert _stable_seed("phase4.8-label-shuffle", "cpu") == _stable_seed("phase4.8-label-shuffle", "cpu")
    assert _stable_seed("phase4.8-label-shuffle", "cpu") != _stable_seed("phase4.8-label-shuffle", "oom")


def test_stable_seed_is_independent_of_pythonhashseed_regression():
    """Regression test for a real defect: the shuffled-label negative
    control's seed used to be derived from ``hash((str, str))``, which
    Python salts per-process via PYTHONHASHSEED (randomized by default)
    -- so despite the caller's comment claiming a "fixed, reproducible"
    seed, it silently changed on every interpreter invocation, including
    across separate pytest runs/workers. ``_stable_seed`` must use a
    process-independent digest (hashlib) instead of the builtin hash()."""
    script = (
        "from src.phase4.prediction_eval_v2 import _stable_seed; "
        "print(_stable_seed('phase4.8-label-shuffle', 'cpu'))"
    )
    seeds = set()
    for hash_seed in ("0", "1", "42"):
        env = {"PYTHONHASHSEED": hash_seed}
        import os
        env.update(os.environ)
        env["PYTHONHASHSEED"] = hash_seed
        out = subprocess.run(
            [sys.executable, "-c", script], cwd=str(__file__.rsplit("tests", 1)[0]),
            env=env, capture_output=True, text=True, check=True,
        )
        seeds.add(out.stdout.strip())
    assert len(seeds) == 1, f"seed varied across PYTHONHASHSEED values: {seeds}"


def test_all_evaluated_modes_covers_bimodal_and_deterministic():
    assert set(ALL_EVALUATED_MODES.keys()) == set(BIMODAL_FAMILY_MODES.keys()) | set(DETERMINISTIC_MODES.keys())


def test_evaluate_all_families_produces_macro_averages_and_never_fabricates_metrics_for_undefined_families():
    seeds = SplitSeeds(train=range(0, 400), validation=range(2000, 2100), test=range(4000, 4100))
    report = evaluate_all_families(seeds, timeout_seconds=0.15)
    # fail/network/corruption are unconditionally deterministic in this
    # sandbox (see controlled_runtime.py's subprocess code). 'gpu' is the
    # one exception the Phase 4.8 report documents explicitly: on a
    # machine that actually has a GPU probe tool available, the real
    # nvidia-smi/rocm-smi timeout race can occasionally produce both
    # outcome labels -- so its status is allowed to vary here rather than
    # asserted, while the other three are asserted unconditionally.
    always_deterministic = {"fail", "network", "corruption"}
    assert always_deterministic <= set(DETERMINISTIC_MODES)
    for mode in always_deterministic:
        assert report["families"][mode]["status"] == "NOT_PREDICTABLE_SINGLE_CLASS"
        assert report["families"][mode]["metrics"] is None
    for mode in BIMODAL_FAMILY_MODES:
        fam = report["families"][mode]
        assert fam["status"] in ("EVALUATED", "NOT_PREDICTABLE_SINGLE_CLASS")
        if fam["status"] == "EVALUATED":
            assert fam["metrics"]["threshold"] is not None
            assert fam["shuffled_control_metrics"] is not None
