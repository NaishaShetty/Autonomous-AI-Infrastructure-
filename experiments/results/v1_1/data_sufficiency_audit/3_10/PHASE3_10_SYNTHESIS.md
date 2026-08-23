# PHASE 3.10 — DATA SUFFICIENCY & DECISION-TIME OBSERVABILITY AUDIT

## 1. Executive Summary

Phase 3.10 audited the actual Alibaba GPU2020 data and processing boundary rather than training another V1.1 candidate. The audit confirms that V1 has a substantial, reproducible pre-outcome feature contract, but the exact runtime prediction timestamp, synchronized scheduler state, queue pressure, environment identity, operational consequence severity, and several provenance fields are absent or unproven. The evidence supports a combined **B + C** interpretation: the current boundary has missing/poorly timestamped decision-time information and is also narrow in independent-environment coverage. Another blind V1.1 model experiment is not scientifically justified.

## 2. Central Question and Hypotheses

The audit evaluated Hypothesis A (V1 is well matched to sufficient data), Hypothesis B (useful decision-time information is missing, poorly timestamped, or inaccessible), and Hypothesis C (the benchmark is narrow or structurally limited). The evidence matrix is stored in `artifacts/hypothesis_evidence_matrix.json`.

## 3. Frozen V1 Control

V1 remains frozen at `d977a32c2f20efa5f8e0d0349d40b270ecabeca2`. No predictor, coefficient, feature, preprocessing, calibration, threshold, runtime, memory, diagnosis, recovery, safety policy, canonical split, or historical artifact was modified. No model was trained by Phase 3.10.

## 4. Phase 3.8 and 3.9 Context

Candidate A remains HOLD, Candidate C remains rejected for its tested implementation, and Phase 3.9 concluded that the failure mechanism remained unresolved. Phase 3.10 therefore audits whether the data and observability boundary can support a scientifically defensible next experiment.

## 5. Data and Provenance Boundary

The official restored Alibaba GPU2020 processed boundary was used. The dataset manifest identifies the official source and archive checksums; processed tables are derived/cleaned artifacts, while V1 features are further aggregated representations. Raw archives are not silently re-imported, and no replacement or fabricated fields were created.

## 6. Actual Data Inventory

The inventory contains 66 field records across the processed tables. A representative extract follows; the complete inventory is `inventory/data_inventory.csv`.

| File | Field | Type | Role | Rows | Sample missingness | V1 use |
|---|---|---|---|---:|---:|---|
| instance_table.main_sample.csv | job_name | str | identifier | 60005 | 0.00% | Not in V1 |
| instance_table.main_sample.csv | task_name | str | identifier | 60005 | 0.00% | Not in V1 |
| instance_table.main_sample.csv | inst_name | str | identifier | 60005 | 0.00% | Not in V1 |
| instance_table.main_sample.csv | worker_name | str | identifier | 60005 | 0.00% | Not in V1 |
| instance_table.main_sample.csv | inst_id | str | identifier | 60005 | 0.00% | Not in V1 |
| instance_table.main_sample.csv | status | str | outcome | 60005 | 0.00% | Not in V1 |
| instance_table.main_sample.csv | start_time | float64 | timestamp | 60005 | 10.60% | Not in V1 |
| instance_table.main_sample.csv | end_time | float64 | timestamp | 60005 | 9.70% | Not in V1 |
| instance_table.main_sample.csv | machine | str | identifier | 60005 | 0.00% | Not in V1 |
| job_table.clean.csv | _source_row_index | int64 | identifier | 1055501 | 0.00% | Not in V1 |
| job_table.clean.csv | job_name | str | identifier | 1055501 | 0.00% | Not in V1 |
| job_table.clean.csv | inst_id | str | identifier | 1055501 | 0.00% | Not in V1 |
| job_table.clean.csv | user | str | identifier | 1055501 | 0.00% | Not in V1 |
| job_table.clean.csv | status | str | outcome | 1055501 | 0.00% | Not in V1 |
| job_table.clean.csv | start_time | float64 | timestamp | 1055501 | 0.00% | Not in V1 |
| job_table.clean.csv | end_time | float64 | timestamp | 1055501 | 17.20% | Not in V1 |
| machine_metric.main_sample.csv | worker_name | str | identifier | 19841 | 0.00% | Not in V1 |
| machine_metric.main_sample.csv | machine | str | identifier | 19841 | 0.00% | Not in V1 |
| machine_metric.main_sample.csv | start_time | int64 | timestamp | 19841 | 0.00% | Not in V1 |
| machine_metric.main_sample.csv | end_time | int64 | timestamp | 19841 | 0.00% | Not in V1 |
| machine_metric.main_sample.csv | machine_cpu_iowait | float64 | resource | 19841 | 8.50% | Not in V1 |
| machine_metric.main_sample.csv | machine_cpu_kernel | float64 | resource | 19841 | 14.80% | Not in V1 |
| machine_metric.main_sample.csv | machine_cpu_usr | float64 | resource | 19841 | 9.00% | Not in V1 |
| machine_metric.main_sample.csv | machine_gpu | float64 | resource | 19841 | 9.10% | Not in V1 |

