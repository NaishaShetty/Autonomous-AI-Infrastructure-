# Phase 5.2 — Synthesis

## What was asked

Construct and mechanically validate the canonical Phase 5 research dataset
per the already-approved, FROZEN Phase 5.1 specification
(`experiments/results/phase5_dataset_specification/20260826T053011Z/`),
resolving its three explicitly-flagged open questions (deterministic
record_id, split/workload compatibility, deterministic regeneration), then
run every listed validation dimension and report honestly.

## What was delivered

- 3,106 canonical records (46 `controlled_runtime`, 3,060 `agent_task`),
  100% schema-valid, 0 duplicate record IDs, 0 leakage violations, 0
  provenance problems, 0 forbidden split overlaps, 0 publication-boundary
  findings, byte-identical on regeneration.
- A deterministic, tested record-ID scheme (`src/phase5/record_id.py` +
  `tests/unit/test_phase52_record_id.py`, 10/10 passing).
- A mechanical split validator with zero forbidden overlaps
  (`scripts/phase5_dataset/validate_splits.py`).
- A full generation pipeline (`src/phase5/`, `scripts/phase5_dataset/`)
  that is a pure function of frozen evidence, with no wall-clock or random
  dependence anywhere in ID, ordering, or split-assignment logic.
- All 20 required deliverable artifacts (dataset files, metadata,
  statistics, lineage, record-ID spec+code+test, split manifest+audit,
  6 validation reports+audits, README, construction report, this synthesis,
  and a SHA256 manifest generated last).

## What is honestly incomplete or limited

This dataset construction draws only on the per-record raw evidence that
actually retains individual episode/task-instance identity (46 + 3,060
records across 5 source files). A substantial amount of Phase 4's
evaluation evidence — environment-generalization results, prediction
predictability verdicts, memory/adaptive-learning studies, agent-scope
routing — exists only as **aggregate, family/environment-level metrics**
with no retained per-episode join key, and could not be responsibly
expanded into individual dataset records without fabricating identifiers
that do not exist in the frozen evidence. This is disclosed exhaustively in
`PHASE5_2_DATASET_CONSTRUCTION_REPORT.md` §9 and
`PHASE5_2_DATASET_AUDIT.md`'s limitations section, and is the single
largest scope boundary of this release: **a future Phase 5.3 could extend
this dataset with record-level extraction from those aggregate sources only
if a future Phase-4-side change begins persisting per-episode identifiers
for them; this construction did not invent joins that the frozen evidence
does not support.**

The `outcome_class` field is an honest, additive resolution of a genuine
inconsistency between Phase 5.1's own narrative specification (which
mandates it) and its own machine-readable schema (which does not define
it) — flagged explicitly rather than silently patched into the frozen
schema file, which was never modified.

## Bottom line

Every mechanical validation that was run, passed, with zero violations in
every dimension actually checked. The dataset is honest about what it does
not cover rather than silent about it. Phase 4 and Phase 5.1 remain
byte-for-byte untouched by this work.
