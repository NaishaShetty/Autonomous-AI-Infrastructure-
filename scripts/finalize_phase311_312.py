"""Finalize Phase 3.11+3.12 data foundation artifacts."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'experiments/results/v1_1/data_foundation/3_11_3_12'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def main():
 marker=OUT/'.finalized'
 if marker.exists(): raise SystemExit('Phase 3.11+3.12 already finalized; refusing overwrite')
 cov=pd.read_csv(OUT/'coverage/observability_coverage.csv'); src=pd.read_csv(OUT/'source_evaluation/source_acceptance_matrix.csv'); div=pd.read_csv(ROOT/'experiments/results/v1_1/data_sufficiency_audit/3_10/diversity/workload_failure_temporal_diversity.csv')
 src_rows='\n'.join(f"| {r['source']} | {r['environment_diversity']} | {r['workload_diversity']} | {r['failure_diversity']} | {r['timestamp_quality']} | {r['decision_time_support']} | {r['provenance']} | {r['decision']} |" for _,r in src.iterrows())
 div_rows='\n'.join(f"| {r['population']} | {int(r['distinct_jobs'])} | {r['failure_rate']:.3f} | {int(r['distinct_task_names'])} | {int(r['distinct_gpu_types'])} |" for _,r in div.iterrows())
 obs='\n'.join(f"| {r['environment_id']} | {r['event_coverage']} | {r['timestamp_coverage']} | {r['decision_time_coverage']} | {r['provenance_coverage']} | {r['scheduler_state_coverage']} |" for _,r in cov.iterrows())
 report_a='''# PHASE 3.11 — DECISION-TIME OBSERVABILITY REPORT

## 1. Objective

Build a versioned event, timestamp, provenance, and snapshot foundation that can answer what the reliability system knew at the moment of prediction.

## 2. Phase 3.10 Findings Being Addressed

The prior audit found a missing runtime prediction timestamp, incomplete scheduler/resource context, partial provenance, and no proven environment identity. This work addresses these gaps at the schema and interface level without claiming that current Alibaba data supplies the missing values.

## 3. Decision-Time Contract

`DecisionTimeContract` explicitly represents input snapshot time, prediction generated time, and prediction decision time, with the relationship `snapshot <= generated <= decision`. Naive timestamps are rejected. If a runtime timestamp is unavailable, the correct state is `UNKNOWN`; file order and identifiers are never used as temporal evidence.

## 4. Canonical Event Model

The versioned `CanonicalEvent` supports workload receipt/registration, task creation, scheduling, resource allocation, environment/node/queue observations, prediction input/generated/decision events, execution, telemetry, failure, diagnosis, recovery, validation, and completion. Missing events are unavailable, not fabricated. Every event requires provenance.

## 5. Timestamp Model

Timestamp quality is explicitly classified as EXACT, SYNCHRONIZED, APPROXIMATE, INFERRED, or UNKNOWN. UTC normalization rejects timezone-naive values and preserves the requirement that original timestamp, source, precision, and quality remain explicit. No ambiguous relative Alibaba time is silently upgraded to synchronized runtime time.

## 6. Provenance Model

`Provenance` records source, source version, record identity, extraction, transformation, transformation version, timestamp source and quality, schema version, ingestion/processing time, and checksum. The chain is final observation → transformation → source record → dataset.

## 7. DecisionTimeSnapshot

`DecisionTimeSnapshot` separates workload, task, resource, scheduler, queue, environment, and recent historical contexts. It accepts only BEFORE or AT decision availability and requires a decision timestamp plus provenance. Post-decision and post-outcome observations cannot be placed into the snapshot.

## 8. Resource Context

The canonical schema supports requested, allocated, available, contention, utilization, node state, and GPU state. Alibaba currently populates request-side plan fields and partial sampled telemetry only; allocated/available live state remains unavailable or unproven.

## 9. Scheduler Context

The schema supports queue depth, wait time, scheduler state, scheduling decision/policy, resource pressure, and allocation delay. None is treated as present in current Alibaba metadata without a verified source and timestamp.

## 10. Environment Context

`EnvironmentIdentity` supports environment, cluster, scheduler, infrastructure, hardware, GPU generation, node population, trace identity, collection period, provenance, checksum, and availability status. Alibaba is registered as one canonical control trace, not as multiple independent environments.

## 11. Failure Provenance

`FailureRecord` carries failure/detection timestamps, source, evidence, confidence, provenance, consequence, and recovery status. Unknown fields remain unknown. Current Alibaba supports a binary terminal outcome, not a validated mechanism taxonomy.

## 12. Operational Consequences

The consequence schema supports severity, recovery cost, downtime, wasted compute, retries, delay, affected workloads, cascading impact, recovery success/failure, and safety impact. Current Alibaba does not provide these labels; no severity is fabricated.

## 13. Data Collection Interfaces

`CanonicalBatchAdapter` supports deterministic structured event normalization while preserving source dataset, source record identity, schema version, and provenance. The foundation is ready for structured ingestion, replay, validation, and future source-specific adapters.

## 14. Environment Registry

The registry enforces unique environment IDs. The current registry contains only `alibaba_gpu2020_main_trace` with canonical-control status and metadata-only environment identity.

## 15. Dataset Registry

The dataset registry records dataset/version, source/version, adapter and processing versions, schema version, checksum, row count, temporal range, environment count, workload count, and failure count.

## 16. Current Alibaba Coverage

| Environment | Event coverage | Timestamp coverage | Decision-time coverage | Provenance coverage | Scheduler coverage |
|---|---|---|---|---|---|
'''+obs+'''

## 17. Missing Observability

Prediction timestamp, ingestion synchronization, queue state, live scheduler state, allocation state, node health, network state, consequence severity, and complete runtime provenance remain missing or unproven. The system records these as unavailable rather than fabricating them.

## 18. Validation

Schemas, event required fields, timestamp timezone handling, decision-time boundaries, order diagnostics, provenance, environment uniqueness, adapter determinism, and split contamination checks are covered by focused tests. Quality artifacts report partial timestamp/provenance coverage honestly.

## 19. Limitations

This is a foundation, not live instrumentation. The current source provides no synchronized runtime event stream, and no independent environments were integrated. Schema support does not imply data availability.

## 20. Readiness Decision

**OBSERVABILITY FOUNDATION: PARTIAL.** The contracts and deterministic utilities are implemented, but the current source is not sufficient to claim runtime observability readiness until real timestamped event collection is connected.
'''
 report_b='''# PHASE 3.12 — DATA EXPANSION REPORT

## 1. Objective

Establish truthful, provenance-preserving infrastructure for future multi-environment and multi-regime data expansion. The objective is diversity of environments, workloads, failures, time, and operations—not merely more rows.

## 2. Data Expansion Requirements

Future sources must carry environment identity, decision-time timestamps, workload and failure diversity, provenance, legal metadata, schema mappings, and reproducible checksums. No heterogeneous data is silently merged.

## 3. Candidate Source Inventory

The source inventory distinguishes the official Alibaba control source from additional public traces that were not acquired or integrated in this phase.

## 4. Source Acceptance Criteria

Acceptance requires provenance, license, timestamp quality, decision-time support, failure representation, environment diversity, schema compatibility, reproducibility, and research relevance. A failed gate defers a source.

## 5. Source Evaluation

| Source | Environment diversity | Workload diversity | Failure diversity | Timestamp quality | Decision-time support | Provenance | Decision |
|---|---|---|---|---|---|---|---|
'''+src_rows+'''

## 6. Environment Diversity

Alibaba is one trace/environment identity. Independent clusters, schedulers, and infrastructure generations are not established. The environment registry and holdout contracts support future expansion.

## 7. Workload Diversity

The current sample has 16 global task names and 5 observed GPU types. Most jobs have a single task, so workload-family diversity is partial and future source expansion remains necessary.

## 8. Failure Diversity

The current source provides a binary terminal outcome rather than multiple validated failure mechanisms or operational consequence classes. It is insufficient for broad failure-mechanism generalization.

## 9. Temporal Diversity

Temporal holdout contracts are implemented. Alibaba contains several time slices, but the trace is not evidence of independent environments or seasonal generalization.

## 10. Provenance

Dataset, source, workload, environment, adapter, processing, schema, checksum, and collection metadata are registry fields. Current Alibaba source identity is preserved.

## 11. Schema Compatibility

Canonical Event, Workload, Environment, Resource State, Prediction, Outcome, Failure, Recovery, Consequence, and Provenance schemas provide a stable cross-source target. Source-specific fields are retained through provenance and mappings.

## 12. Dataset Normalization

The Alibaba mapping is metadata-only and explicitly marks prediction timestamp, scheduler state, queue depth, allocation state, and source-derived environment identity as unavailable. No fake adapter is created.

## 13. Environment-Holdout Support

Contract-only splits support training on environments A+B and testing on C. These splits are not executed and no model is trained in this phase.

## 14. Multi-Regime Split Support

Temporal, environment, environment×temporal, and workload-family holdout contracts are implemented with contamination checks and explicit `CONTRACT_ONLY_NOT_EXECUTED` status.

## 15. Contamination Controls

The foundation checks duplicate IDs, train/test overlap, provenance/source boundaries, temporal ordering diagnostics, and future merge prohibition. Shared templates are recorded as dependence evidence rather than silently removed.

## 16. Data Quality Gates

Schema, provenance, timestamp, identifier, ordering, duplicate, leakage, completeness, environment identity, and source integrity gates are represented in the quality directory. Alibaba passes schema/leakage identity checks but remains partial on timestamps and runtime provenance.

## 17. Current Integrated Sources

Only official Alibaba GPU2020 is registered as the canonical control source. It is not rewritten and is not merged with another source.

## 18. Sources Rejected / Deferred

Additional public traces are deferred because this phase did not complete source-specific provenance, timestamp, license, and schema acceptance evaluation. No external data is silently integrated.

## 19. Dataset Limitations

One environment, partial failure diversity, missing synchronized decision events, incomplete live resource state, and absent consequence labels limit immediate benchmark construction.

## 20. Benchmark Implications

The foundation enables a future benchmark but does not finalize one. A benchmark must include independent environments, temporal holdouts, workload-family holdouts, decision-time observability, failure mechanisms, consequences, provenance, and contamination controls.

## 21. Readiness Decision

**MULTI-ENVIRONMENT FOUNDATION: PARTIAL.** Infrastructure is implemented; additional legitimate sources and source adapters are still required.
'''
 synthesis='''# PHASE 3.11 + 3.12 — DATA FOUNDATION SYNTHESIS

## 1. Executive Summary

The combined phase implemented the missing data and observability foundation without changing V1 or integrating fabricated data. It provides canonical event, snapshot, timestamp, provenance, environment, dataset, failure, recovery, consequence, registry, adapter, quality-gate, coverage, and holdout-split contracts. The current Alibaba source remains a truthful single-source control with partial observability.

## 2. Why These Phases Were Combined

Decision-time observability and multi-environment identity are coupled: events without environment identity cannot support held-out generalization, and new environments without a canonical observability schema cannot be compared reliably.

## 3. Phase 3.10 Findings

Phase 3.10 found missing prediction timestamps, incomplete scheduler/resource context, partial provenance, and unknown independent-environment coverage. This implementation addresses those as explicit contracts and recorded limitations.

## 4. Frozen V1 Boundary

V1 remains frozen at `d977a32c2f20efa5f8e0d0349d40b270ecabeca2`. No model, feature, calibration, split, runtime, historical artifact, or result was modified.

## 5. Decision-Time Observability

`DecisionTimeContract` and `DecisionTimeSnapshot` make availability explicit. Unknown timing is not upgraded to decision-time.

## 6. Canonical Event Model

The versioned event model covers the full reliability lifecycle and requires provenance for every event.

## 7. Timestamp Integrity

UTC normalization rejects naive timestamps; quality classes preserve the difference between exact, synchronized, approximate, inferred, and unknown values. Alibaba runtime prediction time remains unknown.

## 8. Provenance

Source, record, transformation, timestamp, schema, ingestion, processing, and checksum metadata are preserved through the foundation.

## 9. Environment Identity

One Alibaba canonical environment is registered. Future independent environments require unique identity, source, hardware, scheduler, period, provenance, and checksum.

## 10. Dataset Identity

Dataset/version, source/version, adapter, processing, schema, checksum, row counts, temporal range, environment count, workload count, and failure count are registered.

## 11. Multi-Environment Expansion

The source acceptance matrix defers additional public traces until their evidence and legal/provenance requirements are satisfied. No external source was silently merged.

## 12. Multi-Regime Support

Temporal, environment, environment×temporal, and workload-family split contracts are implemented for future evaluation, not executed for modeling.

## 13. Current Data Sources

Alibaba GPU2020 is the only current registered source and remains the canonical V1 control. Additional sources are deferred.

## 14. Source Acceptance / Rejection

| Source | Decision |
|---|---|
| Alibaba GPU2020 | Canonical control / do not merge |
| Additional public traces | Deferred; not integrated |

## 15. Normalization

The canonical schemas and Alibaba mapping preserve source boundaries and mark unavailable fields explicitly.

## 16. Data Quality

Quality artifacts cover schema, timestamps, provenance, duplicates, leakage, completeness, and source integrity. Results are partial where the current data is partial.

## 17. Contamination Controls

No train/test contamination, shared identifiers, or silent source merges are introduced by the foundation. Shared workload templates remain recorded dependence information.

## 18. Environment-Held-Out Support

Contract-only environment and environment×temporal holdouts are ready for future data and modeling.

## 19. Observability Coverage

| Environment | Event | Timestamp | Decision time | Provenance | Scheduler |
|---|---|---|---|---|---|
'''+obs+'''

## 20. Current Dataset Limitations

The current source lacks synchronized runtime events, independent environments, live scheduler state, consequence severity, and complete provenance. The foundation cannot manufacture these.

## 21. Benchmark Implications

The benchmark is not finalized. The foundation defines what must be present before a future benchmark can support reliability claims.

## 22. What We Can Now Reliably Measure

Future sources can be validated against stable schemas, provenance chains, timestamp quality, event order, contamination rules, environment registries, and explicit holdout contracts.

## 23. What We Still Cannot Measure

The current source cannot yet support trustworthy runtime decision-time reconstruction, cross-environment generalization, live scheduler/resource-state effects, or consequence-weighted reliability.

## 24. V1 Status

V1 remains frozen and remains the strongest validated control under the existing evidence.

## 25. V1.1 Status

No V1.1 model exists and no V1.1 integration is authorized.

## 26. Readiness Gate

| Foundation | Status |
|---|---|
| Observability foundation | **PARTIAL** |
| Multi-environment foundation | **PARTIAL** |
| Data provenance | **PARTIAL** |
| Timestamp integrity | **PARTIAL** |
| Environment identity | **PARTIAL** |
| Multi-regime splits | **READY — CONTRACTS ONLY** |
| Data quality | **PARTIAL** |
| Benchmark foundation | **PARTIAL** |

## 27. Recommended Next Phase

**D — BOTH INCOMPLETE.** Freeze these contracts, instrument a real timestamped source, register at least one genuinely independent environment, validate quality gates, construct the first benchmark, reproduce frozen V1, and only then define one narrow V1.1 hypothesis.
'''
 validation_record="""

