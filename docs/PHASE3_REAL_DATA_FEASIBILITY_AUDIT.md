# Phase 3 Real-Data Replication — Dataset Feasibility Audit

**Status: IN PROGRESS — preliminary audit complete for all 3 currently
acquired datasets.** This pass audits the three datasets fully staged
under `data/raw/`: **AgentRx**, **AIOps KPI**, and **Alibaba GPU2020**
(now including `pai_sensor_table.tar.gz`, whose download completed
during this pass — audited below, all 7 of 7 known GPU2020 archives
are now present and covered). Alibaba 2017 and Google Cluster Data
were never acquired — their `data/raw/` subdirectories were removed
(see prior cleanup) and they are absent from this audit entirely, not
marked PENDING.

This pass is **read-only inspection**. No raw file was modified,
moved, renamed, or extracted-in-place. Where archive contents needed
inspection (CSV rows inside `.tar.gz`, files inside the AIOps `.zip`),
they were streamed/read in memory (`tarfile`/`zipfile` Python
modules, `tar -xOzf ... | ...`) without writing extracted output to
disk. No cleaning, imputation, deduplication, splitting, or feature
selection has been performed. Nothing here modifies Phase 3's frozen
surface (`PHASE3_FREEZE.md`) or touches Phase 4.

Every finding below is either directly observed from the files
(marked with counts/values) or explicitly marked **PENDING** where it
requires information not present in the files themselves (e.g.
official schema docs not fetched this pass, or archives — like the
AIOps per-day zips and Alibaba sensor table — not yet opened).
Nothing is guessed or filled in to make a dataset look more complete
than it is.

---

## Dataset D — Microsoft AgentRx

**Classification: REAL SYSTEM, EVALUATION-HARNESS ENVIRONMENT — not
organic production traffic, but not fault-injected either.** Doesn't
cleanly fit the audit's four buckets (NATURAL REAL-WORLD / REAL
SYSTEM-EXPERIMENTALLY INJECTED / SYNTHETIC / MIXED): trajectories are
genuine LLM-agent executions against real tools/environments
(Magentic-One benchmark tasks; tau-bench retail environment), so
failures are real agent behavior, not synthetic text — but they were
produced by running a benchmark harness, not captured from live user
traffic. Treat as **REAL SYSTEM (non-production, benchmark-harness
origin)** and do not present it as organic production evidence.

### 1–3. Existence, integrity, acquisition record

| File | Bytes | SHA-256 | Records |
|---|---|---|---|
| `magentic_dataset.jsonl` | 4,203,050 | `e2c697a9...c2179` | 58 |
| `magentic_one.jsonl` | 152,350 | `9bfa5629...c3518` | 44 |
| `tau_retail.jsonl` | 36,169 | `95729a0f...49d1a` | 29 |
| `tau_retail_dataset.jsonl` | 831,593 | `21852996...969bf` | 29 |

(Full checksums in `data/provenance/agentrx_download_provenance.md`.)
Source: `huggingface.co/datasets/microsoft/AgentRx` (main branch,
gated — access granted by user). Acquired 2026-08-13. All 4 files
parse as valid line-delimited JSON, 0 malformed lines in any file. No
official checksum manifest was found published alongside the dataset;
the SHA-256s above are our own acquisition-time record, not verified
against a publisher-supplied hash.

### 4. Archive/file structure

Two independent pairs, not a single unified schema:
- **Magentic pair**: `magentic_dataset.jsonl` (raw agent trajectories) +
  `magentic_one.jsonl` (failure/diagnosis annotations for a subset of
  those trajectories).
- **Tau-retail pair**: `tau_retail_dataset.jsonl` (raw trajectories) +
  `tau_retail.jsonl` (failure/diagnosis annotations).

### 5. Schema / field types

**Trajectory files** (`magentic_dataset.jsonl`, `tau_retail_dataset.jsonl`):
`trajectory_id` (str), `instruction` (str), `steps` (list of `{index,
substeps: [{sub_index, role, content}]}`). No timestamps anywhere.

**Annotation files** (`magentic_one.jsonl`, `tau_retail.jsonl`):
`trajectory_id` (str), `failure_summary` (str), `failures` (list of
`{failure_id, step_number, step_reason, failure_category,
category_reason, failed_agent}`), `num_failures` (int), `root_cause`
(dict: `{failure_id, reason_for_root_cause}`), `root_cause_failure_id`
(str), `root_cause_reason` (str). All 7 keys present in 100% of records
in both annotation files (no missing top-level keys).

