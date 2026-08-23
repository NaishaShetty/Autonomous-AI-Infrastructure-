<a id="phase3-real-data-aiops-protocol"></a>
# PHASE3 REAL DATA AIOPS PROTOCOL
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_AIOPS_PROTOCOL.md`  
**Role:** AIOps 2020 real-data extraction/evaluation protocol.

# AIOps KPI (CCF AIOps Challenge 2020) — Extraction Protocol & Temporal Model

**Status: protocol-design document. No Phase 3.1–3.6 evaluation run.
No full 20-day telemetry extraction performed. This document
supplements — and does not overwrite or contradict —
`data/metadata/aiops_kpi/schema_and_telemetry_findings.md`,
`docs/PHASE3_REAL_DATA_CLEANING_REPORT.md`, and
`docs/PHASE3_REAL_DATA_FEASIBILITY_AUDIT.md`. Where this document
resolves something the prior docs left open, it says so explicitly and
points back to the prior text rather than deleting it.**

Machine-readable protocol: `configs/aiops_extraction_protocol_v1.json`
(frozen alongside this document, same version/date).

---

## Step 1 — What was already established (review, not re-derived)

Confirming against `data/metadata/aiops_kpi/schema_and_telemetry_findings.md`:

| Item | Status per prior doc | Confirmed here? |
|---|---|---|
| 81 fault-log events, 0 duplicates, 0 malformed | CONFIRMED | Unchanged |
| Tall/long telemetry format (`itemid,name,bomc_id,timestamp,value,cmdb_id`) | CONFIRMED (real data) | Unchanged |
| Metric sampling rates (60s dominant, 120/300/3600s subset) | CONFIRMED (official docs) | Unchanged |
| Timestamps = Unix epoch ms, real absolute calendar time | CONFIRMED (real data, day-label match) | Unchanged |
| `cmdb_id` = entity ID, matches fault log's `name` | CONFIRMED | Unchanged |
| Business metrics (`esb.csv`), 2-min window | CONFIRMED | Unchanged |
| Distributed traces, 6 files, `success`/`elapsedTime` fields | CONFIRMED (real data) | Unchanged |
| `success=False` real, non-trivial rate (0.37% on sampled day) | CONFIRMED (real data) | Unchanged |
| Fault-log fields = ground truth by construction | CONFIRMED | Unchanged |
| `log_time`/`start_time`/`log_block`/`block` relationship | **UNRESOLVED** (partial) | **RESOLVED this pass — see Step 2** |

Nothing above is repeated in redundant detail below; see the source
doc for full context.

---

## Step 2 — Fault-log timestamp reconciliation

### Confirmed (not assumed): the block↔calendar-date correspondence

All 70 events with `index ≥ 100` were re-parsed and cross-tabulated.
**Result:** `block` corresponds almost exactly to the actual calendar
date carried in `start_time`:

| block | start_time date |
|---|---|
| 1 | 2020-05-22 |
| 2 | 2020-05-23 |
| 3 | 2020-05-24 |
| 4 | 2020-05-25 |
| 5 | 2020-05-26 |
| 6 | 2020-05-27 |
| 7 | 2020-05-28 |
| 8 | 2020-05-29 **and** 2020-05-30 (see exception below) |
| 10 | 2020-05-31 |

These 9 dates (block values 1–8, 10 — **no `block=9` value appears
anywhere in the 81-row fault log**) are **exactly** the 10 dates whose
telemetry ships as password-protected `_lock.zip` archives (per
`sha256sum.txt`, cross-referenced against the feasibility audit) —
i.e. the scored preliminary-round evaluation days.

**Exception, reported honestly, not smoothed over:** `block=8` covers
*two* different `start_time` calendar dates (2020-05-29, tied to
`log_block=8`; 2020-05-30, tied to `log_block=6`). This is inconsistent
with a clean 1:1 block→date mapping and was **not** resolved further —
most plausibly a labeling inconsistency in the organizer's own
(manually-edited — see the `~$0故障说明.xlsx` Excel lock file found in
the archive, itself evidence of manual editing) spreadsheet, but this
is speculation, not a documented fact, and is flagged as such.
`start_time` itself (not `block`) is used as the authoritative
timestamp in this protocol, so this exception does not block using
these events — it only means `block`/`log_block` cannot be trusted as
a clean grouping key on their own.

### Confirmed: time-of-day is preserved from `log_time` to `start_time`

59 of 70 (`index ≥ 100`) rows have **identical** hour:minute between
`log_time` and `start_time` (only the calendar date differs). The
remaining 11 rows (all sharing `log_block ∈ {4, 5}`) show a
**consistent, uniform +6:00 shift** (e.g. `log_time` 2020-04-23 18:17
→ `start_time` 2020-05-24 00:17), not random drift. The existence of a
clean, deterministic shift (rather than scattered noise) supports
`log_time`/`start_time` being genuinely related by a systematic
transformation for this subset — but *why* it's 6 hours specifically
(rather than 0, consistent with everything else) was **not**
determined and is not asserted as understood; documented as an
observed, reproducible pattern, not a fully explained one.

### Confirmed (well-supported, not certain): interpretation of `log_time` vs. `start_time`

Putting the evidence together:
- `index 100–169`: `start_time` (May 22–31) lands exactly on the 10
  scored/locked telemetry days; `log_time` (spanning April 11 – May
  15) does not. The natural reading: **`start_time` is the actual
  fault-injection timestamp in the scored telemetry corpus**; `log_time`
  is a reference to when the *same fault pattern* was originally
  logged/templated, on an earlier occasion, and is not itself a
  telemetry-alignment timestamp for these rows.
- `index 1–11`: no `start_time` at all; `log_time` dates are all
  2020-04-11 — which is **exactly the one unlocked day already
  extracted and confirmed to contain real telemetry**
  (`data/intermediate/aiops_kpi/2020_04_11.zip`, per the cleaning
  report). The natural reading: **for these 11 rows, `log_time` *is*
  the actual fault-injection timestamp**, since April 11 is itself a
  real (unlocked, directly usable) telemetry day, with no separate
  "replay" step needed.

**Confidence level: well-supported by three independent, mutually
consistent lines of evidence (block↔locked-day correspondence,
preserved time-of-day, and index-1–11-dates↔unlocked-day match) — but
not verified by, e.g., organizer confirmation or a written spec
statement of this exact mechanism. Treated as CONFIRMED for protocol
purposes given the strength and consistency of the internal evidence,
with the residual uncertainties (block=8 split, the +6h shift's cause,
whether index 1–11 were truly scored) stated plainly above rather than
hidden.**

### Resolved onset timestamp rule (frozen)

```
fault_onset(event) = start_time  if start_time is non-empty
                    = log_time   otherwise (index 1-11 only)
