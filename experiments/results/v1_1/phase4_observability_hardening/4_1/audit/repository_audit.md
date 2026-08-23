# Phase 4.1 Hardening Repository Audit

| Capability | Existing implementation | Reusable? | Missing? | Action |
|---|---|---|---|---|
| Canonical events | `src/data_foundation/foundation.py` | Yes | No | Reused |
| Timestamp and availability | Phase 3.11+3.12 foundation | Yes | Runtime source unavailable | Enforced in collector/snapshot builder |
| Provenance | `Provenance` and canonical events | Yes | Some runtime fields source-dependent | Required source/source-record/quality |
| In-memory event store | `src/phase4/observability.py` | Yes | Durable restart | Extended with SQLite store |
| Replay | `ObservationReplay` | Yes | Persistent reload | Reused over persistent store |
| V1 runtime | frozen historical control | Protected | No change allowed | Not modified |
| Legitimate external runtime source | None identified | N/A | Yes | Report NOT AVAILABLE |

No duplicate event taxonomy, registry, timestamp system, or model was introduced.
