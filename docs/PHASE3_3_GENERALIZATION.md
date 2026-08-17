# Phase 3.3: Generalization and Robustness Validation

## 1. Research Question

Phase 3.2C identified the Supervised Failure-Risk candidate (existing Phase
2 PCA representation + logistic regression) as the source of Candidate C's
improvement, reaching AUROC 0.6548 [0.6159, 0.6938] on the frozen Phase
3.1/3.2C benchmark — statistically indistinguishable from calibrated
confidence (0.6599 [0.6185, 0.7013]). That result was discovered and
measured on a single benchmark condition (regimes 3+4 at the training
drift strength). This phase asks: **does that signal survive evaluation on
conditions the candidate was never fit on**, without retuning it to look
good on them?

## 2. Candidate Being Tested (frozen, unmodified)

`Phase2RepresentationSupervisedRisk` (`src/evaluation/representations.py`,
unchanged since Phase 3.2C):

- Representation: `src.failure_memory.embedding.FailureEmbedder` — 2-component
  PCA fit on regime-2 **failure** contexts only, producing a 4-dim
  embedding (2 PCA components + `2·|confidence−0.5|` + `|confidence−0.5|`).
- Classifier: `sklearn.linear_model.LogisticRegression(max_iter=1000,
  random_state=seed)`, fit on the embedding of **all** of regime 2
  (successes and failures), target = the sample's own failure/success
  outcome.
- No hyperparameter (PCA components, LR regularization, max_iter) was
  changed from Phase 3.2C. No new preprocessing was added. The fitting
  procedure (`_fit_frozen_candidate` in
  `benchmarks/phase3_3_generalization.py`) is called **exactly once per
  seed**, before any generalization condition is evaluated, and its output
  object is reused unmodified across every condition — verified by
  `test_candidate_fit_exactly_once_and_reused_across_conditions` and
  `test_no_fit_method_called_inside_condition_loop` (AST-level check that
  `.fit(` never appears in the condition-evaluation code path).

## 3. Reading the Generator First

Before designing any "unseen condition," `src/data/synthetic.py` was read
directly (not assumed). Key facts, verified empirically (see the tests
below, not just derived from source reading):

- `generate_regime_stream(regime_sizes, drift_scale=0.35, seed)` draws a
  base weight vector `base_w`, then per regime `regime_idx`, a drift vector
  `drift ~ N(0, drift_scale·regime_idx)`, sets `w = base_w + drift`, and
  generates that regime's features `X ~ N(0, I)` and labels
  `y ~ Bernoulli(sigmoid(X·w))`.
- **`X` (the raw feature draws) does not depend on `drift_scale`.** For a
  fixed seed and `regime_sizes`, calling the generator with two different
  `drift_scale` values produces **byte-identical `X` at every regime**,
  because `rng.normal(scale=s, size=n)` draws the same number of underlying
  random variates regardless of `s`, so the RNG stream position — and
  hence every subsequent `X` draw — is unaffected by `drift_scale`. Only
  `w` (via `drift`), and therefore `y`, differs. Confirmed directly:
  `test_features_invariant_to_drift_scale_but_labels_are_not`.
- **Regime 0 (training) is fully `drift_scale`-invariant**: `regime_idx=0`
  makes `drift_scale·0 = 0` regardless of `drift_scale`, so `w = base_w`
  and both `X` and `y` are identical across every `drift_scale` value at
  regime 0. Confirmed: `test_regime0_training_data_is_fully_drift_scale_invariant`.
- `src.pipeline_builder.build_system` never exposes `drift_scale` — it
  always calls the generator with the library default (0.35). Every prior
  phase's training condition, and this phase's frozen candidate's fitting
  condition, is therefore unaffected by anything this study does.
- `configs/phase3_1_protocol.json` has no drift-related field; `drift_scale`
  was never previously fixed by any protocol document, so introducing it as
  a new, explicitly-documented axis does not conflict with anything frozen.

**Consequence for what "unseen" means here**: `drift_scale` is the only
parameter this generator exposes that produces a genuinely different
failure-generating relationship without being fabricated. Varying it at the
test regimes (3+4) while regimes 0/1/2 stay at the fixed training value
produces a condition where the **input distribution is unchanged** but the
**decision boundary — and therefore which inputs are failures — differs**
from anything the model fit on. This is a **concept-drift generalization
test under a fixed covariate distribution**, not a covariate-shift test;
the report does not claim more than that. Given this, the brief's Test A
("unseen regime conditions") and Test B ("unseen drift strength") collapse
into the same mechanism for this generator — there is no second, independent
lever available without modifying the frozen generator, which this phase
does not do.

