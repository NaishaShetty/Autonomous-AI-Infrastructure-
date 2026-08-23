# PHASE 4.1.2 — CONTROLLED RUNTIME REPORT

## Scope

This phase creates the first legitimate project-owned runtime event source. It does not implement monitoring, anomaly detection, failure detection models, diagnosis, recovery, V1.1, model training, benchmark construction, or production deployment.

## Runtime architecture

A project-owned Python runner launches actual local subprocess workloads. Runtime boundaries emit canonical events through `ObservationCollector`, which enforces provenance and persists through the existing append-only `PersistentEventStore`. `ObservationReplay`, `DecisionSnapshotBuilder`, and `ObservabilityAPI` are reused. No second database or event taxonomy was introduced.

## Actual scenarios

| Scenario | Actual mechanism | Result |
|---|---|---|
| Successful workload | Local Python subprocess exits 0 | **COMPLETED** |
| Actual failure | Local Python subprocess exits with code 7 | **FAILED** |
| Actual timeout | Runtime deadline kills a sleeping subprocess | **TIMEOUT** |
| Telemetry | Runtime samples `/proc` while process is alive | **OBSERVED** |
| Restart/replay | SQLite close/reopen and deterministic replay | **PASS** |

Events correspond to actual process receipt, registration, start, observation, exit, and termination boundaries. Failure and timeout events are emitted only after the corresponding nonzero exit or actual kill.

## Timestamp and provenance semantics

Timestamps are captured at actual runtime boundaries using the UTC-aware Python wall clock. They are exact for the local controlled process boundary, but are not claimed to be synchronized with external infrastructure. Every event records source, source record, runtime version, transformation, schema version, timestamp source, timestamp quality, environment identity, workload identity, and configuration.

## Telemetry and unavailable infrastructure

Process RSS and CPU tick observations are collected from the actual live process state. GPU, scheduler, queue, cluster allocation, node-level scheduling, recovery, validation, and production consequence fields remain **UNAVAILABLE** because they do not exist in this controlled runtime. No fake cluster or scheduler was created.

## Persistence, restart, replay, and snapshots

The runtime persists raw source input separately from normalized canonical events through the existing `PersistentEventStore`. It closes and reopens the same SQLite store, reconstructs event history, verifies deterministic replay equality, and supports decision-time snapshot construction without post-decision observations.

## Scientific boundary

This source is **CONTROLLED_RUNTIME**: project-owned, local, reproducible by configuration, and useful for observability engineering. It is not real external infrastructure, an independent environment, production evidence, benchmark evidence, or evidence of autonomous recovery or generalization. Multiple runs share one controlled environment identity.

## Readiness gate

| Gate | Result |
|---|---|
| Actual workload execution | READY |
| Actual runtime event emission | READY |
| Timestamp semantics | READY — actual local boundaries |
| Timestamp quality | READY — EXACT local clock; not external synchronized |
| Runtime provenance | READY |
| Environment identity | READY — one controlled environment |
| Workload identity | READY |
| Resource telemetry | PARTIAL — process CPU/RSS only |
| Persistence | READY |
| Restart reconstruction | READY |
| Replay | READY |
| Decision-time snapshot | READY |
| API safety | READY |
| Source registration | READY |
| Coverage | PARTIAL — unsupported infrastructure fields explicit |
| Data quality | PASS |
| Historical protection | PASS |
| V1 integrity | PASS |
| Focused tests | PASS — 16 combined |
| Full suite | NOT RUN |

## Final decision

**A — CONTROLLED RUNTIME OPERATIONALLY READY** for observability engineering and controlled Phase 4.2 preparation. This does not authorize real-world or independent-environment claims.

**PHASE 4.2 AUTHORIZATION: AUTHORIZED FOR CONTROLLED-RUNTIME ENGINEERING**

Phase 4.2 must consume this observation layer and remain explicitly bounded to controlled-runtime engineering until independent real-world evidence exists.
