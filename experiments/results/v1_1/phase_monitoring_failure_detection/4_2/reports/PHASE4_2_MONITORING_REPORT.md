# PHASE 4.2 — MONITORING & FAILURE DETECTION REPORT

## Scope and boundary

Phase 4.2 consumes the existing controlled-runtime observation layer and ends at structured failure events. It does not implement diagnosis, root-cause analysis, recovery, infrastructure mutation, V1.1, model training, model tuning, benchmark finalization, or production deployment.

## Monitoring contract

The monitor maintains HEALTHY, DEGRADED, ANOMALOUS, FAILED, and UNKNOWN states. UNKNOWN is not treated as HEALTHY. An anomaly is not a failure. A failure requires actual process evidence. State transitions are explicit and deterministic over the ordered persisted event stream.

## Baseline and rules

The fixed baseline is `phase4.2-baseline-v1`: maximum local process RSS 512 MiB and maximum expected runtime 1.0 seconds. These are a pre-registered conservative engineering envelope, not thresholds tuned on evaluation outcomes. The anomaly detector uses transparent evidence rules. High RSS can produce ANOMALOUS without FAILED; actual nonzero exit and actual runtime-enforced timeout produce confirmed failure evidence.

## Failure taxonomy

Only `PROCESS_NONZERO_EXIT` and `PROCESS_TIMEOUT` are emitted. Each structured failure event includes workload/run/environment identity, failure and detection timestamps, zero measured boundary latency for the controlled runtime event, evidence references, triggering observation, provenance, detector version, certainty `CONFIRMED`, and temporal availability. GPU, scheduler, queue, allocation, and network failures are not emitted because they are unavailable.

## Controlled scenarios and metrics

The persisted controlled-runtime campaign contained 26 events over three runs: one successful completion, one actual nonzero exit, and one actual timeout. Monitoring produced one HEALTHY run and two FAILED runs, with two confirmed structured failures and no false positives.

| Metric | Result |
|---|---:|
| True positives | 2 |
| False positives | 0 |
| False negatives | 0 |
| Precision | 1.0 |
| Recall | 1.0 |
| F1 | 1.0 |
| Detection latency | 0.0 seconds at controlled event boundary |
| Unsupported classes evaluated | None |

A high-RSS anomaly versus failure separation is covered by focused tests. It does not automatically create a failure event.

## Temporal integrity and replay

Monitoring can be evaluated at an explicit `at_or_before` timestamp. A future event inserted after an earlier decision does not alter the earlier state or failure result. Persistent replay preserves original observation timestamps and deterministic ordering; replay processing does not create new observations.

## Coverage and limitations

Process lifecycle, process CPU ticks, RSS, exit status, timeout, workload identity, environment identity, provenance, and local runtime timestamps are observable. GPU, scheduler, queue, cluster allocation, network, recovery, validation, and operational consequence information remain unavailable. The results are controlled-runtime engineering evidence from one environment and cannot establish external generalization or production reliability.

## Safety

The detector emits monitoring states, anomaly records, and structured failure events only. It does not call an executor, recovery planner, rollback, redeployment, retraining, or infrastructure mutation path.

## Readiness gate

| Gate | Result |
|---|---|
| Monitoring contract | READY |
| Monitoring state machine | READY |
| Runtime observation integration | READY |
| Anomaly detection | READY — transparent rules |
| Failure confirmation | READY — two supported classes |
| Failure event schema | READY |
| Temporal integrity | PASS |
| Provenance | PASS |
| Unknown handling | PASS |
| Replay determinism | PASS |
| Controlled failure scenarios | PASS |
| Detection metrics | PASS — controlled scenarios |
| Baseline comparison | PASS |
| Coverage | PARTIAL — unsupported infrastructure explicit |
| V1 integrity | PASS |
| Historical protection | PASS |
| Focused tests | PASS — 24 combined |
| Full suite | NOT RUN |

## Final decision

**B — PHASE 4.2 ENGINEERING-COMPLETE / EVALUATION-LIMITED.** The monitoring and failure-detection chain is implemented and validated on controlled scenarios, but evidence is limited to one controlled local environment and unsupported infrastructure classes remain unavailable.

**PHASE 4.3 AUTHORIZATION: AUTHORIZED** to consume the structured failure-event layer for diagnosis/causal-understanding engineering, subject to the controlled-runtime boundary and without production or independent-environment claims.