The processed boundary contains clean job and task tables, sampled instance records, and sampled sensor/machine metrics. The main V1 feature matrix contains 10,000 sampled terminal jobs and 14 numeric features.

## 7. Raw, Processed, Derived, and Post-Outcome Data

Raw archives are the official source boundary. Clean job/task tables retain source fields. Main-sample task and instance files are linked derived samples. V1 features are job-level aggregates derived from task and instance records. Status, end times, sensor utilization, and machine metrics are outcome/execution-adjacent or post-decision records unless a pre-decision timestamp is explicitly proven.

## 8. Decision-Time Definition

The benchmark does not materialize the runtime prediction timestamp, calibration timestamp, threshold timestamp, abstention timestamp, or memory-retrieval timestamp. Accordingly, the exact decision boundary is **DECISION TIMESTAMP UNKNOWN**. Field presence and a source `start_time` do not establish that a value was available before the V1 prediction.

## 9. Timestamp Audit

The timestamp audit distinguishes source event timestamps from the missing prediction timestamp. Job and instance start times exist, but synchronization, timezone, precision, ingestion ordering, clock skew, and prediction-time ordering are not fully established. Fields without a rigorously demonstrated ordering are marked **TIMING UNKNOWN** rather than treated as decision-time inputs.

## 10. Temporal Dependency Graph

The evidence-supported dependency is: workload/job/task records → plan/resource-request fields → **V1 decision timestamp unknown** → instance start/execution → sensor and machine telemetry → final status/outcome → recovery/validation where available. The graph is intentionally conservative; unknown runtime ordering is not inferred.

## 11. Decision-Time Information Matrix

| Information | Exists? | Timestamp exists? | Before V1 decision? | Used by V1? | Classification |
|---|---|---|---|---|---|
| job_start_time | True | True | UNKNOWN | True | A — USED BY V1 |
| n_tasks | True | False | UNKNOWN | True | A — USED BY V1 |
| n_distinct_task_names | True | False | UNKNOWN | True | A — USED BY V1 |
| sum_inst_num | True | False | UNKNOWN | True | A — USED BY V1 |
| mean_plan_cpu | True | False | UNKNOWN | True | A — USED BY V1 |
| max_plan_cpu | True | False | UNKNOWN | True | A — USED BY V1 |
| mean_plan_mem | True | False | UNKNOWN | True | A — USED BY V1 |
| max_plan_mem | True | False | UNKNOWN | True | A — USED BY V1 |
| mean_plan_gpu | True | False | UNKNOWN | True | A — USED BY V1 |
| max_plan_gpu | True | False | UNKNOWN | True | A — USED BY V1 |
| n_distinct_gpu_types | True | False | UNKNOWN | True | A — USED BY V1 |
| n_instances | True | False | UNKNOWN | True | A — USED BY V1 |
| n_distinct_machines | True | False | UNKNOWN | True | A — USED BY V1 |
| mean_instance_start_time | True | True | UNKNOWN | True | A — USED BY V1 |
| dominant_gpu_type | True | True | UNKNOWN | False | C — AVAILABLE BEFORE DECISION BUT TIMESTAMP UNCERTAIN |
| job_table.user | True | False | UNKNOWN | False | C — AVAILABLE BEFORE DECISION BUT TIMESTAMP UNCERTAIN |
| sensor_table and machine_metric utilization | True | True | UNKNOWN/POST-DECISION | False | D — ONLY AVAILABLE AFTER DECISION |
| job/task final status and end_time | True | True | False | False | E — ONLY AVAILABLE AFTER OUTCOME |
| queue pressure, cluster load, scheduler state, node health, network state | False | False | UNKNOWN | False | F — NOT PRESENT |
| runtime prediction timestamp and ingestion timestamp | False | False | UNKNOWN | False | G — UNKNOWN |

