# Runtime Reliability and Observability Architecture Audit

**Status:** Read-only architecture audit after the validated memory-composition/order-invariant planning checkpoint. No runtime reliability or observability implementation is included in this document or this checkpoint.

## Executive conclusion

The repository now has a coherent **closed-loop research runtime** for structured observations, failure detection, reliability assessment, uncertainty-aware diagnosis, failure-memory retrieval, recovery planning, safety gating, simulated execution, independent validation, complete experience persistence, and memory updates. The canonical runtime path is `RuntimeController`, constructed by `src/runtime/builder.py` and exposed by the API through `src/api/app.py`.

It is not yet a genuine observable AI/ML infrastructure runtime. The API accepts a normalized observation payload, but there is no canonical live telemetry source, no production workload adapter, no versioned runtime-loaded reliability-model artifact, and no real workload monitoring loop. The current default reliability assessor is intentionally unconfigured and returns an honest neutral risk rather than fabricating a model. Dataset replay and simulators are explicit research inputs, not live telemetry.

> **Current boundary:** the repository demonstrates validated runtime mechanisms in controlled and replay-oriented environments. It does not demonstrate production self-healing, real-workload autonomous monitoring, reliable failure prediction on deployed models, or statistically generalizable recovery behavior.

## Checkpoint state and preservation boundary

The validated checkpoint began at commit `981725041ff301fea5d031a8c6b9e8b2375130f0` on `main`, with `origin/main` at the same commit. The checkpoint audit confirmed that no frozen result directory had a diff, the v2 experiment was reproducible, compilation and whitespace checks passed, and no caches, secrets, virtual environments, large files, or generated junk were present.

The following directories are frozen and must remain unchanged during the next phase:

| Frozen path | Meaning |
|---|---|
| `experiments/results/learning_influence/` | Earlier control-versus-learned integration result |
| `experiments/results/generalization/` | Earlier shifted-context retrieval/generalization result |
| `experiments/results/counterfactual_generalization/` | Hidden-latent counterfactual behavior result |
| `experiments/results/memory_composition/` | Historical v1 compositional planner result, including its ordering defect |
| `experiments/results/memory_composition_v2/` | Validated order-invariant follow-up result |

The next implementation must write new artifacts to a new versioned location or to explicitly designated runtime documentation. It must not regenerate historical result directories in place.

## Current runtime architecture

The active path is:

```text
API request
  → structured Observation normalization
  → RuntimeController.process()
  → FailureDetector
  → ReliabilityAssessor
  → scored FailureMemory retrieval
  → DiagnosisEngine
  → RecoveryPlanner
  → safety/feasibility decision
  → simulated or injected RecoveryExecutor
  → independent RecoveryValidator
  → authoritative compatibility-event persistence
  → complete FailureExperience persistence
  → RuntimeLearningManager
  → future FailureMemory state
```

The API entry point is `src/api/app.py`. It converts request payloads through the observation normalizer and calls the canonical controller while preserving the compatibility response shape and metrics endpoint. `src/api/train.py` retains the legacy synthetic research builder for experiments; the API path is intended to use the explicit runtime builder rather than silently training from benchmark data at startup.

`src/runtime/builder.py` constructs the runtime from injected detector, assessor, memory, diagnosis, planner, executor, validator, experience store, and learning manager components. `src/runtime/controller.py` is the orchestration boundary. `src/runtime/contracts.py` defines the typed observation, reliability, diagnosis, recovery, execution, validation, episode, lifecycle, provenance, and memory-lineage contracts.

## Stage-by-stage audit

