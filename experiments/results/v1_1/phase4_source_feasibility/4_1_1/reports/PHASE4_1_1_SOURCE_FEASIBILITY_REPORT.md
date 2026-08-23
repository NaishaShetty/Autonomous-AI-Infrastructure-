# PHASE 4.1.1 — RUNTIME SOURCE FEASIBILITY REPORT

## 1. Repository audit

The repository already contains canonical events, decision-time snapshots, provenance, timestamp validation, a collector, append-only persistent storage, deterministic replay, and a bounded observability API. The audit found no project-owned workload executor, approved simulator with real event semantics, live telemetry source, scheduler source, or synchronized external runtime event stream. The existing store is infrastructure, not a source.

## 2. Candidate source inventory and classification

| Candidate | Classification | Engineering status | Research status | Decision |
|---|---|---|---|---|
| Alibaba GPU2020 processed trace | HISTORICAL_TRACE | Replayable data | Not a live runtime source | REJECT |
| Persistent event store | UNUSABLE as source | Storage infrastructure | Not research evidence | DEFER |
| Synthetic test fixtures | SYNTHETIC_TEST_FIXTURE | Test only | Not research evidence | REJECT |
| External runtime source | UNUSABLE / not connected | Not connected | Deferred | DEFER |

## 3. Observability requirements matrix

The machine-readable matrix is `observability/observability_matrix.json`. Workload/task fields and sampled telemetry are partial historical evidence; prediction timestamps, scheduler, queue, allocation, live resource, node, GPU, recovery, and validation runtime events are unavailable. Provenance and source identity are partial, while synchronized runtime semantics are not proven.

## 4. Decision-time feasibility

The project cannot currently prove `snapshot_time <= prediction_generated_time <= prediction_decision_time` for a real runtime event stream. The Phase 4.1 contracts can enforce this relationship once a legitimate source provides the timestamps, but a schema or persistent store cannot create that evidence.

## 5. Timestamp quality

Alibaba contains time-like source fields and sampled telemetry timestamps, but their relationship to a V1 prediction decision is unknown. They are not upgraded to synchronized or exact runtime timestamps. Synthetic fixtures use controlled test timestamps only.

## 6. Provenance and environment identity

Dataset/source provenance and one Alibaba trace identity are available at the historical data boundary. Complete runtime producer identity, source-record occurrence, clock basis, scheduler identity, node identity, and independent environment identity are not available. Multiple runs must not be labeled independent environments.

## 7. Resource and telemetry feasibility

Schema support exists for CPU/GPU/memory, allocation, utilization, contention, node, queue, and scheduler state. Current evidence only partially supports historical requested/resource aggregates and sampled telemetry; it does not support live decision-time resource or scheduler observations.

## 8. Reproducibility

The existing event store and replay are deterministic for supplied canonical events. This is replayable data/infrastructure, not reproducible runtime observation. Alibaba preprocessing is reproducible at its documented boundary, but the original runtime event occurrence and synchronized clocks cannot be regenerated.

## 9. Instrumentation decision

No legitimate existing runtime path justified a new adapter or controlled instrumentation. No fake source was created, no timestamps were invented, and no simulation was presented as infrastructure evidence.

## 10. Validation and integrity

Existing Phase 4 architecture and hardening tests were reused. New feasibility artifacts are isolated under this phase. V1 and historical Phase 3–4 artifacts remain protected. No model, detector, diagnosis, recovery, benchmark, or Phase 4.2 implementation was added.

## 11. Final decision

**D — NO LEGITIMATE RUNTIME SOURCE CURRENTLY AVAILABLE.** The reusable observability infrastructure is present, but the source gate is not satisfied.

## 12. Phase 4.2 authorization

**PHASE 4.2 AUTHORIZATION: NOT AUTHORIZED.** A future phase may revisit this decision only after an approved real or controlled runtime process can emit actual event occurrences with timestamp semantics, provenance, environment identity, and reproducible storage.
