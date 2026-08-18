<a id="phase3-real-data-3-5-report"></a>
# PHASE3 REAL DATA 3 5 REPORT
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_3_5_REPORT.md`  
**Role:** Real-data Phase 3.5 (attack/generalization) report.

# Phase 3.5-RD — Unseen-Workload Generalization — Completion Report

**Executed under authorization**: explicit chat authorization received 2026-08-13, scoped to Phase 3.5-RD
execution only (Phase 3.6-RD and Phase 4 explicitly not authorized).

---

## 1. Objective

Determine whether the observed real-data failure-risk signal remains useful when evaluated on
workloads/conditions **entirely absent from the corresponding training population** — a distinct axis from
Phase 3.3-RD's temporal distribution-shift characterization, and from Phase 3.1-RD/3.2-RD/3.4-RD's
entity-level (AIOps LOEO) or split-level (Alibaba random/temporal) evaluations.

## 2. Protocol version

`1.0` — unchanged. New companion config: `configs/phase3_5_rd_generalization_protocol.json`, written and
frozen before any Phase 3.5-RD result was produced.

## 3. Exact definition of generalization used here

"Unseen workload/condition" = a categorical partition, already present in the frozen processed data (not
invented for this phase), along which the train and test populations share **zero** overlap in category
membership. This is the pre-existing-categorical-structure axis the authorization explicitly permitted
("GPU/workload categories; predefined workload groups... other already-existing categorical workload
structure"), used in place of the original Phase 3.5's synthetic attack-perturbation mechanism, which has no
legitimate real-data analogue (§26).

## 4. Pre-registered generalization matrix

Frozen in `configs/phase3_5_rd_generalization_protocol.json` before any evaluation:

- **Alibaba**: hold out `dominant_gpu_type == "T4"` entirely from training.
- **AIOps**: hold out the `db` object-family entirely from training.
- **AgentRx**: `NOT_EVALUABLE` (unchanged blocker, restated §14).

**Category-selection rule, applied identically to both eligible datasets, fixed before evaluation**: hold out
the *largest non-dominant* category — large enough for a statistically usable test population, but not the
dominant category (which would leave too little data to train on). This is a mechanical, symmetric rule, not
a choice made after observing which holdout produces a larger or more interesting effect.

## 5. Dataset eligibility

| Dataset | Eligible categorical field | Eligible? |
|---|---|---|
| Alibaba | `dominant_gpu_type` (6 categories: MISC, T4, P100, V100, V100M32, UNKNOWN) | Yes |
| AIOps | entity object-family (docker/db/os, derived from `cmdb_id` prefix) | Yes |
| AgentRx | none — no categorical workload field exists whose holdout would leave a usable population, and the underlying binary-classification blocker (no negative class) makes the question moot regardless | No — `NOT_EVALUABLE` |

## 6. Independent units

Job (Alibaba). Entity (AIOps, cluster bootstrap over the 13 held-out `db` entities). Not applicable (AgentRx).

## 7. Training populations

- **Alibaba**: all main-tier jobs with `dominant_gpu_type != "T4"` — n=7,938 (of the same, unmodified,
  frozen 10,000-job main-tier sample; no resampling, no new jobs).
- **AIOps**: all `docker`+`os` entities' windows — 30 entities, 170 windows (69 positive, 101 negative) (of
  the same, unmodified, frozen 226-window population; no resampling, no new windows).
- **AgentRx**: not applicable.

## 8. Generalization/test populations

- **Alibaba**: all main-tier jobs with `dominant_gpu_type == "T4"` — n=2,062. Verified programmatically
  (`held_out_category_present_in_train: false`) that T4 does not appear anywhere in the training population.
- **AIOps**: all `db` entities' windows — 13 entities (2 positive-bearing, 11 negative-only), 56 windows (12
  positive, 44 negative). Verified programmatically (`held_out_family_present_in_train: false`).
- **AgentRx**: not applicable.

## 9. Representation definitions

R0 (raw/scaled), R1 (log1p-transformed), R2 (PCA(2)-reduced) — identical, unmodified, frozen in Phase
3.2-RD. No new representation was added; none was dropped.

## 10. Baseline definition

Baseline A (no-signal) — a fixed constant equal to the **training population's** empirical positive
prevalence for this specific generalization condition (Alibaba: 29.9% among non-T4 jobs; AIOps: 40.6% among
docker+os windows), applied unchanged to the held-out test population. No new baseline was introduced; no
calibrated-confidence baseline was substituted (none exists in the real-data track, unchanged since Phase
3.1-RD §15).

## 11. Leakage exclusions

Unchanged: `pai_sensor_table`, `pai_machine_metric`, `max_mem`, `max_gpu_wrk_mem` excluded from Alibaba;
`pai_group_tag_table`/`pai_machine_spec` remain unavailable and unused; AIOps restricted to platform
telemetry within the frozen PRE-FAILURE window. **New note specific to this phase**: both `dominant_gpu_type`
(Alibaba) and `object` (AIOps) are themselves model input features. Because the held-out category never
appears in training, the fitted `OneHotEncoder` has no learned column for it — held-out test rows receive an
all-zero encoding for that block (`handle_unknown="ignore"`), which is the correct and intended behavior for
a genuine unseen-category test, not a bug: the model has no category-specific learned weight to fall back on
and must generalize from the remaining features alone.

## 12. Alibaba results

| | n | Positive rate | Baseline A AUROC | R0 AUROC | R1 AUROC | R2 AUROC |
|---|---|---|---|---|---|---|
| Train (non-T4) | 7,938 | 29.9% | — | — | — | — |
| Test (T4, unseen) | 2,062 | **10.8%** | 0.500 [0.500,0.500] | 0.571 [0.532,0.609] | 0.550 [0.512,0.587] | 0.509 [0.469,0.550] |

**A striking, unplanned finding surfaced by this condition** (not the generalization question itself, but
directly relevant context for interpreting it): T4-dominant jobs fail at 10.8%, roughly a third the rate of
non-T4 jobs (29.9%). GPU type carries a strong, direct association with the base failure rate — a fact this
phase's design surfaces as a byproduct of partitioning on it, not something searched for.

| Candidate | Paired ΔAUROC vs. Baseline A | 95% CI | Verdict |
|---|---|---|---|
| R0 | +0.071 | [0.032, 0.109] | Significant, but small |
| R1 | +0.050 | [0.012, 0.087] | Significant, but small — CI barely excludes 0 |
| R2 | +0.009 | [−0.031, 0.050] | **Not significant** — CI includes 0 |

## 13. AIOps results

| | n windows | n entities | Positive rate | Baseline A AUROC | R0 AUROC | R1 AUROC | R2 AUROC |
|---|---|---|---|---|---|---|---|
| Train (docker+os) | 170 | 30 | 40.6% | — | — | — | — |
| Test (db, unseen) | 56 | 13 | 21.4% | 0.500 [0.500,0.500] | 0.748 [0.596,0.933] | 0.725 [0.565,0.910] | 0.446 [0.190,0.634] |

**EXPLORATORY** — the held-out population is very small (13 entities, only 2 positive-bearing), and the
bootstrap itself reflects this: only 1,765 of 2,000 resamples produced both classes (235 resamples drew zero
positive entities from the pool of just 2), which is reported transparently, not hidden.

| Candidate | Paired ΔAUROC vs. Baseline A | 95% CI | Verdict |
|---|---|---|---|
| R0 | +0.248 | [0.096, 0.433] | Significant, and a **large** point estimate — but from a tiny, wide-CI test population |
| R1 | +0.225 | [0.065, 0.410] | Significant, similarly wide |
| R2 | −0.054 | [−0.310, 0.134] | **Not significant** — CI includes 0, and the point estimate is negative |

## 14. AgentRx results

**NOT EVALUABLE.** Both frozen samples (44 Magentic, 29 τ-Retail annotated trajectories) contain zero
trajectories with `num_failures = 0` — the same H1 blocker established in Phase 3.1-RD and reconfirmed every
phase since. No categorical workload field exists whose unseen-holdout could be tested even in principle
without first resolving that structural absence of a negative class. No unannotated trajectory was added; no
substitute task was invented; the two domains remain unpooled.

## 15. AUROC

Reported in full in §12–13. Summary: on Alibaba, R0/R1 show small but statistically real improvements over
no-signal on the unseen-GPU-type population; R2 does not. On AIOps, R0/R1 show large point estimates but with
very wide CIs from a tiny test population; R2 does not improve over no-signal (and its point estimate is
below 0.5).

## 16. AUPRC

Interpreted against each population's own positive prevalence, per the authorization's explicit instruction —
**never compared across the two datasets or across conditions without restating prevalence**:
- Alibaba T4 test: prevalence 10.8%. Baseline A AUPRC 0.108 [0.095,0.121] (as expected, tracks prevalence for
  a constant predictor). R0's AUPRC 0.146 clears this floor modestly; R1 (0.118) and R2 (0.119) barely clear
  it or sit within its CI.
- AIOps db test: prevalence 21.4%. Baseline A AUPRC 0.218 [0.106,0.378] (wide, small-N). R0's AUPRC (0.518)
  and R1's (0.490) clear this floor substantially; R2's (0.331) sits within the baseline's own wide CI —
  consistent with its non-significant AUROC finding.

## 17. Effect sizes

Paired mean differences reported throughout §12–13, computed identically (paired job-level bootstrap for
Alibaba, paired entity-cluster bootstrap for AIOps) to the methodology introduced in Phase 3.4-RD.

## 18. 95% CIs

All reported inline; 2,000 resamples, seed 0, percentile method, at the correct independent-unit level.
AIOps's `n_valid_resamples: 1765` (not 2000) is reported explicitly rather than silently treating it as 2000
— a direct consequence of the tiny (2-entity) positive pool in the held-out population, not a computation
error.

## 19. Distribution-shift context

This is **not** a repeat of Phase 3.3-RD. Phase 3.3-RD characterized the Alibaba **temporal** (Q1–Q3→Q4)
shift — a compound change in label rate, resource-request sizes, and GPU-type mix, with train and test
populations still sharing every GPU-type category, just in different proportions. This phase's Alibaba
condition is structurally different: the T4 category is **completely absent** from training, not merely
underrepresented — a categorical, not proportional, shift. The two are complementary, not duplicative:
Phase 3.3-RD asked "how does performance change when the *mix* of conditions shifts over time," this phase
asks "how does performance hold up on a condition the model never saw at all."

## 20. Positive findings

- On both eligible datasets, R0 and (with a smaller margin) R1 show a statistically real improvement over
  no-signal on an entirely unseen workload category — the failure-risk signal is not purely an artifact of
  having seen every category during training.
- The AIOps db-holdout point estimates (R0 0.748, R1 0.725) are numerically the strongest in this report,
  though this must be read alongside the small-N caveat (§13, §21).

## 21. Negative findings

- **R2 (PCA(2)) shows no statistically distinguishable improvement over no-signal on either dataset's
  unseen-workload test** — CI includes 0 on both Alibaba (T4) and AIOps (db). This is a third, independent
  piece of evidence (alongside Phase 3.2-RD/3.3-RD/3.4-RD's temporal-shift finding) that R2 is the least
  robust of the three representations, now specifically under a categorical-holdout generalization condition
  rather than a temporal one.
- The magnitude of improvement on Alibaba's unseen-GPU-type test (R0 AUROC 0.571) is **substantially smaller**
  than on the random split (0.735) or temporal split (0.793) — the signal generalizes far less completely to
  a truly unseen workload category than it does within a population that shares the same categories, just
  different individual jobs or a different time window.

## 22. Inconclusive findings

- AIOps's large point estimates (R0/R1 ≈ 0.73–0.75) come with CIs wide enough (up to ±0.17 half-width) that
  they should not be read as a confident claim of strong cross-family generalization — the underlying test
  population (13 entities, 2 positive-bearing) is simply too small to support a precise estimate in either
  direction.
- R1's Alibaba paired CI [0.012, 0.087] barely excludes 0 — treated as weak, not strong, evidence.

## 23. NOT_EVALUABLE components

AgentRx (both domains) — §14. The original attack-matrix mechanism itself — §26 (not reproducible on real
data without fabrication, and therefore not attempted in any form, including a diluted or partial version).

## 24. Comparison with Phase 3.1-RD

Phase 3.1-RD established that a supervised signal exists at all (AUROC 0.735 random, 0.793 temporal, 0.646
AIOps LOEO). This phase shows that signal's magnitude is **not uniform across generalization axes** — it
degrades substantially (to 0.51–0.75 depending on dataset and representation) when the test population shares
no categories with training, versus holding up much better (0.72–0.84) when train and test differ only in
time or random assignment but share the same category mix.

## 25. Comparison with Phase 3.2-RD

Phase 3.2-RD established R0≈R1≈R2 on the random split and R1>R0≫R2 on the temporal split. This phase adds a
third data point: on unseen-category generalization, R0 and R1 both show small-to-moderate significant
effects while **R2 shows none** on either dataset — consistent with, and extending, Phase 3.2-RD's finding
that R2 is the least representation-robust choice, now under a condition Phase 3.2-RD never tested.

## 26. Comparison with Phase 3.3-RD

Distinct, complementary axis — see §19. Phase 3.3-RD's compound covariate+label shift and this phase's
categorical holdout are both "distribution shift" in a loose sense but are structurally different
conditions and are not merged or compared numerically against each other in this report.

## 27. Comparison with Phase 3.4-RD

Phase 3.4-RD established, via a paired test, that R2 significantly *harms* relative to no-signal specifically
on the Alibaba temporal split, while R0/R1 significantly help on every condition tested there. This phase's
paired tests show a related but distinct pattern: R2 does not significantly harm on either unseen-workload
condition (both CIs straddle 0, not entirely negative) — R2's failure mode here is "no reliable benefit,"
not "reliable harm," a real and reportable distinction from the temporal-shift finding, not the same result
restated.

## 28. Comparison with original Phase 3.5

| Field | Content |
|---|---|
| **Original Phase 3.5 result** | F (Supervised Failure Risk) survives synthetic covariate-shift attacks (additive noise, feature dropout) on held-out synthetic data without retraining, remaining competitive with (not superior to) calibrated confidence at every severity level; 🟢 GENERALIZATION SUPPORTED, narrowly scoped. |
| **Real-data result** | The original's literal mechanism (synthetic feature perturbation) is **NOT EVALUABLE** on real data — no already-existing real-data analogue of injected noise/dropout exists, and fabricating one is explicitly prohibited. Using the reframed, real, non-synthetic axis this authorization permitted instead (unseen categorical workload), R0/R1 show a real but much smaller generalization margin than on in-distribution splits; R2 shows none. |
| **Direction of agreement/disagreement** | **Not directly comparable** — different mechanism entirely (synthetic post-hoc perturbation vs. real categorical exclusion), explicitly acknowledged rather than forced into a false replication. |
| **Interpretation** | Where a loose qualitative comparison is possible: the original found the frozen candidate "remains competitive... under attack," a relatively strong claim. This phase's real-data finding is more modest — the signal generalizes to an unseen category, but with a visibly smaller effect than in-distribution, and for one representation (R2) with no reliable effect at all. This is reported as a **distinct real-data finding**, not a stronger or weaker version of the original's synthetic-attack result — the two experiments do not test the same thing closely enough to be ranked against each other. |

## 29. Limitations

- Exactly one held-out category per dataset was tested (T4 for Alibaba, `db` for AIOps) — a single
  generalization condition, not a distribution over possible unseen categories. No claim is made about
  whether other categories (e.g., P100, `os`) would generalize similarly; this is explicitly listed as a
  candidate future analysis (§32), not run here to avoid multiplying comparisons.
- The AIOps held-out population is very small (13 entities, 2 positive) — the resulting CIs are wide and the
  bootstrap itself loses ~12% of resamples to single-class draws.
- Both held-out categories were chosen by the same fixed rule (largest non-dominant category) — a defensible,
  pre-registered, symmetric choice, but not necessarily the "hardest" or most representative unseen condition;
  a different rule could plausibly produce a different-magnitude result, and this report does not claim T4/`db`
  are representative of all possible unseen workloads.
- AgentRx contributes nothing to this phase, for the same structural reason as every prior phase.

## 30. Alternative explanations (hypotheses only, per this phase's own findings)

- The large gap between Alibaba's in-distribution performance (AUROC 0.72–0.84) and unseen-category
  performance (0.51–0.57) is consistent with the model relying substantially on GPU-type-correlated signal
  (directly, via the one-hot feature, or indirectly, via other features correlated with GPU-type choice) that
  simply isn't available when the category itself is novel — a plausible, not proven, explanation given the
  striking prevalence difference noted in §12 (10.8% vs. 29.9%).
- R2's consistent lack of a reliable effect across both this phase's conditions and Phase 3.2-RD/3.3-RD/
  3.4-RD's temporal condition may reflect a general fragility of the PCA(2) representation to any distribution
  change (temporal or categorical) rather than a temporal-shift-specific issue — plausible given the breadth
  of conditions under which it now underperforms, but not directly tested by decomposing why (that would be a
  new experiment, listed in §32, not run here).

## 31. Reproducibility information

- New scripts: `scripts/real_data/phase3_5_rd_alibaba_evaluate.py`, `scripts/real_data/phase3_5_rd_aiops_evaluate.py`.
  Both import only the pipeline-construction helpers from the frozen Phase 3.1-RD/3.2-RD modules (never
  executing those modules' own `__main__` blocks, and never writing to their output paths) — per the
  authorization's explicit process-safety rule. Both write exclusively to
  `experiments/results/phase3_real_data/phase3_5/`.
- No historical result file was opened for writing at any point in this phase (unlike Phase 3.4-RD's disclosed
  incident) — verified before finalizing (§Integrity checks).
- Provenance preserved: `dominant_gpu_type`/`object` category membership, train/test population assignment,
  and representation identity are all embedded in the output JSON, sufficient to reconstruct exactly why any
  given job/window was assigned to the seen or unseen population.

## 32. Future experiments (explicitly NOT run — separated from current evidence)

- Repeating the unseen-category test for other categories (Alibaba: P100, V100, V100M32, UNKNOWN; AIOps:
  `os`) to determine whether the T4/`db` results generalize across held-out choices or are specific to those
  two categories.
- A dedicated experiment decomposing *why* R2 fails to generalize reliably across every non-random condition
  tested so far (temporal, unseen-GPU-type, unseen-object-family) — e.g., examining its component loadings
  under each condition.
- A larger AIOps held-out population (if more entities/telemetry become available) to narrow the wide CIs
  observed in §13.
- None of the above informed, or was used to select, any result reported above.

---

## Files created by this execution

- `configs/phase3_5_rd_generalization_protocol.json`
- `scripts/real_data/phase3_5_rd_alibaba_evaluate.py`
- `scripts/real_data/phase3_5_rd_aiops_evaluate.py`
- `experiments/results/phase3_real_data/phase3_5/alibaba_results.json`
- `experiments/results/phase3_real_data/phase3_5/aiops_results.json`
- `docs/PHASE3_REAL_DATA_3_5_REPORT.md` (this document)
- `docs/PHASE3_REAL_DATA_COMPARISON.md` (updated by addition only)

No historical file (Phase 3.1-RD–3.4-RD artifacts, original Phase 3, Phase 4) was opened for writing at any
point in this phase.

---

## STOP — Phase 3.5-RD complete

No later phase (3.6-RD, Phase 4) was started. Awaiting review and separate authorization to proceed.
