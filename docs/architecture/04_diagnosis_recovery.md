# Diagnosis + Recovery Architecture

```mermaid
flowchart TD
    OBS["Observation + retrieved FailureExperience(s)"] --> DG["DiagnosisEngine<br/>(src/phase4/diagnosis.py)"]
    DG --> CLASS["failure_class match<br/>(accuracy 1.0, 35/35 on Phase 5.2 slice)"]
    DG --> CAUSE["suspected_cause<br/>(false-causal-attribution-rate = 1.0 --<br/>no independent causal ground truth exists)"]:::danger

    CLASS --> PLAN["RuleBasedRecoveryPlanner<br/>(src/phase4/recovery.py)"]
    CAUSE --> PLAN
    PLAN --> ACTION["Candidate action<br/>(retry / restart / reconfigure / escalate)"]
    ACTION --> GATE{"RecoverySafetyGate<br/>+ feasibility check"}
    GATE -->|reject| ABST["Abstain / escalate<br/>(6-case adversarial matrix:<br/>0/6 incorrectly authorized)"]
    GATE -->|approve| EXEC["ControlledRuntimeRecoveryExecutor<br/>(real subprocess retry/restart against<br/>this project's own controlled runtime)"]:::partial
    EXEC --> VALID["SignalRecoveryValidator<br/>independent re-derivation, fresh MonitoringEngine<br/>(tested against a deliberately lying executor)"]
    VALID --> OUTCOME["Validated outcome<br/>REC-EVAL benchmark: 0/35 RECOVERED<br/>(genuine negative finding on Phase 5.2 slice)"]:::danger

    classDef partial stroke-dasharray: 5 5,stroke:#b45309,color:inherit;
    classDef danger stroke-dasharray: 5 5,stroke:#b91c1c,color:inherit;
```

## Two separate claims that must never be merged

1. **Ranking generalization** (Phase 4's own environment-generalization
   study): OOM failure-ranking AUROC transfers well across environments —
   dev 0.989, held-out 0.983, robustness 0.935.
2. **Operating-point generalization**: the *fixed decision threshold* does
   **not** transfer cleanly across those same environments. A model that
   ranks well can still make the wrong accept/reject call at a fixed
   threshold in a new environment.

These are reported as two distinct findings throughout this project's
documentation, never collapsed into one "generalizes" claim. Both are
Phase 4 aggregate-level findings; the Phase 5.2 canonical dataset has only
1 represented environment, so `GEN-RANKING-CONTRACT` and
`GEN-OPERATING-POINT-CONTRACT` are `NOT_EVALUABLE` at record level in the
benchmark, and the Phase 4 numbers above are preserved only as
aggregate-reference evidence, never attached to Phase 5.2 records.