## 4. Generalization Conditions (fixed before running any evaluation)

| id | kind | `drift_scale` | rationale |
|---|---|---|---|
| `original_benchmark` | in-distribution reference | 0.35 | `system.test_stream` reused verbatim — the unmodified Phase 3.1/3.2C benchmark. Not regenerated. |
| `unseen_weaker_drift` | unseen | 0.175 (0.5× training) | Decision boundary at test regimes rotated *less* from the training boundary than the model ever fit on. |
| `unseen_stronger_drift` | unseen | 0.70 (2× training) | Decision boundary at test regimes rotated *more* from the training boundary than the model ever fit on. |

The 0.5×/2× factors were chosen for interpretability (symmetric on a log
scale around the training value) before any AUROC was computed under
either condition, and were not adjusted afterward. No other drift value
was tried and discarded.

Sanity check confirming the mechanism behaves as expected (not tuned, just
verified): frozen workload-model failure rate on regime 3+4 at seed 42 is
25.3% at weaker drift, 33.3% at the training drift (matches the original
benchmark exactly), and 42.4% at stronger drift — monotonically increasing
with `drift_scale`, as the boundary-rotation mechanism predicts.

## 5. Data/Fitting Boundaries

For every seed:

```
Regime 0 (train)   -> workload model            [fixed drift_scale=0.35, unchanged]
Regime 1 (calib)   -> confidence calibrator      [fixed drift_scale=0.35, unchanged]
Regime 2 (log/fit) -> original Failure Memory (C) and Supervised Failure-Risk (D)
                       [fixed drift_scale=0.35, unchanged — fit ONCE]
Regimes 3+4        -> evaluation ONLY, one independently-generated stream per
                       condition (original_benchmark reuses system.test_stream;
                       unseen conditions call generate_regime_stream with a
                       different drift_scale) — NEVER used for fitting anything.
```

No model is refit, re-selected, or re-thresholded per condition. Baseline
A's prevalence constant is computed once from regime 2 at the training
drift and reused unchanged across every condition (never derived from test
data). `_assert_no_regime2_leakage` hashes every regime-2 context and every
condition's test contexts and asserts the sets are disjoint, run inside
every seed's evaluation (not just as a one-off audit script). No separate
validation split was needed beyond the existing regime-1 calibration step,
because no model selection or hyperparameter choice happens anywhere in
this phase — the candidate is entirely frozen from Phase 3.2C.

## 6. Experimental Protocol

- Seeds: `[1, 2, 3, 4, 5, 42]` (frozen `configs/phase3_1_protocol.json`,
  unchanged; all six reported, none dropped or added).
- Metrics: AUROC, AUPRC, AURC, ECE (only for genuine probabilities —
  Failure Memory's similarity score is never reported as ECE, per the
  Phase 3.1/3.2/3.2C calibration-discipline rule), precision/recall at
  fixed coverage 5%/10%/20%/50%.
- Cross-seed CI: Student-t 95% interval over the 6 per-seed point
  estimates (reused `_t_interval` from `benchmarks/phase3_1_evaluate.py`,
  not reimplemented).
- Within-seed CI: nonparametric percentile bootstrap (n=2000 resamples) at
  primary seed 42, reused `bootstrap_ci` unchanged.
- Baselines evaluated under every condition: A (no signal), B (calibrated
  confidence), C (original Phase 2 Failure Memory), D (Supervised
  Failure-Risk candidate).

## 7. Results — All Seeds, All Conditions

AUROC / AUPRC / AURC per seed (ECE omitted from this table for space; C's
ECE is always `N/A` — non-probabilistic score — and is reported in the
full JSON):

