# Autonomy Control Loop — Detail

Expands the single `AutonomyPipeline.run_episode()` call
(`src/phase4/pipeline.py`) into its concrete component classes.

```mermaid
sequenceDiagram
    participant W as Workload/Environment
    participant P as AutonomyPipeline
    participant R as TelemetryRiskPredictor
    participant D as AbstentionAwareDecisionPolicy
    participant M as FailureMemory
    participant DG as DiagnosisEngine
    participant PL as RuleBasedRecoveryPlanner
    participant SG as RecoverySafetyGate
    participant EX as ControlledRuntimeRecoveryExecutor
    participant V as SignalRecoveryValidator
    participant L as LearningManager

    W->>P: telemetry / episode event
    P->>R: predict(features)
    R-->>P: risk score (aggregate-only evidence for 3/4 failure classes)
    P->>D: decide(confidence, risk)
    D-->>P: ANSWER / ABSTAIN (reuses src.decision.policy.DecisionPolicy)
    P->>M: retrieve(workload_id, environment_id, failure_class)
    M-->>P: 0..k historical FailureExperience records
    P->>DG: diagnose(observation, memory_hits)
    DG-->>P: suspected_cause + uncertainty (class-matching, no causal ground truth)
    P->>PL: plan(diagnosis)
    PL-->>P: candidate recovery action
    P->>SG: check(action, safety_rules)
    alt unsafe or infeasible
        SG-->>P: reject -> abstain/escalate
    else safe
        SG-->>P: approve
        P->>EX: execute(action) against ControlledRuntime.run()
        EX-->>P: self-reported outcome (not trusted directly)
        P->>V: validate() -- fresh MonitoringEngine re-derivation from raw events
        V-->>P: independently validated outcome
    end
    P->>L: update(episode, outcome)
    L->>M: write new FailureExperience (synchronous)
```

## What this demonstrates vs. does not

- **Demonstrated**: the pipeline runs end to end against this project's own
  controlled subprocess runtime; validation independently re-derives the
  outcome rather than trusting the executor's self-report (tested against
  a deliberately lying executor); memory measurably changed the planner's
  chosen action across repeated incidents of the same workload in the
  Phase 4.4/5 demo run.
- **Not demonstrated**: production-fleet recovery, statistically
  significant recovery-rate improvement (`REC-EVAL` benchmark result is
  0/35 `RECOVERED` on the Phase 5.2 dataset slice), or causally verified
  diagnosis (false-causal-attribution-rate = 1.0 because no independent
  causal ground truth exists in either the Phase 4 demo or the Phase 5.2
  dataset).
