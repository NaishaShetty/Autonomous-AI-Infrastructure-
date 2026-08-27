# Architecture Diagrams

Eight Mermaid diagrams (render natively on GitHub, no external tooling
required), each verified against actual implemented code before drawing.
Solid vs. dashed borders distinguish implemented/validated components from
simulated, aggregate-only, or `NOT_EVALUABLE` ones — see each file's own
legend.

1. [`01_system_overview.md`](01_system_overview.md) — overall system / control loop
2. [`02_autonomy_control_loop.md`](02_autonomy_control_loop.md) — autonomy loop detail (sequence diagram)
3. [`03_uncertainty_abstention.md`](03_uncertainty_abstention.md) — 3 distinct uncertainty mechanisms + abstention
4. [`04_diagnosis_recovery.md`](04_diagnosis_recovery.md) — diagnosis + recovery, ranking vs. operating-point generalization
5. [`05_failure_memory_lifecycle.md`](05_failure_memory_lifecycle.md) — failure-memory lifecycle
6. [`06_dataset_pipeline.md`](06_dataset_pipeline.md) — Phase 4 evidence -> Phase 5.1 spec -> Phase 5.2 dataset
7. [`07_benchmark_architecture.md`](07_benchmark_architecture.md) — 8 tracks -> 16 tasks -> capability matrix
8. [`08_release_architecture.md`](08_release_architecture.md) — GitHub <-> Hugging Face release relationship

These diagrams are documentation, not new claims: every component and
number shown traces back to `docs/MASTER_RECORD_CONTENT.md`, the frozen
`experiments/results/` evidence, or the benchmark/dataset cards under
`experiments/results/phase5_6_external_release/`.
