# Phase 5.3 — Reproducibility Protocol

Status: SPECIFICATION ONLY. Defines what a future benchmark implementation
must record and enforce; nothing here is executed by this phase.

## 1. Independently versioned axes

| Axis | Current value | Changes when |
|---|---|---|
| `benchmark_version` | `phase5.3-benchmark-v1.0.0` | Task definitions, eligibility statuses, or scoring semantics change |
| `dataset_version` | `phase5.2-dataset-v1.0.0` (consumed, not modified) | A new dataset construction run |
| `schema_version` | `phase5.1-schema-v1.0.0` (consumed, not modified) | The canonical record schema changes |
| `protocol_version` | `phase5.3-protocol-v1.0.0` | Split/leakage/calibration procedure changes |
| `metric_version` | `phase5.3-metrics-v1.0.0` | Any metric's mathematical definition changes (not merely its reported precision) |
| `baseline_version` | `phase5.3-baselines-v1.0.0` | A baseline's definition or fitting procedure changes |

Every benchmark result record (once results exist, in a future
implementation phase) must record all six values, exactly as
`PHASE5_3_BENCHMARK_SCHEMA.json`'s `reproducibility` block requires.

## 2. Deterministic seeding

- No step of task-instance derivation, splitting, or scoring may use
  Python's built-in `hash()` (salted per-process by `PYTHONHASHSEED`
  unless fixed) — this mirrors the exact discipline
  `tests/unit/test_phase52_record_id.py` already validates for dataset
  `record_id`s (a `PYTHONHASHSEED`-independence test is required for any
  new deterministic ID scheme this benchmark layer introduces, e.g.
  `instance_id`).
- Any bootstrap confidence interval computation must use an explicitly
  seeded random-number generator (e.g. `numpy.random.default_rng(seed)`),
  with the seed value itself recorded in the reported result.
- `instance_id` derivation (per `PHASE5_3_BENCHMARK_SCHEMA.json`) is a pure
  SHA-256 function of `task_id + record_id + sub_index` — never
  filesystem order, dict iteration order, or wall-clock dependent.

## 3. Environment and software metadata

A future benchmark result must record:
- Python version, key library versions (numpy/scipy/scikit-learn/
  jsonschema), OS/platform string (coarsened, not raw `platform.node()`
  per `PHASE5_1_PUBLICATION_BOUNDARY.md`'s host-identity exclusion).
- Hardware metadata only where relevant (e.g. for MET-TIME-COST-OVERHEAD,
  which depends on wall-clock timing) — irrelevant for purely statistical
  metrics (AUROC, ECE) which are hardware-independent given fixed inputs.

## 4. Provenance chain

```
git commit (this repo, this phase's deliverables)
  -> benchmark_spec_sha256 (SHA256_MANIFEST.json of this directory)
    -> dataset_sha256 (already recorded in dataset_metadata.json / SHA256_MANIFEST.json
                        under experiments/results/phase5_dataset_construction/20260826T054422Z/)
      -> source_artifact_hash (per-record provenance.checksum, already in every
                                canonical dataset record)
```

This chain lets any result be traced back to an exact frozen source byte
sequence, exactly as `PHASE5_1_PROVENANCE_CONTRACT.md` §4 established for
the dataset layer — this protocol extends the same chain one level up to
the benchmark layer, adding `benchmark_spec_sha256` and (once code exists)
a benchmark-code commit hash as two new links.

## 5. Independent reproducibility requirement per task

Every task in `PHASE5_3_TASK_CATALOG.json` has an
`independent_reproducibility` field stating what a third party would need
to reproduce that specific task's result (fixed bootstrap seed, fixed
split, task-specific derivation rule). No task's `independent_reproducibility`
field says "not reproducible" — the ones that are `NOT_EVALUABLE` from
current data simply state that reproducibility is moot until the
prerequisite data exists.

## 6. What this protocol explicitly forbids

- Any unseeded `random`/`numpy.random` call anywhere in a future scoring
  implementation.
- Any reliance on dict/set iteration order for tie-breaking (must use an
  explicit, documented sort key, per the same discipline
  `src/phase5/record_id.py`'s `sequence` field already uses at the dataset
  layer).
- Reporting a metric without its accompanying `metric_version` and
  `benchmark_version`.
- Re-running a scoring pass with different code and reporting it under the
  same `benchmark_version` without incrementing at least PATCH.
