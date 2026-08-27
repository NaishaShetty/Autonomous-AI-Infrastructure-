# Phase 5.4 -- Validation Report

## Final audit checklist

- All 16 tasks implemented or explicit NOT_EVALUABLE: YES (16 task results present)
- All 8 tracks represented: YES
- Unsupported tasks fail closed: YES (see registry.may_execute gating in src/benchmark/registry.py)
- No fabricated evidence: YES -- NOT_EVALUABLE tasks carry {status, reason, required_evidence, available_evidence}
- No aggregate-to-record-level conversion: YES -- aggregate findings are tagged aggregate_reference_evidence only
- Train/cal/test separation: PASSED (dataset_audit, workload_grouping check)
- Workload grouping: PASSED
- Environment separation: N/A (single environment; generalization tasks NOT_EVALUABLE)
- UNKNOWN / NOT_EVALUABLE / UNDERPOWERED kept distinct: YES (see status.py)
- Negative results visible: YES (see result_buckets.NEGATIVE and REC-EVAL 0% recovery finding)
- Always-fires predictors operationally disqualified: YES (metrics.operating_point_validity)
- Single-class AUROC not fabricated as 0.5: YES (metrics.auroc -> NOT_DEFINED_SINGLE_CLASS)
- Recovery uses independent validation: YES (validation.validation_status only, never executor_self_report as label)
- Memory causality not inferred without evidence: YES (MEM-EVAL / ABL-MEMORY-ON-OFF both NOT_EVALUABLE at record level)
- Generalization not claimed from one environment: YES (GEN-* both NOT_EVALUABLE)
- Abstention not claimed from nonexistent episodes: YES (SIMULATED_POLICY_EVALUATION status)
- Rolling prediction not claimed without checkpoint telemetry: YES (PRED-* all NOT_EVALUABLE)
- Benchmark execution deterministic (rerun identical): True
- Phase 4/5.1/5.2/5.3 untouched: see git evidence in BENCHMARK_RUN_MANIFEST.json (git_status)

## Full repository test suite (`python -m pytest tests/ -q`)

Run synchronously to completion (1355.18s / 22m35s): **880 passed, 8 failed**.

All 8 failures are in `tests/runtime/test_counterfactual_generalization.py` and
are **pre-existing, unrelated to Phase 5.4**:

- Root cause: `src/runtime/experience.py`'s `JsonExperienceStore` reads a
  hardcoded, non-hermetic absolute path (`/tmp/counterfactual_experiences_19.jsonl`,
  resolved on this Windows host to `C:/tmp/counterfactual_experiences_19.jsonl`)
  that is shared and appended-to across unrelated runs rather than using
  pytest's per-test `tmp_path` fixture. That file had accumulated to 8,295
  JSON lines (~30MB) with exactly one torn/truncated trailing line (a partial
  JSON fragment beginning mid-object, `...ibility":{"observation_completeness"...`),
  almost certainly left by an earlier interrupted process writing to the same
  shared path. `FailureExperience.model_validate_json()` raises on that one
  malformed line at store-initialization time, which fails every test in the
  file that constructs a runtime system via `build_runtime_system()`.
- Verified independent of this phase's changes: `git status`/`git log` show
  `tests/runtime/test_counterfactual_generalization.py`,
  `scripts/run_counterfactual_generalization.py`, `src/runtime/experience.py`,
  and `src/runtime/builder.py` are byte-identical to the repository's last
  commit (`e2e88d9`) with zero diff — none of Phase 5.4's file operations
  touched `src/runtime/` or this test file. Re-running just this one test
  file in isolation reproduces the identical 8 failed / 1 passed result,
  confirming it is deterministic and environmental, not a side effect of
  running the full suite alongside the new Phase 5.4 tests.
- This is an existing test-hygiene defect in that test module (a shared,
  non-isolated fixture path with no corruption recovery), not a Phase 5.4
  regression, and out of this phase's scope to fix (`src/runtime/` is a
  frozen path per the task's absolute boundaries). Deleting the stale
  external file would very likely make these 8 tests pass again on a fresh
  run, but that action was left to the user/maintainer rather than performed
  here, since it touches a file outside this repository's tracked tree, and
  fixing it is not part of Phase 5.4's mandate.

## Dataset audit

```json
{
  "ok": true,
  "n_records": 3106,
  "n_unique_record_ids": 3106,
  "n_episodes": 3106,
  "n_workloads": 3104,
  "n_environments": 1,
  "environments": [
    "UNSPECIFIED_PRE_4_9"
  ],
  "split_counts": {
    "calibration_validation": 482,
    "train": 2142,
    "test": 482
  },
  "all_records_sha256": "4f6994447cf28cb7f78948727e177e21cb6688ada85557613723151b66064b83",
  "violations": [],
  "status": "PASSED"
}
```