| Stage | What exists and where | Runtime-connected? | Data character | Interface/output | Missing or next work |
|---|---|---:|---|---|---|
| Workload | Workload identifiers and observation payloads; research workload models in `src/reliability/workload_model.py` | Partial | Synthetic, replay, or caller-supplied | `workload_id`, observation metadata | No live workload registry, deployment lifecycle, or production workload adapter |
| Telemetry source | Mapping, dataset-replay, and deterministic simulator sources in `src/runtime/sources.py` | Partial | Explicit research/replay inputs | `ObservationSource.next()` / normalized `Observation` | No live telemetry connector, batching, clock discipline, backpressure, or source health contract |
| Normalization | `src/runtime/observation.py` and `Observation` in `src/runtime/contracts.py` | Yes for API and experiments | Source-agnostic but caller-provided | Validated features, metrics, environment, metadata, provenance | Canonical telemetry semantics and required-vs-optional field policy need formalization |
| Failure/anomaly detection | `FailureDetector` in `src/runtime/components.py` | Yes | Rule/threshold-like runtime logic | `DetectionResult` | Detection categories are not yet separately modeled for anomaly, drift, resource, latency, prediction, or repeated-failure events |
| Reliability/risk | `ReliabilityAssessor`, workload model, calibrator, and `ReliabilityAssessment` | Yes as an interface; default model unconfigured | Model-based path exists, default is neutral | calibrated confidence, risk, decision, uncertainty, provenance | No valid persisted model/calibrator artifact, loader, registry, compatibility checks, or production feature contract |
| Abstention | Decision policy and planner safety/uncertainty gates | Yes | Runtime policy | answer/abstain/review and recovery abstention | Need explicit policy version, calibration-aware thresholds, and separate reliability abstention from recovery abstention |
| Failure memory | `src/failure_memory/memory.py` | Yes | Structured events and controlled seed/replay sets | scored matches, dirty/fitted state, memory version | Need production retention, concurrency, versioned indexes, eviction, auditability, and clear online-update policy |
| Diagnosis | `DiagnosisEngine` in `src/runtime/components.py` | Yes | Observed evidence plus retrieved history | causes, confidence, uncertainty, supporting IDs | Current diagnosis is shallow evidence aggregation; no validated causal or drift diagnosis for live workloads |
| Recovery planner | `RuleBasedRecoveryPlanner` | Yes | Explicit evidence, outcomes, safety context | bounded `RecoveryPlan` | No production action catalog, feasibility registry, resource impact model, or planner evaluation outside declared simulators |
| Safety gate | Planner safety checks and recovery status | Yes | Current constraints and unsafe-action metadata | approved, rejected, abstain | Need centralized policy object, independent audit log, authorization boundaries, and fail-closed defaults for live actions |
| Executor | `SimulatedRecoveryExecutor` plus injectable executor contract | Yes in research/runtime tests | Controlled simulator by default | `ExecutionResult` with workload state | No production executor is implemented or claimed; future executor must be isolated and permissioned |
| Validation | `SignalRecoveryValidator` | Yes | Independent simulated workload state | recovered/failed/uncertain and metrics | Need workload-specific health probes, baseline windows, delayed effects, rollback verification, and validation timeout semantics |
| Experience recorder | `src/runtime/experience.py` and existing `FailureExperience` foundation | Yes | Complete runtime episode | persisted episode, provenance, lineage, eligibility | Need durable store lifecycle, schema migration policy, deduplication across distributed sources, and retention/PII policy |
| Learning/update | `RuntimeLearningManager` | Yes after authoritative persistence | Validated runtime events | memory ingestion/rebuild/version update | Not production continual learning; no model retraining, approval gate, drift-triggered retraining, or safe promotion workflow |
| Future decisions | Memory version and subsequent controller calls | Yes in controlled runs | Same-process or explicitly loaded memory | retrieval and evidence influence | No durable cross-process runtime memory service or production state management |

## Current research architecture

The repository also contains research infrastructure that is intentionally broader than the active runtime. The failure-experience schema models observations, failures, uncertain diagnosis, recovery, validation, outcome, provenance, temporal lineage, and learning eligibility. The recovery package contains controlled environments, policies, validators, and historical experiment machinery. The generalization, counterfactual, and memory-composition protocols define fixed simulator worlds, seeds, baselines, leakage controls, and per-seed metrics.

These components are valuable because they test the runtime boundary under controlled conditions. They do not constitute live infrastructure evidence. The simulator executors, fixed protocols, synthetic builders, and evaluation-only artifacts must remain explicitly labeled as research inputs. `src/api/train.py` and `src/pipeline_builder.py` are research/benchmark construction paths and must not become implicit API startup dependencies again.

## Observability audit

The current runtime has an `Observation` contract, but it is not yet a complete telemetry model for an AI/ML workload. The available fields are caller-provided and can contain features, metrics, resource signals, error text, environment, metadata, timestamp, and provenance. The following table separates what is representable from what is operationally integrated.

| Telemetry concept | Current status | Assessment |
|---|---|---|
| Inference latency | Representable in metrics/features | No live collection or windowed aggregation |
| Throughput | Representable in metrics/features | No live rate calculation or workload baseline |
| Error rate | Representable and used in some experiments | No production counter source or alert semantics |
| Resource utilization | Representable in resource signals/features | No host/container/GPU telemetry connector |
| Model confidence | Present in reliability/event contracts | Default runtime has no valid model artifact |
| Prediction distribution | Not a first-class normalized field | Must be added to the future telemetry contract |
| Drift indicators | Not a coherent runtime telemetry family | Research features may contain proxies, but no detector contract exists |
| Workload state | Present only in simulator execution state | No live workload-state provider or health snapshot |
| Failure events | `ReliabilityEvent` is a durable event representation | No live event bus or source ownership contract |
| Temporal context | Timestamp and episode lineage exist | No window store, event-time policy, or clock-skew policy |
| Deployment/model version | Can be placed in metadata/provenance | Not required and validated consistently at runtime |
| Environment metadata | Supported as a free-form mapping | No controlled vocabulary or security/redaction policy |

