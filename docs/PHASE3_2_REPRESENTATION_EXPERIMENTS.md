# Phase 3.2 — Controlled Failure Representation Experiments

Status: complete. Stops here — no Phase 3.3 work performed. Reproduce with:

```bash
python benchmarks/phase3_2_evaluate.py
python -m pytest tests/ -v
```

Nothing under `configs/phase3_1_protocol.json`, `src/evaluation/{metrics,bootstrap,protocol}.py`, `benchmarks/phase3_1_evaluate.py`, `src/pipeline_builder.py`, or `src/failure_memory/` was modified. New code lives in `src/evaluation/representations.py` and `benchmarks/phase3_2_evaluate.py`, and is imported nowhere outside evaluation/tests.

---

## 1. Research Question

Phase 3.1 found the Phase 2 Failure Memory representation (PCA → 3-cluster KMeans → Gaussian-kernel similarity) statistically indistinguishable from a no-signal baseline (AUROC 95% CI `[0.4914, 0.5368]`, spanning 0.5, across 6 seeds). Phase 3.1 also identified a plausible mechanism: feature distributions are stable across regimes while the feature→label decision boundary drifts, so a representation built on feature-space proximity to a small number of failure cluster centroids has no statistical reason to transfer to a rotated boundary.

**Question**: is that poor result caused by the *representation* (PCA + coarse 3-centroid clustering), or is historical failure information fundamentally uninformative for this task? A small, predetermined set of alternative representations is tested against the same frozen protocol to find out.

## 2. Hypotheses

- **H1**: the current feature-space representation is poorly matched to regime drift, and a representation incorporating additional failure-history information (not just distance to 3 coarse centroids) may provide stronger transferable failure-risk signal.
- **H0**: alternative representations do not provide meaningful predictive improvement over the Phase 2 Failure Memory baseline under the frozen evaluation protocol.

Both are evaluated without an expectation that H1 wins — see §9 for how the actual results split between the two candidates.

## 3. Candidate Representations

| Candidate | What it is | Why it was selected |
|---|---|---|
| **A (control)** | Phase 2's unmodified `FailureMemory`: PCA(2) → KMeans(3) → Gaussian-kernel similarity to nearest centroid | The official Phase 3.1 result. Not reimplemented — the actual `src.failure_memory.memory.FailureMemory` object is used, exactly as Phase 3.1 used it. |
| **B — raw structured features** | Same KMeans(3) + Gaussian-kernel mechanism as the control, but clustering directly on `[f1..f5, confidence_signal, margin]` (7-dim) instead of `[pca0, pca1, confidence_signal, margin]` (4-dim) | Isolates one question: is PCA destroying information the clustering mechanism could otherwise use? Everything else (n_clusters, kernel width, downstream formula) held identical to the control. No extra normalization was added — `f1..f5 ~ N(0,I)` in every regime by the generator's own construction (independently confirmed in the Phase 3.1 leakage audit), so raw features are already unit-scale; introducing a scaler would be an unjustified transformation per the Phase 3.2 brief. |
| **C — failure-history features** | 3 explicit statistics — (1) distance to the k=5th nearest logged historical failure, (2) count of historical failures within a fixed radius (local density), (3) mean calibrated confidence of the k nearest historical failures — fed into a `LogisticRegression` | Tests whether a continuous, less-lossy summary of the failure log (versus 3 coarse centroids) carries more signal. All 3 features are computable at prediction time from information already available (raw context + the historical failure log); none uses the true label of the sample being scored. |
| **D — temporal/recency** | Not executed — see §3b | Investigated first; the benchmark does not support it validly (below). |

No other representations were tried. No hyperparameter sweep was run over Candidate B/C's parameters (`n_clusters=3` for B, matching the control exactly; `k_neighbors=5` for C, a single round-number choice made before any evaluation, not selected by trying several values and keeping the best).

### 3b. Candidate D — why it was not executed

