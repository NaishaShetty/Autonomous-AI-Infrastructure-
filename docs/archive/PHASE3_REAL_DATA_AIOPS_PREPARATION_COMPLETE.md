<a id="phase3-real-data-aiops-preparation-complete"></a>
# PHASE3 REAL DATA AIOPS PREPARATION COMPLETE
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_AIOPS_PREPARATION_COMPLETE.md`  
**Role:** AIOps real-data preparation completion record.

# AIOps KPI — Final Data Preparation Report

**Status: data preparation complete for the frozen 20-minute-window
scope. No Phase 3.1–3.6 evaluation run. Raw files unmodified (verified
by checksum, see below). Supplements — does not overwrite —
`docs/PHASE3_REAL_DATA_AIOPS_PROTOCOL.md`,
`docs/PHASE3_REAL_DATA_AIOPS_NEGATIVE_WINDOW_PROTOCOL.md`,
`data/metadata/aiops_kpi/schema_and_telemetry_findings.md`.**

---

## 1. Telemetry extraction

All 15 extractable daily archives (per
`configs/aiops_extraction_protocol_v1.json`) were processed:
`2020-04-11, 04-20, 04-21, 04-22, 04-23, 05-22…05-31`. No date was
added or dropped from the frozen list; no password/lock mechanism was
actually needed for this copy of the archive (the outer per-day zips
in `data/raw/aiops_kpi/`'s copy are directly readable — see below).

- **Platform metrics** (5 files/day) + **business metrics**
  (`esb.csv`) extracted **in full**, all 15 days — not filtered, per
  the frozen scope. Written to
  `data/processed/aiops_kpi/{platform,business}/`.
- **Call-traces** (6 files/day) stream-filtered to rows whose
  `cmdb_id` is one of the 43 fault-eligible entities AND whose
  timestamp falls inside a pre-registered window (positive or
  sampled-negative) — the window set was frozen from fault-log timing
  alone, *before* any trace content was read, so this is a
  computational-feasibility filter, not a results-driven one. Written
  to `data/processed/aiops_kpi/trace_windows/`. Verified by an
  independent re-check: **0 kept rows fall outside their scheduled
  window** (spot-checked in full on `2020-04-22`).
- Full per-day, per-file counts: `data/audit/aiops_kpi/extraction_report.json`.
- **Raw archive integrity:** `sha256sum` of
  `data/raw/aiops_kpi/AIOps挑战赛2020预赛数据.zip` re-verified
  unchanged (`0b50d8a6...5162dce`) after extraction.

### Correction to a prior assumption: no password layer needed

`docs/PHASE3_REAL_DATA_AIOPS_PROTOCOL.md` and
`configs/aiops_extraction_protocol_v1.json` both stated the 10
`2020-05-22`…`2020-05-31` dates were "password-locked" per the
dataset's own `passwd.txt`/`unzip_all.sh`/`sha256sum.txt`. On actual
extraction, **this copy of the archive does not have that lock layer**
— each day's outer zip (e.g. `AIOps挑战赛数据/2020_05_22.zip`) opens
directly with no inner `_lock.zip` and no password prompt. Whoever
originally staged this raw file for the project evidently already
merged/unlocked it before packaging. This is a factual correction, not
a silent one — the original documents' statements are left as written
(they were correct **about the dataset's own distribution
mechanism**, just not applicable to this particular staged copy).

### New finding: every daily archive covers only 00:00–05:59:59 local time

**Confirmed across all 15 days independently** (not a single-day
artifact): every extracted platform-metric file's timestamp range is
exactly `00:00:00`–`05:59:59` local (UTC+8), regardless of date. This
was not known or assumed in either prior protocol document — both
implicitly modeled a full 24-hour day (the negative-window grid used
72 20-minute blocks/day). It was discovered here, empirically, by
extraction — not guessed, not assumed, and it directly explains why
the majority of randomly-sampled negative-window candidates failed
telemetry-coverage validation (Section 3 below), and *why all 81 fault
events happen to fall inside this window* (organizers evidently only
ran/collected telemetry during a fixed daily 6-hour window, and only
injected faults inside it).

**This finding does not retroactively change the frozen 20-minute
window or the frozen negative-window construction rule** — per the
brief's explicit instruction not to alter a frozen protocol to obtain
more convenient data. It does mean the actual usable negative-window
population is smaller than the naive 45,911-candidate "natural
population" figure computed in
`docs/PHASE3_REAL_DATA_AIOPS_NEGATIVE_WINDOW_PROTOCOL.md` implied (that
figure assumed all 72 blocks/day were viable; only ~18/72 are, given
the true 6-hour coverage). A coverage-adjusted natural-population
estimate: `43 entities × ~15 usable days × 18 blocks × (fraction not
excluded)` ≈ roughly a quarter of the original 45,911 figure — i.e.
still in the low thousands, still far larger than what was sampled,
so this does not change the qualitative conclusion that positives are
rare relative to the natural population. The original 45,911 number is
left in its source document unedited, with this correction pointing to
it rather than replacing it.

---

## 2. Timestamp anomaly resolution (data-driven, not guessed)

Per your instruction to resolve conservatively using actual data:

| Issue | Prior status | New status | Evidence |
|---|---|---|---|
| Were `index 1–11` events actually injected into real telemetry? | UNRESOLVED (plausible from date-matching only) | **CONFIRMED** | `docker_003`'s `container_cpu_used` metric on `2020-04-11` shows a clean baseline (~1–2%) jumping to **98–100%** for ~5 minutes starting ~3 minutes after event `index=1`'s resolved onset (`2020-04-11 00:05`) — a textbook CPU-fault signature at the exact right entity, metric, and time. |
| Is `start_time` (not `log_time`) the real injection timestamp for `index ≥ 100`? | PROBABLE (date/structural evidence only) | **PROBABLE, now with direct signal support** | `docker_001`'s `container_cpu_used` on `2020-05-22` shows elevated values (up to 107%, vs. a noisier ~30-80% baseline) concentrated in the minutes following event `index=101`'s resolved onset (`2020-05-22 00:48`) — noisier than the April example (this entity/day has a higher baseline load) but directionally consistent. **Not independently checked for every fault category** — only `CPU fault`-type events were spot-checked, since `container_cpu_used` gives the cleanest single-metric signature; `network delay`/`network loss`/`db connection limit`/`db close` events were not signal-verified this pass. |
| `block=8` spans two different `start_time` calendar dates | UNRESOLVED | **Still UNRESOLVED** | No new evidence found; most plausibly a labeling inconsistency in the organizer's (manually-edited) spreadsheet. **Does not affect this protocol's correctness** — `block`/`log_block` are never used as the authoritative timestamp source, only `start_time`/`log_time` (per-row) are, and those remain valid and internally consistent regardless of the `block` grouping label's own inconsistency. |
| +6h `log_time`→`start_time` shift for `log_block∈{4,5}` | UNRESOLVED (pattern confirmed, cause unknown) | **Still UNRESOLVED** | No new evidence found. Same non-impact rationale as above — `start_time` itself (not the shift's explanation) is what this protocol relies on. |

**Conservative handling adopted:** all 81 events are retained and used
via the already-frozen `fault_onset` rule (`start_time` if present,
else `log_time`) exactly as documented previously — no event was
discarded, reinterpreted, or given a fabricated timestamp because of
the two still-unresolved items above.

---

## 3. Positive window validation

Script: `scripts/real_data/aiops_validate_positive_windows.py`.
Full results: `data/audit/aiops_kpi/positive_window_validation.json`.

**Result: 81/81 VALID.** Every positive window independently
re-derived from the raw fault log (catching any transcription bug —
none found), has exactly a 20-minute span, has ≥1 telemetry
observation from the object-appropriate metric family within the
window, has zero observations at or after the fault's own onset
inside that window (no post-failure contamination), and does not
overlap another event's onset for the same entity.

One implementation bug was caught and fixed during this step: an
early version of the validation script's "no post-onset
contamination" check scanned an entity's *entire day* of telemetry
rather than only the rows already confirmed to be inside the window,
which spuriously flagged all 81 windows as contaminated (since of
course telemetry exists somewhere later in the day). Corrected before
trusting the result — documented here rather than silently fixed.

---

## 4. Negative window validation

Script: `scripts/real_data/aiops_validate_negative_windows.py`.
Full results: `data/audit/aiops_kpi/negative_window_validation.json`
(includes a full rejection report for all 715 rejected candidates).

**Result: 145/860 VALID, 715 rejected.** Rejection breakdown: **all
715** rejections were `has_telemetry_coverage=False` (Section 1's
6-hour-coverage finding) — **zero** rejections were due to the
fault-exclusion or positive-overlap checks failing, confirming the
frozen exclusion-window construction logic (§Step 4 of the negative
protocol) was itself correctly built; the shortfall is purely a data-
availability constraint discovered only once extraction ran, not a
flaw in the sampling rule.

**No negative window was added, swapped, or re-sampled to compensate
for the low yield.** The 145 that passed are the final, honest
negative pool.

---

## 5. Final effective sample size

| Quantity | Count |
|---|---|
| Raw fault-log events | 81 |
| Qualifying positive windows (validated) | **81** (100%) |
| Unique positive-window entities | 16 |
| Candidate negative windows (frozen sampled pool) | 860 |
| Final valid negative windows | **145** (16.9%) |
| Unique negative-window entities | 43 |
| Entities appearing in both positive and negative pools | 16 |
| Entities only in the negative pool | 27 |
| **Total unique entities across both pools** | **43** |
| Positive events per entity | min 1 (`os_001`), median 5, max 10 (`docker_001`) |
| Negative windows per entity | min 2, median 3, max 7 (`docker_003`) |

**Independent unit:** entity (43 clusters), not window (226 total
positive+negative windows). A naive analysis treating 226 as i.i.d.
would overstate precision — any real evaluation must use
entity-clustered variance/bootstrap, or an entity-disjoint split for
any entity-generalization claim (`docker_001`'s 10 positives + 3
negatives cannot be split across train/test without leaking that
specific entity's baseline behavior across the split).

---

## 6. Updated power / feasibility assessment

Using the actual final population (n_pos=81, n_neg=145, total=226),
Hanley-McNeil AUROC-precision analysis (same method as
`scripts/real_data/alibaba_power_analysis.py`):

| Assumed AUROC | 95% CI half-width at n=226 |
|---|---|
| 0.55 | ±0.079 |
| 0.60 | ±0.078 |
| 0.65 | ±0.076 |
| 0.70 | ±0.074 |
| 0.75 | ±0.069 |
| 0.80 | ±0.064 |

Compare to Alibaba's main tier (n=10,000), which achieves ≈±0.02–0.03.
**AIOps remains EXPLORATORY, not confirmatory** — a ±0.07-ish AUROC CI
supports a directional read ("is there any detectable signal at all")
but not a precise estimate or a confident comparison against a
baseline.

| Planned experiment | Effective N | Updated verdict |
|---|---|---|
| Binary 20-min-window fault-vs-no-fault detection | 81 pos / 145 neg, 43 entity clusters | **EXPLORATORY** — now has an actual, real, non-hypothetical population (previous assessment could only note this required an undefined negative population); ±0.07 CI at best |
| 5-class fault-category classification | same per-class counts as before (5–31) | **UNDERPOWERED / INCONCLUSIVE-PRONE**, unchanged |
| Object-type (docker/os/db) classification | 49/20/12 positive events | **EXPLORATORY**, unchanged |
| Entity-level generalization | 43 entities, 16 with positives | **UNDERPOWERED**, unchanged, now with confirmed real per-entity window counts (median 3-5) reinforcing this |

No change was made to any window, entity list, or sampling rule after
seeing these numbers — this table reports what the already-frozen
protocol yielded.

---

## 7. Files created this pass

- `scripts/real_data/aiops_build_windows.py` (positive/negative window
  definitions — pure logic, run before any telemetry beyond
  `2020-04-11` existed)
- `scripts/real_data/aiops_extract_telemetry.py` (the extraction
  itself)
- `scripts/real_data/aiops_validate_positive_windows.py`
- `scripts/real_data/aiops_validate_negative_windows.py`
- `data/audit/aiops_kpi/{positive_windows,negative_window_natural_population,negative_windows_sampled,extraction_report,positive_window_validation,negative_window_validation}.json`
- `data/processed/aiops_kpi/{platform,business,trace_windows}/*.csv`
  (all provenance-tagged: `source_dataset`, `source_file`,
  `extraction_day`)
- `docs/PHASE3_REAL_DATA_AIOPS_NEGATIVE_WINDOW_PROTOCOL.md` (written
  in the prior turn, referenced not modified)
- This document.

---

## 8. Remaining unresolved issues

1. `block=8`'s two-date split — unexplained (no operational impact,
   §2).
2. The +6h `log_time` shift for `log_block∈{4,5}` — unexplained (no
   operational impact, §2).
3. Only `CPU fault`-category events were signal-verified against real
   telemetry; `network delay`/`network loss`/`db connection limit`/
   `db close` were not independently checked for a detectable
   signature.
4. The coverage-adjusted natural-population count (§1) is an estimate,
   not a re-run of the exact grid computation — if a future step needs
   the precise adjusted figure, `aiops_build_windows.py`'s grid
   construction would need a documented new version restricted to
   `00:00–06:00`, which was **not done here** (would count as altering
   the frozen protocol after seeing data, exactly what's prohibited).
5. 27 of the 43 fault-eligible entities never appear in the fault log
   at all — still an open question (noted originally in the negative-
   window protocol) whether this reflects genuine normalcy or an
   unrelated exclusion reason.

---

## Is AIOps now ready for the frozen Phase 3.1 real-data protocol?

**Yes, with its limitations stated plainly, not hidden:** a real,
validated, entity-clustered positive/negative population now exists
(81/145), every window has confirmed telemetry coverage, provenance is
preserved throughout, and the power ceiling is known and modest
(±0.07 AUROC CI). This is sufficient to support an **EXPLORATORY**
Phase 3.1 real-data evaluation on AIOps — not a confirmatory one, and
any Phase 3.1 protocol document should say so explicitly rather than
implying AIOps carries the same evidentiary weight as Alibaba's
much larger sample.

Per your instruction, **stopping here** — no Phase 3.1 run. Raw files
unmodified (checksum re-verified). Phase 3 frozen docs and Phase 4
untouched. Waiting for explicit authorization before Phase 3.1.