## 12. Missing Information Audit

The current benchmark does not contain verified queue pressure, cluster load at prediction time, resource contention, node health, network state, scheduler state, queue delay, recent workload history, recent failure rate, complete workload provenance, or consequence severity. These are future data requirements, not fabricated candidate features.

## 13. Missingness and Completeness

Missingness is reported in `missingness/missingness_by_population.csv` by population, field, and outcome. The audit does not automatically impute missing data. Clean job/task tables are complete at their documented source level; sampled linked tables and telemetry are partial; prediction timestamp and runtime provenance are missing; outcome labels are complete for the terminal benchmark population.

## 14. Join and Entity Integrity

Job-to-task and job-to-instance joins are available for the main sample. The source cleaning report records no duplicate clean job names and no task job-name orphans in the full cleaned boundary. Node/GPU/runtime provenance is incomplete in the processed research boundary. One-to-many task and instance relationships are expected; they are not independent observations.

## 15. Dependence and Duplication

The dependence audit is forensic only and does not remove records. Shared task names and repeated workload structures indicate template dependence across populations. Job identifiers remain disjoint in the registered splits. Feature-vector overlap and shared task templates limit the strength of claims about independent environments, without automatically constituting leakage.

## 16. Workload Diversity

| Population | Jobs | Failures | Failure rate | Task names | GPU types | Temporal range |
|---|---:|---:|---:|---:|---:|---|
| train | 6999 | 1816 | 0.259 | 16 | 5 | 962704–6449460 |
| validation | 1498 | 389 | 0.260 | 12 | 5 | 999357–6439600 |
| random_test | 1503 | 389 | 0.259 | 15 | 5 | 960837–6449352 |
| canonical_temporal | 2499 | 1085 | 0.434 | 11 | 5 | 5540091–6449460 |
| fold_1_test | 2000 | 345 | 0.172 | 14 | 5 | 3563831–4789055 |
| fold_2_test | 2000 | 635 | 0.318 | 14 | 5 | 4789772–5667324 |
| fold_3_test | 2000 | 757 | 0.379 | 11 | 5 | 5668729–6449460 |

The sample contains 16 global task names and 5 GPU types. Most jobs have a single task, so workload composition is not maximally diverse.

## 17. Failure Diversity

The terminal sample contains binary success/failure outcomes, but no validated multi-class failure-type taxonomy or operational severity. The failure label is therefore narrow: it distinguishes terminal `Failed` from `Terminated`, not distinct mechanisms or consequences. Broad reliability learning should not be claimed from this label alone.

## 18. Temporal Diversity

The sampled jobs span approximately 960,837 to 6,449,460 in the dataset's relative time units. Chronological folds cover distinct slices and show changing failure rates, including 0.1725 in Fold 1, 0.3175 in Fold 2, 0.3785 in Fold 3, and 0.4342 in the canonical temporal test. This supports temporal variation, but not necessarily independent environments or seasonal identification.

## 19. Environment Diversity and Generalization Boundary

The repository does not expose a verified independent cluster, scheduler, trace, or environment identifier for the main V1 sample. GPU types and time periods provide some heterogeneity, but the strongest defensible classification is **UNKNOWN / FEW OBSERVED ENVIRONMENT DIMENSIONS**, not multiple independent environments. The temporal split tests later portions of the same restored trace; it is temporal extrapolation within one benchmark source, not proven cross-environment OOD generalization.

## 20. Distribution Shift and Stability of Information

Failure prevalence changes materially across temporal populations, while several workload-resource means also move. Phase 3.9 found `n_tasks`, `n_distinct_task_names`, `mean_plan_mem`, and `max_plan_mem` directionally consistent exploratory signatures; CPU/GPU and timing signatures were unstable. Phase 3.10 cannot convert those associations into causal or decision-time claims because the prediction timestamp and synchronized availability are not recorded.

## 21. V1 Information Coverage Map

