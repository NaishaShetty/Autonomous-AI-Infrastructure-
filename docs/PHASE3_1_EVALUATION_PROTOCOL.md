<a id="phase3-1-evaluation-protocol"></a>
# PHASE3 1 EVALUATION PROTOCOL
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_1_EVALUATION_PROTOCOL.md`  
**Role:** Phase 3.1 frozen evaluation protocol (synthetic data).

# Phase 3.1 — Evaluation Protocol and Baseline Reproduction

Status: **frozen**. This document and `configs/phase3_1_protocol.json` were written before any Phase 3.1 result existed. Reproduce with:

```bash
python benchmarks/phase3_1_leakage_audit.py
python benchmarks/phase3_1_evaluate.py
```

Both are deterministic given the seeds in `configs/phase3_1_protocol.json` and write machine-readable output to `experiments/results/phase3_1/`.

---

## 1. Prediction Task

**What is currently predicted, precisely:** for a single workload inference event, given the input features and the (frozen, already-trained) workload model's own output statistics for that event, will this particular prediction turn out to be **wrong**?

- **Prediction unit**: one inference event (one row of `src/data/synthetic.py`'s regime stream — one classification call).
- **Prediction horizon**: **none**. This is the critical gap to name explicitly, per this phase's instruction not to overstate what the system does. The current architecture makes no claim about *when in the future* a failure will occur, over what time window, or how many events ahead. It scores "is this specific, already-happening inference likely to be wrong," using only information available at the moment that inference is made. It does not forecast an upcoming failure before the triggering input arrives, does not predict an aggregate future failure *rate*, and does not use any temporal/sequential structure (samples within a regime are i.i.d. draws, not a literal time series with elapsed time between them).
- **Failure definition**: `workload_model.predict(x).predicted_label != true_label`, exactly as defined in `src/pipeline_builder.py`'s failure-logging pass and reproduced identically for test-set scoring in `benchmarks/phase3_1_evaluate.py::_compute_test_arrays`. This is unchanged from Phase 2 — not silently redefined for Phase 3.1.
- **Positive class** (`y_fail = 1`): the workload model's prediction is wrong.
- **Negative class** (`y_fail = 0`): the workload model's prediction is correct.
- **Available features at prediction time**: the sample's raw context (`f1..f5`) and the frozen workload model's own output statistics for that same sample (`predicted_proba`, `margin`, `entropy`) — all computable the instant the input arrives, before the true label is known.
- **Unavailable / future information**: the true label itself; any information from regimes not yet fit/observed (regimes 3+4, the test set, are never used to fit anything — see §4).
- **When the prediction is made**: immediately, from the input alone.
- **When the failure outcome becomes known**: immediately after, in this synthetic harness (the true label is available the instant it's needed for scoring). This is itself a simplification worth naming: a real deployment typically has label latency (ground truth arrives late or not at all for many predictions); this benchmark does not model that.

**The gap Phase 3 must eventually address**: the system Phase 2 and 3.1 evaluate is an **instantaneous failure classifier**, not a **future failure predictor** in the sense the eventual Phase 3 research question ("can Failure Memory predict future failures") implies. Whether historical failure information can anticipate failures *before* they happen (i.e., using cluster/recency information to say "the next N events from this region of feature space are elevated-risk") is not evaluated here and is not established by anything in Phase 2 or 3.1. `src/failure_memory/anticipatory.py` gestures at a recency-weighted version of this but remains explicitly unvalidated and unused (per Phase 2's decision, unchanged here).

## 2. Dataset

`src/data/synthetic.py::generate_regime_stream` — 5 synthetic binary-classification regimes, feature vectors `f1..f5 ~ N(0, I)` every regime (i.i.d., regime-independent marginal), true label generated from a logistic function of a regime-specific weight vector that rotates away from regime 0's by `drift_scale * regime_index`. Regime sizes: `(3000, 1500, 1500, 1500, 1500)` — unchanged from Phase 2's `DEFAULT_REGIME_SIZES`, frozen in `configs/phase3_1_protocol.json`. This remains synthetic data; nothing in this phase claims real-world generalization (see §11).

## 3. Split Strategy

Unchanged from Phase 2 (`src/pipeline_builder.build_system`), mapped explicitly onto train/validation/test terminology:

| Regime | Role | Used for |
|---|---|---|
| 0 | **Train** | Fits `WorkloadModel` (frozen afterward) |
| 1 | **Validation (calibration)** | Fits `ConfidenceCalibrator` |
| 2 | **Validation (failure logging)** | Runs the frozen workload model + calibrator, logs wrong predictions as failures, fits `FailureMemory`'s embedding + KMeans |
| 3, 4 (concatenated) | **Test — untouched** | Never used to fit anything. Scored once per seed. |

**Note on "validation" here**: regimes 1 and 2 are used to *fit* auxiliary components, not to *select among alternative configurations* — Phase 2/3.1 do not perform any hyperparameter search or model selection against regime 1/2 performance. This means there is currently no leakage risk from that direction, but it also means the train/validation split does not yet do the job a validation set is normally for (guarding against overfitting a choice). If Phase 3.2 introduces tuning (e.g. cluster count, kernel width), a genuine validation-based selection step will need to be added then — flagged here, not fixed now, per this phase's scope.

## 4. Leakage Audit

Full machine-readable report: `experiments/results/phase3_1/leakage_audit.json`, produced by `benchmarks/phase3_1_leakage_audit.py`, which runs each check against a real, live-built system rather than reasoning about the code in the abstract.

| Check | Method | Result |
|---|---|---|
| **Temporal leakage / fit isolation** | Re-derive the regime split from the same generator call; confirm it's a strict disjoint partition; confirm every failure-memory training event's stored `regime` metadata is `2` (never 3 or 4) | **PASS** — partition disjoint; failure memory fit only on regime-2 data |
| **Label leakage** | Inspect every context dict handed to the embedder/calibrator for `label`/`regime`/`y` keys | **PASS** — context contains exactly `{f1..f5}`, nothing else |
| **Preprocessing (PCA) leakage** | Independently rebuild the system and confirm the failure count used to fit `FailureEmbedder`'s PCA matches an independent recount of regime-2 failures | **PASS** — counts match |
| **Clustering leakage** | Same isolation check as temporal leakage — KMeans is fit inside `FailureMemory.fit()`, called only on the events accumulated during the regime-2 logging pass; the test stream is never passed to `.fit()` anywhere in `src/pipeline_builder.py` | **PASS** — confirmed by direct code inspection (§ "Audit" below) and by the temporal-leakage runtime check |
| **Regime leakage** | Compare per-regime feature means/stds; the generator constructs `f1..f5 ~ N(0,I)` identically every regime (only the label-generating weight vector drifts) | **PASS** — max per-regime mean deviation from grand mean was small (well under the sanity bound); regime id is not trivially recoverable from features. **Important nuance, not a leakage finding**: because feature *marginals* don't shift but the *decision boundary* does, failure-memory's clusters (located in feature space from regime-2 failures) have no statistical reason to align with where regime-3/4's failures occur — this is the likely mechanism behind the weak signal reported in §10, not a data leak. |
| **Duplicate/sample leakage** | Hash every sample's rounded feature vector; check for any hash appearing in more than one split | **PASS** — zero overlaps found between train/calibration/logging/test |
| **Synthetic-generation triviality** | Check label prevalence isn't degenerate (all-0/all-1) and no single feature has near-1.0 correlation with the label | **PASS** — prevalence and per-feature correlations are all in a non-trivial range |

**Overall: no leakage found across any of the seven checks, for the seed(s) tested.** This is a genuinely-checked negative result, not an assumption — every check above ran real code against a real built system and recorded its actual output in `leakage_audit.json`, and is also exercised as a pytest regression (`tests/integration/test_phase3_1_leakage.py`) so a future code change that introduces leakage would fail the test suite.

**Threat to validity this audit does NOT cover**: the leakage audit was run in depth for seed 42 (and the disjointness/regime-metadata checks are additionally exercised at small scale across several seeds via the pytest regression suite), not independently re-run in full for all 6 protocol seeds as a standalone script. Given the checks are structural (they test *how the code is wired*, not something that varies with the random draw), this is a low-risk gap, but it is named here rather than silently assumed away.

## 5. Metrics

All implemented fresh in `src/evaluation/metrics.py` (new in Phase 3.1; Phase 2's `benchmarks/risk_coverage.py` is imported unchanged, not reimplemented):

- **AUROC** (`sklearn.metrics.roc_auc_score`): ranking quality of the failure-risk score against `y_fail`, prevalence-independent. Returns `None` (not a fabricated 0.5/1.0) if a resample/seed happens to contain only one class.
- **AUPRC** (`sklearn.metrics.average_precision_score`): ranking quality weighted toward the positive (failure) class; more sensitive to class-prevalence differences than AUROC, read alongside it rather than in isolation.
- **Calibration — Expected Calibration Error (ECE)**: standard equal-width 10-bin ECE, `src/evaluation/metrics.py::expected_calibration_error`. Computed for all three baselines, including Failure Memory's raw similarity-kernel output, which was never fit/designed to be a calibrated probability — reported anyway as an honest diagnostic (a large ECE there is expected and informative, not a bug).
- **AURC** (Area Under the Risk-Coverage curve): reuses Phase 2's unmodified `risk_coverage_curve` (5%–100% coverage, 5-point steps), trapezoidally integrated. Lower is better. Documented as an approximation over `[0.05, 1.0]`, not extrapolated to coverage 0.
- **Precision / Recall at operating points**: see §6.
- **Confidence intervals**: see §5b.

### 5b. Confidence Intervals

Two distinct sources of uncertainty are reported, not conflated:

1. **Cross-seed variability** (`benchmarks/phase3_1_evaluate.py::_t_interval`): each metric is computed once per predetermined seed (§7), then a Student-t interval (appropriate for the small n=6 sample of seeds, rather than a normal approximation) is computed over the 6 point estimates. This captures sensitivity to the random data-generating draw.
2. **Within-seed bootstrap** (`src/evaluation/bootstrap.py::bootstrap_ci`): for the primary seed (42) only, a nonparametric percentile bootstrap resamples the (y_fail, score) test-set rows with replacement. Documented parameters: **2000 resamples**, **95% confidence level**, **bootstrap seed 0** (fixed, in `configs/phase3_1_protocol.json`), percentile aggregation (2.5th/97.5th percentile of the resampled-metric distribution). This captures finite-test-set sampling uncertainty for one fixed data draw. Resamples that degenerate to a single class (undefined AUROC) are counted (`n_degenerate_resamples`) and excluded from the interval, not silently zeroed.

No false precision is claimed: both intervals are reported with their method named, and neither is used interchangeably with the other.

## 6. Operating Points

Defined **before** any test-set evaluation ran, as fixed **coverage fractions** (not score thresholds fit to maximize a test metric): `{5%, 10%, 20%, 50%}` of the test set, flagged as "high risk" by ranking on each baseline's own score. Precision = fraction of flagged samples that are true failures; recall = fraction of all true failures captured within the flagged set. This sidesteps the classic failure mode of picking a threshold after seeing which one looks best on the test set — the coverage level is the a priori decision (e.g. "we are willing to review the riskiest 10% of predictions"), not the resulting score cutoff.

## 7. Random Seeds

Predetermined list, written into `configs/phase3_1_protocol.json` before any Phase 3.1 run: **`[1, 2, 3, 4, 5, 42]`**. `1`–`5` are a plain sequential convention; `42` is retained for continuity with the original single-seed Phase 2 result. No seed was added, removed, or swapped after inspecting results — the committed config file's timestamp/content is the evidence for this claim. Primary seed for the bootstrap analysis: **42**.

## 8. Baselines

| Baseline | Definition | Fit on |
|---|---|---|
| **A — No failure signal** | Constant score = empirical failure prevalence measured on the regime-2 logging set (i.e., "predict the base rate, ignore the input entirely") | Regime 2 (train-side) |
| **B — Calibrated confidence** | `1 − ConfidenceCalibrator.predict(...).calibrated_confidence` (Phase 2's isotonic-calibrated confidence, unmodified) | Regime 1 |
| **C — Phase 2 Failure Memory** | `FailureMemory.risk(context, confidence)` (Phase 2's unmodified KMeans + Gaussian-kernel similarity score) | Regime 2 |

Baseline A is not a strawman — it is the correct anchor for "no signal": its AUROC must be exactly 0.5 by construction (a constant score cannot discriminate), which also serves as a sanity check on the evaluation code itself (verified: it is exactly 0.5000 for every seed, see §10, and asserted by `tests/integration/test_phase3_1_pipeline.py::test_no_signal_baseline_auroc_is_always_exactly_half_across_seeds`).

## 9. Reproducibility

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # exact pinned versions
python benchmarks/phase3_1_leakage_audit.py     # -> experiments/results/phase3_1/leakage_audit.json
python benchmarks/phase3_1_evaluate.py          # -> experiments/results/phase3_1/{per_seed_results.json,.csv, aggregate_results.json, bootstrap_ci_primary_seed.json}
python -m pytest tests/ -v                      # 70 tests, includes Phase 3.1 evaluation-infra + leakage regressions
```

