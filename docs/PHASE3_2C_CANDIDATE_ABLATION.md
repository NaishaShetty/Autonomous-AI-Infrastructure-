# Phase 3.2 Follow-Up: Candidate C Ablation Study

## 1. Research Question

Phase 3.2's Candidate C (rich k-NN failure-history features → logistic
regression) beat the Phase 2 Failure Memory control at all six predetermined
seeds, with a 95% CI excluding 0.5 (AUROC = 0.5809 [0.5472, 0.6146]). But
Candidate C changed two things simultaneously relative to the control:

1. **Representation**: coarse 3-centroid KMeans summary → richer k-NN
   failure-history features.
2. **Learning mechanism**: fixed Gaussian-kernel similarity → supervised
   logistic regression.

This follow-up asks: **which of these two changes actually caused the
improvement** — the richer representation (H1), the supervised learner
(H2), their interaction (H3), or is the original result not robust to a
cleaner decomposition (H0)?

## 2. Existing Evidence (not rerun)

Copied verbatim from Phase 3.1/3.2 — these are fixed historical reference
points, not reproduced by this study:

| Representation | AUROC (mean, 95% CI) |
|---|---|
| No signal | 0.5000 |
| Phase 2 Failure Memory (control) | 0.5141 [0.4914, 0.5368] |
| Candidate B — raw-feature KMeans | 0.5308 [0.5018, 0.5598] |
| Candidate C — failure-history + LR | 0.5809 [0.5472, 0.6146] |
| Calibrated confidence | 0.6599 |

## 3. Ablation Design

All three experiments share the same 3 k-NN failure-history features from
Candidate C, unless noted otherwise:

- `knn_distance_failure` — Euclidean distance to the k-th (k=5) nearest
  logged historical failure.
- `local_failure_density` — count of logged failures within a fixed radius
  (median k-NN distance among the failure set itself).
- `confidence_of_nearest_failures` — mean calibrated confidence of the k
  nearest logged failures.

Feature computation was factored into one shared class,
`_FailureHistoryFeaturizer` (`src/evaluation/representations.py`), used by
both Experiment A and Experiment C so the two experiments are *provably*
computing identical numbers — the only thing allowed to differ between them
is how those numbers are combined into a score.

**Experiment A — rich representation, fixed/unlearned scoring**
(`FixedRuleFailureHistoryRisk`). Standardizes each of the 3 features
(scaler fit on regime-2 data only), then combines with equal (1/3) weight
and a sign fixed by the feature's own definition — never by looking at
test performance:
- `knn_distance_failure`: closer → more risk → sign −1.
- `local_failure_density`: more nearby failures → more risk → sign +1.
- `confidence_of_nearest_failures`: nearby historical failures that
  occurred at *high* confidence indicate the calibrator is fooled in this
  region → more risk → sign +1.

`score = mean(sign_i · z_i)`. This is a ranking score, not a probability
(`is_probability = False`); ECE is not reported (`N/A`), per the frozen
calibration-discipline rule. No weight, sign, or threshold was chosen after
looking at any AUROC number.

**Experiment B — old (Phase 2) representation, supervised learning**
(`Phase2RepresentationSupervisedRisk`). Reuses
`src.failure_memory.embedding.FailureEmbedder` **unmodified and imported**,
exactly as Phase 2's `FailureMemory.fit` uses it: 2-component PCA fit on
the regime-2 failure contexts only, producing a 4-dim embedding (2 PCA
components + confidence-signal + margin). That embedding is then fed into
a `LogisticRegression` with the same configuration Candidate C uses
(`max_iter=1000`), fit on all of regime 2 (successes and failures), so the
supervised-fitting convention matches Experiment C exactly and the *only*
difference between B and C is the representation.

**Experiment C — Candidate C, reproduced unchanged**
(`FailureHistoryRiskModel`). Same k=5, same feature definitions (now
delegated to the shared featurizer, computing the identical formulas that
existed before this study), same fitting data, same classifier
configuration. This is the positive control for the ablation.

No hyperparameter (k, LR parameters, scoring weights, thresholds) was
swept. No new seeds, representations, or clustering algorithms were
introduced.

## 4. Leakage Controls

- Regimes 0/1/2 are used for fitting (workload model / calibrator /
  failure-history representation & any supervised fitting); regimes 3+4
  are the untouched test stream, exactly as the frozen Phase 3.1 protocol
  defines.
