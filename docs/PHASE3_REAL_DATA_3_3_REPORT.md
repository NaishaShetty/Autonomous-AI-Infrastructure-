# Phase 3.3-RD — Real-Data Generalization / Distribution-Shift Evaluation — Completion Report

**Executed under authorization**: explicit chat authorization received 2026-08-13, scoped to Phase 3.3-RD
execution only (Phase 3.4-RD–3.6-RD and Phase 4 explicitly not authorized).

---

## 1. Objective

Determine how well the real-data failure-risk signal generalizes when the evaluation distribution differs
from the training distribution — specifically, whether the representation behavior already observed on
Alibaba's frozen temporal split in Phase 3.2-RD (R0 ≈ 0.79, R1 ≈ 0.84, R2 collapsing to ≈ 0.40) reflects a
genuine generalization phenomenon, characterized here (not re-optimized, not repaired). This phase does
**not** search for a better representation, does not tune PCA, and does not attempt to make the temporal
result "look better."

## 2. Protocol version

`1.0` (`configs/phase3_real_data_protocol.json`, `docs/PHASE3_REAL_DATA_PROTOCOL.md`) — unchanged.
Representation matrix (`configs/phase3_2_rd_representation_matrix.json`) — unchanged, reused as-is; no
fourth representation added, none removed.

## 3. Authorization scope

Authorized: Phase 3.3-RD only. Not authorized: Phase 3.4-RD, 3.5-RD, 3.6-RD, Phase 4, any modification to
the frozen Real-Data Phase 3 protocol, any modification to original Phase 3 results. Confirmed respected
throughout (§21, §Files-created).

## 4. Integrity checks (pre-execution, per the authorization's explicit 10-point checklist)

| # | Check | Result |
|---|---|---|
| 1 | Phase 3.1-RD results unchanged | Alibaba random AUROC re-read: `0.7348398689698409` (identical to original); Alibaba temporal AUROC: `0.7931707840566771` (identical); AIOps AUROC: `0.6455824250651649` (identical) |
| 2 | Phase 3.2-RD results unchanged | Temporal R0/R1/R2 re-read: `0.7931707840566771 / 0.8433965882788796 / 0.39450623763274134` (identical to the frozen Phase 3.2-RD report); random R0/R1/R2 and AIOps R0/R1/R2 also re-confirmed identical |
| 3 | Frozen protocol version still 1.0 | Confirmed |
| 4 | Alibaba random split unchanged | 6,999 / 1,498 / 1,503 (train/val/test) — identical to Phase 3.1-RD/3.2-RD |
| 5 | Alibaba temporal split unchanged | 6,177 / 1,324 / 2,499 — identical |
| 6 | AIOps population unchanged | 81 valid positive windows, 145 valid negative windows — identical |
| 7 | AgentRx composition unchanged | Magentic 58 total / 44 annotated / 0 with zero failures; τ-Retail 29 total / 29 annotated / 0 with zero failures — identical to Phase 3.1-RD's finding |
| 8 | No excluded leakage features entered the pipeline | This phase's only new script (`phase3_3_rd_alibaba_distribution_shift.py`) reuses `build_feature_matrix()` and `assert_no_excluded_columns()` unmodified from Phase 3.1-RD's module; no new field was read; `pai_sensor_table`/`pai_machine_metric`/`max_mem`/`max_gpu_wrk_mem` remain unread |
| 9 | Phase 4 untouched | No file under `experiments/results/phase4_*`, `docs/PHASE4_*`, `configs/phase4_*` opened for writing |
| 10 | Original Phase 3 untouched | `experiments/results/phase3_1/aggregate_results.json` mtime unchanged, not opened for writing |

No integrity check failed. Execution proceeded.

## 5. Exact datasets

Alibaba GPU2020 main tier (identical 10,000-job sample, identical splits). AIOps 2020: **NOT EVALUABLE FOR
THIS GENERALIZATION ANALYSIS** (§9). AgentRx: **NOT EVALUABLE** (§10).

## 6. Independent units

Job (Alibaba) — unchanged from Phase 3.1-RD/3.2-RD. No unit-level change in this phase.

## 7. Exact splits

Alibaba temporal split, reused verbatim and unmodified: train/validation = relative-time Q1–Q3 (n=6,177/
1,324), test = strict future holdout Q4 (n=2,499). This **is** the frozen generalization/distribution-shift
condition specified by the protocol (`docs/PHASE3_REAL_DATA_PROTOCOL.md` §9) — Phase 3.3-RD does not define a
new split, does not rebalance Q4, and does not use Q4 labels to alter the model in any way.

