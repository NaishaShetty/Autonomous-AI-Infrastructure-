<a id="phase3-real-data-protocol"></a>
# PHASE3 REAL DATA PROTOCOL
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_PROTOCOL.md`  
**Role:** The overall frozen real-data Phase 3 protocol (all three datasets).

# Phase 3 Real-Data Replication — Frozen Evaluation Protocol

**Status: FROZEN (protocol design only — no evaluation has been run under this document).**
**Version: 1.0**
**Date frozen: 2026-08-13**

---

## 0. Relationship to the original Phase 3

This document defines **"Phase 3 Real-Data Replication"** (internally: **Phase 3.1-RD**, to avoid collision
with the original synthetic `docs/PHASE3_1_EVALUATION_PROTOCOL.md`). It is a **separate, additional** research
track, not a continuation, correction, or replacement of the original Phase 3.

- The original Phase 3 (`docs/PHASE3_1_EVALUATION_PROTOCOL.md` through `docs/PHASE3_6_DIAGNOSIS_ABSTENTION_RECOVERY.md`,
  frozen by `docs/PHASE3_FREEZE.md`) evaluated the failure-risk pipeline on a fully synthetic, controlled generator
  (`src/data/synthetic.py::generate_regime_stream`). Its results, configs, scripts, and reports are **frozen and
  will not be edited, rerun, or reinterpreted** by this document or by anything downstream of it.
- This document instead asks: **do the original Phase 3 findings hold up when the same class of questions is
  asked of real-world data?** The answer may be "yes," "no," "partially," or "not evaluable" per hypothesis
  per dataset — all four outcomes are acceptable and none is preferred a priori (see §21, Research Integrity).
- No file under `experiments/results/phase3_1/` … `phase3_6/`, no file listed in `docs/PHASE3_FREEZE.md`'s
  frozen-artifact list, and no synthetic-data config (`configs/phase3_1_protocol.json`,
  `configs/phase3_5_attack_protocol.json`, `configs/phase3_6_decision_recovery_protocol.json`) is modified by
  this protocol or by any phase run under it.
- All real-data results are written to a **new, separate** results tree: `experiments/results/phase3_real_data/`.
  This tree does not exist yet and is not created by this document — it is created only when Phase 3.1-RD is
  actually run, which requires separate authorization (see §26).

---

## 1. Research objective

Determine whether the six hypotheses established in the original (synthetic) Phase 3 —

- **H1** — a supervised failure-risk signal exists beyond calibrated confidence (Phase 3.1/3.2)
- **H2** — that signal's source is supervised learning, not representation richness (Phase 3.2C)
- **H3** — the signal generalizes across concept drift (Phase 3.3)
- **H4** — the signal generalizes across covariate-shift attacks (Phase 3.5)
- **H5** — the signal is complementary to calibrated confidence (Phase 3.6.1) and changes decision-cost
  outcomes (Phase 3.6.2)
- **H6** — the pipeline can diagnose the cause of a failure/anomaly (Phase 3.6.3)
- **H7** — the pipeline can recover from a diagnosed failure (Phase 3.6.4–3.6.5)

remain supported, are contradicted, are only partially supported, or cannot be adjudicated, when the same
class of question is posed against real-world operational data: Alibaba GPU Cluster Trace 2020, AIOps
Challenge 2020, and Microsoft AgentRx (Magentic-One, τ-Retail).

This is explicitly **not** an attempt to reproduce or exceed the original AUROC/AUPRC numbers, and the
protocol below is not tuned to make any result "work." See §21.

---

## 2. Dataset inventory

| Dataset | Domain | Raw record scale | Real-data-eligible sample | Independent unit | Effective N |
|---|---|---|---|---|---|
| Alibaba GPU Cluster Trace 2020 | ML training job scheduling/failure | 1,055,501 jobs / 7,522,002 instances | 988,910 eligible terminal jobs; sampled tiers 2,000 / 10,000 / 50,000 | job | 10,000 (main tier, used for all confirmatory-capable analysis) |
| AIOps Challenge 2020 (CCF) | Microservice fault detection | 81 fault-log events across 15 telemetry days | 81 positive windows + 145 negative windows | fault entity | 226 windows / 43 entities (16 positive, 27 negative-only) |
| Microsoft AgentRx — Magentic-One | LLM agent trajectory failure/diagnosis | 58 trajectories | 44 annotated trajectories | trajectory | 44 |
| Microsoft AgentRx — τ-Retail | LLM agent trajectory failure/diagnosis | 29 trajectories | 29 annotated trajectories | trajectory | 29 |

These four datasets are evaluated **separately**. They are never pooled into one experiment (see §4, §12, §21).
Provenance for each is documented in `docs/PHASE3_REAL_DATA_FEASIBILITY_AUDIT.md` and
`docs/PHASE3_REAL_DATA_CLEANING_REPORT.md`.

---

## 3. Dataset-to-hypothesis mapping

`✅ EVALUABLE (confirmatory-capable)` · `🟡 EVALUABLE (exploratory only)` · `⚪ NOT EVALUABLE`

| Hypothesis | Alibaba GPU2020 | AIOps 2020 | AgentRx Magentic | AgentRx τ-Retail |
|---|---|---|---|---|
| H1 — supervised risk signal exists | ✅ (n=10,000 job main tier) | 🟡 (n=226 windows, 43 entities) | 🟡 (n=44) | 🟡 (n=29) |
| H2 — mechanism is supervision, not representation | ✅ | 🟡 | ⚪ (no representation-ablation axis in the data — no engineered feature families to compare) | ⚪ |
| H3 — concept-drift generalization | 🟡 (relative-time only; real distribution shift confirmed, see §9) | 🟡 (real absolute calendar time across 15 days) | ⚪ (no timestamps in AgentRx at all — see §13) | ⚪ |
| H4 — covariate-shift / attack generalization | 🟡 (only naturally occurring covariate variation available; no synthetic attack matrix applies to real data) | 🟡 (naturally occurring telemetry noise/outage conditions, not a controlled attack matrix) | ⚪ | ⚪ |
| H5a — complementarity (risk signal adds to confidence) | ✅ | 🟡 | ⚪ (no confidence/calibration signal exists in AgentRx transcripts) | ⚪ |
| H5b — decision-cost policy | 🟡 (no real operational cost model exists for Alibaba; any cost model would be assumed, not measured — see §21) | 🟡 (same caveat) | ⚪ | ⚪ |
| H6 — diagnosis | ⚪ (no cause-of-failure field in Alibaba trace; `status` is the outcome, not a diagnosis) | 🟡 (fault category is the injected ground truth — diagnosis task is real but injected-fault, not organic) | ✅ (organic `root_cause_failure_id` + `root_cause_reason` fields — strongest diagnosis dataset available; still small-N, see §17) | ✅ (same fields, n=29) |
| H7 — recovery | ⚪ (no recovery action recorded) | ⚪ (no recovery action recorded) | ⚪ (no recovery field) | ⚪ (no recovery field) |

**H7 (recovery) is NOT EVALUABLE on any real dataset currently held.** This is reported as a limitation
(§24), not worked around by inferring or fabricating recovery outcomes (prohibited, §21).

Where a cell is marked `⚪ NOT EVALUABLE`, no experiment is designed for it in this protocol, and none may be
added later by adapting the hypothesis to fit the data (§21).

---

## 4. Independent units (do not inflate N)

| Dataset | Independent unit | What is NOT an independent unit |
|---|---|---|
| Alibaba GPU2020 | **job** (`job_name`) | task rows (child of job), instance rows (child of task), sensor rows (child of instance), machine_metric rows — these are correlated children of a sampled job and must not be counted as separate observations. Machine-level generalization claims are bounded by **1,737 distinct machines**, not by job or row count. |
| AIOps 2020 | **fault entity** (`cmdb_id`), with fault events nested inside entities | the 226 windows are not 226 independent observations — 81 positives cluster into 16 entities (median 5 events/entity, max 10) and 145 negatives cluster into 43 entities (median 3, max 7). Any statistical test must either block/cluster on entity or explicitly report the window count as an upper bound on the effective N with entity count as the conservative lower bound. |
| AgentRx (each domain) | **trajectory** (`trajectory_id`) | steps/substeps within a trajectory are not independent units; failure records within one trajectory's `failures` list are not independent units for a per-trajectory-outcome test. |

No experiment in this protocol treats a correlated child record as an additional independent observation.
Where an analysis is entity-clustered (AIOps) or trajectory-level (AgentRx), the reported N is the unit count,
and any variance/CI estimate accounts for clustering (e.g., cluster bootstrap over entities, not over windows).

---

## 5. Effective sample sizes (frozen, pre-registered)

| Dataset | Nominal N | Effective independent N | Confirmatory-capable? |
|---|---|---|---|
| Alibaba, random-stratified split | 10,000 jobs (7,000/1,500/1,500 train/val/test) | 10,000 jobs | Yes — power analysis (§18) supports ±0.02–0.03 AUROC precision and detection of a 0.03 AUROC difference at power 0.80 |
| Alibaba, temporal split | 10,000 jobs (Q1–Q3 train/val, Q4 test) | 10,000 jobs, but Q4 test carries a confirmed base-rate shift (§9) | Yes for descriptive/shift reporting; treat point estimates on the shifted test set with caution |
| AIOps | 226 windows | 43 entities (16 positive-bearing, 27 negative-only) | No — exploratory only (±0.064–0.079 AUROC CI half-width at assumed AUROC 0.55–0.80, n=226; entity-level N is smaller still) |
| AgentRx Magentic | 44 trajectories | 44 trajectories | No — exploratory only, wide CIs expected |
| AgentRx τ-Retail | 29 trajectories | 29 trajectories | No — exploratory only, wide CIs expected |

---

## 6. Alibaba sampling protocol (already frozen upstream — reused verbatim)

This protocol does not re-sample. It reuses the sample already frozen in
`docs/PHASE3_REAL_DATA_CLEANING_REPORT.md` §14 and `data/audit/alibaba_gpu2020/`:

- **Sampling unit**: job (`job_name`).
- **Population**: 988,910 eligible terminal jobs (status ∈ {Terminated, Failed}; Running/Waiting excluded as
  right-censored, not imputed).
- **Strata**: `outcome_status × dominant_gpu_type × relative_time_quartile`.
- **Allocation**: proportional to each stratum's population share.
- **Selection**: deterministic, `seed=42`, lexicographic sort of `job_name` then `random.Random.sample`.
- **Tiers**: pilot (2,000), **main (10,000, used for this protocol)**, robustness (50,000, not used here —
  reserved for a future robustness check, not part of Phase 3.1-RD).
- **Verification already performed**: sampled Failed-rate for the main tier is 25.94%, matching the population
  rate of 25.94% to four significant figures.
- **This protocol will not draw a new sample, change the seed, or change the tier.** If the main tier proves
  insufficient for some sub-analysis discovered during execution, that is reported as a limitation; the
  robustness tier is not silently substituted mid-protocol.

---

## 7. Alibaba feature eligibility / leakage exclusions (frozen upstream — reused verbatim)

Per `docs/PHASE3_REAL_DATA_ALIBABA_SENSOR_LEAKAGE_GATE.md`, the following are **excluded from every
decision-time predictive feature set** in this protocol, for every Alibaba experiment under every hypothesis:

- `pai_sensor_table` in its entirety — official documentation confirms these are per-instance-lifetime
  averages (and, for `max_mem`/`max_gpu_wrk_mem`, per-instance-lifetime maxima), i.e. computed over the full
  span of the very instance whose outcome is being predicted.
- `pai_machine_metric` in its entirety — same lifetime-average construction, machine-level.
- `max_mem`, `max_gpu_wrk_mem` specifically (redundant with the table-level exclusion above, restated because
  these two fields are the most likely to be reintroduced by accident as "just a summary statistic").

**Allowed (pre-outcome, request/scheduling-time) predictive fields:**

| Table | Allowed fields |
|---|---|
| `pai_job_table` | `user`, `start_time` (submission time only) |
| `pai_task_table` | `task_name`, `inst_num`, `plan_cpu`, `plan_mem`, `plan_gpu`, `gpu_type`, task `start_time` |
| `pai_instance_table` | `machine` (once scheduled), instance `start_time` |
| `pai_group_tag_table` | `gpu_type_spec`, `group`, `workload` (sparse) |
| `pai_machine_spec` | all fields (static machine specs — never leak, since they don't depend on job outcome) |

**Consequence, stated explicitly (per instruction and per the leakage-gate doc):** the Alibaba real-data
representation/failure-prediction experiment is necessarily based primarily on **request- and
scheduling-time information**, not runtime telemetry. This is a real constraint on what the Alibaba real-data
experiment can show about H1/H2 — it cannot be interpreted as testing the same "richer runtime representation"
question that Phase 3.2 tested on synthetic features, only the narrower "does pre-outcome
scheduling/spec information carry a supervised failure-risk signal" question. This distinction is carried into
the H1/H2 result write-up, not glossed over.

No lifetime telemetry field is reintroduced into any predictive experiment under this protocol, including
indirectly (e.g., no engineered feature is a function of an excluded field). Sensor/machine-metric tables
remain usable **only** for post-hoc descriptive/exploratory analysis, explicitly labeled as such and never fed
to a predictive model.

---

## 8. Alibaba random split (frozen upstream — reused verbatim)

- 70/15/15 train/validation/test.
- Stratified on `outcome_status × dominant_gpu_type`.
- Source: `data/audit/alibaba_gpu2020/splits_random_stratified.json`.
- Observed class balance: 25.95% / 25.97% / 25.88% Failed across train/val/test — closely matched, as
  intended by stratification.
- Test set is frozen at the point this protocol is authorized to run and is used only for final evaluation
  (§19).

---

## 9. Alibaba temporal split (frozen upstream — reused verbatim; distribution shift disclosed up front)

- Train/validation = relative-time **Q1–Q3**.
- Test = strict future holdout **Q4**.
- Source: `data/audit/alibaba_gpu2020/splits_temporal.json`.
- **Base-rate shift, discovered during data preparation, before any model evaluation, and disclosed here in
  full:**
  - Failed rate in Q1–Q3 (train/val): **≈20.1%**
  - Failed rate in Q4 (test): **≈43.4%**
- This is a genuine, already-observed distribution shift in the real data, not an artifact of sampling. It is
  treated as a **finding to report**, not a problem to correct by rebalancing, resampling, or reweighting the
  temporal test set. Any H3 (generalization) result on the Alibaba temporal split is interpreted with this
  shift explicitly stated alongside the metric, and raw AUROC/AUPRC under a 2.2x base-rate change between
  train and test is not compared directly to the random-split numbers without that caveat.
- No machine-disjoint split exists for Alibaba (job↔machine is many-to-many; not solved by this protocol) —
  documented as a limitation (§24), not silently skipped.

---

## 10. AIOps temporal/window protocol (frozen upstream — reused verbatim)

Per `docs/PHASE3_REAL_DATA_AIOPS_PROTOCOL.md`:

- **PRE-FAILURE window**: `[fault_onset − 20min, fault_onset)` — the only region usable as predictive input.
- **DURING-FAILURE window**: `[fault_onset, fault_onset + 5min)` — usable only for diagnosis, never prediction.
- **POST-FAILURE**: everything after `fault_onset + 5min` — usable only for diagnosis, never prediction.
- Rationale for 20 minutes: global minimum gap between consecutive fault onsets is 25.0 minutes (min per-entity
  gap 30.0 minutes); a 20-minute window leaves a 5-minute safety margin against cross-event contamination for
  effectively the whole population. A 60-minute window was considered and rejected because it is
  contamination-free for only ~62% of events (51/81).
- `fault_onset(event) = start_time` if non-empty, else `log_time`.
- Telemetry inclusion/exclusion (verbatim from the frozen table): platform metrics, business metrics
  (`esb.csv`), and call-trace fields other than same-call `success`/`elapsedTime` are usable as PRE-FAILURE
  predictive features; `success`/`elapsedTime` are usable only as aggregated PRE-window features (e.g. "%
  failed calls in preceding 20 min"), never as same-call input; fault-log descriptive fields are diagnosis/label
  only; fault-log timing fields are used only to draw the T0 cutoff, never as a feature value.
- These rules are **not** revisited after seeing any evaluation result.

---

## 11. AIOps positive/negative population (frozen upstream — reused verbatim)

- **Positive windows**: 81/81 fault-log events validated (exact 20-min span, ≥1 telemetry observation, zero
  observations at/after onset, no cross-event overlap for the same entity). Source:
  `scripts/real_data/aiops_validate_positive_windows.py`.
- **Negative windows**: 145 valid, drawn from a frozen candidate pool of 860 (43 eligible entities × 20
  candidates/entity, `seed=42`), rejected only for lack of telemetry coverage (715/715 rejections were
  `has_telemetry_coverage=False`; zero rejections were due to the fault-exclusion/overlap logic failing).
  Exclusion window around each entity's own fault onset: `[w_start − 60min, w_start + 20min + 60min]`.
  Negative-eligible entities are the same 43 fault-eligible entities as the positive pool (8 docker_*, 13
  db_*, 22 os_*); `csf_*`/`redis_*`/`osb_*` are excluded as never fault-injection targets.
- **Total**: 226 windows (81 positive + 145 negative).
- This population is not re-sampled, re-balanced, or filtered further by this protocol.

---

## 12. AIOps entity-level dependence (must be reported alongside every AIOps result)

- 43 total entities in the final positive/negative window population.
- 16 entities have at least one positive (fault) window; 27 entities appear only in the negative pool.
- Positive events per entity: min 1, median 5, max 10.
- Negative windows per entity: min 2, median 3, max 7.
- Every AIOps statistical result in Phase 3.1-RD reports **both** the window count (226) and the entity count
  (43, with the 16/27 positive/negative-only split), and any variance estimate accounts for entity clustering.
  A result that only reports "n=226" without the entity breakdown is not a valid Phase 3.1-RD deliverable.
- **AIOps is classified EXPLORATORY for every hypothesis in §3.** No AIOps result is described as confirmatory,
  regardless of p-value or point estimate.
- Two known, unresolved timestamp irregularities remain documented and are **not silently fixed**:
  1. `block=8` spans two calendar dates (2020-05-29 and 2020-05-30) with no operational explanation found.
  2. An unexplained **+6-hour** shift between `log_time` and `start_time` for `log_block ∈ {4,5}` (11 of 70
     index≥100 rows).
  Neither irregularity is corrected, imputed around, or excluded without being reported as a limitation (§24).

---

## 13. AgentRx domain separation

- **Magentic-One**: 44 annotated trajectories.
- **τ-Retail**: 29 annotated trajectories.
- These are evaluated as **two separate small-sample datasets**, never pooled to reach a combined N=73. Any
  aggregate statement about "AgentRx" as a whole reports both numbers separately; it never reports a single
  merged AUROC/accuracy figure across domains.
- Explicit constraints carried into every AgentRx analysis:
  - No timestamps exist anywhere in either dataset (only ordinal step/substep indices) — H3 (drift) and any
    wall-clock temporal analysis are **NOT EVALUABLE** on AgentRx.
  - Origin is a benchmark-harness evaluation environment: genuine LLM-agent executions against real tools, but
    not organic production traffic and not a controlled fault-injection design either. Results are never
    described as "production evidence."
  - `failure_summary`, `failures`, `num_failures`, `root_cause_failure_id`, `root_cause_reason` are all
    post-hoc fields, available only after the trajectory concluded — never used as decision-time predictive
    input, only as diagnosis-task labels/targets.
  - n=44 and n=29 are both far below any conventional threshold for a stable AUROC/AUPRC estimate. Every
    AgentRx result is reported with a confidence interval, and no AgentRx point estimate is treated as
    decisive on its own.

---

## 14. Statistical tests

| Context | Test / estimator |
|---|---|
| AUROC/AUPRC point estimate, any dataset | Empirical estimator on the frozen test split |
| Alibaba random split (confirmatory-capable) | Cross-seed Student-t interval is not applicable (single real split, not multi-seed synthetic regeneration) — instead: nonparametric bootstrap over jobs (test-set rows), matching the within-seed bootstrap method already used in the original Phase 3 (`n_resamples=2000`, `seed=0`, 95% percentile CI) |
| Alibaba random vs temporal split comparison | Report both metrics side by side with CIs; do not compute a single paired difference test across splits with different base rates — report the base-rate shift (§9) as the primary explanatory factor before any performance delta is interpreted |
| AIOps (any hypothesis) | Cluster bootstrap over the 43 entities (resample entities with replacement, not windows), 2000 resamples, seed 0, 95% percentile CI — window-level bootstrap is not used as the primary estimator because it treats correlated within-entity windows as independent |
| AgentRx (either domain) | Nonparametric bootstrap over trajectories, 2000 resamples, seed 0, 95% percentile CI; given n=29–44, CIs are expected to be wide and are reported as-is, not narrowed by any post-hoc adjustment |
| Any cross-dataset comparison (e.g. AIOps vs Alibaba on H3) | Qualitative consistency check only (same-direction / different-direction, overlapping / non-overlapping CIs) — never a single pooled statistical test across datasets with different units, domains, and sample sizes |

P-values, where computed at all, are reported alongside effect sizes and confidence intervals, never alone.

---

## 15. Effect-size reporting

Every quantitative result reports, at minimum:
- Point estimate (AUROC, AUPRC, accuracy, or the task-appropriate metric) with its 95% CI.
- A paired or unpaired effect-size measure against the relevant baseline (e.g., ΔAUROC vs. no-signal baseline,
  vs. calibrated-confidence baseline, matching the baseline structure used in the original Phase 3 where an
  analogous baseline exists on the real dataset).
- The independent-unit N used for the CI (job count, entity count, or trajectory count — never raw row count).
- Where a baseline used in the original Phase 3 (no-signal, calibrated confidence) has a real-data analogue,
  it is computed and reported alongside the candidate signal, exactly as Phase 3.1/3.4 did on synthetic data —
  so real-data H1/H5a results are directly comparable in structure (not necessarily magnitude) to the original.

---

## 16. Confidence-interval methodology

- **Bootstrap CIs**: nonparametric percentile bootstrap, `n_resamples=2000`, `seed=0`, 95% confidence level —
  identical methodology to the original Phase 3 (`configs/phase3_1_protocol.json`), applied at the
  independent-unit level appropriate to each dataset (job for Alibaba, entity for AIOps, trajectory for
  AgentRx).
- No cross-seed Student-t interval is used for real data, because real data is not regenerated across
  synthetic seeds; there is exactly one real sample per split. Where multiple random splits or resampling
  schemes are legitimately available (e.g., repeated stratified resampling of the Alibaba main tier for a
  robustness check), that is treated as a distinct, explicitly labeled sub-analysis, not substituted silently
  for the frozen primary split.

---

## 17. Power / feasibility limitations (frozen upstream — reused verbatim, restated here for the record)

| Dataset | Power analysis result | Conclusion |
|---|---|---|
| Alibaba main tier (n=10,000) | Hanley-McNeil approximation at observed 25.94% base rate: n≈3,500–4,300 for ±0.02 AUROC precision; n≈7,700–8,100 for 80% power to detect a 0.03 AUROC difference at α=0.05 | Main tier exceeds both thresholds — confirmatory-capable |
| AIOps (n=226 windows) | 95% CI half-width at n=226 ranges ±0.064 (AUROC≈0.80) to ±0.079 (AUROC≈0.55) | Explicitly exploratory, not confirmatory, for every hypothesis |
| AIOps fault-category classification (5 classes) | Per-class n ranges 5–31 | Underpowered / inconclusive-prone by design; any per-class metric reported with this caveat attached |
| AIOps entity-level generalization | 16 entities with positives, 15 with ≥2 events | Underpowered for a leave-entities-out generalization claim; any such analysis is reported as a directional/qualitative observation only |
| AgentRx (n=44, n=29) | No stable-AUROC threshold met at either sample size | Exploratory only; wide CIs expected and reported as such, never treated as decisive |

The power analysis was performed **before** sampling (Alibaba) and before window extraction (AIOps), per
`docs/PHASE3_REAL_DATA_CLEANING_REPORT.md` §15 and `docs/PHASE3_REAL_DATA_AIOPS_PREPARATION_COMPLETE.md` §6.
No tier or window count is chosen or changed after seeing any evaluation result under this protocol.

---

## 18. Confirmatory vs. exploratory status (explicit, per dataset)

| Dataset | Status | Basis |
|---|---|---|
| Alibaba, random-stratified split, request/scheduling-time features | **Confirmatory-capable** | Power analysis (§17) supports the target precision; leakage gate (§7) ensures features are genuinely pre-outcome |
| Alibaba, temporal split | **Confirmatory-capable for the metric itself; interpretation constrained** by the disclosed base-rate shift (§9) | Same power basis, but cross-split comparison is not a clean apples-to-apples confirmatory test given the shift |
| AIOps (all hypotheses) | **Exploratory** | §17 — CI half-widths of 0.06–0.08 at n=226 windows / entity-clustered N as low as 16 |
| AgentRx, Magentic and τ-Retail (all hypotheses) | **Exploratory** | §17 — n=44 and n=29, no stable-estimate threshold met |

No exploratory-status result is later relabeled confirmatory based on how the numbers turn out.

---

## 19. Train/validation/test rules

- **Alibaba random split**: train (70%) used for model fitting; validation (15%) used for any legitimate
  model-selection/hyperparameter decision (e.g., regularization strength for a supervised risk model, mirroring
  the frozen-candidate-F structure from the original Phase 3); test (15%) is touched exactly once, for final
  evaluation, after all modeling decisions are frozen.
- **Alibaba temporal split**: Q1–Q3 (train+validation, further split internally if a validation set is needed)
  used for fitting/selection; Q4 test is touched exactly once, for final evaluation.
- **AIOps**: given the small entity-clustered N, no separate validation split is carved out of the 226-window
  population for AIOps; any model-selection decision needed for an AIOps experiment is made using the
  Alibaba validation set's selected configuration where the same model family applies, or is fixed a priori
  from the original Phase 3's frozen candidate definitions (`src/evaluation/representations.py`) — not tuned
  on AIOps data itself. This constraint is stated explicitly in any AIOps sub-report.
- **AgentRx**: same rule as AIOps — no held-out validation carved from 44 or 29 trajectories; any modeling
  choice reuses a configuration fixed elsewhere, never tuned on AgentRx test data.
- **Test sets, once designated, are frozen for the remainder of Phase 3.1-RD.** They are read exactly once
  per experiment, for final evaluation. No metric computed on a test set is used to revise sampling,
  preprocessing, features, representation, hyperparameters, thresholds, model selection, extraction windows,
  or negative-window selection (see §21 for the full prohibited-actions list).

---

## 20. Leakage prevention

- Alibaba: §7's exclusion list (`pai_sensor_table`, `pai_machine_metric`, `max_mem`, `max_gpu_wrk_mem`) is
  enforced for every predictive experiment, including any derived/engineered feature that is a function of an
  excluded field.
- AIOps: §10's PRE/DURING/POST partition is enforced for every predictive experiment; fault-log descriptive
  and timing fields are never predictive features.
- AgentRx: post-hoc annotation fields (`failure_summary`, `failures`, `num_failures`, `root_cause_failure_id`,
  `root_cause_reason`) are never predictive input for any prediction-task experiment; they are the label/target
  for diagnosis-task experiments only (H6), which is the one task class where AgentRx is evaluable (§3).
- Entity leakage (AIOps) and machine leakage (Alibaba, where feasible): no entity/machine that contributes to
  a test window/job may also contribute a window/job used for fitting or model selection on the same
  experiment, wherever the split design makes this checkable. Where it is not fully checkable (Alibaba's
  job↔machine many-to-many relationship, §9), this is documented as a limitation, not silently ignored.
- Temporal leakage: for the Alibaba temporal split and for any AIOps analysis that uses absolute calendar time,
  no feature computed using information from after the prediction cutoff (`T0` for AIOps, job `start_time` for
  Alibaset scheduling-time features) enters training or evaluation for that unit.

---

## 21. Research integrity — explicit prohibited actions

The following are prohibited for the duration of Phase 3.1-RD, without exception:

- Tuning on the test set, in any dataset.
- Selecting or dropping a dataset after seeing its evaluation result.
- Removing difficult test cases.
- Rebalancing a test set after evaluation (including the Alibaba Q4 base-rate shift, §9 — reported as-is).
- Changing sampling seeds after evaluation.
- Altering AIOps window definitions after evaluation.
- Selecting a representation or candidate model based on test-set performance.
- Cherry-picking datasets or metrics for the write-up.
- Fabricating labels.
- Inferring unavailable recovery outcomes for H7 (AgentRx, AIOps, Alibaba all lack a recovery field — H7 is
  reported NOT EVALUABLE, not approximated).
- Treating missing information as negative evidence (e.g., an AIOps entity never appearing in the fault log is
  not treated as evidence that entity cannot fail — it is an open question, per §24).
- Inflating sample size by treating correlated child rows/windows as independent observations (§4).
- Hiding inconclusive or negative findings.
- Modifying any original (synthetic) Phase 3 frozen result, config, script, or report.

If a hypothesis is inconclusive after evaluation, the protocol requires it to be **reported as inconclusive**,
using the same INCONCLUSIVE label the original Phase 3 already used for its own H1/H5/H7-equivalent findings
(Phase 3.2, 3.4, 3.6) — inconclusive is a legitimate, expected outcome class in this research program, not a
failure of the protocol.

---

## 22. Reproducibility requirements

- Every script under `scripts/real_data/` used to build a Phase 3.1-RD input is deterministic, with
  `seed=42` wherever randomness is involved, matching the seed already used for sampling and negative-window
  construction upstream.
- Every Phase 3.1-RD result artifact records: protocol version (this document's version, §above), full
  resolved config (this document's companion `configs/phase3_real_data_protocol.json`), dataset source file(s)
  and their provenance (source dataset name, source file path/day, extraction script and version), split
  membership, seed(s) used, and a UTC timestamp — mirroring the `meta` block convention already used by
  `benchmarks/phase3_1_evaluate.py`.
- No raw file under `data/raw/` is modified by any Phase 3.1-RD script. All derived artifacts are written under
  `data/processed/`, `data/audit/`, or the new `experiments/results/phase3_real_data/` tree.

---

## 23. Comparison with original Phase 3

A comparison structure — not a rewrite — is produced once real-data evaluation actually runs. It is designed
now so the comparison is specified before any result exists:

For every hypothesis (H1–H7), the eventual comparison report records:

| Field | Content |
|---|---|
| Hypothesis | H1–H7, as defined in §1 |
| Original Phase 3 result | Verbatim from the frozen synthetic-data reports (`docs/PHASE3_1_EVALUATION_PROTOCOL.md` … `PHASE3_6_...md`) — not restated with new interpretation |
| Real-data result(s) | Per dataset, per §3's mapping; `NOT EVALUABLE` where applicable |
| Direction of agreement/disagreement | Supports / contradicts / partially supports / cannot adjudicate |
| Confidence/uncertainty | CI width and independent-unit N carried through from §14–17 |
| Dataset limitations | Restated from §17/§24 relevant to that hypothesis/dataset pairing |
| Interpretation | Whether the real-data result strengthens, weakens, contradicts, or cannot adjudicate the original finding — **disagreement is not automatically treated as evidence the original result was wrong**; both results are reported and the reasons a real-data result might diverge (different feature availability, different domain, different N, different leakage constraints) are stated alongside any interpretation |

This comparison structure is stored as its own document (e.g. `docs/PHASE3_REAL_DATA_COMPARISON.md`) when
produced — it does not overwrite `docs/PHASE3_4_COMPARISON.md` or any other original Phase 3 file.

---

## 24. Known limitations (carried forward, not resolved by this protocol)

- Alibaba: no machine-disjoint split exists (job↔machine many-to-many). Alibaba real-data H1/H2 experiments
  are necessarily scheduling/request-time-feature-only, not runtime-telemetry-based, per §7. Temporal split
  carries a confirmed ~2.2x base-rate shift (§9), which confounds any raw performance-delta interpretation
  between random and temporal splits.
- AIOps: `block=8` two-date irregularity and the +6-hour `log_time`/`start_time` shift for `log_block∈{4,5}`
  remain unexplained (§12). Whether fault-log index 1–11 were part of the scored evaluation or an unscored
  preview batch is uncertain. 27 of 43 fault-eligible entities never appear in the fault log — genuinely
  fault-free, or excluded for an unrelated reason, is an open question, and is not resolved by assumption.
  AIOps fault categories are injected (via the CCF challenge design), not organic — diagnosis results on AIOps
  are not claimed to generalize to organic fault taxonomies.
- AgentRx: benchmark-harness origin means results are not organic production evidence (§13). No timestamps
  exist, so H3/H4 are not evaluable. n=44/n=29 mean every AgentRx result carries wide, sometimes uninformative
  confidence intervals — a null or inconclusive AgentRx result is not strong evidence against a hypothesis; it
  may simply reflect insufficient power, and is reported with that caveat.
- No dataset supports H7 (recovery). This is a structural gap in the currently held real data, not a design
  choice of this protocol.
- No unified cross-dataset schema is imposed (§25) — this preserves each dataset's real structure but means no
  single combined statistical claim can be made across all three data sources; only qualitative
  consistency-checking is possible (§14).

---

## 25. Future unified benchmark/dataset implications

This protocol intentionally does not force Alibaba, AIOps, and AgentRx into a common schema — each dataset's
native structure, units, and limitations are preserved as-is (per the design intent already stated in
`docs/PHASE3_REAL_DATA_AIOPS_PROTOCOL.md` §10 for AIOps). For a future unified benchmark to be buildable from
this work, every Phase 3.1-RD extraction/processing artifact preserves, where the field genuinely exists in
the source data (never fabricated where it doesn't):

- `source_dataset` (e.g. `"Alibaba_GPU2020"`, `"AIOps_2020"`, `"AgentRx_Magentic"`, `"AgentRx_TauRetail"`)
- `source_record_id` / `source_event_id` (native ID: `job_name`, fault-log `index`, `trajectory_id`)
- `entity_id` (native: `machine`/`cmdb_id`/N/A for AgentRx — no forced remapping between datasets' conventions)
- `workload_id` (native: `task_name`/`domain` where applicable)
- `timestamp` (native format preserved alongside any converted UTC value; explicit `MISSING` marker, never
  imputed, where a dataset has none — e.g. AgentRx)
- `label_provenance` (how the label was derived: observed terminal status, injected fault, organic annotation)
- `processing_version` (script + version that produced the derived record)
- `split_membership` (random/temporal, train/val/test, as applicable)
- `data_quality_flags` (e.g. AIOps's `has_telemetry_coverage`, Alibaba's `_source_row_index` provenance
  column, the leakage-status flag for excluded fields)

No field is forced onto a dataset that does not naturally have it; a future benchmark record for AgentRx, for
example, carries an explicit missing-timestamp flag rather than a synthesized timestamp.

---

## 26. Stopping/decision rules — DO NOT RUN PHASE 3.1-RD YET

This document is a **protocol design and freeze deliverable only**. Per explicit instruction:

- No model training, evaluation, or representation comparison is performed under this document.
- Phase 3.1-RD (and any subsequent 3.2-RD…3.6-RD or Phase 4 real-data work) requires **separate, explicit
  authorization** before execution begins.
- Once authorized, execution follows this document and its companion config
  (`configs/phase3_real_data_protocol.json`) exactly; any deviation discovered to be necessary during
  execution is documented as an amendment with a rationale and timestamp, not applied silently.

---

## Appendix: file inventory referenced by this protocol

**Authoritative real-data sources (read, not modified):**
- `docs/PHASE3_REAL_DATA_FEASIBILITY_AUDIT.md`
- `docs/PHASE3_REAL_DATA_CLEANING_REPORT.md`
- `docs/PHASE3_REAL_DATA_AIOPS_PREPARATION_COMPLETE.md`
- `docs/PHASE3_REAL_DATA_AIOPS_PROTOCOL.md`
- `docs/PHASE3_REAL_DATA_AIOPS_NEGATIVE_WINDOW_PROTOCOL.md`
- `docs/PHASE3_REAL_DATA_ALIBABA_SENSOR_LEAKAGE_GATE.md`

**Original (synthetic) Phase 3 — frozen, read-only:**
- `docs/PHASE3_1_EVALUATION_PROTOCOL.md`, `PHASE3_2_REPRESENTATION_EXPERIMENTS.md`,
  `PHASE3_2C_CANDIDATE_ABLATION.md`, `PHASE3_3_GENERALIZATION.md`, `PHASE3_4_COMPARISON.md`,
  `PHASE3_5_ATTACK_GENERALIZATION.md`, `PHASE3_6_DIAGNOSIS_ABSTENTION_RECOVERY.md`, `PHASE3_FREEZE.md`
- `configs/phase3_1_protocol.json`, `phase3_5_attack_protocol.json`, `phase3_6_decision_recovery_protocol.json`
- `experiments/results/phase3_1/` … `phase3_6/` (all frozen, unmodified)

**Data (read-only for this protocol):**
- `data/raw/{alibaba_gpu2020,aiops_kpi,agentrx}/`
- `data/processed/{alibaba_gpu2020,aiops_kpi,agentrx}/`
- `data/audit/alibaba_gpu2020/{sampling_frame,sampling_report,splits_random_stratified,splits_temporal,splits_report}.json`

**New deliverables of this task:**
- `docs/PHASE3_REAL_DATA_PROTOCOL.md` (this document)
- `configs/phase3_real_data_protocol.json`