- Experiment A's per-feature standardization (mean/scale) is fit only on
  the regime-2 sample set passed into `fit()` — verified by
  `test_experiment_a_standardization_fit_only_on_regime2_contexts`, which
  confirms querying an extreme out-of-distribution point does not change
  the stored mean/scale.
- Experiment B's PCA is fit only on the regime-2 *failure* contexts (not
  all of regime 2, not test data) — verified by
  `test_experiment_b_pca_fit_only_on_failure_contexts` (two different
  failure sets against the same regime-2 successes/failures produce
  different embeddings) and
  `test_standardization_and_scalers_fit_only_on_regime2` (the fitted PCA's
  `n_samples_` equals exactly the regime-2 failure count).
- `test_experiments_never_see_test_stream_during_fit` hashes every regime-2
  context and every test-stream context and asserts the two sets are
  disjoint.
- `test_experiment_a_uses_identical_features_to_candidate_c` confirms
  Experiment A and Experiment C compute byte-identical raw features for
  the same query.
- `test_experiment_c_exactly_reproduces_phase3_2_candidate_c` runs the
  original Phase 3.2 evaluator's Candidate C path and this follow-up's
  Experiment C path on the same seed/protocol and asserts identical scores
  and AUROC.
- 27 new unit/integration tests pass (`tests/unit/test_phase3_2c_ablation_representations.py`,
  `tests/integration/test_phase3_2c_ablation_pipeline.py`); all 92
  pre-existing tests continue to pass unmodified (119 total).

## 5. Results — All Seeds

| Seed | Experiment | AUROC | AUPRC | ECE | AURC |
|---|---|---|---|---|---|
| 1 | A (fixed rule) | 0.4681 | 0.3224 | N/A | 0.3698 |
| 1 | B (old repr. + LR) | 0.6325 | 0.4444 | 0.0896 | 0.2546 |
| 1 | C (control) | 0.5370 | 0.3745 | 0.1594 | 0.3141 |
| 2 | A (fixed rule) | 0.5485 | 0.2686 | N/A | 0.2265 |
| 2 | B (old repr. + LR) | 0.6875 | 0.3823 | 0.0780 | 0.1589 |
| 2 | C (control) | 0.6258 | 0.3407 | 0.0785 | 0.1804 |
| 3 | A (fixed rule) | 0.4970 | 0.1947 | N/A | 0.2041 |
| 3 | B (old repr. + LR) | 0.7106 | 0.3672 | 0.0473 | 0.1114 |
| 3 | C (control) | 0.5668 | 0.2367 | 0.0955 | 0.1721 |
| 4 | A (fixed rule) | 0.5082 | 0.3314 | N/A | 0.3331 |
| 4 | B (old repr. + LR) | 0.6188 | 0.4190 | 0.1218 | 0.2600 |
| 4 | C (control) | 0.5981 | 0.4022 | 0.1176 | 0.2643 |
| 5 | A (fixed rule) | 0.5078 | 0.2191 | N/A | 0.2192 |
| 5 | B (old repr. + LR) | 0.6547 | 0.3171 | 0.0227 | 0.1462 |
| 5 | C (control) | 0.5977 | 0.2934 | 0.0860 | 0.1723 |
| 42 (primary) | A (fixed rule) | 0.5142 | 0.3307 | N/A | 0.3205 |
| 42 (primary) | B (old repr. + LR) | 0.6249 | 0.4171 | 0.0922 | 0.2520 |
| 42 (primary) | C (control) | 0.5599 | 0.3783 | 0.1283 | 0.2932 |

No seed was rerun or omitted.

## 6. Aggregate Results (mean, std, 95% cross-seed Student-t CI)

| Experiment | AUROC | AUPRC | AURC (lower=better) |
|---|---|---|---|
| A — fixed rule | 0.5073 ± 0.0260, CI [0.4800, 0.5346] | 0.2778 ± 0.0602 | 0.2789 ± 0.0705 |
| B — old repr. + LR | 0.6548 ± 0.0371, CI [0.6159, 0.6938] | 0.3912 ± 0.0457 | 0.1972 ± 0.0658 |
| C — control | 0.5809 ± 0.0321, CI [0.5472, 0.6146] | 0.3376 ± 0.0622 | 0.2327 ± 0.0653 |

Precision/recall at fixed coverage points (mean, n=6 seeds):

