# Phase 5.6 — Clean-Room Reproduction Report

## Setup

A temporary directory was created **outside** the repository
(`%LOCALAPPDATA%\Temp\claude\...\scratchpad\phase5_6_cleanroom\`, a
session-scoped scratch location, not this repository's working tree) and
populated with **only**:

- `dataset/` — an exact copy of this phase's `release/dataset/`
- `benchmark/` — an exact copy of this phase's `release/benchmark/`
  (i.e. the copy that already had the `regeneration_audit.json`
  redaction applied — the clean-room test therefore validates the
  *actual* artifact being proposed for release, not the pre-redaction
  Phase 5.5 copy)

Nothing else from the parent repository was copied in — no `.git`, no
`src/phase4`, `src/runtime`, `src/recovery`, no other `tests/`, no
`docs/`, no scripts outside the two `release/*/scripts` subtrees.

Before running anything, the clean-room copy was grepped for
`Autonomous AI infrastructure`, `C:\Users\naish`, and the repository's
own directory name — 0 matches, confirming the package carries no
back-reference to the original repository or developer machine.

## Steps performed, acting as an external researcher with no repo access

1. **Install dependencies:** `python -m pip install -r benchmark/requirements.txt`
   — numpy 2.4.6, pandas 3.0.5, scikit-learn 1.9.0, scipy 1.17.1 (all
   already satisfied on this test machine at the pinned versions; no
   version conflict).

2. **Load and validate the dataset:** the benchmark's own
   `src/benchmark/dataset_loader.py` (fail-closed loader) was exercised
   by running the benchmark itself (step 4) and separately the record
   count/SHA-256 was independently verified by hand:
   - 3,106 lines, each a valid JSON object — 0 parse failures.
   - SHA-256 of `dataset/data/all_records.jsonl`:
     `4f6994447cf28cb7f78948727e177e21cb6688ada85557613723151b66064b83`
     — matches `dataset/data/SHA256_MANIFEST.json`'s recorded hash
     exactly.

3. **Run the unit tests:** `python -m pytest benchmark/tests/unit/test_phase54_benchmark.py -q`
   → **41 passed** in 23.23s, 0 failed, run entirely inside the
   clean-room copy.

4. **Run the supported benchmark tasks (full run, not just uncertainty
   track):** `python benchmark/scripts/run_phase5_4_benchmark.py`
   (invoked from inside `benchmark/`, its self-detected `REPO_ROOT` is
   the clean-room `benchmark/` directory, confirming the loader's
   relative-path resolution needs nothing outside the package). The
   script:
   - Loaded the dataset, validated it fail-closed.
   - Ran all 16 tasks (executing the supported ones, marking the rest
     `NOT_EVALUABLE`, per design).
   - Ran the 5 ablations.
   - Built the capability matrix.
   - Ran the whole benchmark **twice** internally and reported
     `determinism_check`.
   - Wrote a fresh `SHA256_MANIFEST.json` for its own output.
   Completed successfully with no exceptions and no missing-file errors
   (after the redaction — see "packaging bugs" note below, none were
   newly introduced this phase; the file layout inherited from Phase
   5.5 already resolved the two packaging bugs it had found).

5. **Verify determinism:** the run's own
   `determinism_check` reported all four flags `true`:
   `task_results_identical`, `ablation_results_identical`,
   `capability_matrix_identical`, `split_assignments_identical`.

6. **Verify reproduction of reported results:** compared the clean-room
   run's `PHASE5_4_BENCHMARK_RESULTS.json` against the frozen Phase 5.4
   reference (`experiments/results/phase5_benchmark_implementation/20260826T150824Z/PHASE5_4_BENCHMARK_RESULTS.json`)
   field-by-field, excluding only fields that must differ because the
   clean-room copy has no `.git` and a different run timestamp
   (`generated_at_utc`, `code_commit`, `git_status`). Result:
   **identical** on every task's metric values, sample counts, status,
   `config_hash`
   (`d8d349a545a1910bfada66de5628cf3ebb52c50f9a15465dd34840ab8de5e08b`),
   ablation results, and capability matrix.

7. **Verify SHA-256 hashes:** dataset hash (step 2) matches; the
   clean-room's fresh `SHA256_MANIFEST.json` for its own run output was
   generated successfully by the shipped
   `scripts/generate_sha256_manifest.py` with no errors.

8. **Path-leak check on generated output:** the clean-room run's own
   output directory was grepped for the repository name / developer
   username. One expected hit: the run's own
   `SHA256_MANIFEST.json` records `"run_dir": "<absolute clean-room path>"`
   — this is the benchmark tooling recording *its own local run
   location* for provenance (a normal, expected reproducibility field
   any user's run will populate with their own machine's path); it is
   generated fresh by each user's own invocation and is not part of the
   *shipped* `release/benchmark/` package itself (it did not exist
   before this test's own run). This is not a packaging defect.

## Packaging bugs

None found or fixed in this phase — Phase 5.5's two packaging fixes
(missing dataset-loader-required audit files; `tests/unit/` nesting
depth) were already applied and are inherited unchanged. This phase's
own clean-room run succeeded with no further packaging changes required
beyond the security redaction in `SECURITY_AUDIT.md` (which is a content
redaction, not a packaging-layout fix, and was applied before this
clean-room test was run).

## Result

**Clean-room reproduction: PASS.** An external researcher with zero
access to the original repository can install dependencies, load and
validate the dataset, run the unit tests (41/41 pass), run the full
benchmark, obtain a byte-comparable (modulo expected run metadata) result
to the frozen Phase 5.4 reference, and confirm determinism — entirely
from the release package contents alone.
