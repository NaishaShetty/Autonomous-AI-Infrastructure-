<a id="phase3-real-data-cleaning-report"></a>
# PHASE3 REAL DATA CLEANING REPORT
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_CLEANING_REPORT.md`  
**Role:** Real-data cleaning report (Alibaba/AIOps/AgentRx).

# Phase 3 Real-Data Replication — Cleaning, Sampling & Preparation Report

**Status: preprocessing stage complete for what was authorized this
pass. No Phase 3.1–3.6 evaluation has been run. Phase 3's frozen
results (`docs/PHASE3_FREEZE.md`) and Phase 4 are untouched.** This
report is a new, separate artifact — "Phase 3 Real-Data Replication,"
not "corrected Phase 3."

All raw files under `data/raw/` were re-verified byte-identical
(SHA-256) to their originally recorded checksums before and after this
pass — nothing under `data/raw/` was modified, moved, renamed, or
extracted in place. All derived artifacts live under
`data/intermediate/`, `data/processed/`, `data/audit/`,
`data/metadata/`, `data/provenance/`.

---

## 1. Raw dataset inventory

| Dataset | Files | Total size |
|---|---|---|
| AgentRx | 4 `.jsonl` | 5.2 MB |
| AIOps KPI | 1 `.zip` (31 nested entries) | 2.9 GB |
| Alibaba GPU2020 | 7 `.tar.gz` | ~1.5 GB compressed |

## 2. Provenance

- AgentRx: `data/provenance/agentrx_download_provenance.md` (source
  URLs, SHA-256, acquisition date).
- Alibaba GPU2020: `data/provenance/alibaba_gpu2020/official_README.md`
  — the **official** schema doc, fetched this pass from
  `raw.githubusercontent.com/alibaba/clusterdata`. Its published
  checksum block was cross-checked against our own acquisition-time
  SHA-256 values for all 7 archives — **exact match**, confirming file
  integrity against the publisher's own record, not just our re-hash.
- AIOps KPI: acquired pre-staged; internal file structure (own
  `sha256sum.txt`, `passwd.txt`, `unzip_all.sh`) identifies it as the
  CCF AIOps Challenge 2020 preliminary-round release; no independent
  external re-verification of the acquisition URL was performed this
  pass (unchanged from the earlier audit).

## 3. Official schema references

- `data/metadata/alibaba_gpu2020/schema_dictionary.md` — full field
  dictionary for all 7 tables, sourced from the official README, not
  inferred from column names. Every job_table/task_table/
  instance_table column name in the earlier audit's position-inferred
  guesses is now confirmed correct against the official doc except
  job_table's `inst_id` (previously unlabeled, now resolved: ≈
  job_id).
- `data/metadata/aiops_kpi/schema_and_telemetry_findings.md` — full
  telemetry schema (tall/long `itemid,name,bomc_id,timestamp,value,
  cmdb_id` format), per-metric sampling rates, and trace-call schema
  (including the `success` field), all sourced from the dataset's own
  shipped `.xlsx`/text dictionaries and cross-validated against one
  fully-extracted real day (`2020_04_11`).
- AgentRx: no separate schema doc needed — its JSON field names are
  already self-descriptive and were fully characterized in the
  feasibility audit.

## 4. Raw record counts

Unchanged from the feasibility audit; see
`docs/PHASE3_REAL_DATA_FEASIBILITY_AUDIT.md` for the full per-table
breakdown (job_table 1,055,501; task_table 1,261,050; instance_table
7,522,002; sensor_table 3,033,232; machine_metric 2,009,423;
machine_spec 1,897; group_tag_table 1,055,032; AgentRx 87 trajectories
across 4 files; AIOps fault log 81 rows).

## 5–6. Cleaning rules and records removed

**Alibaba `job_table`/`task_table`** — the only tables cleaned at full
scale this pass (`scripts/real_data/clean_alibaba_job_task.py`). A row
is removed only if genuinely malformed: wrong field count, an
unparseable required numeric field, a `status` outside the documented
enum, or `end_time < start_time`.

**Important self-correction during this pass:** the first version of
this script treated an empty `start_time` as malformed for *every*
row and removed 3,663 job rows / 3,714 task rows. Investigation showed
every single removed row had `status=Waiting` — i.e. these are jobs/
tasks that legitimately have not launched yet, per the official
schema, not corrupted records. The rule was corrected to require
`start_time` only for non-`Waiting` rows. Re-run result: **0 rows
removed from either table** — both are fully well-formed at the raw
level; all apparent "missingness" is the documented right-censoring
pattern (Running/Waiting jobs with no `end_time`, Waiting jobs with no
`start_time`), not corruption. This is itself a real, reportable
finding: Alibaba's job/task tables need no repair, only correct
handling of meaningful missingness. The incorrect first pass and its
removed-record log were overwritten by the corrected re-run; the
`removed_records.csv` audit files are consequently empty for both
tables, reflecting the final, correct run.

**Alibaba `instance_table`/`sensor_table`/`machine_metric`** — not
cleaned at full scale (7.5M/3M/2M rows). Per the brief's own Step 6
guidance (sample jobs first, then retain only linked child records),
full-table cleaning was deferred in favor of extracting and validating
only the records linked to the sampled job population (§8 below).
Malformed-row detection (field-count check) *was* run inline during
that extraction (`scripts/real_data/alibaba_extract_linked_records.py`)
and found 0 malformed rows in the extracted subset.

**AIOps KPI** — no destructive cleaning performed this pass. The fault
log (81 rows) was fully parsed and validated in the feasibility audit
(0 duplicates, all 81 rows well-formed). Full-scale telemetry cleaning
across all 20 daily archives was **not performed** — see the scope
decision in `data/metadata/aiops_kpi/schema_and_telemetry_findings.md`
(tens of GB of trace data; deferred until the real-data protocol
defines what window/entity subset is actually needed, to avoid
extracting data before the criteria for using it are frozen).

**AgentRx** — no records removed (0 malformed lines across all 4
files, confirmed in the feasibility audit and re-confirmed by the join
script this pass). The canonical trajectory-level join
(`scripts/real_data/agentrx_build_joined_tables.py`) found 0 orphan
annotations (every annotation matches a real trajectory) in both
domains.

## 7. Records retained

- Alibaba job_table: 1,055,501 / 1,055,501 (100%)
- Alibaba task_table: 1,261,050 / 1,261,050 (100%)
- Alibaba instance/sensor/machine_metric: only the subset linked to
  the "main" sampled 10,000 jobs was materialized (60,005 / 26,350 /
  19,841 rows respectively) — not a cleaning removal, a deliberate
  hierarchy-respecting extraction (§8).
- AgentRx: 87/87 trajectories retained (73 with annotations, 14
  without — none dropped).
- AIOps fault log: 81/81 rows retained.

## 8. Missingness before/after

No change from the feasibility audit's findings (no imputation was
performed, per the brief's explicit prohibition): Alibaba job_table
28.08% censored `end_time` (Running/Waiting); task_table analogous;
AIOps `kpi`/`container` fields structurally empty depending on fault
type; AgentRx 100% key presence in all 4 files. All preserved as-is.

## 9. Duplicate analysis

Alibaba `job_name`: 0 duplicates (1,055,501 unique, re-confirmed).
Alibaba `(job_name, inst_name)` in sensor_table: 0 duplicates
(re-confirmed in the audit, not re-run at full scale this pass).
AgentRx: 0 duplicate `trajectory_id` within any file. AIOps fault log:
0 duplicate `index` (81/81 unique).

## 10–11. Integrity / referential-integrity results

**New this pass:** `task_table.job_name` was checked against the
cleaned `job_table.job_name` set — **0 of 1,261,050 task rows** have a
`job_name` absent from job_table. Referential integrity between job
and task tables is **perfect**, resolving a PENDING item from the
feasibility audit.

Instance/sensor/machine_metric referential integrity against
job_table/task_table was checked only for the extracted "main"-tier
subset (by construction — every extracted row's `job_name` is drawn
from the sampled job set, so integrity is guaranteed for that subset
by the extraction method itself, not separately verified against the
full raw tables).

## 12. Timestamp validation

Alibaba: confirmed via official docs to be relative seconds with an
undocumented per-trace offset, **not** epoch — but day-of-week/
time-of-day *are* preserved under a UTC+8 interpretation (new
information from the official README, not available in the earlier
audit). AIOps: confirmed via real extracted data to be genuine Unix
epoch milliseconds (`1586534693000` → 2020-04-11 00:04:53 UTC+8,
exactly matching the file's own date label) — the only dataset with
fully recoverable absolute calendar time. AgentRx: confirmed, no
timestamps exist anywhere in the schema.

## 13. Leakage analysis

**Mandatory gate resolved** (Step 2): both `pai_sensor_table` and
`pai_machine_metric` are **CONFIRMED LEAKING** for any decision-time
prediction task — both are explicitly documented by Alibaba as
full-instance-lifetime averages/maxima, not pre-outcome windowed
measurements. Full decision and rationale:
`docs/PHASE3_REAL_DATA_ALIBABA_SENSOR_LEAKAGE_GATE.md`. This is a
stricter, evidence-based conclusion than the earlier audit's
provisional "unresolved" status — in particular it corrects an
earlier speculation that `machine_metric` might have an independent,
possibly-safe reporting window; it does not.

AIOps: fault-log fields (`object`, `fault_desrcibtion`, `kpi`, `name`,
`container`) are ground truth by construction, usable only as `y`.
Trace `success`/`elapsedTime` are that call's own outcome, not an
input feature for predicting the same call. See the full table in
`data/metadata/aiops_kpi/schema_and_telemetry_findings.md`.

AgentRx: `failure_summary`, `failures`, `num_failures`, `root_cause*`
are demonstrably post-hoc (reference the trajectory's full, final
step) — confirmed unchanged from the audit.

## 14. Sampling protocol (Alibaba)

Sampling unit: **job** (`job_name`). Population: 988,910 eligible
terminal jobs (`Terminated`+`Failed`; `Running`/`Waiting` excluded as
censored). Strata: `(outcome_status × dominant_gpu_type ×
relative_time_quartile)`. Allocation: proportional to each stratum's
population share (not equalized — equalizing would misrepresent real
prevalence). Selection: deterministic (`SEED=42`, lexicographic sort +
`random.Random.sample`). Full protocol, strata sizes, and exact
selected IDs:
`data/audit/alibaba_gpu2020/{sampling_frame,sampling_report}.json`
and `sample_job_ids_{pilot,main,robustness}.txt`.

Sanity check: sampled Failed-rate matches the population rate almost
exactly at every tier (pilot 26.00%, main 25.94%, robustness 25.94%,
vs. population 25.94%) — confirms the stratified procedure preserves
real-world class balance rather than distorting it.

Linked child records for the **main** tier (10,000 jobs) were
extracted respecting the entity hierarchy — never sampling
instance/sensor/machine_metric rows independently of their parent job
(`scripts/real_data/alibaba_extract_linked_records.py`): 11,750 tasks,
60,005 instances, 26,350 sensor rows, 19,841 machine_metric rows.
Pilot and robustness tiers' linked records were **not** extracted this
pass (deferred until those tiers are actually put to use, to avoid
unnecessary large-file processing ahead of an authorized next step).

## 15. Power analysis

Full results: `data/audit/alibaba_gpu2020/power_analysis.json`
(`scripts/real_data/alibaba_power_analysis.py`, run and frozen
**before** any sampling). Method: Hanley-McNeil (1982) approximate
AUROC variance, at the real observed class balance (25.94% Failed).
Sensitivity swept across AUROC ∈ {0.55, …, 0.80} rather than a single
favorable assumption.

- To estimate a single AUROC to ±0.02 (95% CI half-width): **n ≈
  3,500–4,300** jobs, depending on assumed AUROC.
- To detect a **0.03 AUROC difference** between two candidates (power
  0.80, α=0.05, conservative independent-samples bound — a paired/
  DeLong test on the same test set would need fewer): **n ≈
  7,700–8,100** jobs.

These numbers directly set the tier sizes: pilot (2,000, pipeline
verification only, not powered for a difference claim), main (10,000,
exceeds the ~8,100 needed for a 0.03 difference with margin for
attrition), robustness (50,000, generous margin for subgroup/attack
analyses). **No tier size was chosen after, or influenced by, any
evaluation result** — this script and the sampling script were run in
that order, before any model was ever fit.

## 16. Split protocol

Two split protocols built on the **main** tier (10,000 jobs),
answering two different generalization questions — not one split
forced to serve both. Full construction and per-split class balance:
`data/audit/alibaba_gpu2020/{splits_random_stratified,splits_temporal,
splits_report}.json`.

1. **Random-stratified** (70/15/15, stratified on outcome×gpu_type):
   class balance preserved almost exactly across train/val/test
   (25.95% / 25.97% / 25.88% Failed).
2. **Temporal** (train/val = relative-time Q1–Q3, test = strict future
   holdout Q4): **class balance is NOT preserved** — Failed rate is
   ~20.1% in train/val but **43.4% in the Q4 test holdout**. This is a
   genuine, unforced finding — real temporal drift in the failure rate
   exists in this trace, discovered by the split construction itself,
   before any model was evaluated. This is directly relevant to the
   real-data H2 (drift/generalization) hypothesis and should be
   reported prominently regardless of how any future model performs
   under it — a model evaluated on this temporal split faces a
   materially different base rate than it trained on, which is exactly
   the kind of distribution shift Phase 3.3/3.5-equivalent real-data
   experiments should be measuring.

**Not built this pass:** a machine-disjoint split. Alibaba's job↔
machine relationship is many-to-many; a clean job-disjoint split does
not automatically avoid machine overlap across splits, and building
one without dropping a nontrivial share of jobs is a real
graph-partitioning problem. Documented as a limitation, not silently
skipped.

## 17. Final effective sample sizes

| Dataset | Independent unit | Effective N |
|---|---|---|
| AgentRx — magentic | trajectory | 44 annotated / 58 total |
| AgentRx — tau-retail | trajectory | 29 annotated / 29 total |
| AIOps KPI | fault-injection event | 81 (or 70, pending the IDs-1–11-vs-100–169 reconciliation, see AIOps findings doc) |
| Alibaba GPU2020 (job-level) | job | 988,910 eligible; sampled tiers 2,000 / 10,000 / 50,000 |
| Alibaba GPU2020 (machine-level) | machine | 1,737 total — no machine-disjoint sample constructed this pass |

## 18. Dataset-to-hypothesis matrix (updated, post-cleaning)

| Dataset | 3.1 | 3.2 | 3.3 | 3.4 | 3.5 | 3.6 | Independent unit | Effective N | Evidence available | Limitations |
|---|---|---|---|---|---|---|---|---|---|---|
| AgentRx (magentic) | Yes | Partial | Insufficient evidence | Partial | Partial | Diagnosis: **Yes**; Recovery: No | trajectory | 44 | explicit `root_cause`/`failure_category`, joined & verified 0 orphans | n=44, no timestamps, benchmark-harness origin |
| AgentRx (tau-retail) | Yes | Partial | Insufficient evidence | Partial | Partial | Diagnosis: **Yes**; Recovery: No | trajectory | 29 | same as above, ID-mapping resolved & verified | n=29, different domain — not pooled with magentic |
| AIOps KPI | Yes | Yes | **Yes** | Yes | Yes | Diagnosis: Yes (injected-fault category); Recovery: No | fault-injection event | 81 (or 70) | real absolute timestamps confirmed on real data; tall-format telemetry schema resolved; per-call `success` field found (organic outcome signal, new this pass) | injected, not organic; full 20-day telemetry not yet extracted; fault-log start_time/log_time semantics only partially reconciled |
| Alibaba GPU2020 | Yes | Yes | Partial (relative-time only, but **real drift confirmed** this pass) | Yes | Yes | Diagnosis: No; Recovery: No | job (988,910 eligible) | 2,000 / 10,000 / 50,000 sampled tiers, power-justified | sensor/machine_metric CONFIRMED leaking (not just unresolved); referential integrity between job/task confirmed perfect; no machine-disjoint split yet |

Changes from the pre-cleaning matrix: Alibaba's 3.3 cell strengthened
from "Partial (relative-time only)" to "Partial, but real drift now
empirically confirmed" — this is new evidence, not a re-interpretation
of anything frozen. AIOps gained a new organic outcome signal (trace
`success`) not visible before extraction. AgentRx's two domains are
now split into separate matrix rows rather than one combined row, per
the "do not pool" instruction.

## 19. Known limitations (consolidated)

- Alibaba: no machine-disjoint split; instance/sensor/machine_metric
  cleaned only for the sampled subset, not the full raw tables; AIOps
  full-telemetry extraction deferred (tens of GB, scope decision
  documented); AgentRx small-n and cross-domain non-poolability stand
  as before. AIOps fault-log ID-gap (1–11 vs 100–169) reconciliation
  remains partial.
- This preprocessing pass covered the **main** sampling tier
  end-to-end; **pilot** and **robustness** tiers have their job IDs
  selected and frozen but not yet had linked child records extracted.

## 20. Reproducibility instructions

All scripts are under `scripts/real_data/`, deterministic (fixed
`SEED=42` where randomness is used), and read only from `data/raw/`
or from another script's own output — never from anything hand-edited.
Run order:
```
python scripts/real_data/clean_alibaba_job_task.py
python scripts/real_data/alibaba_power_analysis.py
python scripts/real_data/alibaba_stratified_sampling.py
python scripts/real_data/alibaba_extract_linked_records.py main
python scripts/real_data/alibaba_build_splits.py
python scripts/real_data/agentrx_build_joined_tables.py
```
Each script's outputs are content-addressed by the deterministic
inputs above — re-running with unchanged raw files and unchanged
script code reproduces byte-identical `data/audit/`/`data/processed/`
outputs.

---

## Is the data ready for a new frozen Phase 3.1 real-data protocol?

**Partially — main-tier Alibaba and AgentRx are ready; AIOps needs one
more decision before it is.**

- **Alibaba (main tier):** cleaning validated (0 malformed rows once
  the Waiting-status bug was caught and fixed), referential integrity
  confirmed, leakage gate resolved definitively, power-justified
  sample drawn, two split protocols built and frozen. Ready to inform
  a Phase 3.1 protocol draft for job-level failure prediction using
  the request/scheduling-time feature set only (per the leakage gate).
- **AgentRx:** joins verified, domains correctly kept separate,
  leakage fields identified. Ready, with the caveat that n≈44/29 means
  any Phase 3.1 protocol must plan for wide confidence intervals and
  should not set acceptance criteria that assume more statistical
  power than these sample sizes can deliver.
- **AIOps KPI:** schema and leakage semantics are now resolved with
  high confidence, and the one representative day validated
  end-to-end — but the full telemetry corpus is not yet extracted, and
  the fault-log's `start_time`/`log_time`/`log_block` semantics are
  only partially reconciled. A Phase 3.1 protocol could be drafted for
  this dataset now, but the decision of *what time window / how much
  telemetry* to extract should itself be written into that protocol
  **before** doing the extraction — extracting everything now, ahead
  of that decision, risks exactly the kind of "shape the data toward a
  convenient analysis" pattern the brief prohibits.

No cleaning, sampling, or split decision in this report was made after
looking at, or was influenced by, any evaluation metric — none has
been computed. Per your instruction, **stopping here** and waiting for
explicit authorization before Phase 3.1.
