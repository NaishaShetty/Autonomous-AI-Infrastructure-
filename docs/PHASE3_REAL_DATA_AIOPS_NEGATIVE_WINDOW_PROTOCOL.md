# AIOps KPI — Negative/Control Window Protocol (frozen before extraction)

**Status: FROZEN, version 1.0.0, 2026-08-13. Written and frozen BEFORE
any telemetry beyond the single already-validated day (`2020_04_11`)
was extracted, and before any window's actual telemetry values were
inspected.** This is a pure temporal/entity-membership rule — nothing
here depends on what any window's data looks like.

Companion to `docs/PHASE3_REAL_DATA_AIOPS_PROTOCOL.md` (the extraction
scope/timestamp/window protocol this builds on) and
`configs/aiops_extraction_protocol_v1.json`. Does not modify either.

## Why a fault-free-day discovery matters here

Applying the already-resolved `fault_onset` rule
(`docs/PHASE3_REAL_DATA_AIOPS_PROTOCOL.md` Step 2) to all 81 events
shows every event's onset falls on exactly one of 11 calendar dates:
`2020-04-11` (11 events) or one of the ten `2020-05-22`…`2020-05-31`
dates (70 events). The dataset's other 4 extractable telemetry days —
**`2020-04-20`, `2020-04-21`, `2020-04-22`, `2020-04-23`** — have **zero**
resolved fault onsets. This was determined by pure date arithmetic on
already-frozen onset timestamps, not by inspecting any telemetry
value, and is recorded here before extraction, not discovered by
looking for "convenient" negative examples after the fact.

## Eligible entities

The same **43 fault-eligible entities** used throughout this protocol
family: 8 `docker_*`, 13 `db_*`, 22 `os_*` (per
`data/metadata/aiops_kpi/schema_and_telemetry_findings.md`'s entity
roster). `csf_*`/`redis_*`/`osb_*` entities are **excluded** — they
were never fault-injection targets in this preliminary round (per the
fault log's `object` field, only ever `docker`/`db`/`os`), so using
them as "negative" examples would compare across entity *types*, not
just fault/no-fault states — a confound this protocol avoids by
construction, not by post-hoc filtering.

**Known limitation, stated not hidden:** 27 of the 43 fault-eligible
entities never appear in the actual 81-row fault log at all. It is
possible (not confirmed, not ruled out) that these entities were
excluded from injection for some operational reason unrelated to their
"normalcy" — this protocol cannot distinguish "never targeted because
representative of normal operation" from "never targeted for an
unrelated reason." Both fault-log entities (in their fault-free
periods) and never-targeted entities are included as candidate
negative sources; this limitation applies to the latter group.

## Window definition

- **Length: 20 minutes** — identical to the frozen positive
  (PRE-FAILURE) window, for direct comparability.
- **Grid construction:** each extractable telemetry day is partitioned
  into 72 fixed, sequential, non-overlapping 20-minute blocks aligned
  to day boundaries (`00:00–00:20`, `00:20–00:40`, …, `23:40–00:00`).
  Non-overlap is guaranteed by construction, not checked after the
  fact.

## Exclusion rule (per entity, per candidate block)

A candidate block `[w_start, w_start+20min)` for entity `E` is
**ineligible** if `E`'s own resolved fault onset falls within
**60 minutes before or after** `w_start` (i.e., excluded interval
`[w_start − 60min, w_start + 20min + 60min]`). Rationale for 60
minutes: comfortably exceeds the 20-minute PRE-FAILURE window plus the
5-minute DURING-FAILURE duration, with an added ~35-minute margin for
unmodeled recovery/aftereffects — a round, conservative number chosen
without reference to any observed recovery duration (none has been
measured; if one is measured later, this number is not silently
revised to fit it).

This rule is entity-specific: a block excluded for `docker_001` (near
one of its own faults) may still be eligible for `docker_002` on the
same day/time, since faults target one entity at a time.

Blocks on the 4 confirmed fault-free days require no exclusion check
per this rule (no fault onset exists to exclude against) but are still
subject to the eligible-entity restriction above.

## Overlap with positive windows

By construction, no candidate negative block can overlap a positive
window for the *same* entity (the exclusion rule above already removes
anything within 60 minutes of that entity's own fault onset, a strict
superset of the 20-minute positive window). No additional check is
needed, but the validation pass (separate document) verifies this
holds rather than assuming it.

## Natural population vs. sampled pool (two separate, both documented)

Per the "avoid artificial balance" instruction: this protocol reports
**both** a natural population size (the full eligible-grid count,
computed by date/entity/exclusion arithmetic alone, no telemetry
extraction required) and a separate, smaller, **sampled** pool that is
actually extracted and materialized — extracting telemetry for the
full natural population (tens of thousands of candidate blocks) before
any decision exists to use them would be unjustified extraction, not
a reproducibility improvement.

- **Natural population:** computed and reported in
  `data/audit/aiops_kpi/negative_window_natural_population.json`
  before any sampling.
- **Sampled pool** (frozen rule, decided here, not after inspecting
  the natural population's size):
  - Per-entity cap: **20 negative windows per entity** (round number,
    chosen for tractability, not tuned to any target ratio).
  - Selection: within each eligible entity, sort all its eligible
    candidate blocks lexicographically by `(date, block_start)`, then
    draw up to 20 via `random.Random(SEED=42).sample(...)` — same
    deterministic pattern as the Alibaba sampling scripts.
  - If an entity has fewer than 20 eligible blocks, all of its
    eligible blocks are taken (no shortfall padding from another
    entity).
  - **No selection may be based on inspecting that block's own
    telemetry values** — the grid, exclusion rule, and per-entity
    sample are fixed entirely from timestamps and entity IDs.

This yields an expected sampled-pool ceiling of `43 entities × 20 =
860` negative windows (fewer in practice wherever an entity has fewer
than 20 eligible blocks) against 81 positive windows — an
**imbalanced, not artificially 50/50**, pool (~10.6:1 at the ceiling),
which is reported alongside the natural population's true (much
larger) imbalance, not presented as "the" real-world prevalence.

## What negative windows must NOT be

Enforced by the rules above, restated explicitly per the brief's
checklist:
- Must not overlap a positive window (guaranteed by the 60-min
  exclusion, a strict superset of the 20-min positive window).
- Must not contain a known impending fault within the prediction
  horizon (guaranteed — a block within 60 min *before* a fault onset
  is excluded).
- Must not be a post-failure recovery window (guaranteed — a block
  within 60 min *after* a fault onset is excluded).
- Must not use information from after its own prediction cutoff (the
  block's own end time *is* its cutoff — nothing beyond it is used to
  select it).
- Must not be selected because telemetry "looks normal" (guaranteed —
  selection is timestamp/entity arithmetic only, performed before any
  telemetry for these days beyond `2020-04-11` was extracted).
