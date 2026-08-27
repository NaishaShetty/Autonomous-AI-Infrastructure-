# Step 3 Protocol — P3 Predictability Re-Evaluation

Pre-registered BEFORE running any evaluation or looking at any test-split
result. Written directly from the Step 2 audit's per-family
recommendations (`audits/P3_PREDICTIVE_OBSERVABILITY_AUDIT.md`). Nothing in
this document may be changed after results are seen; any change to
protocol after that point must be logged as a new, separately-labeled
protocol revision, never a silent edit.

## Hypotheses (one per family, stated before running)

1. **`cpu`:** `elapsed_ratio` alone carries real, above-chance signal for
   PROCESS_TIMEOUT; the full 5-feature model may score no better, or
   worse, than the 1-feature model because the additional (now-real, but
   task-irrelevant) RSS/host-memory dimensions dilute a small-sample
   logistic fit (this is what Step 1's engineering-fix finding already
   showed once; this step tests whether it replicates on fresh splits).
2. **`oom`:** real precursor signal exists only in the (minority) subset of
   runs with ≥2 telemetry samples before the outcome; the majority subset
   with 0–1 samples carries no more signal than chance, and pooling them
   (as every prior evaluation has done) is expected to produce a diluted,
   near-chance aggregate that hides real skill on the observable subset.
3. **`resource_unavailable`:** the new pre-flight probe feature
   (`resource_preflight_available`) produces a near-ceiling AUROC, for the
   environment-explained reason documented in the audit (probe and outcome
   are separated by milliseconds in this synthetic corpus, so they should
   correlate almost perfectly) — this is expected and will be reported as
   such, not treated as a suspicious result to explain away.
4. **`flaky`:** no feature derived from this episode's own process
   telemetry carries real signal (the deciding state is exogenous to this
   episode, per the audit) — expected to replicate chance-level AUROC.

## Data source and splits

- Same `ControlledRuntime`/`scenario_for_seed` corpus generator already
  used by `prediction_training.py`/`prediction_eval_v2.py` — no new
  synthetic-data source introduced.
- **Replication, not a single split:** each family is evaluated across 3
  independent, non-overlapping seed-range replicates (train/validation/test
  seed ranges disjoint both within and across replicates). Mean ± standard
  deviation is reported across replicates for every metric. A single-split
  point estimate is not treated as a stable measurement.
- Per replicate: `train` (400 seeds), `validation` (100 seeds), `test`
  (300 seeds) — sized for the four bimodal families to have enough
  examples of each label after per-family filtering; exact seed ranges are
  fixed in `run_p3_step3_predictability.py` before execution and are not
  adjusted after seeing results.

## Features (fixed per family, per the audit's recommendation — not chosen post-hoc)

| Family | Variant(s) evaluated | Feature set |
|---|---|---|
| `cpu` | A: full 5-feature v2; B: elapsed-only | A = `(rss_ratio, anomaly_rate, elapsed_ratio, sample_count_ratio, rss_growth_rate)`; B = `(elapsed_ratio,)` |
| `oom` | full 5-feature v2, split by observability | Same 5 features as A above; test rows split post-hoc **by a property available at decision time** (`n_telemetry_samples_before_checkpoint`), not by outcome — this is not label-based splitting |
| `resource_unavailable` | full 5-feature v2 + preflight probe | v2's 5 features plus `resource_preflight_available` (1.0 available / 0.0 unavailable / 0.5 no probe event found) |
| `flaky` | full 5-feature v2 (unchanged) | Same as v2 baseline; no new feature exists to add per the audit |

## Model

- **Simple model first, per P3-W4:** `StandardScaler` + `LogisticRegression`
  (`class_weight="balanced"`, `max_iter=2000`) — identical model class
  already used by `prediction_eval_v2.py`/`prediction_training.py`. No
  more complex model (tree ensembles, neural nets) is introduced in this
  step. A more complex model would only be justified by evidence a linear
  model cannot capture available signal — no such evidence exists yet.

## Baselines (computed for every family/variant)

- **Shuffled-label negative control:** same run-level label permutation
  already implemented in `prediction_eval_v2.py::_shuffle_labels_by_run`,
  seeded via the (now process-independent) `_stable_seed`.
- **Prevalence baseline:** predicts the training-set positive rate for
  every test row (constant score); AUROC undefined by construction (used
  for Brier/ECE comparison, not AUROC).
- **Always-negative baseline:** predicts 0.0 for every row (recall = 0 by
  construction; used to contextualize precision/recall, not cherry-picked
  to look good).

## Metrics (computed for every family/variant/replicate)

AUROC, AUPRC, Brier score, ECE, precision, recall, specificity, false
positive rate, run-level false alarms (count and rate), mean lead time,
mean useful lead time (excludes near-zero leads), run-level
detection-before-failure rate (= run-level recall). Across the 3
replicates: mean ± standard deviation for every metric above.

## Stopping rule

Each family/variant is evaluated **exactly once** per replicate, 3
replicates, no re-running with different splits/features/thresholds after
seeing a result. If the real model does not clearly separate from its own
shuffled-label control (defined as: the real model's mean AUROC across
replicates does not exceed the shuffled control's mean AUROC by more than
one pooled standard deviation), the family/variant is reported as **no
demonstrated predictive signal under this observability regime** — full
stop, no further feature/model iteration for that family/variant in this
step. This matches the master remediation register's explicit instruction:
"If after legitimate observability improvements the best predictor still
performs at chance, STOP trying to force prediction."

## What counts as a violation of this protocol

- Running a family/variant more than the 3 pre-registered replicates and
  reporting only the best.
- Adding, removing, or reweighting a feature after seeing a replicate's
  result.
- Changing the classification threshold after seeing test-set performance
  at the originally calibrated threshold.
- Reporting only families/variants that came out above chance.

None of the above will occur; this document exists specifically so a
reader can verify that against the implementation and the results report.
