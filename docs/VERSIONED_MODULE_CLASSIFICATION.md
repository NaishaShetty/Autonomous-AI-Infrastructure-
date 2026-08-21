# Versioned and Historical Module Classification

This document makes the active path unambiguous without deleting modules required by frozen experiments.

| Module family | Classification | Runtime status | Reason |
|---|---|---|---|
| `src/recovery/environment.py` | Frozen controlled research | Not runtime | Phase 4.3 controlled environment; retained for reproducibility |
| `src/recovery/environment_v2.py` | Frozen controlled research | Not runtime | Phase 4.4 sequential environment; retained for reproducibility |
| `src/recovery/policy.py` | Frozen controlled research | Not runtime | Phase 4.3 recovery-learning policies and baselines |
| `src/recovery/policy_v2.py` | Frozen controlled research | Not runtime | Phase 4.4 sequential recovery policies and baselines |
| `src/recovery/schema.py` | Frozen controlled research | Not runtime | Phase 4.3 controlled episode schema with leakage boundaries |
| `src/recovery/schema_v2.py` | Frozen controlled research | Not runtime | Phase 4.4 controlled sequential episode schema |
| `src/recovery/splits.py` | Frozen controlled research | Not runtime | Phase 4.3 protocol-specific data split |
| `src/recovery/splits_v2.py` | Frozen controlled research | Not runtime | Phase 4.4 protocol-specific data split |
| `src/recovery/io.py` | Frozen controlled research | Not runtime | Phase 4.3 controlled I/O helpers |
| `src/recovery/io_v2.py` | Frozen controlled research | Not runtime | Phase 4.4 controlled I/O helpers |
| `src/recovery/sample_size.py` | Frozen controlled research | Not runtime | Phase 4.3 sample-size protocol |
| `src/recovery/sample_size_v2.py` | Frozen controlled research | Not runtime | Phase 4.4 sample-size protocol |
| `src/experience/` | Benchmark/historical | Not runtime | Older synthetic retrieval benchmark representation |
| `src/patterns/` | Historical/benchmark | Not runtime | Older pattern implementation; active real-data pattern code is `src/failure_patterns/` |
| `src/failure_experience/` | Canonical experience foundation | Runtime-compatible | Complete episode representation for observations, diagnosis, recovery, validation, outcome, provenance, and eligibility |
| `src/runtime/` | Active runtime | Canonical | Controller, contracts, observation normalization, runtime adapters, experience store, and learning lifecycle |
| `src/pipeline_builder.py` | Research builder | Not canonical runtime | Synthetic regime-drift construction retained for benchmark reproducibility; explicit alias `build_synthetic_experiment_system` added |

No versioned module was deleted or moved. Frozen benchmark imports remain unchanged. The new runtime uses `src/runtime/` and does not import the controlled `policy_v2`, `environment_v2`, or older `patterns` package as live runtime implementations.
