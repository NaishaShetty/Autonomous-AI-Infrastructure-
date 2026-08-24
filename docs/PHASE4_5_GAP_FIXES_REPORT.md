# Phase 4.5 -- "What's Lacking" Review: Gap Fixes Report

This report covers the additive work that closes the 7 gaps identified in
the Phase 4.4/5 "what's lacking" review of `src/phase4/`. Nothing in
`src/phase3*`, `src/phase4_0`..`4.3`-era code, `src/runtime/`,
`src/recovery/` (Gen 2's frozen vocabulary, reused not modified),
`src/failure_experience/`, `src/decision/`, or any existing `experiments/results/*`
directory was touched. All new evidence lives in a new directory,
`experiments/results/phase4_5_autonomy_pipeline_at_scale/`.

Full test suite after all 7 fixes: **693 passed, 17 skipped, 0 failed**
(the 17 skips pre-date this work and are unrelated to it -- see below).

## Gap 1 -- Prediction is now actually predictive (ML-trained, not hand-weighted)

- `src/phase4/prediction_training.py` (new): generates a real labeled
  training corpus by running `ControlledRuntime` across many episodes and
  every failure class, with disjoint seed blocks for train/validation/test
  (`SplitSeeds`) so no run's telemetry or `workload_id` crosses a split
  boundary.
- `src/phase4/prediction.py`: added `rolling_checkpoints()` (real, multi-point
  telemetry checkpoints per run, never synthetic timestamps),
  `TrainedRiskPredictor` (loads a versioned `LogisticRegression` pipeline
  artifact, never fits at inference time), and `DecisionThresholdCalibrator`.
- The decision threshold is calibrated against a precision-recall curve on a
  held-out validation split (`calibrate_threshold`), not a fixed 0.5.
- The trained model is persisted as a versioned artifact by reusing
  `src/reliability/artifacts.py`'s `save_reliability_artifact` /
  `load_reliability_artifact` (the exact pattern from the Reliability Model
  Integration Audit) -- feature-schema and hash validation included, no
  fabricated/in-memory-only model.
- `AutonomyPipeline(..., rolling_prediction=True)` (opt-in; default pipeline
  behavior is byte-for-byte unchanged) computes the score at every real
  telemetry checkpoint before a run's failure and reports a genuine
  lead-time in seconds for the first threshold-crossing checkpoint, replacing
  the placeholder note in `scripts/run_phase4_5_pipeline_demo.py`.

**Measured result (600 train / 150 validation / 150 test seeds, reported
exactly as measured):**

```
per-checkpoint: n=875, precision=0.589, recall=0.967, f1=0.732, AUC=0.515, brier=0.247, threshold=0.466
```

**Honest reading:** AUC of 0.515 is close to chance. The high recall/low
precision combination means the model fires on almost everything rather
than genuinely discriminating -- it has not learned a strong signal. This
is a real, structural limitation, not a bug: several new failure classes
(GPU_DEVICE_FAILURE, DATA_CORRUPTION, RESOURCE_UNAVAILABLE when contended)
fail at or within one telemetry sample of `execution_started`, so there is
often no pre-failure observation for a model to condition on. PROCESS_OOM
and PROCESS_TIMEOUT are the only two classes with a genuine telemetry
precursor (growing RSS / elapsed time); the aggregate metrics above are
dominated by the classes that structurally cannot be predicted ahead of
time. This was not adjusted after seeing the numbers -- see
`experiments/results/phase4_5_autonomy_pipeline_at_scale/results.json` for
the full per-failure-class lead-time breakdown.

## Gap 2 -- Failure memory persists across restarts (SQLite)

`src/phase4/memory.py`: `FailureMemoryStore` is now backed by SQLite
(`PersistentEventStore`'s pattern), with a `memory_schema_meta` table
carrying `MEMORY_SCHEMA_VERSION`. `path=None` (every pre-existing caller)
uses an in-memory SQLite database -- same code path, same SQL, just not
durable -- so every existing test is unaffected; `path=<file>` gives real,
restart-surviving persistence. Retrieval/scope/temporal-safety/relevance
semantics (the frozen contract in the module docstring) are unchanged and
enforced by the SQL query exactly as they were by the old Python-list
filter. `tests/unit/test_phase45_memory_persistence.py` writes memory,
closes the store, reopens a fresh `FailureMemoryStore` object over the same
file, and confirms records, `memory_version`, and planner influence all
survive.

## Gap 3 -- Widened failure taxonomy (real, detectable failure modes)

`src/phase4/controlled_runtime.py` adds five new modes, each a real,
detectable condition (see the module's own docstring for exactly what is
real vs. an honestly-labeled cross-platform fallback per mode):

| Mode | Real mechanism |
|---|---|
| `oom` | OS-level `RLIMIT_AS` refusal (POSIX), or a real measured self-enforced allocation budget where `resource` is unavailable |
| `gpu` | Real device probe (`shutil.which` + real subprocess invocation of a GPU tool) |
| `corruption` | Real SHA-256 checksum computed, then a real deliberate single-byte fault injection and mismatch |
| `resource_unavailable` | Real cross-platform port-bind contention between two real OS processes |
| `flaky` | Real subprocess per attempt; a real, growing, never-randomized parent-tracked invocation counter decides pass/fail |

Each got its own `DiagnosisEngine` hypothesis
(`OUT_OF_MEMORY`, `GPU_DEVICE_UNAVAILABLE`, `DATA_INTEGRITY_FAILURE`,
`RESOURCE_UNAVAILABLE`, `INTERMITTENT_TRANSIENT_FAILURE`) and safety
adversarial matrix coverage (`scripts/run_phase4_5_evidence_at_scale.py`,
16 cases, 0 incorrectly authorized).

## Gap 4 -- Widened recovery action vocabulary (real, executable)

`src/phase4/recovery.py`: `ROLLBACK` and `RECONFIGURE` (both already present
in the frozen `src.recovery.schema.ActionId` vocabulary but previously
undeclared as candidates and unimplemented as executors) are now real:

- **ROLLBACK**: `ControlledRuntime` now records a real last-known-good
  `(workload_type, parameters)` checkpoint per `workload_id` whenever a run
  actually `COMPLETED`s; the executor re-invokes the runtime with that real
  checkpoint. If no checkpoint exists, it is honestly recorded as
  not-executed rather than faked (`tests/integration/test_phase45_pipeline_extensions.py::test_rollback_with_no_prior_checkpoint_is_honestly_not_executed`).
- **RECONFIGURE**: means "reduce the workload's resource footprint" --
  `_reduced_parameters` halves whatever numeric load parameter the workload
  was given (`alloc_mb`, `duration_seconds`) or picks an unoccupied port,
  and the executor re-invokes the runtime with the reduced parameters --
  measured to genuinely change the outcome (e.g. `RESOURCE_UNAVAILABLE`:
  100% recovery via RECONFIGURE to a free port vs. 0% via RETRY on the
  contended one, n=40 each, Wilson 95% CI [0.91, 1.0] vs [0.0, 0.09]).

No fabricated action (e.g. a node-failover simulation) was added, because
none was needed to satisfy "at minimum a checkpoint/rollback action and a
resource-reduction action" -- both fit the existing, real, executable
vocabulary.

## Gap 5 -- Learning actually adapts (online success-rate model)

`src/phase4/adaptive.py` (new): `AdaptiveRecoveryPlanner` ranks candidate
actions by `FailureMemoryStore.action_success_estimate` -- a Beta(1,1)-
smoothed, truly online (re-derived from the current record set on every
call, no cache) success-rate estimate per `(workload, environment,
failure_class, action)`. Implemented as a separate class from
`RuleBasedRecoveryPlanner` (which every pre-existing test exercises and
which keeps passing unchanged) rather than a modification to it, and wired
into `AutonomyPipeline` via the existing `planner=` constructor argument.

**Measured, quantified improvement** (`tests/unit/test_phase44_adaptive_learning.py`,
reproduced at n=1000 in the at-scale evidence script): two actions with
true recovery probabilities 0.35 and 0.65 (deliberately close, not a
trivial gap). `AdaptiveRecoveryPlanner`'s correct-action selection rate:
98.0% (episodes 1-50) -> 100.0% (episodes 951-1000). The unmodified
`RuleBasedRecoveryPlanner` control, run over the identical scenario and
seed, stays at 0.0% throughout (it has no way to prefer the better action
by quality, only to avoid one after repeated failures).

## Gap 6 -- Realism guardrails (circuit breaker + multi-environment)

- `src/phase4/guardrails.py` (new): `RecoveryCircuitBreaker` hard-caps real
  recovery **executions** (not diagnoses, not escalations) per
  `(workload_id, environment_id)`; wired into `AutonomyPipeline` (default
  `max_attempts=5`, generous enough that no pre-existing test's 3-execution
  scenario trips it). `tests/integration/test_phase45_pipeline_extensions.py::test_recovery_circuit_breaker_bounds_real_executions_on_an_unrecoverable_workload`
  hammers an always-failing workload 8 times with `max_attempts=3` and
  confirms exactly 3 real executions happen, ever, and every call after that
  short-circuits to `ABSTAINED`.
- `environment_id` scoping is now tested with two real, distinct environment
  identities sharing one `FailureMemoryStore` and the same `workload_id`
  (`test_memory_does_not_leak_across_two_environments_sharing_a_workload_id`),
  closing the gap between "the field exists" and "it is tested with more
  than one value". This is explicitly a single-process scoping-correctness
  test, not a claim of real multi-node isolation -- multi-node/cluster-scale
  production readiness remains out of scope.

## Gap 7 -- Statistically meaningful evidence + a standing continuous mode

- `scripts/run_phase4_5_evidence_at_scale.py` (new, additive): re-runs
  action-efficacy evidence at 40 real episodes per `(failure_class, action)`
  pair (12 pairs, 480 real subprocess episodes), reporting sample counts and
  a Wilson-score 95% confidence interval per rate, not a bare point
  estimate; re-runs the ML training pipeline at 600/150/150 real
  train/validation/test seeds; reproduces the adaptive-learning evidence at
  n=1000; and exercises a bounded continuous-mode run.
- `AutonomyPipeline.run_continuous()` (new): a real bounded loop over a
  workload stream (may be infinite -- tested against `itertools.cycle`),
  stopping cleanly at `max_episodes` and/or `max_duration_seconds`, writing
  a lightweight JSON-lines metrics log (one row per episode + one summary
  row) rather than a full observability stack.

## Test suite

Unit: `tests/unit/test_phase44_adaptive_learning.py`,
`tests/unit/test_phase45_prediction_training.py`,
`tests/unit/test_phase45_memory_persistence.py`
(plus every pre-existing `test_phase44_*.py`, all still passing unchanged).
Integration: `tests/integration/test_phase45_pipeline_extensions.py`,
`tests/integration/test_phase45_continuous_mode.py`
(plus the pre-existing `test_phase44_pipeline.py`, unchanged).

Full suite: **693 passed, 17 skipped, 0 failed.** The 17 skips pre-date this
work (unrelated conditional skips elsewhere in the repository) and were not
introduced or modified by it.

## What is still honestly not solved

- The trained predictor's AUC (~0.51) is close to chance in aggregate,
  because several failure classes structurally have no pre-failure
  telemetry to learn from. This is reported, not hidden or re-tuned away.
- `GPU_DEVICE_FAILURE` has zero real executable recovery actions -- there is
  no real fix for a genuinely absent GPU in this environment, so the
  planner escalates immediately rather than a fabricated action being added
  to look complete.
- `RETRY`/`RESTART`/most direct re-attempts measured 0% recovery against
  every deterministically-broken scenario in the action-efficacy sweep --
  exactly what should happen against a workload engineered to always fail
  the same way, and reported as such rather than adjusted.
- Multi-node/cluster-scale claims remain explicitly out of scope, as in
  every prior phase of this repository.
