# Step 4 Protocol — P4 Environment Generalization Re-Evaluation

Pre-registered BEFORE running any evaluation or looking at any held-out/
robustness result. Builds on the pre-existing Phase 4.9 environment
infrastructure (`src/phase4/environments.py`: three genuinely distinct
`ControlledRuntime` configurations — `baseline_cpu` [development, role
that everything is fit/calibrated on], `memory_constrained` [held-out,
never fit on], `dependency_network_constrained` [robustness, never fit
on]) and the pre-existing zero-shot evaluation script
(`scripts/run_phase4_9_environment_generalization.py`, "Model A" below).

## Hypothesis

The prior finding was: OOM development AUROC ≈0.678 collapses to held-out
≈0.506 (chance). Root-cause hypothesis, developed from reading
`environments.py`'s `memory_constrained` profile and `prediction.py`'s
`extract_features`: the `rss_ratio` feature normalizes peak observed RSS
against `MonitoringBaseline.max_process_rss_bytes` — a **fixed 512MB
constant, identical in every environment** — with no relationship to the
`oom` mode's actual per-run `limit_mb` budget (32MB at baseline vs 8MB in
`memory_constrained`, a 4x difference). The same absolute RSS reading
therefore represents a very different "fraction of budget consumed"
depending on environment, and the original model was never told the
run's actual configured limit (it was not emitted into any event before
this step). **Hypothesis: normalizing RSS against the run's own known
configured budget (Model B, `rss_ratio_env_normalized`) will show less
AUROC degradation from development to held-out than the original
fixed-baseline normalization (Model A), specifically for the `oom`
family.** No prediction is made for `cpu`/`resource_unavailable`/`flaky`
generalization — those families' features were not identified as having
an environment-dependent normalization problem in the Step 2 audit or
Step 4 preparation, and are evaluated as a control (expected to show
similar degradation under both Model A and Model B, since neither
feature set changed for them).

## Data source and environments

- Exactly the three pre-existing `ALL_ENVIRONMENTS` profiles — no new
  environment is introduced. `baseline_cpu` role=`development`;
  `memory_constrained` role=`held_out`; `dependency_network_constrained`
  role=`robustness`.
- Development train: seeds `range(0, 500)`; development validation: seeds
  `range(500_000, 500_150)`; test (evaluated identically in every
  environment): seeds `range(900_000, 900_150)` — same ranges the
  pre-existing Phase 4.9 script already used, reused here unchanged so
  Model A's numbers in this step are a direct, comparable replication of
  the pre-remediation numbers, not a new, differently-scoped measurement.
- **The model is frozen before any held-out/robustness evaluation runs**:
  fit and threshold-calibrate on `baseline_cpu` only, then evaluate the
  identical frozen `(model, threshold)` pair zero-shot against all three
  environments' test sets. Held-out/robustness data never influences
  fitting, calibration, or feature selection.

## Models compared

- **Model A (replication of pre-existing Phase 4.9 result):** original 4
  features (`rss_ratio, anomaly_rate, elapsed_ratio, sample_count_ratio`),
  `rss_ratio` normalized against the fixed `MonitoringBaseline` constant.
- **Model B (this step's new work, P4-W2):** same 4 features plus
  `rss_ratio_env_normalized` (5 total) — RSS normalized against the run's
  own configured `limit_mb` when known (the `oom` family only; every
  other family falls back to the same value as `rss_ratio`, never
  fabricating a budget it doesn't have — see
  `src/phase4/prediction_features_env.py`). `limit_mb` is read from a
  genuinely pre-outcome event (`workload_received`'s `workload_parameters`,
  a real configuration input, added to `controlled_runtime.py` in this
  step) — it is never sourced from the run's own outcome.

Both models use the same `StandardScaler` + `LogisticRegression`
(`class_weight="balanced"`, `max_iter=2000`) — no more complex model
introduced, per P3-W4's simple-model-first rule applied consistently here.

## Metrics

Per family, per model, per environment: AUROC, AUPRC, Brier, ECE,
precision, recall, specificity, false positive rate, false alarm rate.
Degradation is reported as `dev_auroc - other_env_auroc` (matching the
pre-existing script's convention) for both models side by side.

## Stopping rule

Each model is fit and evaluated exactly once (single dev split, not
replicated — this matches the pre-existing Phase 4.9 script's design, kept
identical here for direct comparability of Model A's replication; Step 3's
multi-replicate discipline is not repeated here specifically so this run
is an apples-to-apples rerun of the original Phase 4.9 measurement under
Model A, with Model B added alongside it). No feature, threshold, or
environment definition is changed after seeing a result. If Model B does
not show less degradation than Model A for `oom`, that is reported as a
failure of the hypothesis, not iterated on further in this step.
