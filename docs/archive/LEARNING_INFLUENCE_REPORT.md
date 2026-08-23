# Learning-Influence Experiment Report

## Scope

This is a **new experiment on the repaired runtime**. It does not modify, replace, or reinterpret frozen Phase 4.1–4.4 protocols or results. The experiment measures two separate hypotheses:

> **Influence:** Does a validated prior experience change future retrieval, diagnosis, planning, or policy behavior?

> **Benefit:** Does that behavior change improve validation success, recovery success, or safety under the controlled simulator?

The experiment is deterministic and intentionally labeled an integration experiment rather than a statistical generalization study.

## Protocol and leakage controls

The protocol is stored at [`configs/runtime_demo/learning_influence_protocol.json`](../configs/runtime_demo/learning_influence_protocol.json). Results are stored separately from historical Phase 4 outputs under [`experiments/results/learning_influence/`](../experiments/results/learning_influence/).

The simulator uses an `execution_error` failure class with a fixed action-outcome table: `retry` fails and `reconfigure` succeeds. One training episode is run with `reconfigure` as the explicitly configured training policy. Evaluation conditions then use the same observation distribution and the same action outcome table. The **control** condition starts each episode with empty memory. The **learned** condition starts each episode with only the declared training episode in memory. Evaluation outcomes are never used to seed either condition.

| Boundary | Definition |
|---|---|
| Training/experience | One validated training episode, `training-episode-000` |
| Development | None; no evaluation episode is used for tuning |
| Evaluation | 20 deterministic episodes per condition, with separate control and learned memory |
| Dataset | No external dataset; explicitly labeled deterministic simulator |
| Frozen artifacts | Phase 4 results and protocols are not read or modified |

The experiment manifest records the current Git commit, protocol hash, training episode ID, and memory condition for reproducibility.

## Baseline matrix

| Baseline | Status | Interpretation |
|---|---|---|
| B0 — reliability only | Not run | No explicit workload model artifact is configured; the safe default abstainer is not treated as a model baseline |
| B1 — model + calibration | Not run | No explicit workload model and calibrator artifacts were injected |
| B2 — model + memory | Measured in controlled conditions | Retrieval count, relevant retrieval count, and risk are compared with empty versus seeded memory |
| B3 — model + memory + diagnosis | Measured | Diagnosis confidence, uncertainty, and evidence are compared |
| B4 — model + memory + diagnosis + recovery | Measured | Candidate actions, selected action, safety, and attempts are compared |
| B5 — complete closed loop | Measured | Validation success, recovery success, and safety violations are compared |

The B0 and B1 entries are deliberately not fabricated. The default API runtime has no explicit calibrated model artifact.

## Exact results

| Metric | Control: empty memory | Learned: training experience available | Learned − control |
|---|---:|---:|---:|
| Episodes | 20 | 20 | — |
| Mean retrieval count | 0.0 | 1.0 | **+1.0** |
| Mean relevant retrieval count | 0.0 | 1.0 | **+1.0** |
| Mean risk | 0.0 | 0.0 | **0.0** |
| Mean diagnosis confidence | 0.6 | 0.8 | **+0.2** |
| Mean diagnosis uncertainty | 0.4 | 0.2 | **−0.2** |
| Selected action | retry in 20/20 | reconfigure in 20/20 | **100% action change** |
| Abstention rate | 0.0 | 0.0 | 0.0 |
| Mean recovery attempts | 1.0 | 1.0 | 0.0 |
| Validation success rate | 0.0 | 1.0 | **+1.0** |
| Recovery success rate | 0.0 | 1.0 | **+1.0** |
| Safety violations | 0 | 0 | 0 |

## Interpretation

The controlled experiment provides evidence of **learning influence** in this deterministic environment. The seeded experience is retrieved with explicit similarity/relevance metadata, diagnosis confidence increases, uncertainty decreases, and the recovery planner changes from `retry` to the validated historical action `reconfigure`. The action changes in 20/20 paired evaluations.

The experiment also shows a **learning benefit under the simulator’s declared outcome table**: control selects the failing `retry` action and has 0/20 validation successes, while learned selects `reconfigure` and has 20/20 validation successes. Safety violations remain zero in both conditions.

These results are not evidence of production self-healing or real-world recovery improvement. They are not a causal claim about live infrastructure. The action outcomes are deterministic by design, the sample contains repeated controlled episodes rather than independent real-world incidents, and no confidence interval or generalization claim is appropriate. The trustworthy conclusion is narrower: the repaired architecture contains a leakage-controlled mechanism through which validated historical experience can genuinely influence diagnosis and recovery choice, and the mechanism produces the expected benefit in this explicitly controlled simulator.

The experiment also demonstrates a boundary condition: the default closed-loop demo’s risk remains unchanged at zero because the unconfigured reliability assessor emits a neutral safe-default signal. Memory-version increments alone are not treated as learning benefit.

## Additional implementation evidence

`FailureMemory.retrieve_matches()` now exposes event ID, distance, similarity, relevance, and memory version. Diagnosis only treats matches meeting the relevance threshold as historical evidence. Recovery planning uses validated historical actions only after diagnosis and relevance gates pass. A hard unsafe-action constraint overrides a historical preference and forces abstention. Irrelevant history does not fabricate a diagnosis or action change.

The runtime also exposes `MappingEventSource`, `DatasetReplaySource`, and `DeterministicSimulatorSource`. Dataset replay and simulation are explicitly labeled in provenance and are not presented as live telemetry.

## Warning audit

Before this task, the verified suite had **439 passed, 17 skipped, 0 failed, and 21 warnings**. The warnings were one Starlette/httpx dependency deprecation and small-sample PCA warnings from the memory embedding path.

The embedding implementation now guards empty input, one-sample fitting, component count, zero-variance data, and duplicate KMeans embeddings. After the changes, the verified suite has **444 passed, 17 skipped, 0 failed, and 1 warning**. The remaining warning is the external Starlette/httpx deprecation. No global warning suppression was added.

## Claims supported and unsupported

Supported claims are limited to the repaired research runtime, explicit relevance-aware retrieval, evidence-aware diagnosis and planning, deterministic simulation, and the controlled learning-influence experiment described here.

Unsupported claims include production self-healing, real rollback/redeployment/retraining, live telemetry operation, real-world recovery-rate improvement, calibrated default-model performance, and causal generalization beyond the declared simulator. The historical Phase 4 negative findings remain unchanged.