## 8. Representation definitions

Identical to Phase 3.2-RD, reused unmodified from `configs/phase3_2_rd_representation_matrix.json`: R0
(raw/scaled), R1 (log1p-transformed heavy-tailed fields), R2 (PCA(2)-reduced numeric block). No fourth
representation was added. No representation was dropped. PCA dimensionality was **not** changed (no PCA(3),
PCA(5), PCA(10) or any variant was tested — that would be a new experiment, explicitly out of scope per the
authorization, and is instead listed as a possible future experiment in §22).

## 9. Distribution-shift characterization (new analysis performed in this phase, label-free except for the
already-disclosed base-rate figure)

A purely descriptive comparison of each feature's train (Q1–Q3) vs. test (Q4) distribution was computed —
**no model was fit, no test label was used to select or transform any feature**, and the previously-disclosed
failure-rate shift is restated, not recomputed differently. Source:
`experiments/results/phase3_real_data/phase3_3/alibaba_distribution_shift.json`
(`scripts/real_data/phase3_3_rd_alibaba_distribution_shift.py`).

**Already-established label shift** (identical figure to Phase 3.1-RD/3.2-RD, restated for context): train
20.11% Failed, test 43.42% Failed.

**Newly characterized covariate shift** (this phase's contribution):

| Feature | Train mean | Test mean | Train median | Test median | Note |
|---|---|---|---|---|---|
| `mean_plan_cpu` | 691.8 | 465.9 | 600 | 600 | test jobs request ~33% less CPU on average |
| `max_plan_cpu` | 708.6 | 478.6 | 600 | 600 | same pattern |
| `mean_plan_gpu` | 70.5 | 56.4 | **50** | **25** | test median GPU allocation halves |
| `max_plan_gpu` | 70.6 | 56.4 | 50 | 25 | same pattern |
| `sum_inst_num` | 6.29 | 4.33 | 1 | 1 | test jobs request fewer total instances on average |
| `n_instances` | 6.57 | 4.64 | 1 | 1 | same pattern |
| `n_distinct_machines` | 4.71 | 3.41 | 1 | 1 | same pattern |
| `job_start_time` (std) | 1,279,722 | 262,293 | — | — | test period (Q4) spans a much narrower absolute time window than the pooled Q1–Q3 train period, as expected from quartile construction |

| `dominant_gpu_type` | Train proportion | Test proportion |
|---|---|---|
| MISC | 62.1% | **80.9%** |
| T4 | 23.6% | 12.1% |
| P100 | 7.2% | 4.0% |
| V100 | 3.1% | 1.2% |
| V100M32 | 2.0% | 0.5% |
| UNKNOWN | 2.1% | 1.2% |

**Observation**: this is a genuine covariate shift, not merely a label-rate shift — the Q4 test period has
systematically smaller resource requests (CPU, GPU, instance counts) and a substantially different GPU-type
mix (MISC share rising ~19 points) than the Q1–Q3 training period. Both the label distribution and the
feature distributions differ between train and test. This is reported as a factual characterization of the
evaluation environment; no causal claim about *why* the platform's workload composition changed over time is
made — that is outside what this data can determine.

## 10. Alibaba generalization results

**These are the exact, unmodified R0/R1/R2 temporal-split results already produced and frozen in Phase
3.2-RD** (`experiments/results/phase3_real_data/phase3_2/alibaba_results.json`,
`results.temporal.representations`). They are reused here, not rerun, not recomputed, and not altered in
any way — re-running the identical deterministic script (fixed seeds throughout) against unmodified data
would reproduce them bit-for-bit, so no new computation was performed. This is precisely the frozen temporal
generalization experiment the objective (§1) calls for; Phase 3.3-RD's contribution is characterizing (§9)
and interpreting (§17) that already-frozen result, not re-deriving it.

| Representation | AUROC | 95% CI | AUPRC | 95% CI |
|---|---|---|---|---|
| R0 (raw/scaled) | 0.793 | [0.774, 0.812] | 0.636 | [0.608, 0.667] |
| R1 (log1p-transformed) | **0.843** | [0.826, 0.861] | 0.736 | [0.705, 0.769] |
| R2 (PCA(2)-reduced) | **0.395** | [0.371, 0.418] | 0.356 | [0.337, 0.377] |

Baseline A (no-signal), for reference: AUROC 0.500 [0.500, 0.500], AUPRC 0.434 [0.415, 0.454] (AUPRC above
0.5-baseline-AUROC because AUPRC's uninformative floor equals the positive prevalence, 43.42% at Q4, not
0.5 — see §11 for why raw AUROC/AUPRC must be read against this prevalence, not in isolation).

## 11. AUPRC and AUROC, interpreted against Q4 prevalence

Q4's positive (Failed) prevalence is 43.42% — over double the 20.11% train-period rate. A few consequences,
stated explicitly per the authorization's instruction not to interpret AUPRC without this context:

- AUPRC's uninformative baseline is the positive prevalence itself (here, 0.434), not 0.5. R0's AUPRC (0.636)
  and R1's (0.736) both clear that elevated floor by a wide margin; R2's AUPRC (0.356) falls **below** the
  0.434 floor — i.e., R2 is worse than a random-ranking classifier would be expected to score on this
  prevalence, consistent with (and reinforcing) its sub-0.5 AUROC.
- A higher raw AUROC on the Q4 test set is **not**, by itself, evidence of better real-world deployment
  performance: Q4's substantially higher base rate changes the cost/benefit profile of any fixed decision
  threshold, and the covariate shift documented in §9 means the *feature values* a deployed model would see
  in a Q4-like future period differ systematically from what it was trained on. AUROC/AUPRC quantify ranking
  quality on this specific, already-shifted test set — they do not by themselves certify that a threshold
  calibrated on Q1–Q3 would behave sensibly on Q4, a question this phase does not attempt to answer (no
  threshold/calibration analysis was in scope or run).

## 12. Effect sizes

| Comparison | ΔAUROC | Interpretation |
|---|---|---|
| R1 vs. R0 (temporal) | +0.050 | Non-overlapping 95% CIs — a real, reproducible difference under this specific train/test pair, not noise |
| R2 vs. R0 (temporal) | −0.398 | Large, adverse, tightly-bounded (CI width 0.047) — R2 is not merely weaker, it is anti-informative on this split |
| R0 (temporal) vs. R0 (random, Phase 3.2-RD reference 0.735) | +0.058 | Not comparable at face value — different test populations with different prevalence (§11); not interpreted as "temporal generalizes better than random" |

## 13. Comparison with Phase 3.1-RD

Phase 3.1-RD evaluated only R0 (called "Candidate F" there) on the temporal split: AUROC 0.793 [0.774,0.812].
That number is exactly R0's value here (same computation, same data, same code path) — **no change**. Phase
3.1-RD did not test whether this behavior was representation-dependent; that question was first answered in
Phase 3.2-RD (§14) and is now characterized further (not re-answered) in this phase.

## 14. Comparison with Phase 3.2-RD

Phase 3.2-RD is where R0/R1/R2's temporal-split behavior was first measured (§10 of that report) — this
phase reuses those exact numbers unchanged (§10 above) and adds the covariate-distribution characterization
(§9) that Phase 3.2-RD's scope (representation robustness) did not include. No representation's result
changed between Phase 3.2-RD and this phase, because none was re-run with any different configuration — this
persistence is itself the finding requested by the objective (§1): the previously observed R1>R0≫R2 ordering
is not an artifact of a single run; it is the frozen, reproducible state of the evaluation, now placed in the
context of a characterized (not just observed) real covariate shift.

## 15. Comparison with original Phase 3

The original (synthetic) Phase 3.3 (`docs/PHASE3_3_GENERALIZATION.md`) tested **concept drift** — varying
`drift_scale` at test time only, under a **fixed covariate distribution** — and found the frozen Candidate F
representation generalized: AUROC stayed well above no-signal across weaker (0.698), original (0.655), and
stronger (0.602) drift conditions, without needing to vary representation (only one representation, the
frozen Candidate F, was ever tested in the original Phase 3.3).

This real-data Phase 3.3-RD result is **not a replication of that finding** — it is a different, complementary
condition:
- The original Phase 3.3 explicitly excluded covariate shift (fixed feature distribution) and tested only
  concept drift (label-generating relationship changing).
- Alibaba's Q1–Q3→Q4 split, as characterized in §9, is **both** a label-rate shift **and** a genuine covariate
  shift (resource-request sizes and GPU-type mix both shift), and Phase 3.2-RD showed representation choice
  interacts strongly with it (R1 improves, R2 collapses).
- The two experiments therefore **cannot be directly compared** as confirming or contradicting one another —
  they probe different shift types (concept-only vs. concept+covariate) and, unlike the original, this one
  varies representation rather than holding a single representation fixed. This is reported as **NOT
  DIRECTLY COMPARABLE**, not forced into a replicated/contradicted classification.
- The qualitative lesson that *does* carry over loosely: the original Phase 3.3 found the frozen candidate
  representation (their only one) generalized under concept drift; this real-data result shows that whether
  a real-data representation generalizes under a real (concept+covariate) shift **depends on which
  representation** — a nuance the original single-representation design could not have surfaced, since it
  never had a second representation to compare against under drift.

## 16. Distribution-shift findings

Summarized from §9: Q1–Q3→Q4 is a compound shift — failure-rate increase (20.1%→43.4%), reduced average
resource requests (CPU/GPU/instance counts all lower in Q4), and a substantial GPU-type composition shift
(MISC share 62.1%→80.9%). This is presented as a factual characterization; §17 discusses (as hypotheses, not
proven mechanisms) how this might relate to R1/R2's divergent behavior.

## 17. Alternative explanations (explicitly hypotheses, not demonstrated causes)

Per the authorization's instruction, the following are offered as **candidate hypotheses only** — none is
claimed as demonstrated:

- **Heavy-tailed feature behavior under shift (favors R1's improvement)**: `sum_inst_num`, `plan_cpu`,
  `plan_gpu`, and instance/machine counts are right-skewed (train means far exceed medians in every case,
  e.g. `mean_plan_cpu` mean 691.8 vs. median 600). A linear model on raw values can be disproportionately
  sensitive to the tail; log-compression may make the learned relationship more stable across a shift in the
  tail's shape. This is a plausible mechanism for R1 > R0, not a proven one.
- **PCA projection instability under covariate shift (favors R2's collapse)**: PCA(2) is fit only on Q1–Q3
  training data. If the dominant axes of variance in Q1–Q3 (the directions PCA(2) captures) do not align the
  same way with the failure label once the covariate distribution shifts (§9's GPU-type and resource-size
  changes), a linear classifier trained on those axes could see its learned "risk-increasing" direction
  become partially or wholly inverted on the shifted test data — a known failure mode of unsupervised
  dimensionality reduction under covariate shift. Also plausible, not demonstrated: no experiment
  decomposing the PCA components' loadings pre/post shift was run in this phase (that would be a new
  analysis — see §22).
- **Changed workload composition changing the feature-label relationship (concept drift, not just covariate
  shift)**: it is possible that the *relationship* between a given resource-request pattern and failure
  probability itself changed between Q1–Q3 and Q4 (true concept drift), independent of or in addition to the
  covariate shift documented in §9. This phase's design (fixed model, fixed train/test split) cannot
  distinguish covariate shift from concept drift as the dominant driver — doing so would require a dedicated
  experiment (e.g., holding covariates fixed and varying only time, which the real data does not allow to be
  cleanly separated) and is not attempted here.

No claim of causality is made for any of the above. They are offered as candidate explanations consistent
with the observed pattern, explicitly to satisfy the requirement not to assert an unproven mechanism as fact.

## 18. AIOps

**NOT EVALUABLE FOR THIS GENERALIZATION ANALYSIS.** The frozen AIOps protocol provides no legitimate
independent distribution-shift/generalization condition: the 226-window population has no frozen train/test
temporal partition (unlike Alibaba's Q1–Q3/Q4 split), and constructing one now (e.g., an April-vs-May split)
would be inventing a new split after the fact — explicitly prohibited by this authorization ("Do NOT
manufacture temporal splits from the data simply to obtain a generalization experiment"). The existing LOEO
structure tests entity-level generalization, not distribution shift, and was already exercised in Phase
3.1-RD/3.2-RD; it is not re-run here since nothing about it would test a *shift* condition. AIOps remains
EXPLORATORY ONLY per the frozen protocol and this phase adds no AIOps result.

## 19. AgentRx

**NOT EVALUABLE**, for the same reason established in Phase 3.1-RD and reconfirmed in Phase 3.2-RD: both
frozen samples (44 Magentic, 29 τ-Retail annotated trajectories) contain no negative class (every trajectory
has ≥1 recorded failure), so no supervised classifier exists whose generalization could be tested. No
unannotated trajectories were added; the two domains were not pooled; no workaround was attempted.

## 20. Positive findings

- R1 (log1p-transformed) not only survives but *improves* under the temporal distribution shift relative to
  R0 (+0.050 AUROC, non-overlapping CI) — a genuinely positive, reproducible result for that representation
  under this specific shift.
- The distribution-shift characterization (§9) is itself a positive contribution: it establishes, using only
  pre-outcome covariates and without any test-label tuning, that Q1–Q3→Q4 is a real, multi-faceted shift
  (label rate, resource-request sizes, GPU-type mix) — not a sampling artifact.

## 21. Negative findings

- **R2 (PCA(2)) remains below the no-signal baseline under the temporal shift** (AUROC 0.395, tight CI
  [0.371, 0.418]) — reported prominently, exactly as instructed, not minimized. This is the same result
  already reported in Phase 3.2-RD, reconfirmed here as the frozen, unmodified state (§4, checks 1–2), not a
  new negative finding but a persistent one.

## 22. Inconclusive findings / limitations

- The mechanism behind R1's improvement and R2's collapse (§17) remains **undetermined** — three plausible
  hypotheses are offered, none confirmed. This is intentionally left inconclusive rather than resolved by a
  new, unauthorized experiment.
- AIOps and AgentRx contribute no generalization evidence in this phase (§18, §19) — the real-data
  generalization question is answered by Alibaba alone in this execution.
- The Alibaba temporal result reflects one single train/test partition (Q1–Q3 vs. Q4); no repeated or
  cross-validated temporal generalization estimate exists (the frozen protocol defines only this one
  temporal split), so the precision of "how well does this generalize" is bounded by having exactly one
  such comparison, not several.

## Future experiments (explicitly NOT run in this phase — separated from current findings)

The following are documented as candidate follow-up work only. **None of them was performed, and none
influenced any result reported above**:

- Testing PCA at other dimensionalities (PCA(3), PCA(5), PCA(10), …) to see whether R2's collapse is
  specific to 2 components — would require a new, separately pre-registered representation matrix under a
  future authorized phase, not this one.
- Decomposing PCA(2)'s component loadings before vs. after the shift to directly test the "projection
  instability" hypothesis in §17, rather than leaving it as an untested hypothesis.
- A dedicated experiment isolating covariate shift from concept drift (e.g., reweighting or matching on
  covariates) to determine which dominates the Q1–Q3→Q4 shift's effect on representation robustness.
- Threshold/calibration analysis under the shifted Q4 prevalence, since §11 notes that ranking-quality
  metrics (AUROC/AUPRC) alone do not certify deployment-time decision quality under a shifted base rate.

## 23. Reproducibility information

- New script: `scripts/real_data/phase3_3_rd_alibaba_distribution_shift.py` — deterministic, no randomness
  involved (purely descriptive statistics), reuses `build_feature_matrix()` from the unmodified Phase 3.1-RD
  module.
- No model-fitting script was created or run in this phase; §10's results are citations of
  `experiments/results/phase3_real_data/phase3_2/alibaba_results.json`, not new computations.
- Result artifact: `experiments/results/phase3_real_data/phase3_3/alibaba_distribution_shift.json`, embedding
  phase, protocol version, dataset identifier, and the exact train/test sample sizes.
- Provenance preserved: the distribution-shift script operates on the same provenance-carrying processed CSVs
  and the same frozen split-membership file as all prior phases; no field was stripped or renamed.

---

## Files created by this execution

- `scripts/real_data/phase3_3_rd_alibaba_distribution_shift.py`
- `experiments/results/phase3_real_data/phase3_3/alibaba_distribution_shift.json`
- `docs/PHASE3_REAL_DATA_3_3_REPORT.md` (this document)
- `docs/PHASE3_REAL_DATA_COMPARISON.md` (updated by addition only — see that file's new H3 section)

No file outside `scripts/real_data/`, `experiments/results/phase3_real_data/phase3_3/`, and these two `docs/`
files was modified. Phase 3.1-RD's and Phase 3.2-RD's artifacts, the frozen Real-Data Phase 3 protocol, the
original Phase 3 results, and Phase 4 were all re-verified unchanged (§4).

---

## STOP — Phase 3.3-RD complete

No later phase (3.4-RD…3.6-RD, Phase 4) was started. Awaiting review and separate authorization to proceed.