Observed `failure_category` values (from samples, not a full-enum
scan): "Instruction/Plan Adherence Failure", "Invention of new
information" — full taxonomy not yet extracted.

### 6. Record counts

58 / 44 / 29 / 29 as above. (Earlier `wc -l` on `tau_retail_dataset.jsonl`
reported 28 due to a missing trailing newline on the last line; the
JSON-parse-based count of 29 is authoritative.)

### 7. Timestamps / temporal coverage

**None.** Only ordinal `index`/`sub_index` fields establish order
within a trajectory. **NOT EVALUABLE** for any wall-clock temporal
split, calendar-based drift analysis, or "unseen time period"
generalization test (Section 6/13 of the protocol). Only
trajectory-level entity-disjoint splits are meaningful here.

### 8. Identifiers / persistent entities

- Magentic pair joins directly on `trajectory_id`: **44/44 annotated
  IDs are a strict subset of the 58 trajectory IDs** (14 trajectories
  have no failure annotation — presumably unannotated or successful
  runs, not confirmed which). Zero duplicate IDs in either file.
- Tau-retail pair does **not** join directly: `tau_retail_dataset.jsonl`
  uses IDs like `"tau_retail_2"`, `tau_retail.jsonl` uses bare `"2"`.
  Verified: stripping the `tau_retail_` prefix gives a **full 29/29
  bijection**, zero orphans either direction. This mapping must be
  applied explicitly in any future join — it is not automatic.
- Each trajectory is its own entity; there's no shared cross-trajectory
  ID (e.g. no "agent" or "user" field), so entity-disjoint splitting
  reduces to trajectory-disjoint splitting.

### 9. Missingness

All declared top-level keys present in 100% of records, both
annotation files. Deeper value-level missingness (e.g. empty strings
nested inside `failures[]`) has not been scanned — flagged as a
follow-up before any cleaning rule is written.

### 10. Duplicates

Zero duplicate `trajectory_id` confirmed within each of the 4 files
individually (verified for magentic pair explicitly; tau-retail pair's
1:1 bijection after prefix-stripping implies the same).

### 11. Failure/anomaly labels

`failures[].failure_category` + `num_failures` is the label source.
Small taxonomy, not yet fully enumerated across all 73 annotated
trajectories.

### 12. Diagnosis / root-cause info

**Present** — uniquely among the three audited datasets, AgentRx has
an explicit `root_cause_failure_id` + `root_cause_reason` (free text)
pointing into the `failures[]` list. This is the strongest current
candidate for Phase 3.6 / H6 (diagnosis) evaluation.

### 13. Recovery / action / outcome info

**Not present as a field.** No "recovery attempted"/"recovery
succeeded" label. **NOT EVALUABLE for H7** (recovery safety) without
inferring recovery from raw trajectory steps (e.g. detecting a retried
action after a failure) — and if that inference is ever built, it must
be labeled explicitly as *inferred*, not treated as ground truth.

### 14. Post-outcome leakage fields

`failure_summary`, `failures`, `num_failures`, and all `root_cause*`
fields are demonstrably produced **after** observing the complete
trajectory (they reference step numbers throughout the entire run and
explain why the trajectory ultimately failed). **AVAILABLE ONLY AFTER
OUTCOME** — must never be used as decision-time input for a real-time
failure-prediction evaluation. They are only valid as (a) ground truth
for an after-the-fact diagnosis task, or (b) training targets for
offline classification restricted to trajectory content strictly
before the labeled failure step.

### 15. Phase 3 hypotheses this dataset can support

| Hypothesis | Evaluable? | Note |
|---|---|---|
| H1 representation | Possible | using pre-failure trajectory content as features |
| H2 drift | **NOT EVALUABLE** | no timestamps |
| H3 F-vs-B | Weakly possible | needs a real decision-time feature/label split |
| H4 attack-generalization | Weakly possible | same caveat |
| H5 complementarity | Weakly possible | same caveat |
| H6 diagnosis | **Best candidate of all 3 datasets** | explicit root_cause field |
| H7 recovery | **NOT EVALUABLE** | no recovery field |
| H8 authority | General | qualitative only |

### 16. Limitations

Extremely small n (87 trajectories total, 73 annotated, single root
cause each); two unrelated task domains (open-ended web/file agent
tasks vs. retail tool-use tasks) that should **not** be pooled without
justification; no timestamps; benchmark-harness origin, not production
traffic — must not be presented as organic real-world production
evidence in the final writeup.

---

## Dataset A1 — Alibaba GPU2020 (PAI trace) — all 7 archives

