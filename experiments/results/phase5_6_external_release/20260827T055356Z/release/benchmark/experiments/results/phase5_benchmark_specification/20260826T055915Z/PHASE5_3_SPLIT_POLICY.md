# Phase 5.3 — Benchmark Split Policy

Status: SPECIFICATION ONLY. This policy governs how a future benchmark
harness must partition dataset records into task-instance evaluation sets.
It inherits, and does not relax, `PHASE5_1_SPLIT_POLICY.md`.

## 1. Two axes, inherited unchanged

- **Sample-level axis**: `train` / `calibration_validation` / `test`,
  already assigned per record in `split_assignment_manifest.json`
  (2,142 / 482 / 482 records respectively, `split_audit.json`).
- **Environment axis**: `development` / `held_out` / `robustness`. This
  axis is **not currently instantiable** — every record's
  `identity.environment_id` is `UNSPECIFIED_PRE_4_9` (§ see
  `PHASE5_3_DATASET_COVERAGE.json`). Any benchmark task that requires this
  axis (GEN-RANKING-CONTRACT, GEN-OPERATING-POINT-CONTRACT) is
  `UNSUPPORTED_CONTRACT_ONLY` until a future dataset revision adds real
  per-episode environment identity.

These two axes remain orthogonal at the benchmark-task level exactly as at
the dataset level: a benchmark task instance's `split_assignment` and
`environment_role` are copied unmodified from its source dataset record(s),
never re-derived or re-assigned by benchmark tooling.

## 2. Task-instance derivation must not break existing groupings

A benchmark task instance derived from one or more dataset records
inherits the strictest applicable split assignment of its constituent
records. For single-record tasks (the common case — every task in
`PHASE5_3_TASK_CATALOG.json` except MEM-EVAL's repeated-incident sequences)
this is simply the record's own `split_assignment`. For a
repeated-incident-sequence task instance (MEM-EVAL, when future data makes
it evaluable), every record in the sequence must share the same
`workload_id`-grouped split per `PHASE5_1_SPLIT_POLICY.md` §2 — a benchmark
harness must reject, not silently repair, a sequence whose records were
somehow assigned to different splits (this would indicate a dataset-level
defect upstream, not a benchmark-level one to work around).

## 3. Calibration discipline (benchmark-level restatement)

- `calibration_validation`-split instances may be used to fit any
  threshold, temperature-scaling parameter, or policy cutoff (per-family,
  per design principle — never one threshold pooled across uncertainty
  families).
- `test`-split instances are used ONLY for final, unfitted evaluation.
  No metric computed on `test` may ever feed back into threshold,
  feature, model, or policy selection (leakage rule 13, restated as
  benchmark leakage rule L11 in `PHASE5_3_LEAKAGE_POLICY.md`).
- `train`-split instances are available for any model fitting a benchmark
  submission wishes to do (this specification does not train anything
  itself, but a future benchmark harness scoring third-party submissions
  must enforce that submissions state which split(s) they fit on).

## 4. Minimum sample requirements gate task eligibility, not just reporting

Each task in `PHASE5_3_TASK_CATALOG.json` declares a
`minimum_sample_requirement`. A benchmark run that has fewer test-split
instances than this minimum for a given task MUST report that task's
result as `UNDERPOWERED/DESCRIPTIVE ONLY`, never as a headline statistic.
This is not a new rule invented here — it operationalizes the task brief's
own instruction and Phase 5.1/5.2's own honesty discipline
(`PHASE5_2_DATASET_AUDIT.md`'s per-family sample-size disclosures).

## 5. What must never be split across a task-instance boundary

- A single dataset `record_id` must never be split across two benchmark
  task instances that treat it as belonging to two different splits.
- A `workload_id`'s records must never be split across two sample-level
  splits (inherited, unchanged, from `PHASE5_1_SPLIT_POLICY.md` §5).
- A repeated-incident sequence (when future data supports MEM-EVAL) must
  never span both `train` and `test`.
- The environment axis and sample-level axis must never be conflated into
  one field at the benchmark-task level either — a task instance's
  `environment_role` and `split_assignment` remain two distinct fields
  (per `PHASE5_3_BENCHMARK_SCHEMA.json`'s top-level object).

## 6. Known limitation carried forward

Because `environments: 1` for the entire canonical dataset, the
environment-axis split is currently a no-op in practice (every instance is
`environment_role = UNSPECIFIED`). This is disclosed here exactly as
`PHASE5_1_SPLIT_POLICY.md` §6 disclosed the analogous Phase 4.10 gap — it
is a coverage gap in the source evidence, not a flaw in this policy, and it
is the single reason `GEN-RANKING-CONTRACT`/`GEN-OPERATING-POINT-CONTRACT`
are `UNSUPPORTED_CONTRACT_ONLY` rather than `LIMITED`.
