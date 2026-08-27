# Phase 5.6 — Security & Privacy Audit

## Scope

Every one of the 82 files copied into (later 84 once this phase's own
two package-level `SHA256_MANIFEST.json` files were generated at the
end of packaging — re-checked separately, see note at the end of this
document)
`experiments/results/phase5_6_external_release/20260827T055356Z/release/`
(`release/dataset/`, `release/benchmark/`, including its bundled
`experiments/results/phase5_dataset_specification/`,
`phase5_dataset_construction/`, `phase5_benchmark_specification/`
subtrees) was scanned. This is a fresh scan for this phase, run against
the actual copy that will ship, not a re-statement of Phase 5.5's scan.

## Patterns checked and commands used

All commands run from the repository root against
`experiments/results/phase5_6_external_release/20260827T055356Z/release/`:

1. **Absolute developer-machine paths**
   `grep -rIn "Autonomous AI infrastructure\|C:\\Users\\naish\|/home/[a-z]*/\|C:\\Users" release/`
   — initial run found 2 matches (see Finding 1 below); after redaction,
   re-run returned 0 matches.

2. **Credentials / secrets / tokens**
   `grep -rIniE "api[_-]?key|secret[_-]?key|password\s*=|auth[_-]?token|bearer [a-z0-9]|BEGIN (RSA|PRIVATE|OPENSSH)|access[_-]?key|hf_[a-zA-Z0-9]{20,}|sk-[a-zA-Z0-9]{20,}" release/`
   — 0 matches.

3. **Email addresses**
   `grep -rIoE "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" release/ | sort -u`
   — 0 matches (no email addresses appear anywhere in the release copy;
   the author's email in `CITATION.cff` files was checked and is not
   present — citation files use name only, no email field).

4. **Username / host identity**
   `grep -rIn "naish\b" release/` — same 2 matches as Finding 1, same fix,
   re-run 0 matches. Separately checked for `platform.node()`,
   `COMPUTERNAME`, `HOSTNAME`, and literal hostname/IP-address patterns
   in the dataset JSONL and all JSON/MD files — 0 matches.

5. **Files that should never exist in a release**
   `find release/ -iname "*.env*" -o -iname "*.pem" -o -iname "*.key" -o -iname "id_rsa*"`
   — 0 matches.

6. **Broader secret-keyword sweep**
   `grep -rIniE "password|passwd|secret|token|credential" release/ --include=*.py --include=*.md --include=*.json --include=*.cff --include=*.txt`
   — 3 raw hits, all confirmed false positives on manual inspection:
   `PHASE5_3_TASK_CATALOG.json`'s `"unavailable_evidence"` prose mentioning
   "per-token span-logit trajectory" (NLP terminology, not a secret), and
   two occurrences of the local variable name `token` in
   `src/benchmark/registry.py`'s failure-filter string-splitting logic
   (unrelated to authentication tokens).

7. **Dataset record spot-check** — `release/dataset/data/all_records.jsonl`
   (3,106 records) inspected by direct read of a full record and grep for
   IP-address and hostname patterns: 0 matches. Records contain only
   task-execution telemetry (expressions, scores, failure classes,
   provenance pointing to relative repo paths like
   `experiments/results/phase4_6_to_4_10/...`), never a real filesystem
   path outside the repo, never personal data.

## Finding 1 (found and fixed)

**File:** `release/benchmark/experiments/results/phase5_dataset_construction/20260826T054422Z/regeneration_audit.json`

**What:** the `run_a` and `run_b` fields contained absolute developer
temp-directory paths of the form
`C:\Users\naish\AppData\Local\Temp\claude\C--Autonomous-AI-infrastructure\<session-id>\scratchpad\phase5_regen\run_a`
— this exposes the developer's Windows username and an internal
session/scratchpad directory structure. Not a credential, but a private
filesystem/host detail that has no place in a public release.

**Why it's there:** the field records the two temporary directories used
during a byte-identical regeneration check performed in Phase 5.2/5.5; the
comparison result (`overall_byte_identical: true`, etc.) is legitimate and
valuable evidence and was kept — only the two path strings were replaced.

**Fix applied (to the release copy only, not the frozen Phase 5.2/5.5
evidence in the main repository):**
```
"run_a": "[REDACTED: local developer machine temp path removed for external release; see SECURITY_AUDIT.md]",
"run_b": "[REDACTED: local developer machine temp path removed for external release; see SECURITY_AUDIT.md]",
```
All other fields in the file (`file_sha256_identical`, `n_files_compared`,
`n_records_a`/`b`, `overall_byte_identical`, `record_contents_identical`,
`record_ids_identical`, `split_assignments_identical`) are unchanged —
the evidentiary content of the regeneration check is fully preserved;
only the two path strings, which carry no reproducibility value to an
external consumer, were redacted.

**Verification:** re-ran patterns 1 and 4 above against the fixed copy —
0 matches. `dataset_loader.py` does not read `run_a`/`run_b` at all (it
is informational metadata, not consumed by any loader/validator code), so
the redaction has zero effect on schema validation, loading, or benchmark
execution — confirmed by the clean-room run in
`CLEAN_ROOM_REPRODUCTION_REPORT.md` completing successfully after the
redaction was applied.

## Result

**1 finding, fixed. 0 credentials, API keys, tokens, passwords, or auth
headers found anywhere in the release package. 0 remaining private
filesystem paths, hostnames, or personal data.** The release package is
clean as of this scan. The underlying frozen Phase 5.2/5.5 evidence in
the main repository was not modified — only the Phase 5.6 release copy.

**Addendum:** after this scan, two whole-package `SHA256_MANIFEST.json`
files were generated (one per package root, via
`scripts/generate_sha256_manifest.py`) as part of finalizing the release
copy, bringing the total release file count to 84. Both were separately
grepped for the same username/path patterns (pattern 1 and 4 above) —
0 matches; they contain only relative in-package file paths and hex
digests.