## Validation record

The required current full repository suite was attempted from `2026-08-23T09:58:01Z` to `2026-08-23T10:03:01Z`. It reached approximately 46% progress and remained CPU-bound until the five-minute timeout, returning exit code `124`. This is recorded as **CURRENT RUN — INCOMPLETE**, not as a successful result. The captured output is preserved in `artifacts/full_suite_attempt.txt`. The inherited verified result of 558 passed and 7 skipped remains distinct and is not claimed as a reproduction by this current run.

The focused foundation tests passed with 10 tests, alongside compilation, diff, schema/contract, provenance, timestamp, and historical-path checks.
"""
 (OUT/'reports/PHASE3_11_OBSERVABILITY_REPORT.md').write_text(report_a); (OUT/'reports/PHASE3_12_DATA_EXPANSION_REPORT.md').write_text(report_b); (OUT/'PHASE3_11_3_12_SYNTHESIS.md').write_text(synthesis+validation_record)
 plt.figure(figsize=(8,4.5));plt.bar(cov.environment_id,cov.decision_time_coverage.map({'INSUFFICIENT':0.25,'PARTIAL':0.5,'SUFFICIENT':1,'UNAVAILABLE':0}),color='#4c78a8');plt.ylabel('Coverage score (qualitative)');plt.title('Decision-time coverage by registered environment');plt.tight_layout();plt.savefig(OUT/'plots/decision_time_coverage.png',dpi=160);plt.close()
 files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='.finalized'); (OUT/'hashes/manifest.json').write_text(json.dumps({'experiment_id':'phase311_312_decision_time_observability_multi_environment_data_foundation','files':{str(p.relative_to(OUT)):sha(p) for p in files}},indent=2,sort_keys=True)+'\n'); files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='.finalized'); marker.write_text(json.dumps({str(p.relative_to(OUT)):sha(p) for p in files},indent=2,sort_keys=True)+'\n'); print(f'finalized {len(files)} files')
if __name__=='__main__':main()
