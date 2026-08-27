# Reproducibility Guide

## Environment used to produce the reference results

- Python: 3.11.3 (MSC v.1934 64 bit, AMD64)
- OS: Windows-10-AMD64
- Dependencies (exact versions): numpy 2.4.6, pandas 3.0.5, scipy 1.17.1,
  scikit-learn 1.9.0 (see `requirements.txt`)
- Bootstrap seed: 20260826 (1000 resamples, 95% percentile CI)
- config_hash (task_ids + n_records fingerprint):
  `d8d349a545a1910bfada66de5628cf3ebb52c50f9a15465dd34840ab8de5e08b`
- Dataset SHA-256 (`experiments/results/phase5_dataset_construction/20260826T054422Z/dataset/all_records.jsonl`):
  `4f6994447cf28cb7f78948727e177e21cb6688ada85557613723151b66064b83`

## Steps

1. `pip install -r requirements.txt`
2. `python scripts/run_phase5_4_benchmark.py --out-dir <any writable dir>`
3. Compare `<out-dir>/PHASE5_4_BENCHMARK_RESULTS.json` against the
   reference values in `BENCHMARK_CARD.md` and the frozen
   `experiments/results/phase5_benchmark_implementation/` artifacts in the
   parent repository (not bundled in this package, since they are a
   record of one specific historical run, not part of the benchmark
   definition itself).

## What must match exactly

- `dataset_audit.all_records_sha256` — proves the bundled dataset is
  byte-identical to the one used to produce every reference number.
- `determinism_check` — every field `true` (the runner performs its own
  internal double-run).
- `task_results` for the 3 uncertainty tasks (the only track with a full
  ranking-metric evaluation) — AUROC/AUPRC/Brier/ECE point estimates
  should match `BENCHMARK_CARD.md` exactly (deterministic given the fixed
  dataset and fixed seeds); bootstrap CIs will also match exactly because
  the bootstrap seed is fixed.

## What may legitimately differ

- `reproducibility.platform` / `python_version` / `dependency_versions`
  will reflect whatever machine you run this on — this does not indicate
  a reproducibility failure as long as `task_results` matches.
- `reproducibility.code_commit` / `git_status` will be `null` /
  `{"clean": null, ...}` if you run this package outside a git
  repository (e.g. from a clean-room extraction) — this is expected and
  handled gracefully by `src/benchmark/reproducibility.py` (a failed
  `git` subprocess call returns `None` rather than raising).

## Known, pre-existing, out-of-scope test failures

None. This package's own test suite (`tests/test_phase54_benchmark.py`)
is fully green (41/41) in isolation. The parent repository has 8
unrelated, pre-existing failures in a different, non-benchmark test file
(`tests/runtime/test_counterfactual_generalization.py`, caused by a
non-hermetic hardcoded path in `src/runtime/experience.py`) — that file
and that runtime module are **not part of this release package** and are
not reachable from any code in `src/benchmark/`.