Per the brief's explicit instruction to check before fabricating a temporal signal: `src/data/synthetic.py::StreamSample` has **no timestamp field** (`context`, `label`, `regime` only), and `generate_regime_stream` builds each regime's `X`/`p`/`y` via single vectorized `rng` calls, then appends samples in a plain index loop — row order is array index, not elapsed time, and carries no sequential dependence between consecutive samples (confirmed by reading the generator directly, reproduced as `benchmarks/phase3_2_evaluate.py::candidate_d_temporal_analysis()`, and covered by `tests/integration/test_phase3_2_pipeline.py::test_candidate_d_reports_negative_finding_not_fabricated_results`).

**Conclusion, as required by the brief: "Temporal representation cannot be validly evaluated under the current benchmark."** A controlled temporal extension (real timestamps, drift that evolves continuously rather than only at fixed regime boundaries) would be needed first — that is a benchmark-design requirement for a future phase, not something Phase 3.2 introduces.

### 3c. Alternative clustering method (brief §4) — not added

The brief authorizes testing one clustering alternative to KMeans, but only if justified by the representation experiments. Candidate C's result (§9) shows the effective fix was **avoiding lossy compression into a small fixed number of cluster centroids at all** — moving to a continuous k-NN-based local density/distance summary, not swapping which clustering algorithm produces the centroids. Candidate B (same KMeans mechanism, different input space) shows only a marginal, largely-not-significant change from the control (§9), which is further evidence the *clustering step itself* (rather than the specific algorithm) is where information is lost. Testing e.g. DBSCAN or a Gaussian mixture in place of KMeans would probe a highly similar hypothesis to what Candidate C already resolved. Per the brief's "do not add one merely for completeness," **no additional clustering algorithm was evaluated.**

## 4. Data and Fitting Boundaries

| Component | Fit on | Notes |
|---|---|---|
| `WorkloadModel` | Regime 0 | Unchanged from Phase 2/3.1, reused via `build_system` |
| `ConfidenceCalibrator` | Regime 1 | Unchanged |
| Control (`FailureMemory`) | Regime 2 failures only | Unchanged — via `build_system` exactly as Phase 3.1 called it |
| Candidate B (`RawFeatureFailureRisk`) | Regime 2 failures only | Same failure set the control uses — regime 2 is regenerated deterministically via the same `generate_regime_stream(seed=...)` call `build_system` makes internally (byte-identical given the same seed; **not new data**), and the reconstructed failure count is asserted equal to `build_system`'s own `n_logged_failures` every run (`benchmarks/phase3_2_evaluate.py::_fit_candidates`) |
| Candidate C (`FailureHistoryRiskModel`) | k-NN reference set: regime-2 failures only. Logistic regression training set: **all** of regime 2 (successes and failures) | This is the one deliberate methodological difference from A/B, stated explicitly per the brief's requirement: regime 2 is legitimately train-side data for both framings; using its non-failure examples too (to teach the model what a *non*-risky region looks like) is a different, more supervised use of the same permitted data, not a boundary violation. |
| All candidates, test scoring | Regimes 3+4, **untouched by any `fit()` call** | Verified structurally (`tests/integration/test_phase3_2_pipeline.py::test_candidates_never_see_test_stream_during_fit`, hash-based disjointness check) and by construction (`_reconstruct_regime2` asserts every reconstructed sample has `regime == 2`) |

No candidate's hyperparameters, feature set, or fitting procedure were chosen by looking at regimes 3/4 performance. `n_clusters=3` and `k_neighbors=5` were fixed before any test-set number was computed.

## 5. Experimental Protocol

Frozen Phase 3.1 protocol, reused without modification: seeds `[1, 2, 3, 4, 5, 42]`, coverage operating points `{5%, 10%, 20%, 50%}`, metrics AUROC/AUPRC/ECE/AURC + precision/recall at each coverage point, cross-seed Student-t 95% CI, within-primary-seed (42) bootstrap 95% CI (2000 resamples, seed 0). `configs/phase3_1_protocol.json` was read (`Phase31Protocol.load()`), never edited.

**Calibration-metric discipline (brief §7)**: ECE is reported only where a representation's output has an actual probabilistic interpretation — `is_probability=True` for the no-signal baseline (a constant equal to an empirical prevalence), calibrated confidence (isotonic-fit, Phase 2), and Candidate C (fit via logistic regression against the true failure label). ECE is explicitly `null`/`n/a` for the control and Candidate B, whose Gaussian-kernel similarity output was never fit or designed to be a calibrated probability — reported as `None`, not manufactured (`src/evaluation/representations.py`'s `is_probability` flag on each class; enforced by `tests/integration/test_phase3_2_pipeline.py::test_ece_not_reported_for_non_probabilistic_representations`).

