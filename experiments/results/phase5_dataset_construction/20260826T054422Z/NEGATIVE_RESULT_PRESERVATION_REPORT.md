# Phase 5.2 — Negative-Result Preservation Report

Per the Phase 5.1 design principle ("preserve negative results") and the
task's explicit instruction not to filter or rebalance them away, this
report lists every honestly-negative or inconclusive result category
actually present in the constructed dataset, with exact record counts as
computed by `dataset_statistics.json`.

| Category | Count | Where it lives in the schema |
|---|---|---|
| `NOT_RECOVERED` recovery outcomes (controlled_runtime track) | 34 | `validation.validation_status == "NOT_RECOVERED"` |
| `UNKNOWN` validation outcome (validator status not resolved in source evidence) | 1 | `validation.validation_status == "UNKNOWN"` |
| Agent-task incorrect answers (across all 3 task families) | 219 | `failure.failure_class == "AGENT_INCORRECT_ANSWER"` |
| Episodes with `predictability_status = NOT_EVALUATED` (no family-level AUROC/false-alarm-rate context was attachable at the per-episode grain available to this construction) | 3,065 | `prediction.predictability_status` |
| `outcome_class = UNKNOWN` (no validation performed and no ABSTAIN decision recorded — a genuine unresolved-outcome episode) | 1 | `outcome_class` (non-schema, additive field; see PHASE5_2_DATASET_AUDIT.md "schema deficiency" note) |
| `NO_FAILURE` (success workloads, retained as first-class negative-for-testing-purposes controls) | 11 | `outcome_class == "NO_FAILURE"` |

## Negative results named in the task brief and their disposition here

- **cpu/pooled-oom/flaky NOT_VALIDATED, resource_preflight ranking-improved-but-not-validated, sentiment discrimination limitation, non-OOM generalization failure** — these are family-level verdicts from `PHASE5_1_SOURCE_INVENTORY.json` (SRC-004, SRC-025, SRC-026) that live in **aggregate evaluation artifacts** (e.g. `post_p5_remediation/.../raw/p4_step4_results.json`, `post_p5_remediation_followups/.../raw/followup*.json`). These aggregate files were read and inspected during construction but are **not per-episode raw evidence** (no retained per-run/per-episode identity to join back to a dataset record — see `SPLIT_VALIDATION_REPORT.md`'s environment-axis disclosure for the identical limitation). They are therefore **not represented as individual dataset records** in this release; they remain fully available as `PUBLIC_METADATA` (their own JSON files, already checksum-manifested by their own frozen `SHA256_MANIFEST.json`s) and are referenced, not duplicated, by this dataset. This is classified as (c) unavailable source evidence at the per-record grain, disclosed here rather than fabricated.
- **ABSTAIN/NOT_RECOVERED episodes** — `NOT_RECOVERED` is present (34 records, above). No `action=ABSTAIN`/`decision=ABSTAIN` episode exists in the two per-episode raw sources actually available to this construction (`phase4_4_autonomy_pipeline/results.json`, `phase4_5_autonomy_pipeline_at_scale/continuous_mode_metrics.jsonl`) — `decision` values observed are only `ANSWER`/`REVIEW`/absent. This is a genuine coverage gap in the specific raw evidence ingested (not every Phase 4 run that ever produced an ABSTAIN decision was dumped to a per-episode raw file), disclosed rather than invented.
- **UNKNOWN diagnoses** — the schema supports `suspected_cause = null`; the two controlled-runtime sources used here always populate a `diagnosis_hypothesis` whenever a diagnosis is recorded at all (0 null-diagnosis-but-diagnosis-attempted records), so `UNKNOWN_diagnosis_episodes = 0` is an honest count, not a filtered-out one.
- **`detectable_only_scope` AUC=0.857 mixing artifact** and **pre-RSS-telemetry-fix Windows OOM evidence** (class 8, SRC-042/SRC-043) — neither is ingested as dataset content (per `PHASE5_1_SOURCE_INVENTORY.json`'s own exclusion and `PHASE5_1_DATASET_SPECIFICATION.md` §6); both remain documented, narratively, in the frozen master record they already live in. This dataset does not reproduce or restate them as records, consistent with "excluded as a label source, retained only as a documented negative finding" — the finding itself is not part of this construction's job to re-derive.

No record was deleted, filtered, or rebalanced to improve the appearance of any distribution. `dataset_statistics.json` reports every count above exactly as constructed.