| Coverage | A precision / recall | B precision / recall | C precision / recall |
|---|---|---|---|
| 5% | 0.193 / 0.034 | 0.438 / 0.081 | 0.376 / 0.068 |
| 10% | 0.236 / 0.085 | 0.427 / 0.157 | 0.378 / 0.138 |
| 20% | 0.281 / 0.200 | 0.416 / 0.303 | 0.361 / 0.261 |
| 50% | 0.291 / 0.522 | 0.377 / 0.682 | 0.322 / 0.579 |

Bootstrap CI (primary seed 42, within-seed sampling uncertainty, n=2000
resamples):

| Experiment | AUROC point estimate | Bootstrap 95% CI |
|---|---|---|
| A | 0.5142 | [0.4926, 0.5345] |
| B | 0.6249 | [0.6031, 0.6452] |
| C | 0.5599 | [0.5387, 0.5805] |

Experiment C's Experiment-level AUROC (0.5809 mean, 0.5599 at seed 42) is
identical to the originally reported Phase 3.2 Candidate C numbers to full
floating-point precision (confirmed by
`test_experiment_c_exactly_reproduces_phase3_2_candidate_c`), not merely
"close."

## 7. Comparison

- **A vs. no-signal (0.5000)**: A's CI [0.4800, 0.5346] contains 0.5 —
  statistically indistinguishable from no signal at the cross-seed level.
  One of six seeds (seed 1) is *below* 0.5.
- **A vs. Phase 2 control (0.5141 [0.4914, 0.5368])**: heavily overlapping
  CIs — A does not clearly beat the original control either.
- **B vs. Candidate C (0.5809 [0.5472, 0.6146])**: B's CI [0.6159, 0.6938]
  is entirely above C's CI, at every one of the six seeds individually
  (0.6325>0.5370, 0.6875>0.6258, 0.7106>0.5668, 0.6188>0.5981,
  0.6547>0.5977, 0.6249>0.5599). B is a clear, consistent improvement over
  the thing it is meant to be a decomposition of.
