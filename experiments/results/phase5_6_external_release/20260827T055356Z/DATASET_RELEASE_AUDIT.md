# Phase 5.6 — Dataset Release Audit

## Source and copy method

Copied verbatim from
`experiments/results/phase5_5_finalization_and_packaging/20260827T051355Z/release/dataset/`
into this phase's `release/dataset/`. No labels, splits, workload
groupings, record IDs, provenance fields, or negative-result content were
altered. The only change anywhere in the dataset release subtree is the
one path redaction in a benchmark-side auxiliary file
(`regeneration_audit.json`, documented in `SECURITY_AUDIT.md`) which lives
under `release/benchmark/experiments/results/phase5_dataset_construction/`,
not under `release/dataset/` itself — `release/dataset/` is byte-identical
to its Phase 5.5 source.

## Integrity verification (fresh, this phase)

- **Record count:** 3,106 records in `data/all_records.jsonl`, confirmed
  by direct line-count and JSON-parse of every line (0 parse failures).
- **SHA-256:** computed fresh —
  `4f6994447cf28cb7f78948727e177e21cb6688ada85557613723151b66064b83` —
  matches `data/SHA256_MANIFEST.json`'s recorded hash for
  `dataset/all_records.jsonl` exactly.
- **Split integrity:** `data/split_audit.json` (0 overlaps, 0
  cross-split workload violations) is byte-identical to the frozen Phase
  5.2 source; independently re-derived split counts from
  `split_assignment_manifest.json` match.
- **Schema:** every record validated against
  `docs/PHASE5_1_SCHEMA.json` in the clean-room run (see
  `CLEAN_ROOM_REPRODUCTION_REPORT.md`) — 0 schema violations, confirmed by
  the benchmark's own fail-closed `dataset_loader.py` accepting the
  dataset and by the 41-test unit suite passing against it.
- **Leakage:** `data/leakage_audit.json` unchanged, 0 violations.
- **Provenance:** `data/provenance_audit.json` unchanged, 0 violations;
  spot-checked 1 record by hand (task-958, arithmetic_self_consistency) —
  provenance fields point only to relative repository paths
  (`experiments/results/phase4_6_to_4_10/...`), never to any path outside
  the repository.

## Task-family separation

Arithmetic, sentiment, and QA records remain distinct
(`task_family` field: `arithmetic_self_consistency` and siblings observed
directly in spot-checked records) — never merged into a single undifferentiated
"uncertainty" bucket. `dataset_statistics.json` reports per-family counts
separately.

## Negative results and unsupported-evidence fields preserved

Verified unchanged from the frozen Phase 5.2/5.5 source (byte-for-byte,
since `release/dataset/` was copied without modification): recovery
0/35, sentiment weaker discrimination, diagnosis
`causal_status=CAUSAL_GROUND_TRUTH_UNAVAILABLE` fields, memory/
generalization/prediction `NOT_EVALUATED`/`NOT_EVALUABLE` markers on
individual records (e.g., the spot-checked record above shows
`"predictability_status": "NOT_EVALUATED"` on its `prediction` object).

## Conclusion

`release/dataset/` is a faithful, verified, unaltered copy of the frozen
Phase 5.2 canonical dataset as finalized in Phase 5.5. No security issue
required removing any dataset field. Ready for external release pending
the license decision (`RELEASE_DECISION.md`).