| Seed | Condition | A | B (confidence) | C (orig. memory) | D (candidate) |
|---|---|---|---|---|---|
| 1 | original | 0.5000 | 0.6302 | 0.5165 | 0.6325 |
| 1 | weaker | 0.5000 | 0.6655 | 0.5105 | 0.6721 |
| 1 | stronger | 0.5000 | 0.5790 | 0.5174 | 0.5789 |
| 2 | original | 0.5000 | 0.6917 | 0.5373 | 0.6875 |
| 2 | weaker | 0.5000 | 0.7437 | 0.5503 | 0.7329 |
| 2 | stronger | 0.5000 | 0.6200 | 0.5335 | 0.6197 |
| 3 | original | 0.5000 | 0.7208 | 0.4729 | 0.7106 |
| 3 | weaker | 0.5000 | 0.7595 | 0.4951 | 0.7527 |
| 3 | stronger | 0.5000 | 0.6325 | 0.4746 | 0.6262 |
| 4 | original | 0.5000 | 0.6251 | 0.5226 | 0.6188 |
| 4 | weaker | 0.5000 | 0.6873 | 0.5425 | 0.6814 |
| 4 | stronger | 0.5000 | 0.5841 | 0.4936 | 0.5794 |
| 5 | original | 0.5000 | 0.6628 | 0.5160 | 0.6547 |
| 5 | weaker | 0.5000 | 0.6882 | 0.5197 | 0.6837 |
| 5 | stronger | 0.5000 | 0.6303 | 0.5112 | 0.6242 |
| 42 (primary) | original | 0.5000 | 0.6289 | 0.5193 | 0.6249 |
| 42 (primary) | weaker | 0.5000 | 0.6681 | 0.5260 | 0.6668 |
| 42 (primary) | stronger | 0.5000 | 0.5874 | 0.5193 | 0.5838 |

No seed or condition was omitted or rerun. Note seed 3's original Failure
Memory (C) AUROC is *below* 0.5 (0.4729) in all three conditions — a
failure mode discussed in section 10.

`original_benchmark` values above are, by construction, identical to
Phase 3.2C's original benchmark and Experiment B numbers (confirmed by
`test_candidate_d_matches_phase3_2c_experiment_b_on_original_benchmark` /
`test_experiment_c_exactly_reproduces_phase3_2_candidate_c`-style checks).

## 8. Aggregate Results (mean, 95% cross-seed Student-t CI)

| Condition | A | B (confidence) | C (orig. memory) | D (candidate) |
|---|---|---|---|---|
| original_benchmark | 0.5000 [0.5000,0.5000] | 0.6599 [0.6185,0.7013] | 0.5141 [0.4914,0.5368] | 0.6548 [0.6159,0.6938] |
| unseen_weaker_drift | 0.5000 [0.5000,0.5000] | 0.7021 [0.6602,0.7439] | 0.5240 [0.5026,0.5454] | 0.6983 [0.6609,0.7356] |
| unseen_stronger_drift | 0.5000 [0.5000,0.5000] | 0.6055 [0.5796,0.6314] | 0.5083 [0.4862,0.5303] | 0.6021 [0.5773,0.6268] |

AUPRC / AURC (mean):

| Condition | B AUPRC / AURC | D AUPRC / AURC |
|---|---|---|
| original | 0.3835 / 0.1941 | 0.3912 / 0.1972 |
| weaker | 0.3474 / 0.1310 | 0.3558 / 0.1324 |
| stronger | 0.4226 / 0.2859 | 0.4265 / 0.2881 |

Bootstrap 95% CI, primary seed 42 (n=2000 resamples):

| Condition | B AUROC (point, CI) | D AUROC (point, CI) |
|---|---|---|
| original | 0.6289 [0.6069, 0.6484] | 0.6249 [0.6031, 0.6452] |
| weaker | 0.6681 [0.6473, 0.6886] | 0.6668 [0.6453, 0.6875] |
| stronger | 0.5874 [0.5672, 0.6071] | 0.5838 [0.5631, 0.6039] |

Precision/recall at fixed coverage (mean; B vs. D):

| Condition | Coverage | B precision/recall | D precision/recall |
|---|---|---|---|
| original | 5% | 0.436 / 0.080 | 0.438 / 0.081 |
| original | 10% | 0.440 / 0.162 | 0.427 / 0.157 |
| original | 20% | 0.416 / 0.302 | 0.416 / 0.303 |
| original | 50% | 0.378 / 0.685 | 0.377 / 0.682 |
| weaker | 5% | 0.393 / 0.089 | 0.390 / 0.090 |
| weaker | 10% | 0.398 / 0.182 | 0.389 / 0.178 |
| weaker | 20% | 0.376 / 0.342 | 0.383 / 0.349 |
| weaker | 50% | 0.336 / 0.757 | 0.333 / 0.751 |
| stronger | 5% | 0.473 / 0.068 | 0.468 / 0.067 |
| stronger | 10% | 0.476 / 0.138 | 0.457 / 0.132 |
| stronger | 20% | 0.452 / 0.260 | 0.450 / 0.258 |
| stronger | 50% | 0.423 / 0.606 | 0.422 / 0.605 |