V1 sees 14 numeric job-level features: job start time; task counts and task-name diversity; requested instance count; CPU, memory, and GPU plan aggregates; GPU-type diversity; and instance/machine counts plus instance-start aggregate. These are transformed/aggregated pre-outcome representations in the declared contract. V1 does not see verified live scheduler state, queue pressure, node health, network state, outcome consequence, or a synchronized runtime decision timestamp.

## 22. Unused, Unknown, and Post-Outcome Information

No field was promoted as a clean B-class unused decision-time variable because the timestamp contract is insufficient. `dominant_gpu_type` and `job_table.user` are potentially useful but timing/provenance uncertain. Queue/scheduler/cluster context is absent. Sensor/machine telemetry and final status/end times are execution or outcome-adjacent and cannot be proposed as original decision-time inputs without new evidence.

## 23. Information Bottleneck Matrix

The principal bottlenecks are missing synchronized runtime context, missing operational consequence labels, incomplete provenance for prior history, and insufficient independent environment identifiers. These bottlenecks prevent distinguishing model limitation from information limitation with high confidence.

## 24. Data-Sufficiency Scorecard

| Dimension | Assessment |
|---|---|
| Decision-time observability | **PARTIAL** |
| Temporal coverage | **PARTIAL** |
| Failure diversity | **PARTIAL** |
| Workload diversity | **PARTIAL** |
| Environment diversity | **UNKNOWN** |
| Provenance | **PARTIAL** |
| Timestamp quality | **INSUFFICIENT** |
| Generalization support | **PARTIAL** |

This is a structured scorecard, not an arbitrary scalar.

## 25. Three-Hypothesis Evidence Matrix

| Evidence | Supports A | Supports B | Supports C | Against A | Against B | Against C | Strength |
|---|---|---|---|---|---|---|---|
| V1 uses 14 pre-outcome workload/resource aggregates and has reproducible temporal performance | True | False | False | False | True | False | moderate |
| Prediction timestamp, scheduler state, queue pressure, and consequence severity are absent or unproven | False | True | True | True | False | False | strong |
| Future-fold signatures and error behavior are regime-dependent | False | True | True | True | False | False | moderate |
| Single Alibaba trace with shared task templates and incomplete independent environment identifiers | False | False | True | False | False | False | moderate |

## 26. Why No V1.1 Model Was Built

Phase 3.10 is an audit, not a model competition. No GB, RF, neural network, error classifier, feature optimization, threshold search, or candidate implementation was performed. Prior performance results are supporting context only.

## 27. Safety and Operational Implications

A future experiment must first establish timestamped availability, provenance, latency, cost, and deterministic fallback for any added information. Post-outcome telemetry cannot safely solve the original prediction. A decision-time context experiment should not begin until the relevant context is instrumented and its availability is verified.

## 28. Final Research Decision

**V1 LIMITATIONS APPEAR DATA-BOUND.** More precisely, the evidence supports **B + C**: missing/poorly timestamped decision-time information and a narrow single-trace environment/evaluation boundary. V1 remains the strongest validated control, but the current data does not justify another blind V1.1 model experiment.

## 29. Recommendation for Next Phase

Do not integrate a V1.1 candidate. First perform an observability/data-collection phase that records prediction, ingestion, scheduling, allocation, and outcome timestamps; scheduler/queue/resource state; provenance and environment identifiers; and operational consequence labels. Then preregister one narrow additive hypothesis and evaluate it across the existing chronological folds plus genuinely independent environments when available.

## References

1. `data/audit/alibaba_gpu2020/dataset_manifest.json`
2. `data/audit/alibaba_gpu2020/cleaning_report.json`
3. `docs/PHASE3_BASELINE_AUDIT.md`
4. `experiments/results/v1_1/failure_forensics/3_9/`
5. `experiments/results/v1_1/candidate_screening/3_8/`
 

## Validation record

The required current full repository suite was attempted from `2026-08-23T09:40:03Z` to `2026-08-23T09:45:03Z`. It reached approximately 47% progress and remained CPU-bound until the five-minute timeout, returning exit code `124`. This is recorded as **CURRENT RUN — INCOMPLETE**, not as a successful result. The captured output is preserved in `artifacts/full_suite_attempt.txt`. The inherited verified result of 558 passed and 7 skipped remains distinct and is not claimed as a reproduction by this current run.

Phase 3.10 focused validation passed: 9 audit tests, compilation, diff checks, and frozen-historical-path protection.
