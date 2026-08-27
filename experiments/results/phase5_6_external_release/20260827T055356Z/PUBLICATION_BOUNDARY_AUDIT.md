# Phase 5.6 — Publication Boundary Audit

This re-verifies, for this phase's release copy specifically, that the
publication boundary established in Phase 5.1
(`docs/PHASE5_1_PUBLICATION_BOUNDARY.md`, shipped in
`release/dataset/docs/`) and re-audited in Phase 5.5
(`PUBLICATION_BOUNDARY_MANIFEST.json`, `publication_boundary_audit.json`
with 0 findings across all 3,106 records) still holds for the actual
files now sitting in `release/`.

## What the boundary excludes, and confirmation each is actually absent

| Excluded category | Confirmation method | Result |
|---|---|---|
| Generation 1/2 (V1) evidence | `find release/ -iname "*v1*" -o -iname "*gen2*"`; manual review of all 82 file paths | 0 matches — no V1/Gen-2 file present |
| Trained model artifacts (pickles) | `find release/ -iname "*.pkl" -o -iname "*.pickle" -o -iname "*.joblib"` | 0 matches |
| SQLite memory-store files | `find release/ -iname "*.db" -o -iname "*.sqlite*"` | 0 matches |
| Raw third-party source data (AgentRx, AIOps 2020, Alibaba GPU2020) | grep for known source-dataset filenames/identifiers in `release/`; inspection of `lineage.json` confirms only relative repo *paths* to where this project stored derived records are present, never the third-party raw files themselves | 0 raw third-party files present; provenance is by reference only |
| Host/platform identity | scanned for `platform.node()`-style strings, `COMPUTERNAME`, `HOSTNAME`, hostnames, IPs (`SECURITY_AUDIT.md` patterns 4) | 0 matches |
| Internal CI/test logs | `find release/ -iname "*test_suite_output*" -o -iname "*.log"` | 0 matches (the one shipped test file, `tests/unit/test_phase54_benchmark.py`, is test *code*, not a log) |
| Engineering-only audit working files (GATE_A_*, this phase's own audits) | manual check of `release/` file list against this directory's top-level files | 0 matches — none of the top-level Phase 5.5/5.6 audit `.md` files were copied into `release/` |

## Record-level boundary check (fresh, this phase)

The dataset ships its own `data/publication_boundary_audit.json`
(0 findings, unchanged from Phase 5.2/5.5 — verified by direct read and
byte comparison against the frozen Phase 5.2 source in
`experiments/results/phase5_dataset_construction/20260826T054422Z/publication_boundary_audit.json`:
identical). No new violation was introduced by this phase's copy
operation, and no record content was altered (only the one
`regeneration_audit.json` path-field redaction described in
`SECURITY_AUDIT.md`, which is not a dataset record and carries no
publication-boundary classification of its own).

## Conclusion

The release package respects the frozen Phase 5.1 publication boundary.
No excluded category is present in `release/`. The one redaction applied
this phase (`regeneration_audit.json` temp paths) is a security fix, not a
publication-boundary violation — that field was never classified
PUBLIC/PUBLIC_METADATA content to begin with, it was leaked incidental
metadata about the developer's machine.