## 6. Results (per seed)

All 6 seeds × 5 representations = 30 rows, none omitted, none rerun. Full data: `experiments/results/phase3_2/per_seed_results.csv`.

| Representation | Seed | AUROC | AUPRC | ECE | AURC |
|---|---:|---:|---:|---:|---:|
| A — No signal | 1 | 0.5000 | 0.3423 | 0.0883 | 0.2973 |
| B — Calibrated confidence | 1 | 0.6302 | 0.4310 | 0.0517 | 0.2622 |
| Control — Phase 2 Failure Memory | 1 | 0.5165 | 0.3579 | n/a | 0.3318 |
| Candidate B — Raw features | 1 | 0.5031 | 0.3461 | n/a | 0.3404 |
| Candidate C — Failure history | 1 | 0.5370 | 0.3745 | 0.1594 | 0.3141 |
| A — No signal | 2 | 0.5000 | 0.2493 | 0.0747 | 0.2724 |
| B — Calibrated confidence | 2 | 0.6917 | 0.3758 | 0.0596 | 0.1533 |
| Control — Phase 2 Failure Memory | 2 | 0.5373 | 0.2830 | n/a | 0.2379 |
| Candidate B — Raw features | 2 | 0.5798 | 0.3162 | n/a | 0.2117 |
| Candidate C — Failure history | 2 | 0.6258 | 0.3407 | 0.0785 | 0.1804 |
| A — No signal | 3 | 0.5000 | 0.2010 | 0.0350 | 0.2091 |
| B — Calibrated confidence | 3 | 0.7208 | 0.3377 | 0.0622 | 0.1045 |
| Control — Phase 2 Failure Memory | 3 | 0.4729 | 0.1966 | n/a | 0.2178 |
| Candidate B — Raw features | 3 | 0.5066 | 0.2047 | n/a | 0.2016 |
| Candidate C — Failure history | 3 | 0.5668 | 0.2367 | 0.0955 | 0.1721 |
| A — No signal | 4 | 0.5000 | 0.3330 | 0.1097 | 0.3721 |
| B — Calibrated confidence | 4 | 0.6251 | 0.4191 | 0.1537 | 0.2550 |
| Control — Phase 2 Failure Memory | 4 | 0.5226 | 0.3580 | n/a | 0.3271 |
| Candidate B — Raw features | 4 | 0.5334 | 0.3690 | n/a | 0.3149 |
| Candidate C — Failure history | 4 | 0.5981 | 0.4022 | 0.1176 | 0.2643 |
| A — No signal | 5 | 0.5000 | 0.2243 | 0.0223 | 0.2027 |
| B — Calibrated confidence | 5 | 0.6628 | 0.3207 | 0.0457 | 0.1444 |
| Control — Phase 2 Failure Memory | 5 | 0.5160 | 0.2354 | n/a | 0.2189 |
| Candidate B — Raw features | 5 | 0.5251 | 0.2474 | n/a | 0.2141 |
| Candidate C — Failure history | 5 | 0.5977 | 0.2934 | 0.0860 | 0.1723 |
| A — No signal | 42 | 0.5000 | 0.3333 | 0.0620 | 0.2660 |
| B — Calibrated confidence | 42 | 0.6289 | 0.4164 | 0.1206 | 0.2453 |
| Control — Phase 2 Failure Memory | 42 | 0.5193 | 0.3519 | n/a | 0.3264 |
| Candidate B — Raw features | 42 | 0.5368 | 0.3697 | n/a | 0.3103 |
| Candidate C — Failure history | 42 | 0.5599 | 0.3783 | 0.1283 | 0.2932 |

**Candidate C (failure-history) beats the control at every one of the 6 seeds, with no exceptions** (1: 0.537 vs 0.5165; 2: 0.6258 vs 0.5373; 3: 0.5668 vs 0.4729; 4: 0.5981 vs 0.5226; 5: 0.5977 vs 0.5160; 42: 0.5599 vs 0.5193). Candidate B (raw features) beats the control at 5 of 6 seeds, essentially ties at seed 1 (0.5031 vs 0.5165 — slightly *worse*).