> **Dataset ingestion is not runtime telemetry.** Dataset replay provides observations at a controlled source boundary. It does not establish that the system can monitor a deployed model, observe infrastructure health, or maintain a real-time event stream.

### Proposed canonical telemetry contract

The next phase should design, but not silently expand, a versioned telemetry contract with these conceptual groups:

```text
TelemetryObservation {
  observation_id
  event_time
  ingest_time
  workload_id
  deployment_id
  model_id
  model_version
  environment_id
  prediction_summary {
    confidence
    predicted_class
    class_distribution
    abstained
  }
  performance {
    latency_ms
    throughput_per_second
    error_rate
    timeout_rate
  }
  resources {
    cpu_utilization
    memory_utilization
    gpu_utilization
    queue_depth
  }
  drift {
    feature_drift_scores
    prediction_drift_score
    label_drift_score
    reference_window_id
  }
  errors
  provenance
}
```

The contract should define units, sampling windows, missingness, monotonic counters, event-time versus ingest-time behavior, version compatibility, privacy/redaction rules, and source health. It should be convertible to the existing `Observation` without coupling the controller to a specific telemetry vendor.

## Failure detection audit

The current detector can identify a runtime failure condition from the normalized observation and produces a `DetectionResult`. It is not yet a complete anomaly/deterioration framework. Detection, prediction, and diagnosis should remain separate:

| Concept | Current status | Required future interface |
|---|---|---|
| Detection | Present as `FailureDetector.detect(observation)` | `DetectionResult` should identify category, trigger, window, severity, and evidence |
| Prediction | Represented indirectly by reliability/model assessment | `ReliabilityAssessment` should remain distinct from observed failure detection |
| Diagnosis | Present after detection and retrieval | `DiagnosisResult` should identify hypotheses, uncertainty, evidence, and provenance |
| Threshold violation | Possible through detector logic | Explicit rule/version and threshold provenance needed |
| Anomaly | Not a first-class detector category | Add anomaly score, reference window, and detector version |
| Model degradation | Not operationally detected | Requires performance/label feedback and delayed evaluation policy |
| Drift | Not operationally detected | Requires feature/prediction distribution windows and reference data |
| Repeated failures | Memory can retrieve prior events | Requires temporal aggregation and recurrence detector |
| Resource failure | Representable in observations | Requires live resource source and category-specific detector |
| Latency failure | Representable in metrics | Requires windowed SLO/SLA policy |
| Prediction failure | Event outcome can record correctness | Requires labels or trusted feedback; not available from inference alone |

The next implementation must not collapse these outputs into one generic failure score. Detection should answer **what was observed**, reliability should answer **how trustworthy the model/inference appears**, and diagnosis should answer **what may explain the condition**.

## Reliability-model audit

The repository contains a workload-model concept in `src/reliability/workload_model.py`, a calibrator in `src/reliability/calibrator.py`, reliability policy code, and a runtime `ReliabilityAssessment` contract. The model expects structured feature vectors and produces a prediction/confidence-like signal; calibration maps model confidence into a calibrated value. Failure-memory similarity also produces a risk-like historical signal, but that is not a trained workload reliability model.

The current limitation is explicit and correct: no protocol-valid persisted model/calibrator artifact is available for runtime injection. The default builder therefore does not fabricate a model or silently train one at API startup. The existing `configs/runtime_demo/model_config.json` and `docs/RELIABILITY_MODEL_INTEGRATION_AUDIT.md` record this boundary.

The next model integration must implement this boundary explicitly:

```text
Offline training pipeline
  → versioned model artifact + calibrator artifact
  → feature schema and training-data manifest
  → leakage and evaluation report
  → compatibility validation
  → runtime artifact loader
  → inference-only ReliabilityAssessor
```

A runtime-loaded artifact should contain model ID/version, calibrator ID/version, feature schema hash, training-data ID, training period, code/configuration hash, and supported workload/deployment scope. Runtime loading must fail closed when the artifact is missing or incompatible. Training, calibration, evaluation, artifact promotion, and runtime inference must be separate processes and permissions.

## Real data versus synthetic data classification

