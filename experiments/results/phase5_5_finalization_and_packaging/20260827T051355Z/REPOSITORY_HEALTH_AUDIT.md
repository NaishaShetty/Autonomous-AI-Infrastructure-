# Phase 5.5 — Repository Health Audit

## A8: full repo test suite failure characterization

Independently re-verified in this phase (see full suite output captured
this session):

- `tests/unit/test_phase54_benchmark.py`: **41 passed**, 0 failed (rerun
  fresh in this phase).
- Grep confirms `src/benchmark/` and `tests/unit/test_phase54_benchmark.py`
  contain **zero references** to `experience`, `src/runtime`, or the
  `/tmp/counterfactual_experiences_*` path family.
- `git diff --stat HEAD -- src/runtime/ tests/runtime/test_counterfactual_generalization.py
  scripts/run_counterfactual_generalization.py` is empty — none of these
  files have been touched this phase, or (per `git log -1`) since commit
  `d951d607`, well before Phase 5.4/5.5.
- The hardcoded, non-hermetic path is in
  `scripts/run_counterfactual_generalization.py:181`
  (`experience_path=f"/tmp/counterfactual_experiences_{seed}.jsonl"`),
  consumed by `src/runtime/experience.py`'s `JsonExperienceStore` — both
  outside `src/benchmark/`'s import graph.
- Confirmed the external file exists on this machine
  (`C:/tmp/counterfactual_experiences_19.jsonl`, 8,295 lines) and is shared/
  appended-to across unrelated test runs (other seed files in the same
  directory show timestamps from this very session, confirming they are
  live-appended by whatever test run touches them).
- **Conclusion: this is a genuine, pre-existing, unrelated repository
  hygiene defect** (a non-hermetic hardcoded path shared across test runs
  outside pytest's `tmp_path` isolation), confirmed independently in this
  phase, not merely re-asserted from the Phase 5.4 report. It is not
  modified here because `src/runtime/` is a frozen path for this phase and
  the defect is outside `src/benchmark/`'s scope entirely.

Full suite result (this phase, run to completion — see
`FULL_TEST_SUITE_OUTPUT.txt` in this directory for the raw log):
see `GATE_A_FINAL_AUDIT.md` for the final pass/fail counts once the run
completed.

## Secrets / credentials scan

Grepped `src/`, `scripts/`, and this phase's output directory for
`api[_-]?key|secret|password|token|BEGIN (RSA|PRIVATE) KEY`. All hits are
false positives: NLP "token" terminology
(`src/phase5/record_id.py`'s `"<NONE>"` sentinel-token comment,
tokenizer/task code), and the publication-boundary validator's own
pattern-matching source code (`scripts/phase5_dataset/validate_publication_boundary.py`,
which exists specifically to *detect* credential-like tokens in candidate
release files — its own regex definition matches the grep). No actual
secret, key, or credential value was found in any scanned file.

## Private paths / host identity

`scripts/phase5_dataset/validate_publication_boundary.py` already
implements a dedicated scanner for absolute local filesystem paths and
host-identity strings, used ahead of Gate B packaging (see
`RELEASE_PACKAGE_AUDIT.md`). No additional local-path leakage was found in
`src/benchmark/` or the dataset directory during this audit beyond what
that validator already screens for.

## Temp / junk / cache files (pre-existing, not created this session)

- `.cowork_scratch/` (untracked, dated 2026-08-23 to 2026-08-26, i.e.
  before this session started): contains `stale_head.lock` and
  `stale_index.lock` (0 bytes each — stale git lock artifacts),
  `phase45b_delivery.tar.gz` (92 KB, an old delivery archive), and a
  `gen_closure_manifest.py` script. **Not deleted** — none of these were
  created by this session, and the task's own instruction is to remove
  only "your own scratch files" created this session. Flagged here for the
  user/maintainer's attention only.
- `C:/tmp/counterfactual_experiences_*.jsonl` (5 files, ~30 MB each,
  outside the repository entirely): the root cause of the pre-existing
  test failures above. Not deleted for the same reason (outside repo,
  outside this session's scope, and the task explicitly says not to modify
  `src/runtime/`-adjacent behavior to force a green number).
- `__pycache__/` directories under `src/benchmark/`, `src/phase5/`,
  `scripts/`: normal Python bytecode cache, already gitignored-equivalent
  in practice (not tracked by git per `git status`), not a hygiene issue.

## Duplicate / stale documentation

Not exhaustively re-audited in Gate A (this is properly a Gate B
packaging-boundary decision per Step B4); addressed in
`RELEASE_PACKAGE_AUDIT.md` if Gate A passes.

## Dead benchmark code

`src/benchmark/leakage.py` defines 8 rule-check functions (L2–L7, L9, L11,
L12) that are not currently invoked anywhere in `src/benchmark/tasks.py` or
`ablations.py`. See `LEAKAGE_AUDIT.md` for the full analysis: this is
inert-but-correct forward-looking code (guards for code paths that don't
exist yet because the tasks they'd guard are gated `NOT_EVALUABLE`), not a
security or scientific-integrity defect. Left in place, documented rather
than silently removed or silently ignored.

## Unused dependencies / large binaries

Not found: `requirements.txt` entries were cross-checked informally against
imports in `src/benchmark/` (numpy, pandas, scipy, sklearn all actively
used); no large binary files were introduced by Phase 5.4/5.5 work (the
only binary found, `.cowork_scratch/phase45b_delivery.tar.gz`, predates
this session and is a delivery artifact, not a repository dependency).
