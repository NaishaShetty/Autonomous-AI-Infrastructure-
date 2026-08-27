# Phase 5.6 — Public Artifact Inventory

Scope: every file present in the finalized release copy at
`experiments/results/phase5_6_external_release/20260827T055356Z/release/`
(84 files total: 21 under `release/dataset/`, 63 under `release/benchmark/`
— each count includes one whole-package `SHA256_MANIFEST.json` generated
fresh at the end of this phase, covering every other file in that
package),
classified PUBLIC / PUBLIC_METADATA / RESEARCH_ONLY / ENGINEERING_ONLY /
EXCLUDED. This inventory is a fresh, file-level audit built for this phase;
it is consistent with, and narrower than, Phase 5.5's directory-level
`PUBLICATION_BOUNDARY_MANIFEST.json`, which is retained as supporting
evidence and not re-derived from scratch.

## Classification key

- **PUBLIC** — the actual data/code artifact intended for external use.
- **PUBLIC_METADATA** — specification/policy/schema/card documents that
  describe the PUBLIC artifacts; safe and useful for an external consumer.
- **RESEARCH_ONLY** — internal research evidence not included in the
  release package (listed here for completeness of the audit trail, not
  because it appears in `release/`).
- **ENGINEERING_ONLY** — CI/test logs, internal audit working files; not
  included in `release/`.
- **EXCLUDED** — anything removed from the release copy for security,
  privacy, or scope reasons (see `SECURITY_AUDIT.md`).

## release/dataset/ (21 files) — all PUBLIC or PUBLIC_METADATA

