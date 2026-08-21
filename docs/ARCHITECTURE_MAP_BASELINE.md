# Architecture Map and Implementation Baseline

**Baseline captured before architectural recovery implementation.**

## Repository baseline

| Item | Value |
|---|---|
| Repository | `NaishaShetty/Autonomous-AI-Infrastructure-` |
| Branch | `main` |
| Commit | `e9a43fa` |
| Working tree | Clean before implementation |
| Existing tests | 432 passed, 17 skipped, 0 failed, 4 warnings |
| Existing test duration | Approximately 211.52 seconds |
| Push status | Nothing pushed by this implementation |

Frozen protocol and result files were not modified during baseline capture. Their content hashes were captured from the clean baseline checkout before implementation.

## Current architecture

```text
FastAPI lifespan
  -> build_default_pipeline()
  -> build_system()
  -> synthetic regime-drift stream
  -> workload model + calibrator + synthetic failure memory
  -> ReliabilityPipeline.analyze()
  -> confidence + risk + fixed decision policy
  -> ReliabilityEvent persistence
  -> API response
```

The current serving path does not include a first-class observation model, failure detector, diagnosis engine, recovery planner, recovery executor, recovery validator, complete episode builder, or learning manager.

## Classification convention

| Classification | Meaning |
|---|---|
| `ACTIVE_RUNTIME` | Code used by the canonical runtime/API path or intended to be used by it after this recovery |
| `CONTROLLED_RESEARCH` | Reusable research implementation or deterministic simulation that is not production/runtime evidence |
| `BENCHMARK` | Experiment runner, evaluation protocol, metric, ablation, or replay harness |
| `FROZEN_HISTORICAL` | Retained implementation, result, protocol, or artifact required for reproducibility or scientific auditability |
| `OBSOLETE` | No longer needed after import and reproducibility analysis; must not be removed until verified |

## Initial classification map

| Area | Classification | Notes |
|---|---|---|
| `src/api/app.py` | `ACTIVE_RUNTIME` | FastAPI surface; will be routed through the runtime controller |
| `src/api/train.py` | `ACTIVE_RUNTIME` / transition point | Current API builder is synthetic-coupled and will be replaced by explicit runtime construction |
| `src/api/pipeline.py` | `ACTIVE_RUNTIME` / transition point | Narrow reliability pipeline retained as a component boundary during migration |
| `src/pipeline_builder.py` | `CONTROLLED_RESEARCH` | Synthetic trained-system builder; retained for reproducible research and renamed/aliased clearly |
| `src/data/synthetic.py` | `CONTROLLED_RESEARCH` | Synthetic stream generator; not live telemetry |
| `src/schema/events.py` | `ACTIVE_RUNTIME` compatibility boundary | Existing API/event contract retained for compatibility; not the complete episode source of truth |
| `src/failure_experience/` | `ACTIVE_RUNTIME` foundation plus research adapters | Strongest existing complete episode representation; must become the canonical experience foundation without changing historical results |
| `src/experience/` | `BENCHMARK` / `FROZEN_HISTORICAL` | Older synthetic retrieval benchmark representation; not a competing runtime memory |
| `src/failure_memory/` | `ACTIVE_RUNTIME` component plus benchmark-derived logic | Existing risk/retrieval implementation retained and given explicit dirty/rebuild lifecycle |
| `src/failure_patterns/` | `CONTROLLED_RESEARCH` / future runtime evidence | Active real-data pattern package; must remain distinct from the older `src/patterns/` package |
| `src/patterns/` | `FROZEN_HISTORICAL` or benchmark-only pending import audit | Older pattern implementation; must not be silently substituted for `failure_patterns` |
| `src/recovery/` | `CONTROLLED_RESEARCH` plus runtime adapter target | Controlled policies and environments remain reproducible; new runtime interfaces will wrap simulated execution explicitly |
| `src/storage/` | `ACTIVE_RUNTIME` | Existing event persistence; ownership will be made authoritative and non-duplicative |
| `src/evaluation/` | `BENCHMARK` | Offline metrics, protocols, and evaluation utilities |
| `benchmarks/` | `BENCHMARK` | Reproducible experiment runners and audits |
| `experiments/` | `FROZEN_HISTORICAL` / generated outputs | Historical results and experiment outputs; do not overwrite |
| `docs/PHASE*.md` | `FROZEN_HISTORICAL` or research documentation | Protocols, reports, deviations, and results remain auditable |
| `tests/unit/` | Mixed component tests | Existing behavior and historical research contracts must remain covered |
| `tests/integration/` | Mixed runtime/research tests | New closed-loop integration coverage will be added without weakening existing tests |
| `tests/recovery/` | `CONTROLLED_RESEARCH` | Controlled recovery contract and leakage tests |
| `tests/e2e/` | `ACTIVE_RUNTIME` transition target | Existing full-pipeline tests will be extended for the canonical controller |

## Versioned-module review scope

The following pairs require explicit classification before any deletion or move:

| Pair | Initial interpretation |
|---|---|
| `recovery/environment.py` / `environment_v2.py` | Controlled Phase 4.3 versus Phase 4.4 environments; preserve both if frozen experiments depend on them |
| `recovery/policy.py` / `policy_v2.py` | Controlled Phase 4.3 versus sequential Phase 4.4 policies; preserve both for historical reproducibility |
| `recovery/schema.py` / `schema_v2.py` | Controlled episode schemas for different frozen protocols; do not use as the live episode schema without an adapter |
| `recovery/splits.py` / `splits_v2.py` | Protocol-specific controlled splits; preserve imports used by frozen benchmarks |
| `recovery/io.py` / `io_v2.py` | Protocol-specific controlled I/O; preserve until benchmark import audit is complete |
| `recovery/sample_size.py` / `sample_size_v2.py` | Protocol-specific sample-size calculations; preserve frozen dependencies |

## Required target architecture

```text
ObservationSource / dataset replay / simulator
  -> EventNormalizer
  -> Observation
  -> RuntimeController
       -> FailureDetector
       -> ReliabilityAssessor
       -> FailureMemory retrieval
       -> DiagnosisEngine
       -> Reliability/recovery policy
       -> RecoveryPlanner
       -> safety and feasibility gate
       -> RecoveryExecutor
       -> RecoveryValidator
       -> canonical FailureExperience
       -> authoritative ExperienceStore
       -> LearningManager / memory update
       -> next episode
```

This document is a baseline record and classification aid. It does not alter frozen research results or claim that the target architecture is implemented yet.
