# Phase 5.3/5.4 Benchmark — Release Package

An executable benchmark of 16 tasks across 8 tracks (uncertainty,
abstention, failure prediction, diagnosis, recovery, memory,
generalization, end-to-end), scored over the Phase 5.2 canonical dataset.

**What this is**: a scoring harness that loads a fixed dataset, validates
it, scans for leakage, executes every task that has enough evidence to
score, and reports a per-task capability matrix — never a single overall
number.

**What this is NOT**: a claim that the underlying system (the "Autonomous
AI Infrastructure" project) reliably predicts failures, recovers from
them, or generalizes across environments. Of the 16 tasks, 0 are
VALIDATED, 6 are PARTIALLY_VALIDATED (real but limited evidence), 3 are
UNDERPOWERED (real point estimates, insufficient sample for a headline
claim), and 7 are NOT_EVALUABLE (the current dataset lacks the evidence
these tasks require). See `BENCHMARK_CARD.md` for the full capability
matrix and `PHASE5_3_LIMITATIONS.md` for every disclosed gap.

## Contents

```
src/benchmark/        executable implementation (runner, tasks, metrics,
                       baselines, ablations, leakage checks, validation,
                       reporting, reproducibility metadata)
src/phase5/            failure_mapping.py (diagnosis->failure-class map)
experiments/results/   frozen specification + the exact dataset this
                       benchmark is defined against (see below)
scripts/               run_phase5_4_benchmark.py (the runner entry point),
                       generate_sha256_manifest.py
tests/                 test_phase54_benchmark.py (unit tests)
```

The `experiments/results/...` subtree preserves the exact relative path
layout the implementation expects (`src/benchmark/constants.py` resolves
paths relative to this package's own root) — do not flatten or rename
these directories.

## Quick start

```
pip install -r requirements.txt
python scripts/run_phase5_4_benchmark.py --out-dir /tmp/my_run
```

This loads the bundled dataset, validates it (fail-closed on any
violation), scans for leakage, executes all 16 tasks (scoring where
supported, `NOT_EVALUABLE` where not), runs the 5 ablations, builds the
capability matrix, runs the whole thing **twice** to verify determinism,
and writes `PHASE5_4_BENCHMARK_RESULTS.json`, `BENCHMARK_RUN_MANIFEST.json`,
`PHASE5_4_BENCHMARK_REPORT.md`, `PHASE5_4_VALIDATION_REPORT.md`,
`PHASE5_4_LIMITATIONS.md`, `PHASE5_4_SYNTHESIS.md`, and a SHA-256 manifest
to `--out-dir`.

## Reproducing the uncertainty-track results

The uncertainty track (`UNC-ARITH`, `UNC-SENT`, `UNC-QA`) is the only
track with enough per-episode evidence to compute full ranking metrics
(AUROC/AUPRC/Brier/ECE) end-to-end from this package alone — see
`BENCHMARK_CARD.md`. Running the quick-start command reproduces these
exactly; see `REPRODUCIBILITY_GUIDE.md` for the full protocol and expected
values.

## Tests

```
python -m pytest tests/ -q
```

## Documentation

- `BENCHMARK_CARD.md` — what each task measures, evidence, sample size,
  status, limitation, one line each.
- `REPRODUCIBILITY_GUIDE.md` — full protocol, environment, seeds, expected
  outputs.
- `CITATION.cff` — how to cite this benchmark.
- `experiments/results/phase5_benchmark_specification/20260826T055915Z/`
  — the frozen specification this implementation follows exactly
  (`PHASE5_3_BENCHMARK_SPECIFICATION.md`, `PHASE5_3_TASK_CATALOG.json`,
  `PHASE5_3_METRIC_CATALOG.json`, `PHASE5_3_LIMITATIONS.md`,
  `PHASE5_3_LEAKAGE_POLICY.md`).

## License / provenance

This benchmark implementation and its bundled dataset copy are released
under the same terms as the parent project (see the parent repository's
license). The dataset is derived exclusively from this project's own
Gen-3 evidence — no third-party dataset content is included (see
`DATASET_CARD.md` equivalent disclosures under the dataset package).