## 7. Aggregate Results (mean ± std, 95% Student-t CI across 6 seeds)

| Representation | AUROC | AUPRC | ECE | AURC (lower better) |
|---|---|---|---|---|
| A — No signal | 0.5000 ± 0.0000 [0.5000, 0.5000] | 0.2806 ± 0.0630 [0.2145, 0.3466] | 0.0653 [0.0310, 0.0997] | 0.2699 [0.2045, 0.3354] |
| B — Calibrated confidence | **0.6599 ± 0.0395 [0.6185, 0.7013]** | **0.3835 ± 0.0463 [0.3349, 0.4320]** | 0.0823 [0.0359, 0.1286] | **0.1941 [0.1227, 0.2655]** |
| Control — Phase 2 Failure Memory | 0.5141 ± 0.0217 [0.4914, 0.5368] | 0.2971 ± 0.0700 [0.2237, 0.3706] | n/a | 0.2767 [0.2166, 0.3367] |
| Candidate B — Raw features | 0.5308 ± 0.0233 [0.5018, 0.5598] | 0.3089 ± 0.0673 [0.2354, 0.3823] | n/a | 0.2655 [0.1997, 0.3313] |
| Candidate C — Failure history | 0.5809 ± 0.0271 [0.5472, 0.6146] | 0.3376 ± 0.0655 [0.2664, 0.4089] | 0.1109 (single-bin-diagnostic; not directly comparable to A/B's ECE — see §9) | 0.2327 [0.1642, 0.3013] |

Precision/recall at predetermined coverage points (mean across 6 seeds):

| Coverage | A | B — Confidence | Control | Candidate B — Raw | Candidate C — History |
|---:|---|---|---|---|---|
| 5% | 0.2622 / 0.0480 | **0.4356 / 0.0795** | 0.3211 / 0.0570 | 0.3456 / 0.0608 | 0.3756 / 0.0679 |
| 10% | 0.2572 / 0.0935 | **0.4400 / 0.1619** | 0.3167 / 0.1126 | 0.3522 / 0.1267 | 0.3783 / 0.1376 |
| 20% | 0.2631 / 0.1898 | **0.4156 / 0.3024** | 0.3100 / 0.2202 | 0.3197 / 0.2301 | 0.3614 / 0.2607 |
| 50% | 0.2711 / 0.4880 | **0.3783 / 0.6849** | 0.2900 / 0.5144 | 0.2971 / 0.5302 | 0.3223 / 0.5787 |

Ordering is consistent: Confidence > Candidate C (History) > Candidate B (Raw) > Control > No signal, at every coverage level, on both precision and recall.

**Within-primary-seed (42) bootstrap AUROC, 2000 resamples**: Control `[0.4969, 0.5413]` (includes 0.5); Candidate B `[0.5149, 0.5586]` (excludes 0.5); Candidate C `[0.5387, 0.5805]` (clearly excludes 0.5). Consistent with the cross-seed picture.

## 8. Comparison With Phase 3.1

- **vs. no-signal (AUROC 0.5000)**: Candidate C's 95% CI `[0.5472, 0.6146]` is clearly and entirely above 0.5 — a genuine, non-trivial discrimination signal that the Phase 3.1 control never demonstrated. Candidate B's CI `[0.5018, 0.5598]` barely clears 0.5 (lower bound 0.5018) — a much weaker, borderline claim.
- **vs. calibrated confidence (AUROC 0.6599)**: neither candidate approaches it. Candidate C closes roughly a third of the gap between no-signal (0.50) and confidence (0.66) — meaningfully better than the control's near-zero closure, but confidence remains the strongest signal by a clear margin on every metric.
- **vs. control (Phase 2 Failure Memory, AUROC 0.5141)**: Candidate C is unambiguously, consistently better (every seed, both cross-seed and within-seed intervals). Candidate B is marginally, less consistently better.

## 9. Failure Analysis

**Why did Candidate C work where the control didn't?** The control compresses the entire regime-2 failure log into 3 KMeans centroids and scores new inputs only by distance to the *nearest* of those 3 points. Candidate C instead keeps the individual failure examples and computes a k-NN-based local density/distance/confidence summary — a continuous, much less lossy description of "how surrounded by historical failures is this input," plus a supervised logistic-regression step that learns how that summary actually relates to the true failure/success label on regime 2 (rather than an unlearned, fixed-form Gaussian kernel). Both changes plausibly matter; this experiment does not cleanly separate "less lossy geometric summary" from "the fact that a supervised classifier was fit on top of it," and that is a real limitation of this comparison, not a hidden result being glossed over.

**Why did Candidate B only marginally help?** Dropping PCA alone (keeping the same lossy 3-centroid compression) barely moved the needle (control 0.5141 → 0.5308 mean AUROC). This suggests **PCA was not the primary bottleneck** — the coarse clustering step was. This directly informed the decision in §3c not to chase a different clustering algorithm: the evidence points at "too much compression," not "wrong compression algorithm."

**Is Candidate C's improvement stable and meaningful, or a fluke?** Stable: positive at all 6 seeds, cross-seed CI excludes 0.5, within-seed bootstrap CI excludes 0.5. Meaningful in the narrow sense of "a real, non-zero, reproducible signal" — yes. Meaningful in the sense of "ready to replace or augment calibrated confidence" — **no**: it remains well below confidence's AUROC (0.58 vs 0.66) and its improvement over the control, while consistent, is modest in absolute terms (+0.067 mean AUROC). A candidate moving AUROC from 0.514 to 0.525 would have been the brief's explicit example of "technically improved, practically not yet meaningful" — Candidate C's actual improvement (0.514 → 0.581) is larger than that illustrative example, which is why this report treats it as a genuine, if modest, positive finding rather than noise, but the reader should weigh "genuine and modest" rather than "solved."

**Candidate C's ECE (0.1109) is worse than confidence's (0.0823)** despite both being legitimate probabilities — the logistic regression was fit on only 3 features from a few hundred regime-2 failures and is a much simpler/less-tuned model than the calibrator; this is expected and not a contradiction of its AUROC result (ranking quality and calibration quality are different properties).

## 10. Complexity / Tradeoffs

| | Control | Candidate B (Raw) | Candidate C (History) |
|---|---|---|---|
| Additional features | — | none (same features, different transform) | 3 engineered features (k-NN distance, local density, neighbor-confidence) |
| Additional computation | — | none (removes PCA transform step, net simpler) | k-NN index build + query per prediction, O(n_failures) per query without an ANN index; plus a logistic regression fit |
| Additional parameters | — | none | `k_neighbors` (=5, fixed a priori) + logistic regression's own 3 coefficients + intercept |
| Additional dependencies | — | none (drops a dependency: PCA) | `sklearn.neighbors.NearestNeighbors`, `sklearn.linear_model.LogisticRegression` (both already transitive deps of scikit-learn, no new package) |
| Interpretability | KMeans centroid distance (already fairly opaque) | Same mechanism, easier to inspect (features are the original units, not PCA components) | More interpretable in one sense (3 named, meaningful features) but the logistic weights add a second layer versus the control's parameter-free kernel |
| Reproducibility | Deterministic given seed | Deterministic given seed | Deterministic given seed; more moving parts (2 fitted objects: NN index + classifier) than the control's 1 (KMeans) |

Per the brief's complexity principle: **Candidate C is not free** — it adds a k-NN structure and a supervised classifier where the control had one unsupervised clustering step. Given its improvement is real but modest and still far below calibrated confidence, this report does **not** recommend adopting it as a production replacement for the control on the strength of this result alone; it recommends treating it as evidence that the *representation family* (continuous failure-history statistics, not coarse clustering) is worth further, more careful investigation — see §12/Question 7.

## 11. Threats to Validity

- **Synthetic data only** — all results are specific to this regime-drift generator; no claim of generalization to real workloads is made (per the brief's explicit warning, §12 there).
- **No genuine temporal structure exists in this benchmark** — Candidate D could not be tested at all; this remains an open gap for the underlying benchmark, not something this phase's results can speak to.
- **Candidate C confounds two changes at once** (less-lossy geometric summary + a supervised-fit downstream model) — this experiment cannot attribute the improvement cleanly between the two; a cleaner ablation (e.g., a supervised classifier on the *same* PCA+centroid-distance feature the control uses, versus the same k-NN features with an unlearned heuristic combination instead of logistic regression) was not run, per the brief's instruction to keep the candidate set small and not chase an algorithm zoo.
- **ECE is not comparable across representations with different feature/model complexity** — Candidate C's 0.1109 and confidence's 0.0823 are each legitimate but reflect very different model sophistication; treat as a diagnostic per-representation number, not a ranked leaderboard entry.
- **`k_neighbors=5` was not swept** — a different fixed value might change Candidate C's result; no sweep was run (per the brief's explicit instruction against hyperparameter tuning in this phase), so this specific number is not claimed to be optimal, only "a reasonable a-priori choice that was not tuned against test performance."
- **The generalization warning applies in full**: these results describe performance under the current held-out synthetic regime evaluation (regimes 3+4 of this specific generator) — not evidence about real workload families or genuinely different distributions.

## 12. Phase 3.2 Decision

**🟡 Inconclusive** (leaning toward a real but modest signal for Candidate C; no useful signal from Candidate B).

Rationale: Candidate C demonstrates a stable, leakage-free, statistically-non-trivial improvement over the Phase 2 control (95% CI excludes 0.5 both cross-seed and within-seed, positive at every one of 6 seeds) — this is not nothing, and rules out "failure history is definitely useless" as a conclusion. But the improvement is modest in absolute terms, remains well below calibrated confidence, confounds two simultaneous representation changes, and has not been tested for practical significance beyond AUROC/AUPRC/AURC movement (e.g. no downstream decision-quality experiment). This does not meet the bar for 🟢 ("meaningful and sufficiently stable improvement" ready to act on), but it is well past 🔴 ("no useful representation found") given Candidate C's result. Candidate B alone would have been 🔴 or borderline 🟡; Candidate C's clearer result is why the phase as a whole lands at 🟡 rather than 🔴.

---

## Required Final Decision Logic

**Q1 — Did any alternative representation outperform the Phase 2 Failure Memory baseline?**
Yes. Both candidates did on mean AUROC; Candidate C's advantage is consistent and stable, Candidate B's is smaller and less consistent (worse than control at 1 of 6 seeds).

**Q2 — Is that improvement statistically and practically meaningful?**
Statistically: yes for Candidate C (CI excludes 0.5 both cross-seed and within-seed; positive at every seed). Practically: partially — real and reproducible, but modest in absolute size and far from calibrated confidence's performance; not yet meaningful enough to justify a production change.

**Q3 — Does it outperform the no-signal baseline convincingly?**
Candidate C: yes, convincingly by the AUROC-CI standard (entirely above 0.5). Candidate B: only marginally (CI lower bound 0.5018, barely above 0.5).

**Q4 — How does it compare with calibrated confidence?**
Both candidates remain clearly below calibrated confidence on every metric (AUROC 0.58/0.53 vs 0.66; AURC 0.233/0.266 vs 0.194). Calibrated confidence remains the strongest single signal found in this project to date.

**Q5 — Is the improvement stable across the six predetermined seeds?**
Candidate C: yes, positive at all 6 seeds, no reversals. Candidate B: mostly yes, one near-tie/slight-reversal at seed 1.

**Q6 — Did any candidate require test-set tuning or otherwise compromise the protocol?**
No. All fitting used only regimes 0-2; hyperparameters (`n_clusters=3` for B, matching the control; `k_neighbors=5` for C) were fixed before any test evaluation ran; verified structurally by disjointness tests (`tests/integration/test_phase3_2_pipeline.py`) and by the `_fit_candidates` assertion that reconstructed regime-2 failure counts match `build_system`'s own count.

**Q7 — Does the evidence justify another iteration?**
A narrowly-scoped one: yes, specifically to disentangle Candidate C's two confounded changes (representation richness vs. supervised fitting) with a cleaner ablation, before considering any further investment. It does **not** justify broad hyperparameter tuning, an algorithm zoo, or integrating Candidate C into any decision path — those remain out of scope until a cleaner, confirmatory result exists. This report stops here; the decision to run that next narrow experiment (or not) is left to whoever reads this, per the brief's instruction not to proceed automatically.
