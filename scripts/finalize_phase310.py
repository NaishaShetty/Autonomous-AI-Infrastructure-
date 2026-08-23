"""Finalize Phase 3.10 data sufficiency audit artifacts."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'experiments/results/v1_1/data_sufficiency_audit/3_10'

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
 return h.hexdigest()

def main():
 marker=OUT/'.finalized'
 if marker.exists(): raise SystemExit('Phase 3.10 already finalized; refusing overwrite')
 inv=pd.read_csv(OUT/'inventory/data_inventory.csv'); div=pd.read_csv(OUT/'diversity/workload_failure_temporal_diversity.csv'); avail=pd.read_csv(OUT/'information/decision_time_information_matrix.csv'); dep=pd.read_csv(OUT/'dependence/dependence_duplication_audit.csv')
 score=json.loads((OUT/'diversity/scorecard.json').read_text())
 manifest=json.loads((ROOT/'data/audit/alibaba_gpu2020/dataset_manifest.json').read_text())
 inv_rows=[]
 for _,r in inv.head(24).iterrows(): inv_rows.append(f"| {r['file']} | {r['field']} | {r['type']} | {r['role']} | {r['row_count']} | {r['missing_pct_sample']:.2f}% | {'A — USED BY V1' if r['used_by_v1'] else 'Not in V1'} |")
 div_rows=[]
 for _,r in div.iterrows(): div_rows.append(f"| {r['population']} | {int(r['distinct_jobs'])} | {int(r['failed_jobs'])} | {r['failure_rate']:.3f} | {int(r['distinct_task_names'])} | {int(r['distinct_gpu_types'])} | {r['temporal_start']:.0f}–{r['temporal_end']:.0f} |")
 info_rows=[]
 for _,r in avail.iterrows(): info_rows.append(f"| {r['information']} | {r['exists']} | {r['timestamp_exists']} | {r['before_v1_decision']} | {r['used_by_v1']} | {r['classification']} |")
 hyp=json.loads((OUT/'artifacts/hypothesis_evidence_matrix.json').read_text())
 hyp_rows=[]
 for r in hyp: hyp_rows.append(f"| {r['evidence']} | {r['supports_A']} | {r['supports_B']} | {r['supports_C']} | {r['against_A']} | {r['against_B']} | {r['against_C']} | {r['strength']} |")
 synthesis=f'''# PHASE 3.10 — DATA SUFFICIENCY & DECISION-TIME OBSERVABILITY AUDIT

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

The inventory contains {len(inv)} field records across the processed tables. A representative extract follows; the complete inventory is `inventory/data_inventory.csv`.

| File | Field | Type | Role | Rows | Sample missingness | V1 use |
|---|---|---|---|---:|---:|---|
{chr(10).join(inv_rows)}

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
{chr(10).join(info_rows)}

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
{chr(10).join(div_rows)}

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
{chr(10).join(hyp_rows)}

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
 '''
 validation_record = """

## Validation record

The required current full repository suite was attempted from `2026-08-23T09:40:03Z` to `2026-08-23T09:45:03Z`. It reached approximately 47% progress and remained CPU-bound until the five-minute timeout, returning exit code `124`. This is recorded as **CURRENT RUN — INCOMPLETE**, not as a successful result. The captured output is preserved in `artifacts/full_suite_attempt.txt`. The inherited verified result of 558 passed and 7 skipped remains distinct and is not claimed as a reproduction by this current run.

Phase 3.10 focused validation passed: 9 audit tests, compilation, diff checks, and frozen-historical-path protection.
"""
 (OUT/'PHASE3_10_SYNTHESIS.md').write_text(synthesis + validation_record)
 # Add a compact distribution-shift table.
 d=div.copy(); d['failure_rate']=d['failure_rate'].astype(float); d.to_csv(OUT/'distribution_shift/population_distribution_summary.csv',index=False)
 plt.figure(figsize=(9,4.5)); plt.bar(div.population,div.failure_rate,color='#4c78a8'); plt.xticks(rotation=25); plt.ylabel('Failure rate'); plt.title('Registered population failure-rate distribution'); plt.tight_layout(); plt.savefig(OUT/'plots/failure_rate_by_population.png',dpi=160); plt.close()
 files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='.finalized')
 (OUT/'hashes/manifest.json').write_text(json.dumps({'experiment_id':'3_10_v1_data_sufficiency_decision_time_observability_audit','files':{str(p.relative_to(OUT)):sha(p) for p in files}},indent=2,sort_keys=True)+'\n')
 files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='.finalized')
 marker.write_text(json.dumps({str(p.relative_to(OUT)):sha(p) for p in files},indent=2,sort_keys=True)+'\n')
 print(f'finalized {len(files)} files')
if __name__=='__main__':main()
