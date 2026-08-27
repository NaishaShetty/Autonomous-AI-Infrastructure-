# Phase 5.5 — Task-by-Task Audit

Method: for each of the 16 `PHASE5_3_TASK_CATALOG.json` tasks, cross-checked
spec definition (Phase 5.3), implementation (`src/benchmark/tasks.py`),
dataset inputs/labels (`dataset/all_records.jsonl`, independently loaded and
recomputed — not trusted from prior reports), split assignment
(`split_audit.json`), metrics (`src/benchmark/metrics.py`), baselines
(`src/benchmark/baselines.py` / `PHASE5_3_BASELINE_CATALOG.json`), ablations
(`ablation_results` in the independent rerun), evidence class, and final
status classification per `SPECIFICATION_RECONCILIATION.md`'s test-split
gating rule.

All counts below were independently recomputed directly from
`experiments/results/phase5_dataset_construction/20260826T054422Z/dataset/all_records.jsonl`
(3,106 records) in this audit, not copied from any prior report, and
cross-checked against `experiments/results/phase5_5_finalization_and_packaging/20260827T051355Z/gate_a_independent_rerun/PHASE5_4_BENCHMARK_RESULTS.json`
(a fresh, from-scratch benchmark run performed in this phase).

| Task | Spec | Implementation | Evidence | Leakage | Metrics | Status | Issues |
|---|---|---|---|---|---|---|---|
| UNC-ARITH | UNC-*, n_test≥500 | `evaluate_uncertainty_task` | n_test=310 (recomputed: 310 `arithmetic_self_consistency` test-split records) | L6/L10/L11 checked: threshold fit only on calibration_validation (n=309); no test leakage | AUROC 0.955, ECE raw 0.197→calibrated 0.083 | UNDERPOWERED | n_test=310<500; correctly labeled, not headline |
| UNC-SENT | UNC-*, n_test≥300 | same | n_test=113 (recomputed) | same, calibration n=94 | AUROC 0.439 (near-chance, disclosed, not "fixed") | UNDERPOWERED | n_test=113<300; genuine discrimination ceiling preserved, not massaged |
| UNC-QA | UNC-*, n_test≥300 | same | n_test=49 (recomputed) | same, calibration n=68 | AUROC 0.938 | UNDERPOWERED | n_test=49<300 |
| ABST-ARITH | ABST-*, simulated policy | `evaluate_abstention_task` | n=310, same population as UNC-ARITH test split | SIMULATED_POLICY_EVALUATION honestly labeled; 0 real ABSTAIN/RETRY episodes confirmed (recomputed: `by_decision_type` has no ABSTAIN/RETRY key in dataset) | Always-abstain baseline flagged `ALWAYS_ABSTAIN_NOT_SUCCESSFUL`, cannot "win" | PARTIALLY_VALIDATED | Correctly distinguishes simulated vs. realized policy |
| ABST-SENT | ABST-* | same | n=113 | same | — | PARTIALLY_VALIDATED | same caveats |
| ABST-QA | ABST-* | same | n=49 | same | — | PARTIALLY_VALIDATED | same caveats |
| PRED-RESOURCE-UNAVAILABLE | PRED-*, n≥300 per family | `evaluate_failure_prediction_task` | n=0 (recomputed: 0 records with `failure_class=="resource_unavailable"`; label does not exist in this dataset's failure_class vocabulary at all) | N/A — gated before scoring | N/A | NOT_EVALUABLE | STRONG_EVIDENCE verdict correctly retained as AGGREGATE_REFERENCE_EVIDENCE only, never recomputed as a record-level score |
| PRED-OOM | PRED-* | same | n=10 (recomputed: 10 `PROCESS_OOM` controlled_runtime records) | gated | N/A | NOT_EVALUABLE | AUROC 0.780 verdict remains aggregate-only per post_p5_remediation_followups; not re-derived here |
| PRED-CPU | PRED-* | same | n=1 (recomputed: 1 `PROCESS_TIMEOUT_CPU` record) | gated | N/A | NOT_EVALUABLE | NOT_VALIDATED verdict preserved as aggregate-only |
| PRED-FLAKY | PRED-* | same | n=13+11=24 (recomputed: `GENERIC_FAIL`=13, `NETWORK_FAILURE`=11; no dedicated "flaky" label) | gated | N/A | NOT_EVALUABLE | NOT_VALIDATED preserved |
| DIAG-EVAL | DIAG-EVAL, n≥30/class | `evaluate_diagnosis_task` | n=35 (recomputed: 35 controlled_runtime records with `failure_class != NONE`) | causal_status=CAUSAL_GROUND_TRUTH_UNAVAILABLE correctly attached to every record | Failure-class-accuracy=1.0 (35/35, recomputed independently) and false-causal-attribution-rate=1.0 (35/35, recomputed: every record's `diagnosis.suspected_cause` is non-null while no independent causal ground-truth field exists) — **both independently reproduced**, matching prior report | PARTIALLY_VALIDATED | Per-class n<30 for all 4 classes (10/13/11/1) correctly flagged UNDERPOWERED; the causal-ground-truth-unavailable caveat is attached to the metric itself, not just prose, so it cannot be silently dropped from a headline |
| REC-EVAL | REC-EVAL | `evaluate_recovery_task` | n=35 (same 35 controlled_runtime failure records) | `executor_self_report` used only for `MET-VALIDATION-CORRECTNESS` discrepancy metric, never as the recovery-success label (confirmed by direct code read, tasks.py:389-394: only `validation.validation_status` feeds `recovery_success_rate`) | recovery_success_rate = 0/35 = 0.0 — **independently recomputed from raw records: 34 NOT_RECOVERED + 1 UNKNOWN, 0 RECOVERED** | PARTIALLY_VALIDATED | 0/35 confirmed genuine (not a benchmark artifact): the dataset's `validation` field is populated per-record from Phase 4 controlled-runtime evidence, not synthesized; 0/35 is a real negative finding for this dataset slice, not an underpowered non-result and not a code defect |
| MEM-EVAL | MEM-EVAL | `evaluate_memory_task` | Repeated workload_ids: **recomputed = 1** (workload_id `"workload-recurring"`, 3 records, episode_ids `phase4.4-recurring_failure_1/2/3`, all `controlled_runtime`, all in `calibration_validation` split — no split-crossing) | L8 checked: this group does not cross a split boundary | N/A — 1 group of 3 is far below any usable sample size | NOT_EVALUABLE | **Finding**: the implementation's own field (`repeated_workload_id_count`) correctly reports 1, not 0 — the code is honest. However, prior-phase prose ("none... are documented as the deliberate repeated-incident design") is imprecise: this group's episode-id naming (`phase4.4-recurring_failure_*`) indicates it IS a genuine, deliberately-repeated Phase 4.4 incident sequence, just at n=1 group / 3 records — nowhere near sufficient scale for MEM-EVAL or ABL-MEMORY-ON-OFF. Classification (NOT_EVALUABLE) is unaffected; documentation precision is corrected here. |
| GEN-RANKING-CONTRACT | GEN-* | `evaluate_generalization_task` | Distinct environment_ids: **recomputed = 1** (`UNSPECIFIED_PRE_4_9`, all 3,106 records) | N/A | N/A | NOT_EVALUABLE | Confirmed no Phase 4 environment IDs were ever attached to any Phase 5.2 record; Phase 4's real 0.989/0.983/0.935 OOM ranking numbers preserved only as aggregate-reference, never joined to per-episode rows |
| GEN-OPERATING-POINT-CONTRACT | GEN-* | same | same (n=1 environment) | N/A | N/A | NOT_EVALUABLE | Phase 4's operating-point transfer failure preserved as aggregate-reference only |
| E2E-EVAL | E2E-EVAL | `evaluate_end_to_end_task` | n=46 (recomputed: all controlled_runtime records, including 11 `failure_class=NONE`) | Component metrics (diagnosis, recovery) reported jointly specifically to prevent a strong/weak E2E number masking an UNDERPOWERED component; masking-check logic confirmed present in code (tasks.py:512-516) and did not trigger (recovery rate is 0%, not >0.5%, so no masking risk here) | e2e_recovery_rate computed from the same 0/35-consistent population | PARTIALLY_VALIDATED | Full 8-stage-loop claim correctly confined to n=46; the 3,060 agent_task records are correctly excluded from this task |

## Status counts (16 tasks)

- VALIDATED: 0
- PARTIALLY_VALIDATED: 6 (ABST-ARITH, ABST-SENT, ABST-QA, DIAG-EVAL, REC-EVAL, E2E-EVAL)
- UNDERPOWERED: 3 (UNC-ARITH, UNC-SENT, UNC-QA)
- NOT_VALIDATED: 0
- NOT_EVALUABLE: 7 (PRED-RESOURCE-UNAVAILABLE, PRED-OOM, PRED-CPU, PRED-FLAKY, MEM-EVAL, GEN-RANKING-CONTRACT, GEN-OPERATING-POINT-CONTRACT)

No new status labels were needed; all 16 tasks map cleanly onto the
required vocabulary.