```

This gives all 81 events a single, fully-parsed, real calendar
datetime, ranging 2020-04-11 00:05 to 2020-05-31 05:48.

---

## Step 3 — AIOps prediction/diagnosis temporal model

```
        PRE-FAILURE              DURING-FAILURE        POST-FAILURE
  |------------------------|--------------------|----------------------|
  T0                  fault_onset          fault_onset+5min      (unbounded)
  (onset - WINDOW)                         (documented duration
                                             is a fixed 5min for
                                             every one of the 81
                                             events)
```

- **T_failure** = `fault_onset` as resolved above.
- **PRE-FAILURE** = `[fault_onset − WINDOW, fault_onset)` — the only
  region legitimately usable as **predictive** input. `WINDOW` is
  fixed in Step 4 below.
- **DURING-FAILURE** = `[fault_onset, fault_onset + 5min)` — the
  documented injection duration. Telemetry in this window reflects the
  fault already happening; usable only for **diagnosis**, never
  prediction.
- **POST-FAILURE** = everything after `fault_onset + 5min`. Usable
  only for **diagnosis** (e.g. "how did the system recover," if
  recovery telemetry is later extracted) — never as a predictive input
  for the same event.

**Rule enforced by this protocol:** any predictive (failure-before-it-
happens) experiment may draw features **only** from PRE-FAILURE.
DURING/POST-FAILURE telemetry may be used **only** in an explicitly
labeled diagnosis experiment, never mixed into the same feature set as
a prediction experiment. This mirrors, at the AIOps level, the same
rule already frozen for Alibaba in
`docs/PHASE3_REAL_DATA_ALIBABA_SENSOR_LEAKAGE_GATE.md`.

---

## Step 4 — Extraction window (frozen, chosen from timing structure, not performance)

All decisions below come from the **observed fault-event timing
structure**, computed once, before any model or metric existed to
optimize against:

- Global minimum gap between any two consecutive fault onsets (sorted
  across all 81 events): **25.0 minutes**. 0/80 consecutive gaps are
  below 25 minutes; the next-smallest gaps are a large cluster at
  exactly 30.0 minutes.
- Minimum per-entity (same `name`) consecutive gap: **30.0 minutes**.
- 50/80 (62.5%) of consecutive gaps are under 45 minutes — a window
  that large would risk absorbing a neighboring fault's effect for a
  majority of events.

**Frozen primary window: 20 minutes pre-failure.**
`T0 = fault_onset − 20min`. This is **strictly inside** the observed
25-minute global minimum gap (5-minute safety margin), so it is
contamination-free for essentially the entire event population — no
event's 20-minute PRE-FAILURE window can include another event's
DURING/POST-FAILURE period. At the dominant 60-second metric sampling
rate this yields **up to 20 observations per metric per entity**;
slower-cadence metrics (300s/600s/3600s — see the metric dictionary)
yield proportionally fewer (down to 0–1 observations for hourly
metrics in a 20-minute window) — this is a real, stated limitation,
not smoothed over by extending the window.

**Frozen DURING window:** `[fault_onset, fault_onset+5min)` — fixed by
the dataset itself (every event's documented `duration` is `5min`),
no design choice involved.

**Explicitly NOT frozen as a default: an extended (e.g. 60-minute)
pre-failure context window.** A 60-minute window would only be
contamination-free for ~51/81 events (62%); for the rest it would
silently blend in a neighboring fault's telemetry. If a longer-context
experiment is wanted later, it must (a) be restricted to the subset of
events with a ≥60-minute preceding gap, explicitly computed and
listed, or (b) individually truncate each event's window to its actual
preceding gap. **Neither is decided or built here** — flagging the
option without picking it, per the "do not create multiple windows and
keep whichever performs best" instruction; if pursued, the exact rule
must be frozen before it's used, same as the primary window was.

**No window was chosen, adjusted, or discarded based on any
preliminary evaluation — no evaluation of any kind has been run
against AIOps telemetry.**

---

## Step 5 — Entity/metric/trace scope (inclusion/exclusion table)

| Data type | Entity level | Pre-failure usable? | Prediction | Diagnosis | Reason |
|---|---|---|---|---|---|
| Platform/infra metrics (`os_linux`, `db_oracle_11g`, `mw_redis`, `dcos_container`, `dcos_docker`) | host/db/middleware/container (`cmdb_id`) | Yes, within the frozen 20-min pre-window | **Yes** | Yes | Genuine pre-outcome telemetry; timestamped, entity-indexed, sampling rate known |
| Business metrics (`esb.csv`) | service (`serviceName`) | Yes, within pre-window (2-min native granularity) | **Yes** | Yes | Same reasoning; coarser granularity (2-min windows, not point samples) |
| Call-trace fields EXCEPT `success`/`elapsedTime` (`callType`, `traceId`, `cmdb_id`, timestamps, entity/service identifiers) | call | Yes, within pre-window | **Yes** | Yes | Structural/identifying fields, not an outcome |
| Call-trace `success`, `elapsedTime` | call | **No**, for predicting that same call's own outcome | **No** (as same-call input) / **Yes** (as an aggregated PRE-window feature, e.g. "% failed calls in the preceding 20 min," which does not use any individual call's own future-relative outcome) | **Yes** | A call's own outcome is what would be predicted — using it as that call's input is circular; using PAST calls' aggregated outcome rate as a feature for a LATER prediction target is legitimate and does not leak |
| Fault log: `object`, `fault_desrcibtion`, `kpi`, `name`, `container` | fault event | No | No | **Yes / label** | Ground truth by construction (organizer-injected) |
| Fault log: `log_time`, `start_time`, `log_block`, `block` | fault event | No (as features) | No | Used only to draw the T0 cutoff | Define the label's timing, not an observable signal |
| Deployment architecture (`1应用部署架构清单.xlsx`: entity→container mapping) | entity | Yes (static) | Yes | Yes | Static topology, never leaking |
| Metric/field dictionaries (units, sampling rate, `bomc_id`) | n/a | Yes (static, defines schema) | Yes (as metadata, not a feature itself) | Yes | Reference data, not an observation |

**Excluded entirely from this protocol's initial scope:** the 5
`.xlsx` per-tech-stack metric catalogs' full contents beyond what's
already extracted into the schema-findings doc (already sufficient for
the field dictionary; no further xlsx parsing planned). The 20-day
telemetry corpus beyond `2020_04_11` (already-validated sample day) —
not extracted until this protocol is explicitly authorized to run.

---

## Step 6 — Event-level independence / effective N

- **81 raw fault-log rows**, but these are **not 81 independent
  samples** in the sense of arising from 81 independent underlying
  systems or conditions:
  - Only **16 distinct entities** (`name`) are targeted across all 81
    events (`docker_001` alone accounts for 10; `db_003`/`docker_006`
    7 each; full distribution in
    `configs/aiops_extraction_protocol_v1.json`). 15/16 entities have
    ≥2 fault events.
  - Object-type split: `docker` 49, `os` 20, `db` 12 — the 5
    fault-category labels are unevenly distributed (`network delay`
    31, `CPU fault` 19, `network loss` 19, `db connection limit` 7,
    `db close` 5).
  - No two events overlap in time (minimum gap 25 min, fixed 5-min
    duration) — so events are **temporally** independent (no double-
    counting the same incident), but repeated faults on the same
    entity are **not statistically independent draws** from a
    population of entities — an entity's baseline behavior, hardware,
    or configuration is a shared confound across its own repeated
    events.
- **Recommended clustering structure for any variance/power
  estimate:** cluster by `name` (16 clusters), not treat n=81 as 81
  i.i.d. observations. A naive n=81 analysis would understate
  uncertainty.
- **Effective N is honestly smaller than 81** — bounded below by 16
  (entity clusters) and above by 81 (raw events), with the true
  effective value somewhere between depending on how much between-
  entity vs. within-entity variance the eventual model captures. This
  protocol does not pick a single number to paper over that — it
  requires any future AIOps power/CI computation to report results
  **both** ways (naive n=81 and entity-clustered) rather than picking
  the more favorable one.

---

## Step 7 — What can realistically be powered

Applying the same class of Hanley-McNeil AUROC-precision reasoning
used for Alibaba (`scripts/real_data/alibaba_power_analysis.py`), but
honestly reporting what n=81 (or effective n≈16–81) can support:

| Planned experiment | Effective N | Verdict |
|---|---|---|
| Binary "any fault vs. no fault" detection, entity×window level | Requires defining a negative (non-fault) window population — **not yet constructed**; even optimistically pairing each of 81 positive windows with matched negatives gives n≈162 raw / ≈32 entity-clustered | **UNDERPOWERED / EXPLORATORY** — even at the generous end this is far below the ~3,500+ Alibaba needed for ±0.02 AUROC precision |
| 5-class fault-category classification | Per-class n = 5 (`db close`) to 31 (`network delay`) | **UNDERPOWERED / INCONCLUSIVE-PRONE** for the rare classes (`db close` n=5, `db connection limit` n=7) — any per-class metric on these will have enormous confidence intervals; only the two largest classes (`network delay` n=31, `CPU fault`/`network loss` n=19 each) could support even exploratory per-class estimates |
| Object-type (docker/os/db) classification | n = 49/20/12 | **EXPLORATORY** — 3-way, moderate imbalance, still well below any AUROC-precision target computed for Alibaba |
| Entity-level generalization ("unseen entity") | 16 entities total, ≤15 with multiple events to split from | **UNDERPOWERED** — leave-some-entities-out at this scale cannot support a confident generalization claim, only a directional/qualitative one |
| Cross-dataset comparison of AIOps vs. Alibaba findings | n/a (different populations) | Valid only as a **qualitative** consistency check ("did the same broad pattern appear"), never a joint statistical test |

**No AIOps hypothesis in this dataset should be framed as
confirmatory.** Every AIOps-based Phase 3.1-equivalent experiment
should be pre-labeled **EXPLORATORY**, and any negative/null/
inconclusive result must be reported as such, not as evidence of
absence.

---

## Step 8 — Frozen extraction protocol

See `configs/aiops_extraction_protocol_v1.json` for the exact,
versioned, machine-readable rules. Summary:

- **Fault events included:** all 81 (no cherry-picking); each tagged
  with its resolved `fault_onset`, `resolution_confidence` (see Step
  2), and cluster id (`name`).
- **Eligibility for a PREDICTION-framed experiment:** an event is
  eligible only if its full 20-minute PRE-FAILURE window falls within
  an extracted, available telemetry day. Since only `2020-04-11` is
  extracted so far, **only events whose PRE-FAILURE window is fully
  contained in `2020-04-11` are currently eligible** — from the fault
  log, that's `index 1–11` only (11 events, all with `log_time` on
  2020-04-11). This is a real, current constraint, not a future one —
  stated plainly so nobody assumes 81 events are already usable.
- **Telemetry dates/files:** for a full-scope future extraction (not
  authorized yet): all 20 daily archives, all 3 telemetry families
  (platform, business, trace) at their native schema — no metric or
  trace file excluded a priori (per the Step 5 inclusion table, only
  the fault-log's own ground-truth fields and same-call outcome
  fields are excluded as features).
- **Entity filtering:** none — extract all `cmdb_id`s present in a
  given day's files (not restricted to only the 16 fault-targeted
  entities), so that non-faulted entities are available as a
  comparison/negative population if a future step needs one.
- **Timestamp conversion:** platform/business/trace timestamps are
  already Unix epoch ms — convert to UTC+8 (`Asia/Shanghai`) for
  human-readable alignment against the fault log's local-time
  `log_time`/`start_time`; **preserve the original epoch-ms value
  alongside** the converted one, never overwrite it.
- **Event-to-telemetry alignment:** join on `cmdb_id == fault_log.name`
  and `telemetry.timestamp ∈ [fault_onset − 20min, fault_onset)` for
  PRE-FAILURE, `[fault_onset, fault_onset+5min)` for DURING.
- **Missing telemetry handling:** if an entity/metric has zero
  observations in a window (e.g. an hourly metric in a 20-min window),
  record explicit `MISSING`/count=0 — never impute a value.
- **Overlapping events:** none exist under the frozen 20-minute window
  (by construction, see Step 4) — no overlap-resolution rule is
  needed at this window size; if a future longer window is pursued,
  an explicit overlap rule must be frozen first (not decided here).
- **Independent unit:** fault event (`index`), with entity (`name`) as
  the required clustering variable for any variance estimate (Step 6).
- **Provenance:** every extracted telemetry row keeps `source_file`
  (the daily zip + inner CSV path), `source_dataset="AIOps KPI"`,
  original epoch-ms timestamp, and the `fault_log.index` it was
  extracted for (if any) — no row is stripped of its origin.
- **Determinism:** extraction is a pure filter (entity + time-window
  membership) with no randomness — fully reproducible from the frozen
  rules above and the raw zip's own checksum.

**This protocol is frozen but NOT yet executed against the remaining
19 daily archives.** Execution requires separate authorization per
Step 9's explicit instruction.

---

## Step 9 — Not extracted

Confirmed: no additional telemetry beyond the already-extracted
`2020_04_11` day was pulled in this pass. The remaining 19 days
(several password-locked) remain unextracted, pending authorization.

---

## Step 10 — Unified benchmark preservation (forward-looking only, not built)

For any future extraction, each output record will carry:
`source_dataset="AIOps KPI (CCF AIOps Challenge 2020)"`,
`source_file`, `cmdb_id` (native entity id, not remapped to Alibaba's
`job_name`/`machine` conventions), native epoch-ms timestamp (plus a
converted UTC+8 field), `fault_log_index` (native event id, when
applicable), and explicit `MISSING` markers for any Alibaba-style
field (e.g. `recovery_action`) that AIOps does not itself provide. No
common schema is forced across AIOps and Alibaba/AgentRx at this
stage.

---

## Deliverables produced this pass

1. Timestamp reconciliation — this document, Step 2.
2. Temporal model — Step 3.
3. Inclusion/exclusion table — Step 5.
4. Independence/effective-N analysis — Step 6.
5. Power/feasibility assessment — Step 7.
6. Frozen extraction protocol — Step 8 + `configs/aiops_extraction_protocol_v1.json`.
7. Updated hypothesis assessment — see table below.
8. Unresolved issues — see below.

### Updated AIOps row for the dataset-to-hypothesis matrix

Supersedes (adds detail to, does not contradict) the AIOps row in
`docs/PHASE3_REAL_DATA_CLEANING_REPORT.md` §18:

| Dataset | 3.1 | 3.2 | 3.3 | 3.4 | 3.5 | 3.6 | Independent unit | Effective N | Notes |
|---|---|---|---|---|---|---|---|---|---|
| AIOps KPI | Yes, protocol now frozen | Yes, but EXPLORATORY (Step 7) | Yes — real absolute time confirmed | Yes, EXPLORATORY | Yes, EXPLORATORY | Diagnosis: Yes (injected-category); Recovery: No | fault event, entity-clustered (16 clusters) | 81 raw / effectively 16–81 depending on clustering; currently only 11 events (index 1–11) have their PRE-FAILURE window inside already-extracted telemetry | Timestamp semantics now resolved with high confidence; extraction scope frozen but not executed beyond 1 day |

### Unresolved issues (explicit, not hidden)

1. `block=8`'s split across two calendar dates (2020-05-29/30) — not
   explained, only documented.
2. The +6-hour `log_time`→`start_time` shift for `log_block ∈ {4,5}`
   — pattern confirmed, cause not determined.
3. Whether `index 1–11` were genuinely part of the *scored* evaluation
   or an unscored preview/template batch — plausible but not certain.
4. No negative (non-fault) window population has been defined yet —
   required before any binary detection framing can move past
   "EXPLORATORY."
5. 19 of 20 daily telemetry archives remain unextracted.
6. The 5 per-tech-stack `.xlsx` metric dictionaries' full row-by-row
   catalogs (beyond what's already summarized) were not exhaustively
   parsed (merged-cell issues noted previously stand).

---

## Is AIOps now ready for inclusion in the frozen Phase 3.1 real-data protocol?

**The AIOps-specific questions this task was scoped to answer are
resolved**: timestamp semantics (high confidence), temporal model
(frozen), extraction window (frozen, evidence-derived), inclusion/
exclusion rules (frozen), independence structure (documented, honestly
smaller than the raw row count suggests), and power expectations
(every AIOps hypothesis pre-labeled EXPLORATORY, not confirmatory).

**Not yet ready for an evaluation-scale protocol**, because: (a) only
one telemetry day is extracted, giving only 11 currently-eligible
predictive events; (b) no negative-window population is defined; (c)
several minor semantic gaps remain (block=8, the 6h shift). These are
exactly the kind of items a Phase 3.1 protocol document itself should
enumerate as open before evaluation, rather than silently resolving by
extracting everything now.

Per your instruction, **stopping here** — no Phase 3.1 run, no further
telemetry extraction, Phase 3 frozen docs and Phase 4 untouched, raw
files unmodified. Waiting for explicit authorization before extracting
the remaining 19 days or beginning Phase 3.1.