**Classification: NATURAL REAL-WORLD** (production PAI cluster, July–
~2 month window 2020, per Alibaba's public documentation). **7 of 7**
known archives now present and audited, including
`pai_sensor_table.tar.gz` (download completed this pass).

### 1–3. Existence, integrity, acquisition record

All 6 present archives pass `gzip -t` integrity checks. Internal
timestamps (from `tar -tzvf`) all read `2021-04-15 07:25`, consistent
across all 6 files — a plausible single-batch repackaging date, not
necessarily the collection date.

| Archive | Bytes (compressed) | SHA-256 | Inner CSV rows |
|---|---|---|---|
| `pai_group_tag_table.tar.gz` | 55,064,781 | `722fef30...23a14` | 1,055,032 |
| `pai_job_table.tar.gz` | 62,065,432 | `5aad7f7c...0a6cb0` | 1,055,501 |
| `pai_task_table.tar.gz` | 35,514,117 | `cd1d6dc3...499ac40e5` | 1,261,050 |
| `pai_instance_table.tar.gz` | 694,839,139 | `1bf1e423...97995ca06` | 7,522,002 |
| `pai_machine_metric.tar.gz` | 206,596,175 | `53ad9171...875892eef5` | 2,009,423 |
| `pai_machine_spec.tar.gz` | 30,449 | `cc0d38a4...1276c2d` | 1,897 |
| `pai_sensor_table.tar.gz` | 406,119,947 | `9a0b82e8...a69c7a0` | 3,033,232 |

No official checksum manifest was fetched/checked against this pass
(the 2017/2018 Alibaba traces are known to ship an MD5 manifest in
some releases; whether GPU2020 does was not verified this session) —
the SHA-256s above are our own acquisition-time record.

### 4. Archive/file structure

Each `.tar.gz` contains exactly one flat `.csv` of the matching name.
No nested directories, no embedded header row in any file.

### 5. Schema / field types

**No CSV in this trace ships a header row.** Alibaba documents column
names separately (repo README/schema doc), which was **not fetched
this session** — everything below is inferred from column position,
value patterns, and general familiarity with this trace family, and
must be cross-checked against the official schema before being relied
on for feature engineering:

- `pai_job_table.csv` (6 cols): `job_name` (confirmed unique key, see
  §8), 2 further hex-token columns of uncertain semantics (PENDING),
  `status` ∈ {Terminated, Failed, Running, Waiting}, `start_time`,
  `end_time`.
- `pai_task_table.csv` (10 cols): `job_name`, `task_name` (values like
  `tensorflow`, `worker`, `ps`, `PyTorchWorker`, `xComputeWorker` —
  high-confidence framework/role labels), `inst_num`, `status` (same 4
  values), `start_time`, `end_time`, `plan_cpu`, `plan_mem`,
  `plan_gpu`, `gpu_type` (values: MISC, T4, P100, V100, V100M32, or
  empty).
- `pai_instance_table.csv` (9 cols): `job_name`, `task_name`, then 3
  further hex-token columns (inst_name/worker_name/machine — exact
  order PENDING), `status`, `start_time`, `end_time`, a trailing hex
  token (PENDING).
- `pai_group_tag_table.csv` (5 cols, one column empty in every sampled
  row): low confidence overall — PENDING.
- `pai_machine_spec.csv` (5 cols): `machine_id`, a type label (`CPU`
  seen; other values not sampled), `cpu_num` (96 in sample), `mem_gb`
  (512 in sample), `gpu_num` (0 in CPU-only sample rows).
- `pai_machine_metric.csv` (12 cols): `worker_name`, `machine`,
  `start_time`, `end_time`, then ~8 numeric telemetry columns with
  partial nulls even on populated rows — column-level semantics
  PENDING.
- `pai_sensor_table.csv` (16 cols): `job_name`, `task_name` (values
  match task_table's role labels — `worker`, `tensorflow`,
  `PyTorchWorker`, `xComputeWorker`, `evaluator`,
  `OssToVolumeWorker`, `ps`, `OpenmpiWorker`, `TVMTuneMain`,
  `LeadingWorker`, confirming this table joins to task/instance level),
  `inst_name` (hex), `worker_name` (hex), `machine` (hex), `gpu_name`
  (`/dev/nvidiaN`, N∈0–7 observed), then **10 numeric GPU sensor
  metrics** — column-level semantics PENDING (values consistent with
  utilization/memory/power/temperature-style GPU telemetry, but exact
  field-to-name mapping not confirmed against official docs). **No
  `start_time`/`end_time` columns** — unlike `machine_metric`, this
  table appears to be one aggregate row per (job, instance, GPU
  device) rather than a time-windowed series.

### 6. Record counts

As in the table above (streamed line counts, robust since there's no
header row to account for).

### 7. Timestamps / temporal coverage

All `start_time`/`end_time` values are small numeric values (e.g.
`1053513.0`) — **relative seconds from an undocumented zero-point**,
not Unix epoch (values are far too small). Consistent with Alibaba's
documented convention for this trace family. **No absolute calendar
timestamp is recoverable from the files themselves** — only relative
ordering and elapsed duration. This means any "unseen time period"
split must use relative-time bucketing (e.g. first N% vs. last
(100−N)% of the trace by `start_time`), not calendar dates. `pai_sensor_table.csv` has **no timestamp columns at
all** — it cannot support any temporal split or drift analysis on its
own; it can only be joined to job/task/instance records (which do
carry `start_time`/`end_time`) to inherit a time context.

### 8. Identifiers / persistent entities

`job_name` confirmed as a **clean unique key** in `pai_job_table.csv`:
1,055,501 rows, 1,055,501 unique `job_name` values, 0 duplicates.
`task_table`/`instance_table` reference `job_name` as an expected
foreign key (many tasks per job, many instances per task) — not yet
cross-validated for referential completeness (whether every
`job_name` in task/instance tables exists in job_table). Machine IDs
appear across `machine_spec`/`machine_metric`/`instance_table` but
cross-table referential integrity is **not yet checked** — flagged as
required before any entity-disjoint (machine-level) split is frozen.
`pai_sensor_table.csv` additionally confirms **1,737 distinct
machines** and its `(job_name, inst_name)` pair is a **clean unique
key** (3,033,232 rows, 3,033,232 distinct pairs, 0 duplicates) — i.e.
one sensor row per (job, instance, GPU device) combination, not a
repeated time series.

### 9. Missingness

- `pai_job_table.csv`: **28.08%** of rows have empty `end_time`,
  corresponding exactly to `status` ∈ {Running, Waiting} (i.e. jobs
  still unresolved when the trace was cut off). This is **right-
  censoring**, not random missingness — per the audit rules these rows
  must be excluded from any binary failure/success label, not imputed
  and not treated as negative (success) examples.
- `pai_task_table.csv`: analogous censoring pattern (Running 9.16% +
  Waiting 0.29%).
- `pai_machine_metric.csv`: partial per-row nulls observed even among
  populated rows — needs a dedicated per-column missingness scan
  before cleaning; not done this pass.
- `pai_sensor_table.csv`: 14 of 16 columns 100% populated. Two numeric
  columns have small missingness (5,829 and 1,217 empty values out of
  3,033,232 rows respectively), and exactly **3 rows** have 6 of their
  10 metric columns empty simultaneously (verified — all
  `worker`/`OssToVolumeWorker` tasks) — consistent with a GPU device
  that reported no usable telemetry, not a random gap. Negligible in
  count (3/3,033,232) but still meaningful (sensor-unavailable)
  missingness, not to be imputed.

### 10. Duplicates

`job_name` uniqueness confirmed (0/1,055,501). Duplicate-key checks
for `(job_name, task_name)` in task_table and
`(job_name, task_name, inst_name)` in instance_table **not yet run** —
flagged PENDING (both are large files; a streaming check is feasible
but wasn't prioritized this pass). `pai_sensor_table.csv`'s
`(job_name, inst_name)` key is confirmed duplicate-free (see §8).

### 11. Failure/anomaly labels

`status` field. Raw distribution (all rows):

| Table | Terminated | Failed | Running | Waiting |
|---|---|---|---|---|
| job_table (n=1,055,501) | 69.38% | 24.31% | 5.96% | 0.35% |
| task_table (n=1,261,050) | 70.19% | 20.36% | 9.16% | 0.29% |

**Terminal-outcome-only failure rate** (excluding censored
Running/Waiting rows, which is the methodologically correct
denominator): job level = 256,555 / 988,910 = **25.94%**; task level =
256,762 / 1,141,835 = **22.49%**.

### 12. Diagnosis / root-cause info

**Not present.** `status=Failed` is a terminal outcome only — no error
code, no failure-reason string in any of the 6 audited tables.
**NOT EVALUABLE for H6** on this dataset (consistent with the
provisional call in the earlier audit draft).

### 13. Recovery / action / outcome info

**Not present as an explicit field.** No resubmission-linkage between
a Failed job and a later retry job. Any recovery signal here would
require heuristic entity matching (same user/similar resource request
shortly after a failure) — that would be an **inferred**, not
ground-truth, recovery label and must be documented as such if ever
attempted. **NOT EVALUABLE for H7** as currently understood.

### 14. Post-outcome leakage fields

`end_time` (and anything derived from it, e.g. duration =
`end_time - start_time`) is only knowable once a job/task has
terminated — **available only after outcome**, must be excluded from
decision-time input for any "predict failure before it happens" task.
`status` is the label itself. `pai_machine_metric.csv` rows are keyed
by a `(worker_name, start_time, end_time)` **reporting interval** —
whether a given metric row's interval precedes, overlaps, or follows
its task's failure point has **not yet been checked**, and must be
before any metric-derived feature is treated as decision-time-safe.
`pai_sensor_table.csv` carries no timestamp of its own (see §7) —
whether a given sensor row reflects the instance's full lifetime or
only a post-hoc summary computed after the instance terminated is
**undetermined** and must be resolved (via the official schema doc,
not guessed) before treating sensor features as decision-time-safe;
until resolved, sensor-table features should be treated as
**potentially leaking** rather than assumed safe.

### 15. Phase 3 hypotheses this dataset can support

| Hypothesis | Evaluable? | Note |
|---|---|---|
| H1 representation | Likely | task/instance/machine_metric/sensor features |
| H2 drift | Possible | only via relative-time splits, not calendar; sensor table has no time axis of its own |
| H3 F-vs-B | Likely | |
| H4 attack-generalization | Possible | synthetic perturbations applied on top of real features, same structural pattern as original Phase 3.5 |
| H5 complementarity | Likely | if a comparable failure-memory representation can be built; sensor table adds a richer per-GPU-device feature set for this |
| H6 diagnosis | **NOT EVALUABLE** | no cause field anywhere, including sensor table |
| H7 recovery | **NOT EVALUABLE** | no recovery field (or inferred-only, must be flagged) |
| H8 authority | General | qualitative |

### 16. Limitations

Single organization, single ~2-month window, one cluster's own
scheduling policy — external validity is bounded by that regime; no
absolute calendar time recoverable; no diagnosis/recovery fields;
sensor-table leakage status is unresolved (see §14) — must not be used
as a decision-time feature until that's settled;
several column semantics are position-inferred, not yet confirmed
against Alibaba's official schema doc (not fetched this session);
`machine_metric` needs a dedicated missingness pass; cross-table
referential integrity for machine/job IDs not yet verified;
`pai_sensor_table.tar.gz` still pending and **excluded** — do not
assume its content ahead of time.

---

## Dataset C — AIOps KPI (identified: CCF AIOps Challenge 2020, preliminary round)

**Classification: REAL SYSTEM / EXPERIMENTALLY INJECTED — not
NATURAL REAL-WORLD.** The fault log's own contents make this
unambiguous: faults (`CPU fault`, `network delay`, `network loss`,
`db connection limit`, `db close`) were deliberately injected into a
docker/db/os testbed for a competition, with organizers recording
exactly what they injected and when. This must not be presented as
organic production-failure evidence — it answers a different, still
valuable question ("can a system recover known-injected fault type
from telemetry"), not "does this system handle real unplanned
production failures."

### 1–3. Existence, integrity, acquisition record

Outer container: `AIOps挑战赛2020预赛数据.zip`, 3,084,639,115 bytes,
SHA-256 `0b50d8a6...5162dce`. `zipfile.testzip()` returned `None`
(CRC-OK for all central-directory entries) — container-level integrity
confirmed. The dataset was already staged by the user before this
audit began; the exact original download URL/date were not
independently re-verified this pass — recording what the archive
itself asserts (internal filenames identify it clearly as the CCF
AIOps Challenge 2020 preliminary-round release).

Uniquely among the 3 audited datasets, this one ships its **own
official checksum manifest** (`sha256sum.txt`, 10 entries, one per
`_lock.zip` daily archive) — not yet cross-verified against the actual
`_lock.zip` contents, since that requires extracting them from the
outer container first (deferred, per "do not extract yet").

### 4. Archive/file structure

31 entries in the outer zip:
- 20 per-day telemetry zips, `2020_04_11.zip` … `2020_05_31.zip` —
  some plain, some `_lock.zip` (password-protected; the 10 filenames
  in `sha256sum.txt` are all `_lock.zip` variants, implying at least
  those 10 dates are password-gated — which specific dates are locked
  vs. plain has not been fully reconciled).
- `data_release_v3.5/` — 9 metadata files: field manifest
  (`1数据字段清单.xlsx`), deployment architecture
  (`1应用部署架构清单.xlsx`), fault description
  (`0故障说明.xlsx`, plus a `~$0故障说明.xlsx` Excel lock/temp file —
  itself a small provenance clue that the source `.xlsx` was open in
  Excel when packaged), and per-layer metric dictionaries (DB, OS,
  DCOS, middleware, business — `.xlsx` except business, which is plain
  text).
- `故障整理（预赛）.csv` at the **top level**, not inside any per-day
  zip — the fault/failure ground-truth log, directly readable without
  a password.
- `passwd.txt` — the zip password for `_lock.zip` files, base64 + a
  `%uXXXX`-escaped Chinese string; decoded (for documentation only,
  **not applied to extract anything**) to `这是挑战赛初赛答案密码`
  ("this is the challenge preliminary-round answer password").
- `sha256sum.txt`, `unzip_all.sh` — the publisher's own verification
  and extraction scripts, confirming which files need the password.

### 5. Schema / field types

`故障整理（预赛）.csv` header (English, source's own typos preserved):
`index, object, fault_desrcibtion, kpi, name, container, log_time,
log_block, block, start_time, duration`.

- `object` ∈ {docker, db, os}
- `fault_desrcibtion` (fault category, free-text-ish but low
  cardinality — see §11)
- `kpi` — semicolon-delimited affected-metric names, present only for
  some fault types (structural, see §9)
- `name` — component instance id (`docker_003`, `db_007`, `os_018`)
- `container` — parent container id, present only for docker faults
- `log_time` — `YYYY/M/D H:MM`, no explicit timezone recorded
- `log_block` / `block` — integer bookkeeping fields, semantics
  **PENDING** (likely trace-round/window indices — not confirmed)
- `start_time` — a **second**, later timestamp distinct from
  `log_time` (see §7 — semantics unclear, PENDING)
- `duration` — constant `"5min"` for every row observed

One metric family's schema is directly documented in
`data_release_v3.5/2业务指标说明` (plain text): `serviceName,
startTime, avg_time, num, succee_num, succee_rate` — business/service
call metrics, 2-minute sampling interval. The other metric families
(OS, docker/DCOS, DB, middleware) have their own `.xlsx` dictionaries,
**not parsed this pass** (would require extraction + spreadsheet
parsing, deferred).

### 6. Record counts

`故障整理（预赛）.csv`: **81 data rows** (82 lines incl. header),
`index` values non-contiguous across 1–169 — **88 index values in
that range are genuinely absent from the file** (verified by full
parse, not a display artifact), e.g. 12–99 entirely missing. Reason
unconfirmed — plausibly reserved for a different data-release phase or
excluded from the preliminary round; not fabricated or filled in.
Zero duplicate `index` values among the 81 present. Per-day telemetry
row counts are **not available without extraction** — deferred.

### 7. Timestamps / temporal coverage

Fault log spans **2020-04-11 through 2020-05-31** (~7 weeks),
corroborated independently by the per-day zip filenames covering the
same range — **this is the only one of the 3 audited datasets with
recoverable absolute calendar time**, making it the only current
candidate for a genuine calendar-based temporal split. Timezone is
unstated — must be confirmed, not assumed, before use.

`start_time` values reuse dates that look like a **later occurrence**
of the same fault pattern (e.g. row index 100: `log_time`
2020-05-15, `start_time` 2020-05-22 — a 7-day offset) — this pattern
recurs across multiple rows and looks systematic, not random, but its
actual meaning (replay window? re-scoring date? a second injection of
the same fault?) is **not determinable from this file alone** and is
flagged as an open question likely answered by the unparsed `.xlsx`
fault-description file.

### 8. Identifiers / persistent entities

`name` (`docker_NNN`/`db_NNN`/`os_NNN`) recurs across multiple fault
rows — a persistent entity. `container` links docker faults to a
parent (`container_001`/`container_002`) — a second entity level. Any
entity-disjoint split must keep all rows for a given `name` together.

### 9. Missingness

`kpi` is empty for all `network delay`/`network loss`/`db close` rows
and populated only for `CPU fault`/`db connection limit` rows (30/81
missing overall) — **structural** (not every fault type maps to a
single KPI column), not random. `container` is empty for all
`db`/`os` rows, populated only for `docker` rows (32/81 missing) —
also structural (only docker faults are nested inside a container).
Both must be treated as meaningful missingness, not imputed, per the
audit rules.

### 10. Duplicates

Zero duplicate `index` values (verified, full parse, n=81). No other
duplicate-row check performed yet (e.g. exact-duplicate fault entries
by `name`+`log_time`) — not run this pass.

### 11. Failure/anomaly labels

The fault log itself is the label source. `fault_desrcibtion`
distribution (n=81): network delay 31, CPU fault 19, network loss 19,
db connection limit 7, db close 5. `object` distribution: docker 49,
os 20, db 12.

### 12. Diagnosis / root-cause info

`object` + `fault_desrcibtion` + `kpi` functions as ground-truth
diagnosis (what failed, how, which metric reflects it) — but this is
**fault-injection ground truth** (organizers control and log exactly
what was injected), not diagnosis inferred from symptoms by any
system. Evaluable as "recover the injected fault type/category from
telemetry," must be labeled as such, not presented as organic root-
cause diagnosis.

### 13. Recovery / action / outcome info

**Not present.** No field records mitigation or a return-to-normal
event beyond the fixed `duration=5min` injection window (which
describes the fault's own timing, not any recovery outcome).
**NOT EVALUABLE for H7.**

### 14. Post-outcome leakage

The fault log is ground truth by construction and must be used only
as `y`, never as a decision-time input feature. Any telemetry
timestamp at or after a given entity's `log_time`/`start_time`
potentially reflects the fault's *consequence* rather than a pre-fault
predictor — this constraint is not yet enforced in any pipeline
(there is no pipeline yet), but must be built into feature
construction once telemetry is extracted.

### 15. Phase 3 hypotheses this dataset can support

| Hypothesis | Evaluable? | Note |
|---|---|---|
| H1 representation | Likely | pending telemetry extraction |
| H2 drift | **Likely — best candidate of the 3** | only dataset with real absolute calendar span |
| H3 F-vs-B | Likely | |
| H4 attack-generalization | Likely | |
| H5 complementarity | Likely | |
| H6 diagnosis | Likely | injected-fault-category classification, not organic diagnosis — must be labeled as such |
| H7 recovery | **NOT EVALUABLE** | no recovery field |
| H8 authority | General | qualitative |

### 16. Limitations

This is injected-fault data on an apparent controlled/testbed
multi-tier application (docker/db/os/middleware), **not** organic
production failures — must never be presented as NATURAL REAL-WORLD
evidence. Most per-day telemetry (10+ of 20 daily zips) is password-
locked and unextracted; extraction is deferred pending explicit
authorization to proceed past the audit stage. Two `.xlsx` metadata
files likely resolve the `start_time`/`log_time` and `log_block`/
`block` ambiguities noted above but have not been parsed. Original
acquisition URL/date not independently re-verified (file was
pre-staged).

---

## Effective independent sample units (item 16 of this pass)

This is a preliminary read, not the formal power analysis the
authorizing brief requires before any Phase 3.1 real-data protocol
lock (Section 7 of that brief) — that still needs to happen as its own
step. But even at this audit stage, the *unit of independence* for
each dataset is already visible and worth recording now, since it
constrains what any later split/comparison can claim.

**AgentRx.** The independent unit is the **trajectory** — each is one
self-contained agent run, no shared entity across trajectories. Total
n=87 (58 magentic + 29 tau-retail), of which n=73 have failure
annotations (44 + 29). The two task domains are structurally different
(open-ended web/file-agent tasks vs. retail tool-use) and should be
treated as **two separate small samples** (n=44, n=29), not pooled to
n=73, unless a specific justification for pooling is made explicit in
the real-data protocol. Both are far below any conventional threshold
for a stable AUROC/AUPRC estimate — any comparison here should expect,
and report, wide confidence intervals, not treat a point estimate as
decisive.

**Alibaba GPU2020.** Multiple candidate units exist at different
granularities, and they are **not interchangeable**:
- Job-level: 1,055,501 jobs total; 988,910 with a decided terminal
  outcome (Terminated/Failed) — this is the right denominator for a
  job-level failure-prediction task; 256,555 positive (Failed) /
  732,355 negative (Terminated).
- Task-level: 1,141,835 terminal tasks; 256,762 positive / 885,073
  negative — **not independent of job-level units**, since many tasks
  share a job; any split must keep all tasks of a job on one side.
- Instance-level (7,522,002 rows) and sensor-level (3,033,232 rows)
  are nested even further inside task/job and are not independent
  sampling units for a job- or task-level claim — they're additional
  features/observations *about* a job or task, not additional
  independent examples of "did a job fail."
- Machine-level: 1,737 distinct machines (from sensor table) — far
  smaller than the job/task counts; any machine-level generalization
  claim (e.g. "unseen machine") is bounded by this much smaller n, not
  by the million-plus job/task counts.

**AIOps KPI.** The fault log gives **n=81 independent fault-injection
events** — the clear independent unit for any diagnosis/anomaly-
category claim on this dataset, and a small-sample regime by any
standard. A finer unit (entity × time-window, once telemetry is
extracted) would raise the nominal n but each window's label is still
derived from the same 81 events, so the *effectively independent*
count for any fault-category-level claim remains bounded near 81, not
the row count of the extracted telemetry. Per-fault-category counts
are smaller still (7–31 per category, see §11 of the AIOps section) —
several categories (`db close`: 5, `db connection limit`: 7) are too
small for a reliable per-class estimate on their own.

---

## Dataset-to-hypothesis matrix

Mapped to the original Phase 3 subphases (3.1 protocol lock / 3.2
representation matrix / 3.3 generalization / 3.4 baseline comparison /
3.5 attack-generalization / 3.6 diagnosis+recovery+decision), per your
requested format. "Evaluable" here means *the dataset contains the
information needed*, not that the comparison would be adequately
powered — see the sample-size notes above and the full Section 7
power analysis still to come.

| Dataset | 3.1 | 3.2 | 3.3 | 3.4 | 3.5 | 3.6 | Evidence available | Limitations |
|---|---|---|---|---|---|---|---|---|
| AgentRx | Yes | Partial | No | Partial | Partial | **Diagnosis: Yes** (best of the 3); Recovery: No | Explicit `root_cause`/`failure_category` fields; trajectory content as features | n≤73 (two domains, n=44/n=29); no timestamps → no drift/temporal-split claims; benchmark-harness origin, not production; no recovery field |
| AIOps KPI | Yes | Yes | **Yes** (best of the 3 — only real calendar span) | Yes | Yes | Diagnosis: Yes (**injected**-fault category, not organic); Recovery: No | Real ~7-week calendar span; 81 labeled fault-injection events across docker/db/os; two-tier entity structure (name→container) | Classification is REAL SYSTEM/EXPERIMENTALLY INJECTED, not natural — must not be presented as organic production evidence; n=81 events, several fault categories n<10; bulk telemetry (20 daily zips) still unextracted; `start_time`/`log_time` semantics unresolved |
| Alibaba GPU2020 | Yes | Yes | Partial (relative-time only) | Yes | Yes | Diagnosis: No; Recovery: No | ~1M jobs / ~1.14M terminal tasks / 7.5M instances / 3M sensor rows, real production cluster, clean unique keys confirmed at job and (job,inst) level | No absolute calendar time (relative seconds only); no diagnosis/recovery field anywhere across all 7 tables; several column semantics still position-inferred, not confirmed against official schema; sensor-table leakage timing unresolved; single org/cluster/window |

No cell above was filled in by assuming a dataset supports a claim
just because it's plausible — every "Yes"/"Partial"/"No" traces back
to a specific field (or specific absence of one) documented in the
per-dataset sections above.

---

## Updated open items

1. **Alibaba GPU2020 official schema doc** — not fetched this
   session; several column-position inferences above (job_table cols
   1–2, instance_table cols 2–4/8, group_tag_table, sensor_table's 10
   metric columns) need confirmation before they're used in any
   feature definition.
2. **`pai_sensor_table.tar.gz`** — now downloaded and audited (see
   Dataset A1 above). Its leakage timing (§14) is still unresolved and
   needs the official schema doc to settle.
3. **AIOps per-day telemetry** — 20 daily zips (some password-locked,
   password identified but not applied) remain unopened; the actual
   KPI time series (the bulk of this dataset's evidentiary value) is
   still unaudited. Needs explicit go-ahead to extract before I do,
   since extraction is a bigger step than the read-only peeking done
   so far.
4. **AIOps `.xlsx` metric/field dictionaries** — unparsed; would
   resolve several PENDING schema questions, including the
   `start_time` vs `log_time` ambiguity.
5. **Formal sample-size/power analysis** (Section 7 of the authorizing
   brief) — the "effective independent sample units" above is a
   preliminary read for this audit, not that formal analysis; it still
   needs to be done as its own step before the Phase 3.1 real-data
   protocol is frozen.
6. No further AgentRx-side open items beyond the small-n/domain-
   pooling caveat already noted.

Per your instruction, **stopping here** — no cleaning, splitting,
feature selection, model tuning, imputation, deduplication, outlier
removal, normalization, feature engineering, merging, or Phase 3.1–3.6
evaluation has been run. Phase 3 frozen docs are untouched, Phase 4
was not touched, and Alibaba 2017 / Google Cluster remain excluded
(not acquired). Waiting for explicit authorization before proceeding
to final cleaning or evaluation.