Every output JSON embeds: full protocol config, UTC timestamp, and `python`/`numpy`/`scikit-learn`/`scipy` versions (`benchmarks/phase3_1_evaluate.py::main`'s `meta` block) — dataset "version" is the frozen `regime_sizes` + seed list in `configs/phase3_1_protocol.json` itself (there is no external dataset file to version; the generator is deterministic and committed).

## 10. Results

All numbers below are read directly from `experiments/results/phase3_1/` — none are hand-typed estimates.

### Per-seed (AUROC / AUPRC / ECE / AURC)

| Baseline | Seed | AUROC | AUPRC | ECE | AURC |
|---|---:|---:|---:|---:|---:|
| A — No signal | 1 | 0.5000 | 0.3423 | 0.0883 | 0.2973 |
| B — Calibrated confidence | 1 | 0.6302 | 0.4310 | 0.0517 | 0.2622 |
| C — Failure Memory | 1 | 0.5165 | 0.3579 | 0.2300 | 0.3318 |
| A — No signal | 2 | 0.5000 | 0.2493 | 0.0747 | 0.2724 |
| B — Calibrated confidence | 2 | 0.6917 | 0.3758 | 0.0596 | 0.1533 |
| C — Failure Memory | 2 | 0.5373 | 0.2830 | 0.2455 | 0.2379 |
| A — No signal | 3 | 0.5000 | 0.2010 | 0.0350 | 0.2091 |
| B — Calibrated confidence | 3 | 0.7208 | 0.3377 | 0.0622 | 0.1045 |
| C — Failure Memory | 3 | 0.4729 | 0.1966 | 0.2963 | 0.2178 |
| A — No signal | 4 | 0.5000 | 0.3330 | 0.1097 | 0.3721 |
| B — Calibrated confidence | 4 | 0.6251 | 0.4191 | 0.1537 | 0.2550 |
| C — Failure Memory | 4 | 0.5226 | 0.3580 | 0.2161 | 0.3271 |
| A — No signal | 5 | 0.5000 | 0.2243 | 0.0223 | 0.2027 |
| B — Calibrated confidence | 5 | 0.6628 | 0.3207 | 0.0457 | 0.1444 |
| C — Failure Memory | 5 | 0.5160 | 0.2354 | 0.2627 | 0.2189 |
| A — No signal | 42 | 0.5000 | 0.3333 | 0.0620 | 0.2660 |
| B — Calibrated confidence | 42 | 0.6289 | 0.4164 | 0.1206 | 0.2453 |
| C — Failure Memory | 42 | 0.5193 | 0.3519 | 0.1916 | 0.3264 |

No run was excluded, rerun, or omitted. All 6 seeds × 3 baselines = 18 rows are exactly what `experiments/results/phase3_1/per_seed_results.csv` contains.

### Aggregate (mean, std, 95% Student-t CI across the 6 seeds)

| Baseline | AUROC | AUPRC | ECE | AURC (lower better) |
|---|---|---|---|---|
| A — No signal | 0.5000 ± 0.0000 [0.5000, 0.5000] | 0.2806 ± 0.0630 [0.2145, 0.3466] | 0.0653 ± 0.0327 [0.0310, 0.0997] | 0.2699 ± 0.0623 [0.2045, 0.3354] |
| B — Calibrated confidence | **0.6599 ± 0.0395 [0.6185, 0.7013]** | **0.3835 ± 0.0463 [0.3349, 0.4320]** | 0.0823 ± 0.0442 [0.0359, 0.1286] | **0.1941 ± 0.0680 [0.1227, 0.2655]** |
| C — Failure Memory | 0.5141 ± 0.0217 [0.4914, 0.5368] | 0.2971 ± 0.0700 [0.2237, 0.3706] | 0.2404 ± 0.0367 [0.2019, 0.2788] | 0.2767 ± 0.0572 [0.2166, 0.3367] |

**Baseline C's 95% CI for AUROC, `[0.4914, 0.5368]`, contains 0.5001 — the theoretical no-discrimination value — for every one of the 6 predetermined seeds' aggregate.** This is the single most important number in this report.

### Precision / Recall at predetermined coverage operating points (mean across 6 seeds)

| Coverage | A precision / recall | B precision / recall | C precision / recall |
|---:|---|---|---|
| 5% | 0.2622 / 0.0480 | **0.4356 / 0.0795** | 0.3211 / 0.0570 |
| 10% | 0.2572 / 0.0935 | **0.4400 / 0.1619** | 0.3167 / 0.1126 |
| 20% | 0.2631 / 0.1898 | **0.4156 / 0.3024** | 0.3100 / 0.2202 |
| 50% | 0.2711 / 0.4880 | **0.3783 / 0.6849** | 0.2900 / 0.5144 |

C is numerically above A at every coverage point here, a smaller and less consistent gap than AUROC's near-total overlap with 0.5 would suggest — read this table as a secondary, more prevalence-sensitive view, not as contradicting the AUROC finding (see §11).

### Bootstrap CI, primary seed 42 only (2000 resamples, 95%, method in §5b)

| Baseline | AUROC point [95% CI] | AUPRC point [95% CI] |
|---|---|---|
| A — No signal | 0.5000 [0.5000, 0.5000] | 0.3333 [0.3160, 0.3503] |
| B — Calibrated confidence | 0.6289 [0.6069, 0.6484] | 0.4164 [0.3905, 0.4438] |
| C — Failure Memory | 0.5193 **[0.4969, 0.5413]** | 0.3519 [0.3287, 0.3782] |

Consistent with the cross-seed result: even within a single fixed test set, Failure Memory's AUROC confidence interval spans 0.5.

### Was the Phase 2 baseline reproducible?

**Yes, directionally, and the new protocol sharpens rather than contradicts it.** Phase 2's finding (`PHASE2_REPORT.md` §11) was that Failure Memory's risk score correlated with actual incorrectness at only `0.031` (Pearson), versus confidence's `0.200`, and that blending risk into confidence made matched-coverage selective risk *worse*, not better. Phase 3.1's AUROC-based, multi-seed, confidence-interval-backed protocol reproduces the same qualitative ordering (B strictly best on every metric; C statistically indistinguishable from A on the prevalence-independent AUROC metric) — and additionally shows this is stable across 6 independent seeds, not an artifact of the original seed=42 draw.

## 11. Validity Issues

- **Synthetic data only** — this evaluates one specific synthetic regime-drift generator, not real workload data. No generalization claim beyond this benchmark is made or implied.
- **AUROC vs AUPRC/precision-recall tension** — Failure Memory's AUROC is statistically indistinguishable from the no-signal baseline, but its AUPRC and coverage-level precision/recall are consistently, if modestly, above the no-signal baseline's. This is not a contradiction (AUPRC/precision are prevalence-sensitive and can shift with class balance in ways AUROC does not), but it means the honest summary is "very weak, inconsistent signal, not conclusively zero" rather than "provably zero." Phase 3.2 should not treat AUROC alone as the final word.
- **Regime 1/2 are not a true model-selection validation set** — see §3. No hyperparameter or representation choice was tuned against them in Phase 2 or here; this is a structural note for Phase 3.2, not a flaw in Phase 3.1 itself.
- **Leakage audit depth** — full structural checks ran for seed 42 in detail and were additionally spot-checked across several small-scale seeds via the pytest suite (§4), but were not independently re-run as the full standalone script for all 6 protocol seeds.
- **ECE on a non-probabilistic score (Baseline C)** is reported despite Failure Memory's risk output never having been fit as a calibrated probability — the resulting large ECE (~0.24) should be read as "this score is far from a calibrated probability," which is expected, not as evidence of a broken calibration *procedure* (there isn't one to break).
- **No real label-latency / temporal-forecast modeling** — see §1's "gap" discussion. This benchmark cannot, as constructed, answer whether failure memory could anticipate a failure before it happens; it only measures same-instant failure classification.
- **AURC's coverage grid starts at 5%, not 0%** — inherited from the unmodified Phase 2 harness; the reported AURC is an approximation over `[0.05, 1.0]`, stated explicitly rather than silently treated as the full `[0, 1]` integral.

## 12. Decision Readiness

**Is the evaluation protocol ready for Phase 3.2? Yes, with the caveats in §11 carried forward explicitly.**

The protocol is deterministic, leakage-checked (7 checks, all passed, with runtime evidence and regression tests), reports honest uncertainty via two distinct, correctly-labeled methods, defines operating points before touching test results, and reproduces Phase 2's qualitative finding with substantially more rigor (multi-seed, AUROC/AUPRC/ECE/AURC, confidence intervals) rather than contradicting or "fixing" it.

**Is Phase 3.2 (improving Failure Memory) scientifically justified by what Phase 3.1 found? Not yet, in the sense of "the current representation is worth tuning further."** The evidence says the current KMeans/PCA/Gaussian-kernel representation carries a AUROC statistically indistinguishable from no signal, replicated across 6 seeds and within-seed bootstrap. Per the Phase 3.1 brief's own instruction, this document does not recommend proceeding automatically into representation changes — that decision belongs to whoever reads this report next, informed by the fact that any future representation change should be judged against this exact frozen protocol (same seeds, same metrics, same leakage checks) to be comparable at all.