## 9. Baseline Comparison

- **D vs. A (no signal)**: D's CI is entirely above 0.5 in every condition
  (lowest bound 0.5773 at stronger drift). Never approaches, let alone
  crosses, no-signal.
- **D vs. C (original Failure Memory)**: D's CI is entirely above C's CI in
  every condition (e.g. stronger drift: D [0.5773, 0.6268] vs. C
  [0.4862, 0.5303] — no overlap). This holds at every individual seed too,
  not just in aggregate.
- **D vs. B (calibrated confidence) — the central comparison**: D tracks B
  extremely closely in every condition, at every seed. Aggregate gap
  (B − D): +0.0051 (original), +0.0038 (weaker), +0.0034 (stronger) — D is
  consistently *very slightly* below confidence, never meaningfully behind,
  and their CIs overlap almost completely in all three conditions. At the
  per-seed level, D exceeds B once (seed 1, both original and weaker
  conditions by ~0.002–0.007) and is otherwise fractionally below B by
  0.001–0.01 AUROC. No seed or condition shows a reversal large enough to
  suggest the ranking is unstable — the D/B gap itself is stable, not the
  identity of which one wins.

## 10. Failure/Degradation Analysis

Degradation relative to the original benchmark (`original − condition`,
positive = the original benchmark was easier):

| Baseline | original → weaker (improvement) | original → stronger (degradation) |
|---|---|---|
| B (confidence) | −0.0422 (improves) | +0.0544 |
| D (candidate) | −0.0435 (improves) | +0.0527 |
| C (orig. memory) | −0.0099 (improves) | +0.0058 |

D's degradation under stronger drift (0.0527) is essentially identical to
B's (0.0544) — the candidate does not degrade faster than the strongest
available signal. No robustness threshold was defined in advance beyond
"does not fall to no-signal and does not fall below the original Failure
Memory" (section 7 of the brief) — that threshold is met in every
condition, so no separate acceptable/unacceptable cutoff was needed for
interpretation.

**Where the mechanism does show a weak point**: C (original Failure
Memory) drops *below* 0.5 at seed 3 in all three conditions (0.4729,
0.4951, 0.4746) — a case where the Phase 2 mechanism actively
anti-correlates with failures for one specific train/test split, regardless
of drift condition. D does not exhibit this at seed 3 (0.7106, 0.7527,
0.6262 — its best-performing seed, if anything). This is reported as an
observation about C's instability across seeds, not something Phase 3.3
was designed to explain further; no seed-specific rescue was attempted, per
the brief's stop condition.

