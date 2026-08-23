# PHASE 4.3 — DIAGNOSIS & CAUSAL UNDERSTANDING REPORT

## Scope

Phase 4.3 consumes confirmed Phase 4.2 failure events and produces structured, provenance-backed diagnoses. It does not implement recovery planning, retry, rollback, rescheduling, infrastructure mutation, retraining, redeployment, V1.1, model competition, or benchmark finalization.

## Diagnosis architecture

The deterministic chain is `CONFIRMED FAILURE → ELIGIBLE EVIDENCE → HYPOTHESES → SUPPORTING/CONTRADICTORY EVIDENCE → CAUSAL STATUS → CONFIDENCE → STRUCTURED DIAGNOSIS`. No learned model or tuned causal score is used. Historical failure memory was not integrated because it is not validated for this controlled-runtime use.

## Controlled-runtime diagnoses

The two confirmed failures were diagnosed from the persisted controlled-runtime stream. A nonzero process exit produces `PROCESS_EXIT_FAILURE` with high diagnostic confidence and causal status `OBSERVED`; its deeper root cause is `UNKNOWN`. A runtime-enforced timeout produces `RUNTIME_TIMEOUT` with high diagnostic confidence and causal status `SUPPORTED_CAUSAL_HYPOTHESIS`; the immediate deadline/termination mechanism is supported, while the deeper workload cause remains `UNKNOWN`.

A failure class is not treated as a root cause. Unsupported GPU, scheduler, queue, network, recovery, and allocation causes remain unavailable.

## Evidence and temporal integrity

Every diagnosis preserves failure ID, workload/run/environment identity, evidence and observation IDs, timestamps, source and source records, timestamp quality, temporal availability, detector and diagnosis references, and hypothesis provenance. Only events at or before the diagnosis boundary are eligible. Post-failure observations are not silently inserted into autonomous diagnosis. Future-event invariance and deterministic replay passed.

## Causal ground truth

`CAUSAL_GROUND_TRUTH_UNAVAILABLE`. The controlled runtime proves actual process outcomes and runtime termination, but does not independently establish deeper root-cause labels. Root-cause accuracy is therefore not computed. Evidence quality and uncertainty handling are evaluated instead.

## Evaluation and baselines

The evaluation covers normal completion as no diagnosis required, nonzero exit, timeout, unsupported evidence, and temporal boundary behavior. Simple failure-class, exit-code, and timeout baselines are recorded. No improvement claim over these baselines is made because true causal ground truth is unavailable.

| Metric | Result |
|---|---:|
| Diagnoses evaluated | 2 |
| Evidence provenance completeness | 1.0 |
| Temporal leakage rate | 0.0 |
| Forced diagnosis rate | 0.0 |
| Unsupported-cause rate | 0.0 |
| Unknown deeper-root-cause rate | 1.0 |
| Root-cause accuracy | Not computed |

## Safety and scientific boundary

Diagnosis emits structured information only. It does not execute retry, recovery, rollback, rescheduling, resource adjustment, retraining, redeployment, or infrastructure mutation. Evidence is controlled-runtime evidence from one environment, not production, external infrastructure, independent-environment, or benchmark-generalization evidence.

## Readiness gate

| Gate | Result |
|---|---|
| Diagnosis contract | READY |
| Failure-event integration | READY |
| Evidence model | READY |
| Hypothesis generation | READY |
| Alternative hypotheses | READY |
| Contradictory evidence | READY — explicit representation |
| Causal-status semantics | READY |
| Confidence semantics | READY |
| UNKNOWN handling | READY |
| Temporal integrity | PASS |
| Memory boundary | PASS — not integrated |
| Provenance | PASS |
| Replay determinism | PASS |
| Controlled scenarios | PASS |
| Diagnosis metrics | PASS — evidence quality only |
| Baseline comparison | PASS |
| Causal-ground-truth validity | LIMITED — unavailable |
| Coverage | PARTIAL — unsupported causes explicit |
| V1 integrity | PASS |
| Historical protection | PASS |
| Focused tests | PASS — 31 combined |
| Full suite | NOT RUN |

## Final decision

**B — PHASE 4.3 ENGINEERING-COMPLETE / CAUSAL-EVALUATION-LIMITED.** The structured diagnosis chain is implemented and validated, but deeper causal truth is unavailable in the controlled runtime.

**PHASE 4.4 AUTHORIZATION: AUTHORIZED** to consume structured diagnoses for failure-memory/experience integration, subject to provenance, temporal, uncertainty, and controlled-runtime boundaries.
