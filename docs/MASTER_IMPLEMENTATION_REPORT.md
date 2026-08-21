# Master Implementation Report: Genuine Learning Influence

## Executive result

The repaired runtime was audited and extended without reverting or deleting `src/runtime/`. The most important unresolved question was whether validated experience changes future behavior rather than merely increasing a memory version. A new, separate, deterministic control-versus-learned experiment now measures that question explicitly.

The result is **mixed but scientifically useful**. In the controlled simulator, prior validated experience genuinely influences retrieval, diagnosis confidence, diagnosis uncertainty, and recovery action. Under the simulator’s declared action-outcome table, that influence also improves validation and recovery success. The result does not establish production self-healing, real-world recovery improvement, calibrated model improvement, or statistical generalization.

No commit was created and nothing was pushed to GitHub. Frozen Phase 4 protocols, results, and documents were not modified.

## Initial audit and verified baseline

The audit confirmed the repository was on branch `main` at commit `e9a43fa` before this continuation. The repaired runtime already had explicit observation, detection, reliability, memory, diagnosis, recovery, validation, experience, learning, and controller components. The API already used `build_runtime_system()` rather than the synthetic benchmark builder. Failure-memory dirty/current lifecycle, synchronous rebuild, duplicate-save prevention, simulated execution, and independent validation were already present.

The remaining limitations were real: the default runtime used an honest neutral abstainer, the original two-episode demo showed retrieval but not behavioral benefit, memory relevance was not explicit downstream, diagnosis and planning did not consume scored historical evidence, source abstractions were incomplete, model provenance was not first-class on assessments, and small-sample PCA warnings remained.

The verified pre-change suite was **439 passed, 17 skipped, 0 failed, and 21 warnings** in approximately 206.67 seconds. The historical experiment paths were clean before implementation.

## Changes implemented

| Area | Implementation |
|---|---|
| Small-sample embeddings | Added empty-input, one-sample, component-count, zero-variance, and duplicate-safe guards in `FailureEmbedder`; far-away queries remain distinguishable through a centered fallback representation |
| Memory relevance | Added `MemoryMatch` with event ID, distance, similarity, relevance flag, and memory version; retained the old tuple retrieval API for compatibility |
| Diagnosis | `EvidenceDiagnosisEngine` now uses only relevant scored matches to add historical evidence, supporting IDs, confidence, and uncertainty changes |
| Recovery planning | `RuleBasedRecoveryPlanner` now ranks validated historical actions, while hard unsafe-action constraints override historical preference and force abstention |
| Provenance | Reliability assessments now carry model ID/version, calibrator version, training-data ID, and configuration; complete experiences record this metadata and memory-version lineage |
| Sources | Added `MappingEventSource`, `DatasetReplaySource`, and `DeterministicSimulatorSource`; replay and simulation are explicitly labeled and separated from live telemetry |
| Episode trace | Runtime episodes now record memory version before and after learning, scored retrieved memory, and complete experience metadata using the existing `FailureExperience` schema |
| Experiment | Added `configs/runtime_demo/learning_influence_protocol.json`, `scripts/run_learning_influence.py`, and separate results under `experiments/results/learning_influence/` |
| Demonstration | Expanded `scripts/run_closed_loop_demo.py` to report reliability, retrieval relevance, diagnosis, candidates, action, safety, execution, validation, memory versions, and deltas |
| Tests | Added coverage for relevance, diagnosis influence, recovery influence, safety override, irrelevant history, source adapters, restart/reload, stale memory, failed/abstained episodes, and exactly-once persistence |
| Documentation | Added `docs/LEARNING_INFLUENCE_REPORT.md` and updated `README.md` with the new experiment, warning counts, commands, boundaries, and limitations |

## Final architecture

```text
Observation source
  → EventNormalizer
  → Observation
  → FailureDetector
  → ReliabilityAssessor
  → FailureMemory scored retrieval
  → DiagnosisEngine using relevant evidence
  → RecoveryPlanner using validated historical actions
  → safety / feasibility / abstention gate
  → RecoveryExecutor
  → independent RecoveryValidator
  → complete FailureExperience
  → one compatibility-event persistence boundary
  → synchronous LearningManager
  → updated memory
  → future episode
```

The research-only synthetic builder remains explicit as `build_synthetic_experiment_system()`. The API continues to use `build_runtime_system()` and does not silently train from benchmark data. The only executor remains `SimulatedRecoveryExecutor`, which is a deliberate simulation boundary.

## Learning-influence protocol

The protocol uses one validated training episode and 20 evaluation episodes per condition. The failure type is `execution_error`. The training action is `reconfigure`. The simulator declares `retry` as unsuccessful and `reconfigure` as successful. The **control** condition has empty memory for each evaluation episode. The **learned** condition contains only the declared training episode. Evaluation outcomes never seed memory. Historical Phase 4 artifacts are not used.