| Repository input or artifact | Category | Interpretation |
|---|---|---|
| `experiments/results/learning_influence/` | C/E: controlled synthetic benchmark and evaluation artifact | Controlled integration result, not production evidence |
| `experiments/results/generalization/` | C/E: controlled synthetic benchmark and evaluation artifact | Multi-seed simulator result |
| `experiments/results/counterfactual_generalization/` | C/E: controlled synthetic benchmark and evaluation artifact | Hidden-latent simulator result |
| `experiments/results/memory_composition/` | C/E: controlled synthetic benchmark and evaluation artifact | Historical compositional result with v1 ordering limitation |
| `experiments/results/memory_composition_v2/` | C/E: controlled synthetic benchmark and evaluation artifact | Order-invariant follow-up with decision/safety metrics |
| `scripts/run_*` experiment harnesses | D/E: runtime simulation and evaluation-only artifact generation | They call controlled runtime components; they are not live telemetry |
| `src/runtime/sources.py` mapping source | D: deterministic observation source | Input adapter for tests/replay-like calls |
| `src/runtime/sources.py` dataset replay source | B/D: derived or replayed dataset input | Dataset replay is not live infrastructure monitoring |
| `src/runtime/sources.py` deterministic simulator | D/C: runtime telemetry simulation and controlled synthetic benchmark | Ground truth remains in the simulator/evaluation harness |
| `src/pipeline_builder.py` and synthetic regime-drift builders | C: controlled synthetic benchmark | Research-only construction path |
| External real workload data | A: not currently integrated | No validated external dataset or live workload connector is part of the runtime checkpoint |

No result should describe categories C, D, or E as evidence of real infrastructure behavior. A future real-data adapter should have its own provenance, licensing, schema, time range, preprocessing, and leakage documentation.

## Proposed canonical runtime interfaces

The next architecture should retain the current controller boundary while making interfaces explicit and source-independent:

```text
TelemetrySource.read() -> RawTelemetry | EndOfStream
ObservationNormalizer.normalize(RawTelemetry) -> Observation
FailureDetector.detect(Observation) -> DetectionResult
ReliabilityModel.assess(Observation) -> ReliabilityAssessment
AbstentionPolicy.decide(ReliabilityAssessment, DetectionResult) -> DecisionGate
FailureMemory.retrieve_matches(Context) -> list[MemoryMatch]
DiagnosisEngine.diagnose(Observation, DetectionResult, ReliabilityAssessment, Matches) -> DiagnosisResult
RecoveryPlanner.plan(DiagnosisResult, ReliabilityAssessment, Matches, SafetyContext) -> RecoveryPlan
SafetyGate.authorize(RecoveryPlan, SafetyContext) -> SafetyDecision
RecoveryExecutor.execute(AuthorizedPlan, Observation) -> ExecutionResult
RecoveryValidator.validate(Observation, ExecutionResult) -> ValidationResult
ExperienceRecorder.record(RuntimeEpisode) -> ExperienceHandle
LearningManager.update(ValidatedExperience) -> LearningUpdate
```

Every interface should carry provenance and version information where relevant. The controller should not know whether observations came from live telemetry, a replay file, or a simulator. Experiments should inject sources and executors through the same interfaces rather than changing controller logic.

## Remaining component gaps

**Memory** is operationally connected and has explicit dirty/fitted/version lifecycle, scored relevance, outcome-aware evidence, and controlled seeding. It still lacks a production persistence/index service, concurrency semantics, retention policy, distributed versioning, and an approved online-update policy.

**Diagnosis** is connected but intentionally lightweight. It records evidence and uncertainty and can use relevant historical matches. It does not yet establish causal diagnosis, distinguish drift from resource failure in live workloads, or use validated workload-specific diagnostic models.

**Recovery** is connected through a safe planner, injectable executor, independent validator, bounded attempts, and complete history. The default executor remains simulated. There is no production action catalog, permission boundary, resource feasibility service, rollback verification against a real deployment, or live health probe.

**Validation** is independent from executor status in the simulator, which is a sound research boundary. It is not yet a production health evaluator with baseline windows, SLOs, delayed effects, timeout handling, or deployment-state verification.

**Learning** persists complete episodes and updates failure memory after authoritative persistence. This is not autonomous production continual learning. There is no model retraining, human/automated promotion gate, artifact registry, rollback of learned state, or statistical monitoring of update harm.

## Proposed next implementation phases

The next phase should not begin by adding another toy simulator. It should proceed in controlled increments:

