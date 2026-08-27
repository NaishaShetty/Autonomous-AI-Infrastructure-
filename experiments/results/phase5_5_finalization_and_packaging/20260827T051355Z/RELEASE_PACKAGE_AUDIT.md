# Phase 5.5 — Release Package Audit (Gate B)

## B1 — Publication boundary

See `PUBLICATION_BOUNDARY_MANIFEST.json` for the full artifact-by-artifact
classification (PUBLIC / PUBLIC_METADATA / RESEARCH_ONLY /
ENGINEERING_ONLY / EXCLUDED), built from `PHASE5_1_PUBLICATION_BOUNDARY.md`
and independently cross-checked against `publication_boundary_audit.json`
(0 findings across all 3,106 dataset records). Excluded from both release
packages: V1/Gen-2 evidence, trained-model pickle artifacts, SQLite memory
stores, host/platform identity (confirmed absent by direct scan), and all
engineering-only test/CI logs.

## B2 — Dataset release package

`release/dataset/`: `data/` (all_records.jsonl + every audit/statistics/
manifest JSON the Phase 5.2 construction produced, needed for someone to
independently re-verify the dataset without the benchmark code),
`docs/` (Phase 5.1 schema/split/leakage/provenance/publication-boundary
documents), `DATASET_README.md` (original construction-time README),
`README.md`, `DATASET_CARD.md`, `CITATION.cff`. Verified in isolation
(see `CLEAN_ROOM_REPRODUCIBILITY_REPORT.md`): SHA-256 matches, all 3,106
records parse.

## B3 — Benchmark release package

`release/benchmark/`: `src/benchmark/` (full implementation, unmodified
from the repo's frozen copy except none — byte-identical), `src/phase5/failure_mapping.py`
(the one cross-module dependency `tasks.py` uses),
`experiments/results/{phase5_dataset_specification,phase5_dataset_construction,phase5_benchmark_specification}/...`
(the exact relative-path layout `src/benchmark/constants.py` requires —
discovered and required during clean-room testing, see below),
`scripts/` (runner + SHA-256 manifest generator), `tests/unit/` (unit
tests, kept at the original nesting depth — see below), `requirements.txt`,
`README.md`, `BENCHMARK_CARD.md`, `REPRODUCIBILITY_GUIDE.md`,
`CITATION.cff`.

**Two packaging bugs were found and fixed during clean-room testing (not
benchmark-result changes):**
1. The dataset subtree was initially missing 7 files
   (`split_assignment_manifest.json`, `leakage_audit.json`,
   `provenance_audit.json`, `record_id_audit.json`,
   `publication_boundary_audit.json`, `lineage.json`,
   `SHA256_MANIFEST.json`) that `dataset_loader.load_canonical_dataset()`
   reads beyond `all_records.jsonl`. Fixed by copying them in.
2. `tests/unit/test_phase54_benchmark.py` computes its own repo root via
   `Path(__file__).resolve().parents[2]`, which assumes the original
   `tests/unit/` nesting depth (2 levels under repo root). An initial flat
   `tests/test_phase54_benchmark.py` placement would have resolved this
   one directory too high. Fixed by preserving the `tests/unit/` nesting.

Full detail in `CLEAN_ROOM_REPRODUCIBILITY_REPORT.md`. Neither fix touched
`src/benchmark/` itself or changed any benchmark result — both are
packaging-directory corrections, confirmed by the post-fix clean-room run
being byte-identical to the pre-existing reference results.

## B4 — Documentation inventory

The repository already has a recent, thorough documentation inventory:
`DOCUMENT_CLEANUP_MANIFEST.md` (dated 2026-08-25, produced during the
Phase 4 closure pass), which classified every file under `docs/` (including
all ~50 `docs/archive/*.md` phase reports) and every `experiments/results/`
subdirectory as historical-evidence / required-for-reproducibility /
superseded / duplicate / obsolete, with an explicit "never delete frozen
evidence" governing rule, and confirmed (via SHA-256) that the only actual
duplicate-hash collisions all live inside protected raw-evidence
directories. This phase does not redo that inventory; it applies it to a
new, narrower question — **what belongs in the release/ package**, which
is a strict subset regardless of a document's repo-retention status:

- **PUBLIC (release-appropriate)**: `PHASE5_1_*` and `PHASE5_3_*`
  specification/policy/card documents (bundled directly in the release
  packages, see above); `docs/MASTER_RECORD_CONTENT.md` and
  `docs/Autonomous_AI_Infrastructure_Comprehensive_Record.docx` are
  referenced by the release README/cards for narrative context but are
  **not copied into `release/`** — they describe the whole project, not
  just the dataset/benchmark, and belong with the repository, not the
  narrower release scope.
- **EXCLUDED from `release/` (but kept in the repository as historical
  evidence, per `DOCUMENT_CLEANUP_MANIFEST.md`'s own governing rule)**:
  every `docs/archive/*.md` phase report, `FINAL_PHASE4_CLOSURE_REPORT.md`,
  `FINAL_SYSTEM_AUDIT.md`, `FINAL_WEAKNESS_REGISTER.md`, all Phase 5.5
  audit working files in this directory. These are internal engineering
  history, valuable for the project's own provenance trail, but not
  release-package material — a benchmark/dataset consumer does not need
  Phase 1-4's internal audit trail to use the release.
- No repository deletion occurs as a result of this step — this is a
  packaging inclusion/exclusion decision only, per the task's explicit
  instruction that B4 is "a packaging decision... not a repository
  deletion decision."

## B9 — Repository hygiene (extends Gate A's `REPOSITORY_HEALTH_AUDIT.md`)

No new findings beyond Gate A's. The release packages themselves were
scanned for secrets (none found — same false-positive pattern as the
repo-wide scan: "token"/"secret" appear only in NLP/tokenizer code and the
publication-boundary validator's own detection regex), for host-identity
strings (none — confirmed absent from the dataset by direct scan), and for
absolute-path leakage back to the development machine (0 matches for the
repo's directory name in any clean-room output, see
`CLEAN_ROOM_REPRODUCIBILITY_REPORT.md`).

## Conclusion

Both release packages are complete, self-contained, and verified
independently runnable from a copy with no reference to the parent
repository. See `DATASET_RELEASE_MANIFEST.json` and
`BENCHMARK_RELEASE_MANIFEST.json` for the full file/size/hash/
classification/purpose listing.
