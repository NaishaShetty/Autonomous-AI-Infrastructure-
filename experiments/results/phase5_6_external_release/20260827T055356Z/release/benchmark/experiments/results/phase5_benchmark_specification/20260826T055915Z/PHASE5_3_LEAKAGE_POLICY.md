# Phase 5.3 — Benchmark Leakage Policy

Status: SPECIFICATION ONLY. This document restates and extends
`PHASE5_1_LEAKAGE_POLICY.md`'s 14 rules at the benchmark-task level (a
benchmark task instance is a derived projection of one or more dataset
records — leakage can be reintroduced at derivation time even if the
underlying dataset itself is leakage-free, which is why this second layer
of rules exists). The task brief requires at least 12 explicit leakage
rules; 12 are given below, mapped to their Phase 5.1 ancestor rule where
one exists, plus 2 benchmark-specific additions (L11 restated, L12
restated) that were implicit in Phase 5.1 but must be explicit at the
benchmark-scoring level.

| # | Rule | Ancestor (Phase 5.1) |
|---|---|---|
| L1 | No future observations may populate a task instance's `input` block — only fields with `Availability` `BEFORE`/`AT` relative to the task's own `decision_time_available_information` list. | Rule 1, 10 |
| L2 | No post-failure evidence may be used as input to a pre-failure prediction task (PRED-*). Any observation timestamped at or after `failure.failure_detected_time` is `hidden`, never `input`. | Rule 1 (specialized) |
| L3 | No recovery outcome (`validation.validation_status`, `recovery.executor_self_report`) may be used as input to the REC-EVAL action-selection sub-metric (`MET-ACTION-SELECTION-ACCURACY`) — action selection must be scored using only what was available at `PLANNING`/`SAFETY_CHECK`. | Rule 8 (specialized) |
| L4 | No diagnosis output (`diagnosis.suspected_cause`, `diagnosis.confidence`) may be treated as `ground_truth` anywhere, including inside a derived `MemoryRecord.root_cause` field traced back to a diagnosis. | Rule 7 |
| L5 | No executor self-report (`recovery.executor_self_report`) may substitute for `validation.validation_status` in any label, split, or metric computation for REC-EVAL or E2E-EVAL. | Rule 8 |
| L6 | No `test`-split instance may be used, in whole or in part, during threshold/model/feature/policy fitting for any task. `calibration_validation` is the only split eligible for that purpose. | Rule 13 |
| L7 | No `held_out`/`robustness`-role instance may be used during fitting for GEN-RANKING-CONTRACT/GEN-OPERATING-POINT-CONTRACT (moot today since no such instances exist in the current dataset, but binding the moment they do). | Rule 4 |
| L8 | No repeated-workload (`workload_id`) sequence may cross a forbidden split boundary for MEM-EVAL once that task becomes evaluable; a benchmark harness must reject, not repair, any sequence found split this way. | Rule 5, Split Policy §2 |
| L9 | No `memory_interaction` read may expose a `MemoryRecord` whose `recorded_at` postdates the querying instance's own `decision_time`. | Rule 9, 5 |
| L10 | No cross-generation (V1/Gen-2 vs Gen-3) evidence may be mixed into any benchmark task instance's input, label, or baseline computation — the entire benchmark spec operates on Gen-3 (Phase 5.2 canonical dataset) evidence exclusively. | Rule 14 |
| L11 | No benchmark-specific threshold, hyperparameter, or feature-selection decision may be tuned against `test`-split results and then re-applied — this is distinct from L6 (L6 forbids using test rows as fitting *input*; L11 additionally forbids using test *results* as a *tuning signal* even indirectly, e.g. picking whichever of several thresholds happened to score best on test). | New (task brief explicit requirement) |
| L12 | No feature selection may be based on final test-split results (a specialization of L11 for the feature-selection case specifically, since the task brief names it as its own item). | New (task brief explicit requirement) |

## Enforcement notes

- Every rule above is mechanically checkable given the existing
  `identity`, `temporal`, `split_assignment`, `label_type`, and
  `provenance` fields already present in every Phase 5.2 dataset record —
  no new field is required to enforce these rules; a future benchmark
  harness should reuse `ensure_decision_snapshot()`-equivalent assertions
  exactly as the live Phase 4 code already does (per
  `PHASE5_1_LEAKAGE_POLICY.md` rule 1's own framing).
- L1-L5, L9, L10 are the same class of violation Phase 5.1/5.2 already
  mechanically audited at the dataset level (`leakage_audit.json`, 0
  violations found). This benchmark-level policy exists because a naive
  task-instance *derivation* step (e.g. accidentally copying a
  `diagnosis` field into a `PRED-*` task's `input` block) could
  reintroduce a violation even though the underlying dataset record itself
  is clean — the leakage vector lives in the derivation code, not
  necessarily in the source record.
- L6, L11, L12 target the specific failure mode of a benchmark harness (or
  a benchmark submitter) "peeking" at test results to pick a better
  threshold/feature set after the fact — a violation that would not show
  up in any dataset-level audit because it happens entirely at
  scoring/reporting time, after the dataset itself was already correctly
  split.
- Every violation of any rule above must cause the affected task instance
  (or the entire benchmark run, for L6/L11/L12) to be excluded from
  reported results and the violation itself logged as an audit-trail
  entry — never silently corrected and never silently dropped without a
  record of why.
