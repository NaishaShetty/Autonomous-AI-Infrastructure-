# Phase 6.1 — Repository Cleanup Report

## Scope

Inspected the full working tree for genuinely unnecessary files (IDE/OS
artifacts, bytecode caches, stray logs, duplicate scratch output) that are
NOT historical evidence, per the frozen-boundary list in the Phase 6 brief.
Nothing under a frozen path (`experiments/results/` pre-existing subdirs,
`docs/archive/`, `docs/MASTER_RECORD_CONTENT.md`, the root `FINAL_*` /
`DOCUMENT_CLEANUP_MANIFEST.md` files, `src/phase4/`, `src/runtime/`,
`src/recovery/`, `src/failure_experience/`, `src/decision/`) was modified,
moved, or deleted.

## Findings

| Item | Type | Disposition | Justification |
|---|---|---|---|
| `.cowork_scratch/` (109 KB: a manifest-gen script, a delivery tarball, 3 stale `.log` files, 2 stale git `.lock` files) | Untracked local scratch directory, not under any frozen path | **Should be deleted; not committed to git** | Pure disposable working-session output (stale `git` index/HEAD lock files, ad-hoc test-run logs, a tarball snapshot). It was never tracked by git (`git status` shows it as `??`), so it carries zero historical-evidence risk. **This session's sandbox permission classifier blocked all file-deletion commands** (`rm`, `Remove-Item`) issued during this phase, so the directory could not actually be removed from disk in this run. It is now excluded from git via `.gitignore` (added below) so it can never be accidentally committed; the user should delete it manually (`rd /s /q .cowork_scratch` or via Explorer) at their convenience. |
| `__pycache__/`, `*.pyc` under `.venv/Lib/site-packages/...` | Virtualenv-internal bytecode cache | No action needed | `.venv/` is already fully gitignored and was never tracked; these are third-party package caches inside the virtual environment, not repository content. |
| `.pytest_cache/` | pytest cache | No action needed | Already gitignored, already untracked, confirmed via `git ls-files | grep pytest_cache` (no hits). |
| `data/failure_experience_dev.db`, `data/unified_dev.db` | Local SQLite dev databases | Left untouched | `/data/` is gitignored; these are runtime state, not source or evidence, and 5 unrelated files under `data/` are already tracked from earlier phases — out of scope for this cleanup and not touched. |
| `.idea/`, `.vscode/`, `.DS_Store`, `Thumbs.db` | IDE/OS artifacts | None found in this repo | Checked explicitly; none present. Ignore rules added preventively (see below) since this is a Windows/cross-platform repo other contributors may open in an IDE. |
| Duplicate/renamed docs (`docs/PHASE4_5B_RECOGNITION_AND_AGENT_EVALUATION_REPORT.md`, `docs/PHASE4_5_GAP_FIXES_REPORT.md`) | Already renamed to `docs/archive/` in the pre-existing uncommitted git status (`R` rename) | Not touched | This rename was staged by the prior phase, not this one; it moves historical reports into the existing `docs/archive/` convention rather than deleting them. Left exactly as the working tree already has it. |

## `.gitignore` changes

Added, so cache/bytecode/local-state files cannot be tracked going forward:

```
# Local scratch / IDE / OS cruft (Phase 6 cleanup)
.cowork_scratch/
*.tmp
*.bak
*~
.idea/
.vscode/
.DS_Store
Thumbs.db
*.log
```

`*.log` is safe to add: the 5 pre-existing tracked `*.log` files under
`experiments/results/system_evaluation/.../raw/full_pytest.log` remain
tracked (git ignore rules never untrack already-tracked files); the rule
only prevents *new* stray log files from being added by accident.

## Directory structure decision

The existing top-level structure (`src/`, `tests/`, `experiments/results/`,
`docs/`, `scripts/`, `data/`, `configs/`, `benchmarks/`) is already coherent
and follows a consistent per-phase-timestamped-directory convention under
`experiments/results/`. **No wholesale reorganization was performed** — the
brief only calls for one if there is a genuine mess, and there is not one.
No path references were broken by this cleanup; no frozen path moved.

## Verification

```
git diff --stat            # confirms no frozen path touched
git status --short         # confirms .cowork_scratch/ no longer listed (deleted from working tree where classifier allowed / now gitignored)
```

Net effect: zero files removed from git history or tracked content (none of
the removed/ignored items were ever tracked); one directory flagged for
manual deletion (blocked by sandbox policy, not by any decision to keep
it); `.gitignore` extended for future hygiene.
