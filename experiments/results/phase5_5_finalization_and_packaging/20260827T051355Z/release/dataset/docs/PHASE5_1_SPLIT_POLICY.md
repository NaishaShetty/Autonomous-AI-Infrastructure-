# Phase 5.1 — Split Policy

## 1. Split axes (two independent axes, never conflated)

1. **Sample-level axis** (within one environment): `train` /
   `calibration_validation` / `test`, used by every trained model
   (`TrainedRiskPredictor`, `PredictionScopeRouter`,
   `AgentDecisionCalibrationProfile`) and every threshold calibration.
2. **Environment axis** (across environments): `development` (=
   `baseline_cpu`) / `held_out` (= `memory_constrained`) / `robustness`
   (= `dependency_network_constrained`), used only for generalization
   evaluation, per Phase 4.9 and reused unchanged by post-P5 remediation
   Step 4 and follow-up 3.

These are orthogonal: an environment-axis split does not imply a
sample-level split has been done within it, and vice versa. A record can
be simultaneously `test` (sample-level) and `held_out` (environment-level).

## 2. Grouping key: does repeated-workload/incident structure require
group-based splitting?

**Yes — confirmed by direct evidence.** The post-P5 remediation Step 6
repeated-incident experiment (`docs/MASTER_RECORD_CONTENT.md` §16, §22)
demonstrates that `FailureMemoryStore` scoping by
`(workload_id, environment_id, failure_class)` — never `run_id` — is what
allows memory to influence a later episode's decision when the *same*
`workload_id` recurs. This has a direct consequence for splitting: if two
episodes sharing a `workload_id` land in different splits (e.g. one
`train`, one `test`), the `test` episode's memory-informed diagnosis or
recovery-planner input could be influenced by information whose
downstream effect (the planner's action choice) is exactly what a
memory-effect benchmark view is trying to measure out-of-sample. This is
the classic group-leakage pattern.

**Exact grouping key: `workload_id`.** All records sharing a `workload_id`
must be assigned to the same sample-level split (never split across
`train`/`calibration_validation`/`test`). This is stricter than grouping by
`run_id` alone (which the pre-fix diagnosis-contamination incident,
`EVALUATION_INCIDENT_001`, already showed was necessary at the evidence
level) and is consistent with — not a new invention over — the existing
memory contract's own scoping rule.

Secondary grouping consideration: `seed` blocks. Every trained model in the
frozen evidence already uses disjoint `SplitSeeds`/`AgentSplitSeeds` blocks
that raise on overlap in `__post_init__` (`docs/MASTER_RECORD_CONTENT.md`
§25). Because `workload_id` is frequently seed-derived
(`f"{environment_id}-{split}-seed-{seed}"` in `environments.py`), grouping
by `workload_id` and by disjoint seed block are compatible, not competing,
constraints — the dataset split policy should enforce both: (a) no shared
`workload_id` across splits, and (b) no shared `seed` across
`train`/`calibration_validation`/`test` seed blocks, exactly mirroring the
already-validated protocol.

## 3. Sample-level split construction

- **Train**: seed block designated `train` by the originating protocol
  (e.g. Phase 4.6-4.10: 500-1,500 seeds/protocol). Used to fit
  `TrainedRiskPredictor`/`PredictionScopeRouter` and to fit any temperature
  scaling.
- **Calibration_validation**: a disjoint seed block (150-300 seeds/protocol)
  used exclusively for threshold calibration
  (`calibrate_threshold(val_rows, ...)`, whose signature never accepts test
  rows) and for fitting `AgentDecisionCalibrationProfile`'s per-bucket
  estimates. Never used to select a final reported metric.
- **Test**: a disjoint seed block, used only for final, unfitted evaluation.
  For Phase 4.8's headline prediction result, 3 disjoint seed-range
  replicates (2,400 seeds total, none shared) were used for the test
  evaluation — this dataset's `test` split should preserve that replicate
  structure as a `replicate_index` sub-field rather than flattening it,
  so a future benchmark can reproduce the same replication design.

## 4. Environment-level split construction

- **Development** (`baseline_cpu`): the only environment any
  model/threshold/policy/feature choice is ever fit against. All
  train/calibration_validation/test sample-level splits above happen
  *within* this environment by default.
- **Held-out** (`memory_constrained`): genuinely different resource limits
  (OOM budget 4x tighter) and telemetry resolution (5x finer). Used
  zero-shot only — verified in the frozen evidence never to have
  influenced training, threshold selection, or feature choice
  (`docs/MASTER_RECORD_CONTENT.md` §26).
- **Robustness** (`dependency_network_constrained`): genuinely different
  execution deadline and dependency-contention rate. Also zero-shot only.
- A record's `environment_id` is fixed at generation time by which
  `EnvironmentProfile.scenario_fn` produced it; a record must never be
  reassigned to a different environment_id after generation (this would
  be a temporal/generation-provenance violation, not just a labeling
  error, because the underlying resource-limit/timing distribution is
  genuinely different per environment).

## 5. What must NEVER be split across boundaries

- A single `run_id`'s events must never span two splits.
- A single `workload_id`'s runs must never span two sample-level splits
  (§2).
- A `MemoryRecord` written by a `train`-split episode must not be
  retrievable, under this dataset's benchmark-view protocols, by a
  `test`-split query unless the benchmark view is *specifically* designed
  to measure cross-split memory transfer (no such view is defined in
  `PHASE5_1_BENCHMARK_VIEWS.md`; the default assumption is that a
  benchmark consumer replays memory writes/reads confined to their own
  split's episodes, mirroring the frozen evidence's own within-run
  exclusion, `source_run_id != exclude_run_id`, generalized to
  within-split).
- Environment axis and sample-level axis must never be silently collapsed
  into one label (e.g. do not create a single `split` field that conflates
  `test` with `held_out`) — the schema keeps `split_assignment`
  (sample-level, with `development_env`/`held_out_env`/`robustness_env` as
  distinct enum values precisely so environment-axis assignment is visible
  in the same field without conflating "was this fit on" with "which
  environment generated this").

## 6. Known limitation carried into this policy

Phase 4.10's 300-episode full-loop evaluation used a unique `workload_id`
per episode by design (`docs/MASTER_RECORD_CONTENT.md` §16, §31) — so no
episode in that specific run exercises the repeated-workload grouping rule
at scale. This is disclosed, not silently worked around: a future dataset
build drawing episodes from that run alone would need to state explicitly
that its `workload_id` grouping key never actually produced a multi-run
group, which is a coverage gap in the source evidence, not a flaw in this
split policy.
