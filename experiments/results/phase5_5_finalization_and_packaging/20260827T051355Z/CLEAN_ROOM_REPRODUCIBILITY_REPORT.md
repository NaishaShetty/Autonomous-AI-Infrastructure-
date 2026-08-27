# Phase 5.5 — Clean-Room Reproducibility Report

## Method

Copied (not symlinked) the release packages into isolated temporary
directories outside the repository, containing **only** the files under
`release/benchmark/` and `release/dataset/` respectively, with no `.git`
directory and no reference back to the original repository's absolute
path. Confirmed isolation (`git rev-parse --is-inside-work-tree` fails:
"not a git repository"). All commands below were run with the isolated
directory as the working directory.

## Benchmark clean-room test

Temp dir:
`.../scratchpad/cleanroom_benchmark` (outside the repo).

1. **First attempt failed — genuine packaging bug found and fixed.**
   `python scripts/run_phase5_4_benchmark.py --out-dir <tmp>` raised
   `FileNotFoundError` for `split_assignment_manifest.json`. Root cause:
   `src/benchmark/dataset_loader.py`'s `load_canonical_dataset()` reads 7
   more files beyond `all_records.jsonl` (`split_assignment_manifest.json`,
   `leakage_audit.json`, `provenance_audit.json`, `record_id_audit.json`,
   `publication_boundary_audit.json`, `lineage.json`, `SHA256_MANIFEST.json`)
   that the initial package build had omitted. **Fixed the packaging**
   (not the benchmark code or results) by copying these 7 files into
   `release/benchmark/experiments/results/phase5_dataset_construction/20260826T054422Z/`
   from the frozen Phase 5.2 output directory.
2. **Second attempt found a second genuine packaging bug.**
   `tests/unit/test_phase54_benchmark.py` computes
   `REPO_ROOT = Path(__file__).resolve().parents[2]`, which assumes the
   original repository's `tests/unit/` nesting depth. The initial package
   had flattened this to `tests/test_phase54_benchmark.py` (1 level), which
   would have resolved `REPO_ROOT` one directory *above* the package root.
   **Fixed the packaging** by nesting the test file at
   `release/benchmark/tests/unit/test_phase54_benchmark.py`, matching the
   original depth exactly.
3. **Third attempt (after both fixes): full success.**
   - `pip install -r requirements.txt` — already satisfied (identical
     versions: numpy 2.4.6, pandas 3.0.5, scipy 1.17.1, scikit-learn 1.9.0).
   - `python scripts/run_phase5_4_benchmark.py --out-dir <tmp>/my_run` —
     completed, `Determinism: {'task_results_identical': True,
     'ablation_results_identical': True, 'capability_matrix_identical':
     True, 'split_assignments_identical': True}`.
   - `task_results`, `capability_matrix`, and `dataset_audit.all_records_sha256`
     compared programmatically against this phase's independent Gate A
     rerun (`gate_a_independent_rerun/PHASE5_4_BENCHMARK_RESULTS.json`):
     **all identical**.
   - `python -m pytest tests/ -q` (run from inside the clean room): **41
     passed**, 0 failed — identical to the in-repo result.
   - Scanned every file under the clean-room output directory for the
     original repository's absolute path string (`"Autonomous AI
     infrastructure"`): **0 matches** — confirms no leaked internal path
     dependency.

## Dataset clean-room test

Temp dir: `.../scratchpad/cleanroom_dataset` (outside the repo, separate
from the benchmark clean room).

- Recomputed SHA-256 of `data/all_records.jsonl` from the isolated copy:
  `4f6994447cf28cb7f78948727e177e21cb6688ada85557613723151b66064b83` —
  matches the published manifest exactly.
- Loaded and JSON-parsed all 3,106 lines successfully with no external
  dependency beyond the Python standard library.

## Disposition of the two packaging bugs found

Both were **packaging-layer omissions** (files/paths not carried into the
release directory), not defects in the underlying benchmark
implementation or its results — `src/benchmark/` and
`tests/unit/test_phase54_benchmark.py` themselves were not modified; only
the release package's file inventory and directory depth were corrected.
Both are documented here rather than silently fixed with no record, per
the task's instruction to fix packaging (not results) when a clean-room
test reveals a hidden internal-path dependency.

## Conclusion

After the above two packaging corrections, both release packages are
fully self-contained and independently reproducible: **byte-identical
benchmark results, matching dataset hash, and a fully green test suite**,
all verified from isolated temporary directories with no reference to the
original repository.