1. Freeze this audit and define the canonical telemetry contract, including units, windows, provenance, model/deployment identity, and source health.
2. Implement a source-neutral telemetry adapter boundary with deterministic tests and a replay adapter; keep live connectors out until the contract is stable.
3. Separate detection categories from reliability assessment and diagnosis, adding explicit interfaces and category-specific tests.
4. Implement offline reliability training and calibration as a separate command that emits a versioned artifact and leakage/evaluation manifest; do not train during API startup.
5. Implement an inference-only artifact loader with schema/version compatibility checks and a fail-closed missing-artifact path.
6. Add workload-health validation abstractions and a controlled test double before considering any real executor.
7. Add persistence and concurrency policies for memory and experiences, including deduplication, retention, version lineage, and restart behavior.
8. Integrate a representative workload adapter only after the telemetry and artifact boundaries are validated, then evaluate on held-out data without changing frozen research artifacts.

## Files that may change in the next phase

The likely implementation surface is limited to new or explicitly versioned modules around:

| Area | Candidate files |
|---|---|
| Telemetry contract | `src/runtime/contracts.py`, new `src/runtime/telemetry.py` |
| Source adapters | `src/runtime/sources.py`, new source-specific adapters |
| Detection | `src/runtime/components.py` or a new `src/runtime/detection.py` |
| Reliability artifact boundary | `src/reliability/`, new offline training/loader modules, `configs/runtime_demo/` |
| Runtime construction | `src/runtime/builder.py`, `src/api/app.py` only after interface tests pass |
| Tests | `tests/runtime/`, new reliability/telemetry fixtures |
| Documentation | `README.md`, new protocol/model audit documents |

These are proposals, not changes made by this audit.

## Files and directories that must remain frozen

The next phase must not modify any historical result file or protocol under the following directories:

```text
experiments/results/learning_influence/
experiments/results/generalization/
experiments/results/counterfactual_generalization/
experiments/results/memory_composition/
experiments/results/memory_composition_v2/
```

Historical Phase 4 documents, frozen experiment protocols, frozen manifests, and prior result summaries must likewise remain unchanged unless a new versioned document explicitly cross-references them without rewriting their claims.

## Regression risks

The most important architectural regression risk is reconnecting API startup to a synthetic benchmark builder. The API must continue to construct the canonical runtime from explicit components and must never silently train on synthetic data. Other risks include treating dataset replay as live telemetry, using failure-memory similarity as a reliability model, allowing evaluation outcomes to leak into memory before decisions, allowing unsafe historical actions to bypass the safety gate, and treating abstention as a failed recovery without reporting decision optimality.

Additional risks include losing provenance when normalizing telemetry, mixing event time with ingest time, loading an incompatible model artifact, allowing model training and evaluation data to overlap, updating memory without version lineage, and changing a frozen experiment directory during a new run.

## Testing and reproducibility strategy

The next implementation should preserve the current full-suite baseline of **477 passed, 17 skipped, 0 failed, and 1 warning** unless a genuine, documented change is introduced. It should add contract tests for telemetry normalization, source provenance, detection/reliability/diagnosis separation, artifact compatibility, missing-artifact abstention, memory restart behavior, and no-training-at-startup behavior.

Every new experiment or evaluation must use a new versioned output directory, deterministic event IDs, fixed seeds where stochastic behavior exists, a protocol hash, a manifest, explicit data provenance, and a two-run byte-identical output check. Frozen directories must be hash-checked before and after the work. `git diff --check`, compilation checks, and a complete diff review are required before any future checkpoint commit.

## Claims currently justified

The repository currently justifies the following bounded claims:

- Failure memory can influence decisions in controlled runtime experiments.
- Local behavior can change under declared simulator generalization conditions.
- Counterfactual behavior can be evaluated without exposing hidden simulator labels to the runtime.
- Safety gating prevents executed unsafe actions in the tested environments.
- Negative experience can be outcome-signed rather than treated as positive evidence.
- Order-invariant evidence aggregation works for the declared v2 permutation and tie tests.
- Multiple historical evidence items can produce a different compositional decision from nearest-neighbor transfer.
- The declared experiments are deterministic and reproducible under their protocols.

## Claims that remain unsupported

The repository does not justify claims of planner recovery-success superiority over nearest-neighbor transfer, production self-healing, broad real-world generalization, real workload autonomous monitoring, real workload failure prediction, production continual learning, statistical significance, or a deployed reliability model. The default runtime remains honestly unconfigured for reliability-model inference until a protocol-valid versioned artifact exists.

> The next research question is no longer only whether memory and planning can work in a hand-designed simulator. It is whether the validated mechanisms can be integrated into one genuine, observable, risk-aware, closed-loop AI/ML infrastructure runtime without reintroducing hidden benchmark coupling.
