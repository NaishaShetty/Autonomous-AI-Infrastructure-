# Phase 5.4 -- Benchmark Report

benchmark_version: `phase5.3-benchmark-v1.0.0` | dataset_version: `phase5.2-dataset-v1.0.0` |
implementation_version: `phase5.4-implementation-v1.0.0`

This report implements and executes the frozen Phase 5.3 benchmark
specification over the frozen Phase 5.2 canonical dataset. No single
overall benchmark score is computed -- Phase 5.3 does not define one; a
capability matrix is used instead.

## Result buckets

- VALIDATED: []
- LIMITED: ['ABST-ARITH', 'ABST-SENT', 'ABST-QA', 'DIAG-EVAL', 'REC-EVAL', 'E2E-EVAL']
- UNDERPOWERED: ['UNC-ARITH', 'UNC-SENT', 'UNC-QA']
- DESCRIPTIVE: []
- NOT_EVALUABLE: ['PRED-RESOURCE-UNAVAILABLE', 'PRED-OOM', 'PRED-CPU', 'PRED-FLAKY', 'MEM-EVAL', 'GEN-RANKING-CONTRACT', 'GEN-OPERATING-POINT-CONTRACT']
- NEGATIVE: []
- AGGREGATE_REFERENCE: ['PRED-RESOURCE-UNAVAILABLE', 'PRED-OOM', 'PRED-CPU', 'PRED-FLAKY', 'MEM-EVAL', 'GEN-RANKING-CONTRACT', 'GEN-OPERATING-POINT-CONTRACT']

## Capability matrix

| Task | Track | Status | Evidence | Primary Metric | Limitations |
|---|---|---|---|---|---|
| ABST-ARITH | abstention | PARTIALLY_VALIDATED | n=310; simulated policy only, no realized abstain/retry episodes | 0.0 | SIMULATED_POLICY_EVALUATION: no realized ABSTAIN-decision or RETRY-triggered episodes exist in the ingested raw sources (dataset by_decision_type has no ABSTAIN |
| ABST-QA | abstention | PARTIALLY_VALIDATED | n=49; simulated policy only, no realized abstain/retry episodes | 0.03125 | SIMULATED_POLICY_EVALUATION: no realized ABSTAIN-decision or RETRY-triggered episodes exist in the ingested raw sources (dataset by_decision_type has no ABSTAIN |
| ABST-SENT | abstention | PARTIALLY_VALIDATED | n=113; simulated policy only, no realized abstain/retry episodes | 0.3125 | SIMULATED_POLICY_EVALUATION: no realized ABSTAIN-decision or RETRY-triggered episodes exist in the ingested raw sources (dataset by_decision_type has no ABSTAIN |
| DIAG-EVAL | diagnosis | PARTIALLY_VALIDATED | n=35 | None | causal_status=CAUSAL_GROUND_TRUTH_UNAVAILABLE for all records in this dataset (no independently-verified root cause distinct from failure_class exists); only fa |
| E2E-EVAL | end_to_end | PARTIALLY_VALIDATED | n=46 | None | Full end-to-end coverage limited to n=46 controlled_runtime records; agent_task records (3,060) do not exercise diagnosis/recovery/memory stages and are exclude |
| GEN-OPERATING-POINT-CONTRACT | generalization | NOT_EVALUABLE | n=0 | None | Same as GEN-RANKING-CONTRACT: single-environment dataset. NOT_EVALUABLE today; CONTRACT for future data. |
| GEN-RANKING-CONTRACT | generalization | NOT_EVALUABLE | n=0 | None | CRITICAL, STATED PLAINLY: the current Phase 5.2 canonical dataset has only ONE represented environment (identity.environment_id == 'UNSPECIFIED_PRE_4_9' for all |
| MEM-EVAL | memory | NOT_EVALUABLE | n=0 | None | The canonical Phase 5.2 dataset (3,106 records, 3,104 distinct workload_ids across 3,106 workloads/runs) has essentially no repeated workload_id structure — dat |
| PRED-CPU | failure_prediction | NOT_EVALUABLE | n=0 | None | Dataset has exactly 1 PROCESS_TIMEOUT_CPU per-episode record (dataset_statistics.json by_failure_class) — far below any usable sample size. NOT_EVALUABLE at sca |
| PRED-FLAKY | failure_prediction | NOT_EVALUABLE | n=0 | None | Dataset has 13 GENERIC_FAIL and 11 NETWORK_FAILURE per-episode records (dataset_statistics.json), below the 300-sample minimum and without a dedicated 'flaky' l |
| PRED-OOM | failure_prediction | NOT_EVALUABLE | n=0 | None | Dataset has 10 PROCESS_OOM per-episode records (dataset_statistics.json), insufficient (below the 300-sample minimum) and lacking the per-episode observability- |
| PRED-RESOURCE-UNAVAILABLE | failure_prediction | NOT_EVALUABLE | n=0 | None | This dataset (Phase 5.2, 3,106 records) has only 10 PROCESS_OOM and 0 resource_unavailable-labeled per-episode records with retained identity (dataset_statistic |
| REC-EVAL | recovery | PARTIALLY_VALIDATED | n=35 | None | recovery.executor_self_report is retained only for discrepancy analysis (MET-VALIDATION-CORRECTNESS) and never substitutes for validation.validation_status as a |
| UNC-ARITH | uncertainty | UNDERPOWERED | n=310 | None | Temperature scaling (T=0.2739) fit on calibration_validation (n=309); raw ECE=0.1967741935483872, calibrated ECE=0.08271192437813482, raw AUROC=0.95520980669495 |
| UNC-QA | uncertainty | UNDERPOWERED | n=49 | None | Temperature scaling (T=0.9704) fit on calibration_validation (n=68); raw ECE=0.07543071613782164, calibrated ECE=0.07746974260115684, raw AUROC=0.93846153846153 |
| UNC-SENT | uncertainty | UNDERPOWERED | n=113 | None | Temperature scaling (T=2.3136) fit on calibration_validation (n=94); raw ECE=0.12235910048036358, calibrated ECE=0.08443492936851578, raw AUROC=0.43867243867243 |

## Determinism

{
  "task_results_identical": true,
  "ablation_results_identical": true,
  "capability_matrix_identical": true,
  "split_assignments_identical": true
}

## Dataset integrity

- n_records: 3106, n_episodes: 3106, n_workloads: 3104,
  n_environments: 1
- split_counts: {'calibration_validation': 482, 'train': 2142, 'test': 482}
- all_records.jsonl sha256: 4f6994447cf28cb7f78948727e177e21cb6688ada85557613723151b66064b83
- status: PASSED

## Leakage scan

{
  "status": "PASSED",
  "n_records_scanned": 3106,
  "n_test": 482,
  "environment_roles": [
    "UNSPECIFIED"
  ],
  "rules_checked": [
    "L8",
    "L10"
  ]
}
