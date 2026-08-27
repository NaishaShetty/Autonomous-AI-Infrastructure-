# Phase 5.5 — Determinism Audit

## Method

This project has twice previously found real nondeterminism masquerading
as benign (hash() salting; timestamp ties), so this audit does not stop at
"the script's own internal double-run reported identical" — it
independently re-executed the entire benchmark from a cold process, on a
different day, and diffed the result against the frozen Phase 5.4 artifact
byte-for-byte, in addition to the script's own built-in double-run.

## Run 1: this phase's independent fresh execution

`python scripts/run_phase5_4_benchmark.py --out-dir experiments/results/phase5_5_finalization_and_packaging/20260827T051355Z/gate_a_independent_rerun`

This itself performs an internal double run (run1/run2 within one process)
and reported:
```
{'task_results_identical': True, 'ablation_results_identical': True,
 'capability_matrix_identical': True, 'split_assignments_identical': True}
```

## Run 2: cross-process, cross-day comparison against the frozen Phase 5.4 artifact

Compared `experiments/results/phase5_5_finalization_and_packaging/20260827T051355Z/gate_a_independent_rerun/PHASE5_4_BENCHMARK_RESULTS.json`
(generated 2026-08-27, this session, fresh Python process) against
`experiments/results/phase5_benchmark_implementation/20260826T150824Z/PHASE5_4_BENCHMARK_RESULTS.json`
(generated 2026-08-26, a prior session):

| Field | Identical? |
|---|---|
| `task_results` (all 16 tasks, full metrics/CIs/baselines) | YES |
| `ablation_results` (all 5 ablations) | YES |
| `capability_matrix` | YES |
| `dataset_audit.all_records_sha256` | YES (`4f6994447cf28cb7f78948727e177e21cb6688ada85557613723151b66064b83`) |
| `leakage_scan` | YES |

No difference of any kind across a full day and two independent process
invocations. Sources of nondeterminism previously found in this project
(Python `hash()` ordering, timestamp-tie resolution) do not reproduce here:
`reproducibility.no_python_hash_used: true` is asserted by the
implementation and is consistent with the observed byte-identical rerun —
if hash-order dependence were present, dict/set iteration order differences
across process restarts (each Python process re-randomizes `hash()` seeding
by default) would very likely have produced at least one differing field
across two independent process starts. None did.

## Investigated, not just relabeled

- Bootstrap CIs use an explicit fixed seed (`BOOTSTRAP_SEED`, distinct
  per-metric offsets `seed`, `seed+1`, `seed+2`, `seed+3`) — confirmed by
  direct code reading of `metrics.ranking_with_ci`, not merely trusted from
  the reproducibility metadata's claim.
- Wilson CIs are closed-form (no RNG involved) — confirmed by direct code
  reading, eliminating one class of potential nondeterminism entirely.
- Split assignments are read verbatim from `split_assignment_manifest.json`
  fields already present on each record — not re-derived at benchmark run
  time — eliminating filesystem-iteration-order as a source of variance
  for split composition. Confirmed identical `split_counts` across runs.
- `config_hash` (`d8d349a545a1910bfada66de5628cf3ebb52c50f9a15465dd34840ab8de5e08b`)
  is identical between the two runs, confirming the effective configuration
  (task_ids, n_records) driving the run did not silently drift.

## Conclusion

No nondeterminism found. The benchmark is genuinely reproducible across
process restarts and across days, given the frozen dataset and code.
