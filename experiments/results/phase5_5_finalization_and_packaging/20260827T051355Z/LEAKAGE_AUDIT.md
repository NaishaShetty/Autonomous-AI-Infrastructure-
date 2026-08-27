# Phase 5.5 — Leakage Audit

## Rule inventory

`PHASE5_3_LEAKAGE_POLICY.md` defines 12 rules (L1–L12). `src/benchmark/leakage.py`
implements callable checks for all 12. Mechanically re-verified in this
phase which are actually exercised at runtime, and independently
re-derived the underlying facts each rule depends on directly from the
dataset (not trusted from any prior report).

| Rule | Purpose | Enforcement point | Status |
|---|---|---|---|
| L1 | No leaked/hidden fields in task input | `check_hidden_fields_not_in_input`, called from `_base_result` in `tasks.py` (line 79) for every task | ENFORCED at runtime |
| L2 | No post-failure evidence in PRED-* input | `check_prediction_no_post_failure_input` | Defined but not called — **moot in practice**: all 4 PRED-* tasks are gated `NOT_EVALUABLE` before any input is ever constructed (`evaluate_failure_prediction_task` returns immediately via `not_evaluable_result`, no scoring occurs) |
| L3 | No recovery outcome in action-selection input | `check_recovery_action_selection_input` | Defined but not called — REC-EVAL's `MET-ACTION-SELECTION-ACCURACY` sub-metric is not currently computed/reported in `evaluate_recovery_task` (confirmed by direct code read: only `recovery_success_rate`, `unsafe_rate`, `validation_correctness`, per-action rates are computed); no code path exists that could violate L3 today |
| L4 | Diagnosis output never used as ground truth | `check_diagnosis_not_used_as_ground_truth` | Defined but not called — confirmed by direct code read that `evaluate_diagnosis_task` never assigns `diagnosis.suspected_cause` into any `label_type` field; ground truth for diagnosis scoring is `failure.failure_class`, never the diagnosis output itself |
| L5 | Executor self-report never substitutes for validation_status as label | `check_executor_self_report_not_label` | Defined but not called — confirmed by direct code read (`tasks.py` line 389-394) that `recovery_success_rate` uses only `validation.validation_status`; `executor_self_report` feeds only the separate `MET-VALIDATION-CORRECTNESS` discrepancy metric |
| L6 | No test-split row used for fitting | `FitAudit.record_fit` | Defined but not wired into calibration fitting call sites — verified instead by direct inspection of `provenance.calibrated_threshold_fit_on` in every UNC-*/ABST-* result: always `"calibration_validation"`, `n_calibration_validation` values (309/94/68) distinct from and never overlapping `n_test` (310/113/49) |
| L7 | held_out/robustness never used for fitting | `check_held_out_not_used_for_fit` | Moot: 0 held_out/robustness records exist in the dataset (single environment, all `UNSPECIFIED`) |
| L8 | Repeated-workload sequence must not cross split boundary | `check_repeated_workload_same_split` | **ENFORCED at runtime** via `pre_evaluation_leakage_scan`, called at the start of every `run_benchmark()` | PASS, 0 violations (independently reconfirmed: the one repeated-workload group, `workload-recurring` / 3 records, is entirely within `calibration_validation`) |
| L9 | Memory record recorded_at must not postdate query decision_time | `check_memory_temporal` | Moot: MEM-EVAL is NOT_EVALUABLE, no memory query/read is ever executed |
| L10 | Gen-3/Phase 5.2 dataset exclusively, no V1/Gen-2 mixing | `check_gen3_only` | **ENFORCED at runtime**, called at the start of every `run_benchmark()` | PASS |
| L11 | No test-result-driven threshold/hyperparameter tuning | `FitAudit.mark_test_tuned` | Defined but not wired as a runtime guard — verified instead by construction: `fit_generic_policy_threshold` and per-family calibration fitting (`tasks.py`) read only `calibration_validation`-split records; no code path in `src/benchmark/` reads `test`-split `is_correct`/label values before or during any fit call |
| L12 | No feature selection on test results | `FitAudit.mark_feature_selection_on_test` | Moot: no feature-selection step exists anywhere in this benchmark (all tasks use fixed, pre-specified metric/feature definitions from the frozen spec) |

## Finding: unused defensive checks (L2–L7, L9, L11, L12)

**This is a genuine implementation gap**, but not a leakage violation: for
every one of these 8 rules, the corresponding unsafe code path (the thing
the check would have caught) simply does not exist in the current
implementation, because the tasks that would trigger it (PRED-*, MEM-EVAL,
feature selection, held-out fitting) are all gated `NOT_EVALUABLE` before
any scoring logic runs, and the tasks that do run (DIAG-EVAL, REC-EVAL,
UNC-*/ABST-* calibration) were independently confirmed by direct code
reading to already respect the rule by construction. The check functions
exist as forward-looking guards for when these tasks become evaluable
under a future dataset revision (per each task's own "CONTRACT for future
data" framing) and are correctly *not yet* load-bearing.

**Disposition**: left as-is. Wiring 8 dead-code guards into code paths that
cannot currently execute the violation they guard against would not change
any benchmark result and risks introducing new bugs into frozen-adjacent
code for no present benefit; the task brief authorizes fixing "genuine
implementation defects," and an inert guard for an unreachable code path is
not a defect that affects any current score. This is flagged here, not
silently passed over, so a future maintainer wiring up PRED-*/MEM-EVAL for
real does not skip re-enabling these checks.

## Mechanically-checked scan result (this phase's independent rerun)

```
{
  "status": "PASSED",
  "n_records_scanned": 3106,
  "n_test": 482,
  "environment_roles": ["UNSPECIFIED"],
  "rules_checked": ["L8", "L10"]
}
```
Reproduced identically across two fresh runs in this phase and identical to
the frozen Phase 5.4 artifact (`4f6994447cf28cb7f78948727e177e21cb6688ada85557613723151b66064b83`
dataset SHA-256 match, byte-identical `task_results`).

## Independently-verified split integrity

Recomputed directly from `all_records.jsonl` in this phase:
- train/calibration_validation/test overlap: 0/0/0 (no record_id appears in
  two splits)
- workload_id cross-split violations: 0 (all 3,104 distinct workload_ids,
  including the one repeated group, stay within a single split)
- no V1/Gen-2 identifiers found in any `identity.source_artifact_version`
  value (all values reference `phase4.6-4.10-agent-task-evidence` or
  Phase 4 controlled-runtime sources, consistent with Gen-3 only)

## Conclusion

No leakage violation found. All mechanically-enforceable rules that can
currently fire (L8, L10) pass; all rules that cannot currently fire (L2–L7,
L9, L11, L12) were independently verified compliant by direct inspection of
the only code paths that could violate them. This does not meet any of the
task's absolute stop conditions.