| File | Classification | Note |
|---|---|---|
| data/all_records.jsonl | PUBLIC | 3,106 canonical records (agent_task + controlled_runtime), SHA-256 verified |
| data/dataset_metadata.json | PUBLIC | version/schema/record-count metadata |
| data/dataset_statistics.json | PUBLIC | aggregate statistics only, no per-record PII |
| data/leakage_audit.json | PUBLIC_METADATA | leakage-rule audit result (0 violations) |
| data/lineage.json | PUBLIC_METADATA | per-record provenance lineage (relative repo paths only) |
| data/provenance_audit.json | PUBLIC_METADATA | provenance-contract compliance audit |
| data/publication_boundary_audit.json | PUBLIC_METADATA | boundary-compliance audit (0 findings) |
| data/record_id_audit.json | PUBLIC_METADATA | record-ID uniqueness/format audit |
| data/split_assignment_manifest.json | PUBLIC | train/calibration/test split assignment per record |
| data/split_audit.json | PUBLIC_METADATA | split-integrity audit (0 overlaps/cross-split violations) |
| data/SHA256_MANIFEST.json | PUBLIC_METADATA | integrity manifest for `data/` |
| SHA256_MANIFEST.json (package root) | PUBLIC_METADATA | whole-package integrity manifest, generated fresh at the end of this phase, covers all other files in `release/dataset/` |
| CITATION.cff | PUBLIC_METADATA | citation metadata |
| DATASET_CARD.md | PUBLIC_METADATA | dataset card (this phase's version at top level; package copy retained) |
| DATASET_README.md | PUBLIC_METADATA | original Phase 5.2 construction-time README |
| README.md | PUBLIC_METADATA | package-level README |
| docs/PHASE5_1_LEAKAGE_POLICY.md | PUBLIC_METADATA | frozen Phase 5.1 policy document |
| docs/PHASE5_1_PROVENANCE_CONTRACT.md | PUBLIC_METADATA | frozen Phase 5.1 policy document |
| docs/PHASE5_1_PUBLICATION_BOUNDARY.md | PUBLIC_METADATA | frozen Phase 5.1 policy document |
| docs/PHASE5_1_SCHEMA.json | PUBLIC_METADATA | frozen Phase 5.1 record schema |
| docs/PHASE5_1_SPLIT_POLICY.md | PUBLIC_METADATA | frozen Phase 5.1 policy document |

## release/benchmark/ (63 files) — all PUBLIC or PUBLIC_METADATA after one redaction

| Area | Files | Classification |
|---|---|---|
| `src/benchmark/*.py` (15 files) | runner, tasks, metrics, ablations, baselines, leakage, validation, splits, registry, reporting, reproducibility, ids, status, constants, dataset_loader, `__init__.py` | PUBLIC — the benchmark implementation itself |
| `src/phase5/failure_mapping.py`, `src/phase5/__init__.py`, `src/__init__.py` | cross-module dependency `tasks.py` requires | PUBLIC |
| `scripts/run_phase5_4_benchmark.py`, `scripts/generate_sha256_manifest.py` | runner + manifest tooling | PUBLIC |
| `tests/unit/test_phase54_benchmark.py` | unit tests (41 pass in clean-room, see `CLEAN_ROOM_REPRODUCTION_REPORT.md`) | PUBLIC |
| `requirements.txt`, `README.md`, `REPRODUCIBILITY_GUIDE.md`, `CITATION.cff`, `BENCHMARK_CARD.md`, `SHA256_MANIFEST.json` (package root, generated fresh at the end of this phase) | package docs | PUBLIC_METADATA |
| `experiments/results/phase5_dataset_specification/20260826T053011Z/PHASE5_1_SCHEMA.json` | 1 file | PUBLIC_METADATA (loader-required schema copy) |
| `experiments/results/phase5_dataset_construction/20260826T054422Z/*` (13 files) | dataset construction audit trail that `dataset_loader.py` reads beyond `all_records.jsonl` | PUBLIC_METADATA — **one field redacted this phase**: `regeneration_audit.json`'s `run_a`/`run_b` fields contained a developer-machine temp path (`C:\Users\naish\...\scratchpad\...`) and have been replaced with `[REDACTED: ...]` in this release copy only (see `SECURITY_AUDIT.md`); no other field or file in this subtree was touched |
| `experiments/results/phase5_benchmark_specification/20260826T055915Z/*` (19 files) | frozen Phase 5.3 benchmark specification (task/metric/baseline/ablation catalogs, policies, schema) | PUBLIC_METADATA |

## RESEARCH_ONLY (not in release/, listed for completeness)

- Trained `RiskPredictor` / `PredictionScopeRouter` pickled model artifacts — excluded; these back the 4 PRED-* tasks which are NOT_EVALUABLE and releasing them would misrepresent an unvalidated artifact as a usable model.
- SQLite `FailureMemoryStore` raw database files — excluded; internal engineering state, not a research artifact.
- Real external source datasets (Alibaba GPU2020, AgentRx, AIOps 2020) raw content — excluded; these are third-party datasets referenced by provenance only (relative source paths in `lineage.json`), never redistributed.

## ENGINEERING_ONLY (not in release/)

- `tests/` (full repo test tree beyond the one benchmark unit-test file), `FULL_TEST_SUITE_OUTPUT.txt`, CI-style logs, Phase 5.5/5.6 internal audit working files (`GATE_A_*`, `TASK_BY_TASK_AUDIT.md`, `METRIC_AUDIT.md`, etc., and this phase's own audit `.md` files) — internal engineering/audit trail, not release-package material. Cross-referenced but not shipped.

## EXCLUDED

- Generation 1/2 (V1) evidence and `docs/archive/V1_RELEASE_AUDIT.md` — pre-Phase-4 prototype evidence, out of scope for this dataset/benchmark release.
- Host/platform identity (`platform.node()`, machine hostnames) — confirmed absent from all 82 release files by direct scan (`SECURITY_AUDIT.md`).
- One field in `regeneration_audit.json` (see above) — the only content-level exclusion/redaction found and applied this phase.

## Totals

- Public release files (PUBLIC + PUBLIC_METADATA): **84** (21 dataset + 63 benchmark).
- Excluded/redacted this phase: **1 field in 1 file** (not a whole-file exclusion); 0 whole files needed removal.
- RESEARCH_ONLY / ENGINEERING_ONLY category files: not counted in the release (by design, never copied into `release/`).
