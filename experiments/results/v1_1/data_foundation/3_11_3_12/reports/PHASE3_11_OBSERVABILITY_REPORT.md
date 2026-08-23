# PHASE 3.11 — DECISION-TIME OBSERVABILITY REPORT

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
| alibaba_gpu2020_main_trace | PARTIAL | PARTIAL | INSUFFICIENT | PARTIAL | UNAVAILABLE |

## 17. Missing Observability

Prediction timestamp, ingestion synchronization, queue state, live scheduler state, allocation state, node health, network state, consequence severity, and complete runtime provenance remain missing or unproven. The system records these as unavailable rather than fabricating them.

## 18. Validation

Schemas, event required fields, timestamp timezone handling, decision-time boundaries, order diagnostics, provenance, environment uniqueness, adapter determinism, and split contamination checks are covered by focused tests. Quality artifacts report partial timestamp/provenance coverage honestly.

## 19. Limitations

This is a foundation, not live instrumentation. The current source provides no synchronized runtime event stream, and no independent environments were integrated. Schema support does not imply data availability.

## 20. Readiness Decision

**OBSERVABILITY FOUNDATION: PARTIAL.** The contracts and deterministic utilities are implemented, but the current source is not sufficient to claim runtime observability readiness until real timestamped event collection is connected.
