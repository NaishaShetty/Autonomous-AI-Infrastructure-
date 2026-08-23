<a id="phase3-real-data-3-1-report"></a>
# PHASE3 REAL DATA 3 1 REPORT
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_3_1_REPORT.md`  
**Role:** Real-data Phase 3.1 (detection) report.

# Phase 3.1-RD — Real-Data Baseline/Signal Evaluation — Completion Report

**Executed under authorization**: explicit chat authorization received 2026-08-13, scoped to Phase 3.1-RD
execution only (Phase 3.2-RD–3.6-RD and Phase 4 explicitly not authorized).

---

## 1. Protocol version

`1.0`, matching `docs/PHASE3_REAL_DATA_PROTOCOL.md` and `configs/phase3_real_data_protocol.json`
(both frozen 2026-08-13, unmodified during this execution).

## 2. Execution date

2026-08-13.

## 3. Environment information

- Python 3.11.3
- numpy 2.4.6, pandas 3.0.5, scikit-learn 1.9.0, scipy 1.17.1
- Platform: Windows (win32), working directory `C:\Autonomous AI infrastructure`
- No GPU/accelerator used (CPU-only `LogisticRegression`, `sklearn.linear_model`)

## 4. Dataset versions/identifiers

| Dataset | Source | Files read |
|---|---|---|
| Alibaba GPU2020 | `data/processed/alibaba_gpu2020/{job_table.clean,task_table.main_sample,instance_table.main_sample}.csv`; splits from `data/audit/alibaba_gpu2020/{splits_random_stratified,splits_temporal}.json`; sample IDs from `data/audit/alibaba_gpu2020/sample_job_ids_main.txt` | main tier, 10,000 jobs |
| AIOps 2020 | `data/processed/aiops_kpi/platform/*.csv`; window manifests `data/audit/aiops_kpi/{positive_window_validation,negative_window_validation}.json` | 226 windows (81 positive, 145 negative) |
| AgentRx | `data/processed/agentrx/{magentic_joined,tau_retail_joined}.jsonl` | 44 (Magentic) + 29 (τ-Retail) annotated trajectories |

No file under `data/raw/` was opened or modified by any Phase 3.1-RD script — only `data/processed/` and
`data/audit/` artifacts were read.

## 5. Integrity checks (pre-execution, per §26 of the protocol)

| Check | Result |
|---|---|
| Execution gate authorized | `configs/phase3_real_data_protocol.json`'s static `execution_gate.authorized_to_run` field reads `false` — this field was never edited (editing the frozen config would itself be a prohibited protocol modification). Authorization for Phase 3.1-RD was instead granted explicitly via chat on 2026-08-13, which is the valid instruction channel the protocol's §26 anticipates ("requires separate, explicit authorization"). This is recorded here as the authorization-of-record; the static file field is left as-is. |
| Protocol version = 1.0 | Confirmed in both `docs/PHASE3_REAL_DATA_PROTOCOL.md` header and `configs/phase3_real_data_protocol.json.protocol_version` |
| Referenced datasets/splits/configs exist | All referenced files (§4 above) confirmed present before use; scripts fail fast (`FileNotFoundError`/`assert`) if a referenced file were missing — none were |
| Raw files unchanged | Not opened by any Phase 3.1-RD script this session; no write operation targeted `data/raw/` |
| Original Phase 3 frozen files untouched | No `docs/PHASE3_1_EVALUATION_PROTOCOL.md`…`PHASE3_6_...md`, no `configs/phase3_{1,5,6}_*.json`, no `experiments/results/phase3_1/`…`phase3_6/` file was opened for writing this session |
| Phase 4 untouched | No `docs/PHASE4_*`, `configs/phase4_*`, or `experiments/results/phase4_*` file was opened for writing this session |
| Execution environment matches frozen protocol | seed=42 (sampling/negative-window reuse), bootstrap seed=0/n=2000/95% CI as specified in `configs/phase3_real_data_protocol.json.statistics` — confirmed applied (§9, §17 below) |

No integrity check failed. Execution proceeded.

## 6. Exact sample sizes

| Dataset | N | Breakdown |
|---|---|---|
| Alibaba, random split | 10,000 jobs | train 6,999 / val 1,498 / test 1,503 |
| Alibaba, temporal split | 10,000 jobs | train 6,177 / val 1,324 / test 2,499 |
| AIOps | 226 windows | 81 positive / 145 negative; 0 dropped for missing telemetry |
| AgentRx Magentic | 44 annotated trajectories (of 58 total in source file) | — |
| AgentRx τ-Retail | 29 annotated trajectories (of 29 total in source file) | — |

## 7. Independent units

- Alibaba: **job** (bootstrap resamples test-set job rows).
- AIOps: **entity** (`cmdb_id`) — cluster bootstrap resamples the 43 entities, not the 226 windows; cross-validation is leave-one-entity-out (see §16).
- AgentRx: **trajectory**, per domain (Magentic and τ-Retail kept separate).

No correlated child row (Alibaba task/instance rows, AIOps within-entity windows) was counted as an
independent observation in any statistical estimator.

## 8. Feature set used

**Alibaba** (pre-outcome, request/scheduling-time only): `job_start_time`, `n_tasks`,
`n_distinct_task_names`, `sum_inst_num`, `mean_plan_cpu`, `max_plan_cpu`, `mean_plan_mem`, `max_plan_mem`,
`mean_plan_gpu`, `max_plan_gpu`, `n_distinct_gpu_types`, `dominant_gpu_type` (one-hot), `n_instances`,
`n_distinct_machines`, `mean_instance_start_time`.

**Feature-availability limitation, discovered during implementation**: the protocol's allowed-field list
(§7 of `docs/PHASE3_REAL_DATA_PROTOCOL.md`) includes `pai_group_tag_table` (`gpu_type_spec`, `group`,
`workload`) and `pai_machine_spec` (all fields). Neither table was ever materialized in processed/sampled
form during the earlier extraction work — only raw `.tar.gz` archives exist for them
(`data/raw/alibaba_gpu2020/pai_group_tag_table.tar.gz`, `pai_machine_spec.tar.gz`). This evaluation does
**not** extract them (doing so would require new extraction/decompression code, a change to the data
pipeline beyond a minimal baseline evaluation). Their absence narrows feature completeness; it does not
violate the leakage ceiling, since omitting an allowed field is always leakage-safe. `job_table.user` was
also deliberately excluded — it is allowed by the protocol but is a very high-cardinality identifier that
would require its own leakage-safe target-encoding design (fit on train only) to use responsibly; that is
out of scope for a minimal Phase 3.1-RD baseline and was not built.

**AIOps** (PRE-FAILURE window only, platform telemetry): `n_observations`, `n_distinct_metrics`, `mean_value`,
`std_value`, `min_value`, `max_value` (aggregated over all platform metric readings within
`[fault_onset−20min, fault_onset)` or the equivalent negative-window bounds), plus `object` (docker/db/os)
as a categorical feature. Source families: `dcos_docker.csv`, `dcos_container.csv` (docker entities),
`db_oracle_11g.csv` (db entities), `os_linux.csv` (os entities).

**Feature-availability limitation**: business telemetry (`esb.csv`) and call-trace windows were **not**
included in this minimal baseline. They are allowed by the protocol but are not cleanly attributable to a
single fault entity without additional join logic (service-name-to-entity mapping) that was not built here.
Documented, not a leakage issue.

**AgentRx**: no predictive feature set was built — see §16 (H1 not executable).

## 9. Leakage exclusions (enforced, verified)

- `pai_sensor_table`, `pai_machine_metric` — not read by the Alibaba script at all (not in any `usecols=`
  list, not merged).
- `max_mem`, `max_gpu_wrk_mem` — not read (these live only in `sensor_table.main_sample.csv`, which is never
  opened by `scripts/real_data/phase3_1_rd_alibaba_evaluate.py`).
- An `assert_no_excluded_columns` check runs against the final Alibaba feature frame before model fitting,
  as a defense-in-depth check (redundant with the above, since the excluded fields are never loaded, but
  verifies no column named `max_mem`/`max_gpu_wrk_mem` slipped in through any future edit).
- AIOps: only the PRE-FAILURE window `[fault_onset−20min, fault_onset)` (or the equivalent frozen negative
  window bounds) is queried for telemetry; DURING/POST-window data and fault-log descriptive/timing fields
  are never read as features.
- AgentRx: `failure_summary`, `failures`, `num_failures`, `root_cause_failure_id`, `root_cause_reason` were
  read only for descriptive reporting (§16), never as predictive input — moot in any case, since no
  predictive model was built for AgentRx.
- **No excluded-field usage was encountered or attempted during execution.**

## 10. Alibaba random-split results

| | Baseline A (no-signal) | Candidate F (supervised risk) |
|---|---|---|
| AUROC | 0.500 [0.500, 0.500] | **0.735** [0.703, 0.766] |
| AUPRC | 0.259 [0.237, 0.281] | **0.540** [0.487, 0.596] |

train n=6,999 (25.95% Failed), test n=1,503 (25.88% Failed). Bootstrap: 2,000 resamples, seed 0, job-level,
95% CI.

## 11. Alibaba temporal-split results

| | Baseline A (no-signal) | Candidate F (supervised risk) |
|---|---|---|
| AUROC | 0.500 [0.500, 0.500] | **0.793** [0.774, 0.812] |
| AUPRC | 0.434 [0.415, 0.454] | **0.636** [0.608, 0.667] |

train/val n=6,177 (Q1–Q3, 20.11% Failed), test n=2,499 (Q4, **43.42% Failed** — the disclosed base-rate
shift, reproduced here to 3 significant figures against the frozen `splits_report.json` values of
20.1%/43.4%). Bootstrap: 2,000 resamples, seed 0, job-level, 95% CI.

**Diagnostic check (not a new experiment — inspection of the already-fitted model's standardized
coefficients)**: because the Q4 test set differs from train partly *by definition* of being later in time,
a natural concern is that the model's apparent temporal-split lift is just memorizing "later `start_time` ⇒
higher risk" rather than learning anything about workload characteristics. The fitted logistic regression's
standardized coefficients do not support that concern: `job_start_time` (coefficient ≈ −0.022) and
`mean_instance_start_time` (≈ +0.032) are both near-zero, far below the dominant coefficients
(`sum_inst_num` ≈ −1.61, `n_instances` ≈ +1.61, `dominant_gpu_type` categories ≈ 0.5–0.6,
`max_plan_mem`/`max_plan_cpu` ≈ 0.4–0.5). The model's signal is driven by workload shape and resource-request
features, not by trivially encoding submission time. This is reported as a transparency check, not as
proof the model captures a deep causal mechanism.

## 12. AIOps exploratory results

Method: leave-one-entity-out (LOEO) cross-validation over the 43 entities (no hyperparameter tuning), then
entity-level cluster bootstrap (2,000 resamples, seed 0, 95% CI) on the pooled out-of-sample predictions.

| | Baseline A (no-signal, global prevalence) | Candidate F (supervised risk, LOEO) |
|---|---|---|
| AUROC | 0.500 [0.500, 0.500] | **0.646** [0.536, 0.760] |
| AUPRC | 0.353 [0.254, 0.438] | **0.575** [0.447, 0.666] |

226 windows (81 positive, 145 negative), 43 entities (16 positive-bearing, 27 negative-only), 0 windows
dropped for missing telemetry. **This result is EXPLORATORY, not confirmatory**, per protocol §12/§17/§18 —
the CI is wide (width 0.224 on AUROC) and reflects the small entity-clustered N, not high-precision
evidence.

**Implementation correction made during execution (documented per protocol §21's transparency requirement,
made before inspecting the candidate result)**: the first version of Baseline A used, for each held-out
entity's fold, the training-fold's own prevalence (i.e., the pool's prevalence with that entity excluded) as
the "no-signal" score. This produced AUROC 0.171 — far from the 0.5 a true no-signal baseline should
produce by construction. Diagnosis: entities vary sharply in how many positive windows they contribute
(median 5, max 10 per positive-bearing entity), so excluding a heavily-positive entity measurably lowers the
remaining pool's prevalence, which spuriously *anti-correlates* that per-fold constant with the excluded
entity's true label. This is an artifact of the per-fold-varying-constant design, not a property of the
data. It was corrected to a single fixed constant (the overall 226-window pool prevalence, 35.8%, applied
identically to every window regardless of fold) — matching Alibaba's Baseline A design (a fixed pre-computed
constant) — which produces AUROC exactly 0.500 as expected. **This correction changed only the reference
baseline's computation; the candidate model's LOEO predictions and resulting AUROC (0.646) were not
recomputed or altered by this fix.**

## 13. AgentRx Magentic results

**H1 (binary failure-risk signal) is NOT EXECUTABLE within the frozen 44-trajectory sample.** See §16.

Descriptive statistics only (44 annotated trajectories, of 58 total in the source file):
- `num_failures`: min 1, max 55, mean 6.70 — **zero trajectories have `num_failures = 0`**.
- `num_steps`: min 5, max 130, mean 50.0.
- `failure_categories` (multi-label, counts across 44 trajectories): Instruction/Plan Adherence Failure 25,
  Guardrails Triggered 23, Misinterpretation of Tool Output 17, Intent Plan Misalignment 7, Intent not
  supported 5, Invention of new information 5, Invalid Invocation 1, System Failure 1.

## 14. AgentRx τ-Retail results

**H1 is NOT EXECUTABLE**, same reason. Descriptive statistics only (29 annotated trajectories, all 29
trajectories in the source file are annotated):
- `num_failures`: min 1, max 4, mean 1.34 — again, zero trajectories with `num_failures = 0`.
- `num_steps`: min 20, max 62, mean 36.7.
- `failure_categories`: Underspecified User Intent 10, Intent Plan Misalignment 8, Misinterpretation of Tool
  Output 7, Instruction Adherence Failure 6, Invalid Invocation 2, Intent Not Supported 2, System Failure 1.

## 15. Baseline results

Summarized in §10–12 above (Baseline A, no-signal, per dataset/split). No calibrated-confidence baseline
(the original Phase 3's "Baseline B") was computed for any real dataset: none of the three real-data sources
has a pre-existing upstream classifier whose confidence output could be measured — this baseline has no
real-data analogue and was not fabricated. This was anticipated by protocol §15 ("Where a baseline… has a
real-data analogue, it is computed… ") and is reported here as a structural absence, not an omission.

## 16. Proposed/evaluated method results

"Candidate F" (supervised-risk analogue): a single `LogisticRegression` (scikit-learn defaults, no
hyperparameter search, `max_iter=2000`, `random_state=42`) fit on standardized numeric features plus
one-hot categoricals, using only the allowed/available pre-outcome feature set per dataset (§8). This
mirrors the original Phase 3's finding that supervised learning — not representation richness — is the
operative mechanism (Phase 3.2C), by using the simplest possible supervised model rather than any
hand-engineered representation. No second candidate, no representation ablation, and no ensemble was run —
that scope belongs to Phase 3.2-RD onward, not authorized in this execution.

**AgentRx H1, not executable — full explanation**: within the frozen sample (44 Magentic, 29 τ-Retail
annotated trajectories), every single trajectory has `num_failures ≥ 1`. There is no trajectory with zero
recorded failures in either frozen sample. A binary "will this trajectory fail" classifier requires both a
positive and a negative class; none exists here. The `has_failure_annotation` field distinguishes annotated
(44/58 Magentic, 29/29 τ-Retail) from non-annotated trajectories, but building a binary label from
"annotated vs. not annotated" would mean **adding the 14 non-annotated Magentic trajectories to the sample**,
which is explicitly prohibited by this authorization ("Do NOT… add/remove records… change the splits").
This was discovered during implementation and is reported here, per the instruction to stop and document
rather than improvise a workaround, as a genuine data-composition finding: **the currently held, frozen
AgentRx sample does not support a binary failure-occurrence prediction task.** A severity-regression
reframing (predicting `num_failures` as a count, or `failure_categories` as a multi-label target) might be
viable, but that is a different task definition than H1's "does a supervised failure-risk signal exist"
framing and was not specified by the frozen protocol — introducing it would be a protocol design decision,
which is outside Phase 3.1-RD's execution authorization and is left for the user's review.

## 17. Effect sizes

| Comparison | ΔAUROC (candidate − baseline A) |
|---|---|
| Alibaba random split | +0.235 |
| Alibaba temporal split | +0.293 |
| AIOps (LOEO, exploratory) | +0.146 |

All three are directionally consistent with the original Phase 3's core finding (a supervised signal exists
above no-signal), though the *magnitude* is not directly comparable — see §24/§25 for why.

## 18. 95% confidence intervals

All reported inline in §10–12; computed via nonparametric percentile bootstrap, 2,000 resamples, seed 0,
at the correct independent-unit level (job for Alibaba, entity for AIOps) per protocol §14/§16.

## 19. Statistical results

- Alibaba random split: Candidate F AUROC 95% CI [0.703, 0.766] excludes 0.5 entirely — signal is clearly
  present at confirmatory-capable precision.
- Alibaba temporal split: Candidate F AUROC 95% CI [0.774, 0.812] excludes 0.5 entirely — signal is present,
  but interpreted alongside the base-rate shift (§11) and the temporal-generalization caveat (§24).
- AIOps: Candidate F AUROC 95% CI [0.536, 0.760] — excludes 0.5, but only barely at the lower bound, and the
  interval is wide (width 0.224). This is exploratory evidence of a signal, not confirmatory evidence.
- No p-values were computed in isolation; every quantitative claim above is paired with its CI and effect
  size (§17), per protocol §14.

## 20. Failure cases

- AIOps Baseline A initial implementation was a genuine failure case (AUROC 0.171 instead of ~0.5) — caught,
  diagnosed, and corrected before finalizing results; full account in §12.
- No Alibaba job/window/trajectory failed to process (0 dropped in Alibaba feature build; 0 AIOps windows
  dropped for missing telemetry; all 226 windows had at least one telemetry observation in their PRE window
  or equivalent negative window).

## 21. Negative findings

- No calibrated-confidence baseline exists for any real dataset (§15) — a structural gap versus the original
  Phase 3, not a result of this execution.
- AgentRx H1 could not be executed at all (§13/§14/§16) — the most significant negative finding of this
  report: two of the four real datasets authorized for Phase 3.1-RD produced no H1 result whatsoever.
- Feature completeness for both Alibaba (`pai_group_tag_table`, `pai_machine_spec` unavailable) and AIOps
  (business/trace telemetry not included) is narrower than the protocol's full allowed set (§8) — the
  reported signal is a lower bound on what a more complete feature set might show, not an upper bound.

## 22. Inconclusive findings

- AIOps's AUROC 95% CI [0.536, 0.760] is exploratory-only and, while it excludes 0.5, the lower bound is
  close enough to 0.5 that this should not be treated as strong evidence — it is consistent with either a
  genuine modest signal or a somewhat optimistic point estimate from a small, entity-clustered sample. Per
  protocol §18, this remains classified EXPLORATORY regardless of the direction of the point estimate.

## 23. Dataset-specific limitations

- **Alibaba**: feature set restricted to a subset of the allowed fields (no `group_tag`/`machine_spec`, no
  `user`) — see §8. Machine-disjoint split was never built (documented upstream, §9 of the protocol doc,
  restated here). Temporal-split base-rate shift (20.1%→43.4%) confounds any raw performance comparison
  between random and temporal splits.
- **AIOps**: exploratory only; feature set restricted to platform telemetry only (no business/trace); the
  two unresolved timestamp irregularities (`block=8` two-date split, +6h `log_time` shift) remain
  undocumented in cause and were not investigated further in this execution (out of scope — they affect the
  frozen window manifests upstream, not this evaluation's logic).
- **AgentRx**: H1 structurally not evaluable given the frozen sample's 100%-failure composition (§16); no
  timestamps exist for either domain; benchmark-harness origin (not organic production traffic).

## 24. Interpretation

The real-data evidence for **H1 ("a supervised failure-risk signal exists beyond calibrated confidence")**
is:

- **Alibaba (both splits)**: a clear, confirmatory-capable-precision signal exists (AUROC 0.735–0.793,
  CIs excluding 0.5 by a wide margin). This is a *stronger* real-data result, in raw AUROC terms, than the
  original synthetic Phase 3.1's Candidate-F-equivalent result (AUROC 0.6548 [0.6159, 0.6938]). **This
  magnitude comparison should not be over-read**: the two tasks are not the same task. The original Phase
  3.1 predicted whether an upstream classifier's own prediction would be *wrong* (a meta-level, deliberately
  hard task calibrated to produce only a modest synthetic signal), whereas this Alibaba evaluation predicts
  whether a scheduled job will *fail outright* — a direct-outcome prediction task with no analogous upstream
  classifier in the loop. A higher AUROC here is not evidence that the original Phase 3 candidate was
  under-performing; it reflects a genuinely different, and arguably easier, prediction target. The
  qualitative finding — "a supervised model beats no-signal by a wide, statistically clear margin" — agrees
  directionally with H1's original conclusion. The magnitude does not transfer and is not claimed to.
- **AIOps**: weak, exploratory-only support for H1 (AUROC 0.646, CI barely excluding 0.5). Consistent in
  direction with H1 but far from confirmatory, exactly as the power analysis anticipated (§17 of the
  protocol document).
- **AgentRx**: cannot adjudicate H1 at all — no experiment could be run.

No claim of causality is made anywhere in this report — all results are associational (a fitted classifier's
discriminative performance), not a causal analysis. No claim of generalization beyond the evaluated domains,
splits, or feature sets is made. No claim of statistical significance is made without an accompanying CI and
effect size. No claim of recovery capability is made — H7 was not evaluated (not authorized, and no dataset
supports it regardless, per the frozen protocol's mapping).

## 25. Comparison implications for the original Phase 3

See the companion document `docs/PHASE3_REAL_DATA_COMPARISON.md`, created alongside this report and scoped
strictly to the H1 result actually produced here. The original Phase 3's frozen files
(`docs/PHASE3_1_EVALUATION_PROTOCOL.md`, `experiments/results/phase3_1/`, etc.) were not modified, read
for reference only.

## 26. Reproducibility information

- Scripts: `scripts/real_data/phase3_1_rd_alibaba_evaluate.py`, `scripts/real_data/phase3_1_rd_aiops_evaluate.py`
  (both deterministic: sampling/window reuse at `seed=42` upstream, model fit `random_state=42`, bootstrap
  `seed=0`); AgentRx descriptive statistics computed inline (no randomness involved).
- Result artifacts: `experiments/results/phase3_real_data/phase3_1/{alibaba_results.json,aiops_results.json,agentrx_descriptive.json}`,
  each embedding protocol version, dataset identifiers, feature set, exclusions, and bootstrap configuration.
- Re-running either script against the unmodified `data/processed/`/`data/audit/` artifacts reproduces the
  same numbers bit-for-bit (no non-seeded randomness is used anywhere in either script).

---

## Files created by this execution

- `scripts/real_data/phase3_1_rd_alibaba_evaluate.py`
- `scripts/real_data/phase3_1_rd_aiops_evaluate.py`
- `experiments/results/phase3_real_data/phase3_1/alibaba_results.json`
- `experiments/results/phase3_real_data/phase3_1/aiops_results.json`
- `experiments/results/phase3_real_data/phase3_1/agentrx_descriptive.json`
- `docs/PHASE3_REAL_DATA_3_1_REPORT.md` (this document)
- `docs/PHASE3_REAL_DATA_COMPARISON.md` (companion comparison artifact)

No file outside `scripts/real_data/`, `experiments/results/phase3_real_data/`, and this pair of new `docs/`
files was modified.

---

## STOP — Phase 3.1-RD complete

No later phase (3.2-RD…3.6-RD, Phase 4) was started. Awaiting review and separate authorization to proceed.
