# Phase 6.2 — Architecture Diagram Audit

## What was produced

Eight Mermaid diagram files under `docs/architecture/` (plus an index
`README.md`), each verified against actual implemented code before being
drawn:

1. `01_system_overview.md` — overall system / control loop
2. `02_autonomy_control_loop.md` — sequence-diagram detail of `AutonomyPipeline`
3. `03_uncertainty_abstention.md` — 3 distinct uncertainty mechanisms + abstention
4. `04_diagnosis_recovery.md` — diagnosis + recovery, ranking vs. operating-point generalization
5. `05_failure_memory_lifecycle.md` — failure-memory lifecycle (state diagram)
6. `06_dataset_pipeline.md` — Phase 4 evidence -> Phase 5.1 spec -> Phase 5.2 dataset
7. `07_benchmark_architecture.md` — 8 tracks -> 16 tasks -> capability matrix
8. `08_release_architecture.md` — GitHub <-> Hugging Face release relationship

## Verification method

Each diagram's node labels were checked against:

- Actual file/class names in `src/phase4/` (`pipeline.py`, `decision.py`,
  `diagnosis.py`, `recovery.py`, `memory.py`, `prediction.py`,
  `classification_task.py`, `qa_task.py`, `uncertainty_eval.py`), `src/decision/policy.py`,
  `src/reliability/`, and `src/benchmark/` (confirmed via `ls`/`grep` against
  the real module tree, not assumed from documentation).
- The numeric claims embedded in diagram annotations (AUROC values, ECE
  values, sample sizes, capability-matrix counts) against
  `docs/MASTER_RECORD_CONTENT.md` and
  `experiments/results/phase5_6_external_release/20260827T055356Z/BENCHMARK_CARD.md`
  / `DATASET_CARD.md` — every number traces to one of those two sources.

## Legend discipline

Every diagram with a mix of implemented/validated and
simulated/aggregate-only/`NOT_EVALUABLE` components uses a dashed border
(orange for "simulated/controlled-environment/aggregate-only", red for
"genuine negative finding / no ground truth") with an explicit legend
entry — none of the eight diagrams renders every component uniformly
"done". Concretely:

- Diagram 1: prediction, decision/abstention, diagnosis, and recovery
  execution are dashed (aggregate-only or controlled-environment-only
  evidence); everything else is solid.
- Diagram 3: the shared decision policy node is dashed because the
  abstention benchmark tasks are `SIMULATED_POLICY_EVALUATION`.
- Diagram 4: the causal-attribution and recovery-outcome nodes are
  red-dashed (false-causal-attribution-rate 1.0; 0/35 recovered).
- Diagram 8: the model-repository node is red-dashed and explicitly
  labeled "NOT PUBLISHED".

## Not done / deliberately out of scope

- No diagram was regenerated as a rendered PNG/SVG — Mermaid fences render
  natively on GitHub per the brief's own instruction ("no external tooling
  needed"), so no image-generation toolchain was invoked.
- Diagrams describing frozen V1 (Generation 2, `src/runtime/` etc.) are
  intentionally folded into diagram 1's "two earlier generations remain
  frozen" note rather than given their own diagram, since V1's own
  architecture is already fully documented in
  `docs/archive/ARCHITECTURE_MAP_BASELINE.md` and
  `docs/archive/VERSIONED_MODULE_CLASSIFICATION.md`; duplicating it here
  risked drifting out of sync with that frozen source.