- **B vs. calibrated confidence (0.6599)**: B's CI [0.6159, 0.6938]
  contains 0.6599 — B is statistically indistinguishable from calibrated
  confidence on this benchmark, using only failure-memory information
  (the calibrator's own confidence output is not one of the two inputs to
  B's embedding beyond the derived confidence/margin features already
  present in Phase 2's embedder).

## 8. Causal Interpretation

This maps onto **Case 2** from the pre-registered decision structure:

```
Experiment A ≈ Control (no signal / Phase 2 control)
Experiment B ≈ or exceeds Candidate C
```

**The evidence supports H2 (supervised-learning effect) as the primary
driver of Candidate C's improvement, not H1 (representation effect).**

The richer k-NN failure-history representation, combined with a
non-trained, semantically-motivated scoring rule, produces essentially no
usable ranking signal (AUROC ≈ 0.51, CI crossing 0.5, one seed even below
0.5). The same three features, run through a logistic regression instead
(Experiment C = the original Candidate C), reach AUROC ≈ 0.58. But
swapping in the *old*, lossier PCA-based representation and keeping only
the supervised learner (Experiment B) does not lose the improvement — it
*exceeds* Candidate C's own result (0.65 vs. 0.58) and gets statistically
close to calibrated confidence (0.66).

This is a stronger and more specific finding than "both contribute"
(Case 3): the representation richness Candidate C added is not carrying
the signal on its own, and is not even necessary — a supervised classifier
fit on the OLD representation outperforms the supervised classifier fit on
the NEW representation. The interaction hypothesis (H3, Case 4) is not
supported either, since B alone (old representation + learning)
reproduces and exceeds the target effect without needing the richer
features at all.

This finding does **not** support treating Candidate C's specific feature
engineering as the reason failure-history information helps. It supports
treating the shift from a fixed similarity kernel to a supervised
classifier as the operative change — and suggests that shift may work even
better on the *existing*, cheaper Phase 2 representation than on the newer,
more complex one Phase 3.2 built.

## 9. Complexity

Experiment B is *simpler* than Candidate C along two axes: it reuses an
already-existing, already-tested component (`FailureEmbedder`) rather than
introducing new k-NN infrastructure (a `NearestNeighbors` index, a
density-radius computation, and 3 hand-engineered features), and it
performs *better*. If a supervised failure-risk model is worth building at
all, this ablation gives no evidence that the richer k-NN feature
engineering Candidate C introduced is worth its added complexity relative
to just fitting a classifier on the representation already in the
codebase. The complexity that *is* justified by this ablation is the shift
from an unlearned similarity kernel to a supervised classifier, which is a
small, well-understood addition (a single `LogisticRegression.fit` call on
already-available features), not the new representation infrastructure.

## 10. Threats to Validity

Carried forward unchanged from Phase 3.1/3.2, still unresolved here:

- Synthetic data only — the regime-drift generator's feature/label
  relationship is a fabricated, controlled setting, not a real workload.
- No genuine temporal structure — row order within a regime carries no
  elapsed-time semantics (confirmed again in Phase 3.2; not re-examined
  by this ablation, which does not touch Candidate D).
- No real-workload validation of any of these representations or
  classifiers.
- Current benchmark limitations (regime sizes, coverage grid, calibration
  bin count) are all inherited from the frozen Phase 3.1 protocol and were
  not re-examined here, by design.
- This ablation adds one further caveat specific to itself: Experiment B's
  apparent superiority over Candidate C is measured on the same synthetic
  benchmark that produced Candidate C's original result. Neither Candidate
  C nor Experiment B has been validated on non-synthetic data — the
  "supervised learning helps" finding is a finding about this benchmark,
  not a general claim about failure-history modeling.

## 11. Decision

**🟢 Clear mechanism.** The ablation isolates the two changes cleanly:
Experiment A (representation alone) collapses to no-signal levels at every
seed-level comparison, Experiment B (learning alone, old representation)
reproduces and exceeds Candidate C's effect at every one of the six
seeds, and Experiment C exactly reproduces the original Phase 3.2 result
bit-for-bit. This is not a "higher AUROC therefore green" call — it is
green because the pattern across A/B/C, checked seed-by-seed rather than
only in aggregate, unambiguously attributes the effect to the supervised
classifier rather than the richer representation, without needing an
interaction explanation.

## 12. Final Questions

1. **Can Candidate C's improvement be reproduced?** Yes, exactly — bit-for-bit identical to the original Phase 3.2 numbers.
2. **Does the richer representation help without supervised learning?** No. Experiment A (AUROC 0.5073, CI [0.4800, 0.5346]) is statistically indistinguishable from no signal, with one seed below 0.5.
3. **Does supervised learning help without the richer representation?** Yes, substantially. Experiment B (AUROC 0.6548, CI [0.6159, 0.6938]) exceeds Candidate C itself, at all six seeds.
4. **Do both components contribute?** Not in an additive/necessary sense. The representation's contribution appears to be near zero on its own; the learning mechanism appears sufficient by itself (and works better on the older, simpler representation than the newer one).
5. **Which component appears primarily responsible?** The supervised-learning mechanism (H2).
6. **Is the effect stable across all six predetermined seeds?** Yes for B vs. C — B beats C at every seed individually, not just in aggregate. A's near-null result is also consistent across seeds (only seed 1 dips below 0.5, well within CI).
7. **Does it remain meaningfully better than the Phase 2 control (0.5141)?** Experiment B, yes, clearly (0.6548 vs. 0.5141, non-overlapping CIs). Experiment A, no.
8. **How large is the remaining gap to calibrated confidence (0.6599)?** For Experiment B, negligible — 0.0051 AUROC, well within B's own CI, which contains 0.6599.
9. **Is the added complexity justified by the observed gain?** Not the k-NN representation's complexity specifically — Experiment B gets a larger gain with less new machinery by reusing the existing PCA-based representation. The supervised-learning addition itself is simple and appears justified.
10. **What should the next research step be?** Investigate why a supervised classifier on the OLD (PCA) representation outperforms one on the NEW (k-NN) representation — e.g. whether the k-NN features are noisier, redundant with what PCA already captures, or whether the fixed k=5 is a poor fit for this representation specifically (note: this would be a new, explicitly scoped experiment, not an unscoped hyperparameter sweep). Per the stop condition below, this is a recommendation for a future phase, not something this study proceeds to.

## Stop Condition

This ablation study stops here. No integration into autonomous
decision-making, no recovery-action wiring, no deployment, no
hyperparameter optimization, no temporal modeling, no real-workload
testing, no additional clustering algorithms, and no automatic
continuation into a "Phase 3.3" were performed. `src/decision/`,
`src/api/`, `src/pipeline_builder.py`, `src/failure_memory/`, and
`configs/phase3_1_protocol.json` were not modified.