No condition caused D's calibration (ECE) to blow up disproportionately to
B's: ECE(D) tracks ECE(B) closely in every condition (original: 0.075 vs.
0.082; weaker: 0.049 vs. 0.039; stronger: 0.131 vs. 0.150) — both get worse
under stronger drift (as expected: the calibrator itself was never refit
for the drifted conditions, so both scores' calibration degrades together),
neither collapses independently of the other.

Precision at low coverage (5%/10%) — the operating region most relevant to
"only act on the highest-risk flagged fraction" — tracks B within ~0.01–0.02
absolute precision in every condition; recall likewise tracks within
~0.005–0.01. No condition produces a precision/recall collapse specific to
D that spares B.

## 11. Threats to Validity

- Synthetic data throughout — the regime-drift generator's feature/label
  relationship is a controlled, fabricated construction, not a real
  workload.
- No genuine temporal structure (unchanged finding from Phase 3.2:
  `generate_regime_stream` draws each regime via vectorized, non-sequential
  RNG calls; row order carries no elapsed-time semantics).
- No real-workload validation of the candidate, the original Failure
  Memory, or calibrated confidence.
- **Specific to this phase**: the "unseen" conditions vary only the
  label-generating decision boundary (`drift_scale`) while holding the
  input feature distribution `X` fixed — a deliberate, documented,
  generator-supported design choice (section 3), but it means this study
  demonstrates robustness to *concept drift under a fixed covariate
  distribution*, not to *covariate shift* (a genuinely different input
  population). The current generator does not expose a mechanism for
  covariate shift without redesigning it, which this phase explicitly does
  not do (see section 15 of the brief; no benchmark modification was made).
- Only two non-training drift magnitudes were tested (0.5× and 2× the
  training value); this characterizes robustness at those two points, not
  a continuous robustness curve.

## 12. Decision

**🟢 Generalization supported** (within the explicitly synthetic, fixed-
covariate-distribution scope documented above). Across all six
predetermined seeds and both predetermined unseen drift conditions, the
Supervised Failure-Risk candidate: (a) remained clearly above the no-signal
baseline, (b) remained clearly above the original Phase 2 Failure Memory,
and (c) tracked calibrated confidence within a small, stable margin that
never widened meaningfully as drift strength moved away from the training
condition in either direction. Degradation under stronger drift was
essentially the same magnitude for the candidate as for calibrated
confidence itself — the candidate is not more fragile than the strongest
available signal. This is not evidence of real-workload generalization,
production readiness, or that failure prediction is solved — see section
14 of the brief and the "final questions" below for the precise, bounded
claim this evidence supports.

## 13. Final Questions

1. **What exactly counts as an unseen condition in this experiment?**
   Regimes 3+4 generated at a `drift_scale` (0.175 or 0.70) different from
   the training value (0.35) that regimes 0/1/2 always use — verified to
   change only the failure-generating decision boundary, not the input
   feature distribution.
2. **Was that definition fixed before evaluating the results?** Yes. The
   two multiplicative factors (0.5×, 2×) were fixed in
   `benchmarks/phase3_3_generalization.py`'s `CONDITIONS` list before any
   AUROC under either condition was computed; no other drift value was
   tried and discarded.
3. **Did the candidate remain above the no-signal baseline?** Yes, at
   every seed and every condition, with CIs entirely above 0.5.
4. **Did it remain above the original Failure Memory baseline?** Yes, at
   every seed and every condition, with non-overlapping CIs.
5. **How did it compare with calibrated confidence?** Statistically
   indistinguishable, tracking within 0.003–0.005 AUROC in aggregate across
   all three conditions; overlapping CIs throughout.
6. **How stable was it across seeds?** Stable — D beats C and A at every
   one of the 6 seeds × 3 conditions = 18 individual comparisons, and its
   gap to B never widens or reverses direction in a way inconsistent with
   sampling noise.
7. **How much did performance degrade from the original benchmark?**
   ≈0.053 AUROC under 2× drift (comparable to confidence's ≈0.054); *improved*
   by ≈0.044 under 0.5× drift (also comparable to confidence's ≈0.042).
8. **Which conditions caused failure or degradation?** Stronger drift
   (2×) degrades all signals roughly equally; no condition caused the
   candidate specifically (relative to confidence) to fail. The original
   Failure Memory baseline (C) showed an unrelated failure mode — dropping
   below 0.5 at seed 3 in every condition — not shared by the candidate.
9. **Did any unseen condition accidentally influence model fitting or
   selection?** No — verified structurally (AST check that no `.fit()`
   call exists in the condition-evaluation path) and empirically (the
   candidate's logistic-regression coefficients are identical before and
   after scoring all three conditions), in addition to the leakage-hash
   check run inside every seed's evaluation.
10. **Does the evidence support generalization, or only benchmark-specific
    performance?** Within this synthetic benchmark's concept-drift axis,
    it supports generalization — not merely a coincidence of the exact
    training drift value. It does not speak to covariate-shift
    generalization or real-workload generalization, which this benchmark
    cannot test (section 11).
11. **Is the current benchmark sufficient for stronger generalization
    claims?** No. It can vary decision-boundary strength but not the input
    feature distribution, workload semantics, or temporal structure. A
    stronger claim would require a benchmark redesign, which is out of
    scope for this phase.
12. **What is the scientifically justified next step?** Either (a) extend
    the synthetic benchmark to support genuine covariate shift (a new,
    explicitly-scoped benchmark-design effort, not a Phase 3.3 addendum),
    or (b) begin real-workload data collection to test whether any of
    these synthetic findings — including Phase 3.2C's finding that the old
    representation outperforms the new k-NN one — hold outside simulation.
    Per the stop condition below, no such step is begun here.

## Stop Condition

This phase stops here. No integration into autonomous decision-making, no
changes to `src/decision/`, no deployment, no retraining based on these
generalization results, no hyperparameter optimization, no temporal
modeling, no real-workload data, and no automatic continuation into a
"Phase 3.4" were performed. `src/pipeline_builder.py`,
`src/failure_memory/`, `src/evaluation/representations.py`, and
`configs/phase3_1_protocol.json` were not modified.