The experiment is a deterministic integration experiment, not a statistical performance study. There are no confidence intervals because repeated deterministic episodes are not independent real-world incidents.

## Exact experiment results

| Metric | Control: no prior experience | Learned: prior validated experience | Difference |
|---|---:|---:|---:|
| Evaluation episodes | 20 | 20 | — |
| Mean retrieval count | 0.0 | 1.0 | **+1.0** |
| Mean relevant retrieval count | 0.0 | 1.0 | **+1.0** |
| Mean risk | 0.0 | 0.0 | **0.0** |
| Mean diagnosis confidence | 0.6 | 0.8 | **+0.2** |
| Mean diagnosis uncertainty | 0.4 | 0.2 | **−0.2** |
| Selected action | `retry` 20/20 | `reconfigure` 20/20 | **100% action change** |
| Abstention rate | 0.0 | 0.0 | 0.0 |
| Mean recovery attempts | 1.0 | 1.0 | 0.0 |
| Validation success rate | 0.0 | 1.0 | **+1.0** |
| Recovery success rate | 0.0 | 1.0 | **+1.0** |
| Safety violations | 0 | 0 | 0 |

The result demonstrates both influence and simulator-specific benefit. It does not demonstrate risk improvement because the default runtime has no injected workload model and neutral risk remains 0.0. It also does not establish that the learned action is superior outside the declared simulator outcome table.

## Baseline matrix

| Baseline | Status | Result |
|---|---|---|
| B0 — reliability only | Not run | No explicit workload model artifact; safe abstainer is not treated as a model baseline |
| B1 — model plus calibration | Not run | No explicit model and calibrator artifacts injected |
| B2 — model plus memory | Measured | Retrieval and relevance differ between empty and seeded memory; risk does not |
| B3 — model plus memory plus diagnosis | Measured | Confidence rises by 0.2 and uncertainty falls by 0.2 |
| B4 — model plus memory plus diagnosis plus recovery | Measured | Action changes from retry to validated reconfigure with zero safety violations |
| B5 — complete closed loop | Measured | Validation/recovery success changes from 0.0 to 1.0 in the deterministic simulator |

B0 and B1 are explicitly marked not run rather than fabricated.

## Warning audit

The original 21 warnings consisted of one dependency deprecation and small-sample PCA warnings. The PCA warnings were caused by mathematically invalid requests for PCA statistics with one sample or zero-variance failure contexts. They were fixed with explicit guards rather than global suppression. Duplicate embeddings also no longer cause unnecessary KMeans cluster requests.

The final suite reports **444 passed, 17 skipped, 0 failed, and 1 warning** in approximately 207.53 seconds. The remaining warning is the external Starlette/httpx deprecation. No global warning suppression was introduced.

## Exact validation commands

```bash
pytest -q
PYTHONPATH=. python3 scripts/run_closed_loop_demo.py
PYTHONPATH=. python3 scripts/run_learning_influence.py
python3 -m compileall -q src/runtime src/failure_memory scripts tests/runtime
git diff --check
git status --short experiments configs/phase4* docs/PHASE*
```

The full test command passed. The demonstration reported first-episode retrieval 0 and second-episode retrieval 1, with diagnosis confidence changing from 0.6 to 0.8 and uncertainty changing from 0.4 to 0.2; the action and outcome remained unchanged in that demonstration. The separate control-versus-learned experiment produced the influence and benefit results above.

## Historical files preserved

No files under frozen `experiments/results/phase4_*`, `configs/phase4_*`, or `docs/PHASE*` were modified. The new results are isolated under `experiments/results/learning_influence/`. Existing v1/v2 recovery implementations remain preserved and classified in `docs/VERSIONED_MODULE_CLASSIFICATION.md`.

## Claims now supported

The project now supports the bounded claim that validated historical experience can genuinely influence future diagnosis and recovery decisions in a leakage-controlled deterministic research environment. It supports explicit relevance measurement, evidence-aware diagnosis, evidence-aware recovery planning, hard safety precedence, independent validation, model provenance fields, and deterministic source separation.

## Claims still unsupported

The project does not support claims of production self-healing, live telemetry operation, real rollback/redeployment/retraining, real-world recovery-rate improvement, generalization beyond the simulator, causal diagnosis, default calibrated model performance, or broad statistical benefit from the 20 repeated deterministic episodes. The negative Phase 4 historical conclusions remain unchanged.

## Remaining limitations

The default API still has no injected workload model/calibrator and therefore uses safe abstention. Recovery remains simulated. Runtime persistence remains JSONL. The learning-influence experiment is controlled and deterministic rather than statistically representative. Real-data replay adapters are available, but real research artifacts are not silently promoted into runtime model state. Production security, deployment hardening, and real executors remain future work.
