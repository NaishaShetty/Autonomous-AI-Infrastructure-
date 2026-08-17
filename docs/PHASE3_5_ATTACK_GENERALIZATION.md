# Phase 3.5 — Attack Generalization

**Status: COMPLETE.** This document is the Phase 3.5 deliverable.

Companion artifacts:
- Frozen protocol: [`configs/phase3_5_attack_protocol.json`](../configs/phase3_5_attack_protocol.json)
- Attack transforms: [`src/evaluation/attacks.py`](../src/evaluation/attacks.py)
- Evaluation script: [`benchmarks/phase3_5_attack_generalization.py`](../benchmarks/phase3_5_attack_generalization.py)
- Leakage audit script: [`benchmarks/phase3_5_leakage_audit.py`](../benchmarks/phase3_5_leakage_audit.py)
- Machine-readable results: [`experiments/results/phase3_5/attack_generalization.json`](../experiments/results/phase3_5/attack_generalization.json), [`experiments/results/phase3_5/leakage_audit.json`](../experiments/results/phase3_5/leakage_audit.json)
- Tests: [`tests/integration/test_phase3_5_attack_generalization.py`](../tests/integration/test_phase3_5_attack_generalization.py)

## 1. Objective

Determine whether the predictive behavior of the selected Supervised
Failure Risk candidate (F — Phase 3.2C's Experiment B, frozen unchanged by
Phase 3.3) survives deliberately different failure/attack conditions
**without retraining or test-condition adaptation**, and compare it
fairly against calibrated confidence (B, a co-equal baseline, not an
already-surpassed one) and the original Phase 2 Failure Memory (C).

## 2. Relationship to Phase 3.1–3.4

- Phase 3.1 froze the evaluation protocol and metrics — reused unchanged
  here (seeds, coverage points, bootstrap settings, calibration bins).
- Phase 3.2/3.2C developed and isolated F's mechanism (supervised
  classifier on the old Phase 2 PCA representation).
- Phase 3.3 tested F under **concept drift**: fixed features, rotated
  label-generating boundary (`drift_scale`).
- Phase 3.4 consolidated everything on the clean benchmark and found F
  clearly beats no-signal (A) and original Failure Memory (C), but does
  **not** consistently beat calibrated confidence (B) — status 🟡
  INCONCLUSIVE. **That conclusion is frozen and is not revisited or
  rewritten here.**
- Phase 3.5 tests a **different** axis: **covariate-shift attacks**
  (corrupted/missing input features, label-generating relationship
  untouched) — the opposite structural change from Phase 3.3's concept
  drift, and explicitly not a repeat of it under a new name.

## 3. Frozen evaluation protocol

Inherited unchanged from `configs/phase3_1_protocol.json` (verified by
the evaluation script, which raises if `phase3_5_attack_protocol.json`'s
`seeds`/`primary_seed` disagree with it):

- Seeds `[1, 2, 3, 4, 5, 42]`, primary seed `42`
- Coverage operating points `5%, 10%, 20%, 50%`
- Calibration bins `10`
- Bootstrap: 2000 resamples, percentile method, seed `0`, 95% CI
- Cross-seed CI: Student-t interval over the six per-seed estimates

New for Phase 3.5, frozen in `configs/phase3_5_attack_protocol.json`
**before** this script was run: the attack matrix (section 6), the
robustness metric definition (section 20), and the fitting/no-refit rule
(section 8).

## 4. Attack/generalization threat model

1. **What is being changed?** Only the feature values (`context`) of the
   held-out regime-3/4 samples — after generation, via a deterministic
   post-hoc transform (`src/evaluation/attacks.py`). `src/data/synthetic.py`
   is not modified and its label-generating mechanism is never touched.
2. **Why does it represent an attack/failure perturbation?** It models an
   attacker or environmental fault corrupting the telemetry/inputs a
   deployed system observes (noisy sensors, a dropped/corrupted field) —
   without changing the underlying, true relationship between inputs and
   correctness that the workload model is ultimately judged against.
3. **What remains fixed?** The true label-generating weight vector, the
   workload model, the calibrator, the original Failure Memory, and F —
   all fit once on clean regime-0/1/2 data and never touched again. The
   sample's true `label` and `regime` are also unchanged.
4. **What information is available to the model?** Exactly the corrupted
   context — the same information every candidate (A/B/C/F) would
   observe in a real deployment if its input pipeline were compromised.
5. **What information is unavailable?** The clean, uncorrupted feature
   values — the model has no way to recover them, and no candidate is
   given attack-identity information (which condition is active, or
   attack parameters) at scoring time.
6. **Is the condition seen or unseen?** Unseen. Every candidate is fit
   exclusively on clean regime-0/1/2 data (`build_system`'s own, always
   at the default `drift_scale`, no corruption). No attack transform is
   ever applied before or during fitting.
7. **Is the model allowed to retrain?** No. Verified by a runtime
   leakage check (`no_fit_calls_during_attack_scoring`) confirming no
   `.fit(` call occurs anywhere in the per-condition scoring loop, and by
   the structural pattern reused from Phase 3.3 (fit once, score
   many times).
8. **Why does this constitute generalization rather than ordinary
   train/test variation?** Regimes 3/4 were always held out at the SAME
   (clean) distribution the model was fit on, modulo drift_scale (Phase
   3.1/3.2/3.2C/3.4) or concept drift (Phase 3.3). Here, the held-out data
   is additionally passed through a corruption process the fitting
   pipeline never saw in any form, on any regime, at any seed — this is a
   structurally different distribution shift (covariate shift on inputs),
   not a re-draw of the same generative family.

## 5. Why each attack condition is scientifically justified

The synthetic generator (`src/data/synthetic.generate_regime_stream`)
exposes exactly three knobs: `regime_sizes`, `drift_scale`, `seed`.
`drift_scale` (concept drift) was already Phase 3.3's axis. `seed`
controls both features and the concept jointly and is already the
frozen cross-seed variability axis — treating a new seed as an "attack"
would violate the brief's explicit warning (section 20) that a different
random seed is not automatically a new regime. That leaves **no
generator-native axis for a genuinely different attack** without either
modifying the frozen generator or reimplementing its RNG stream
externally.

Given that, Phase 3.5's attacks are **post-hoc, deterministic
transforms of already-generated held-out samples** — additive feature
noise and feature zeroing — which:
- require no change to `src/data/synthetic.py` or any other frozen file,
- have a clean, standard interpretation (corrupted/missing telemetry) as
  an attack on a deployed system's input pipeline,
- are fully deterministic and reproducible given `(seed, attack_ordinal)`,
  and
- create a genuine, different-in-kind distribution shift (covariate
  shift, not concept drift) from everything tested in Phase 3.1–3.4.

**Explicitly excluded, and why** (frozen in
`configs/phase3_5_attack_protocol.json.excluded_axes`, not silently
dropped):
- *Label-boundary manipulation* — would require modifying the frozen
  generator or reimplementing its weight-vector/RNG construction
  externally; neither was done, to avoid touching frozen code or
  introducing an undocumented, possibly-inconsistent reimplementation.
- *Failure-rate shift* — not independently controllable via the
  generator's exposed parameters without changing the meaning of the
  task.
- *Further concept-drift severities* — already covered by Phase 3.3;
  repeating it under a new name would not test a new axis.

## 6. Attack matrix

Frozen in `configs/phase3_5_attack_protocol.json` before evaluation.

| ID | Mechanism | Parameters | Severity | Seen/unseen |
|---|---|---|---|---|
| `clean` | none (reference) | — | — | — |
| `feature_noise_mild` | additive Gaussian noise on all 5 features | σ=0.5 (half native scale) | mild | unseen |
| `feature_noise_severe` | additive Gaussian noise on all 5 features | σ=1.5 (1.5x native scale) | severe | unseen |
| `feature_dropout` | zero out 2 of 5 features | `f2`, `f4` (fixed a priori) | n/a — binary corruption | unseen |

RNG for the noise attacks is derived deterministically as
`np.random.default_rng((seed, attack_ordinal))` — reproducible, no
uncontrolled randomness (verified by
`check_attack_determinism` in the leakage audit).

## 7. Candidate systems

Per the brief section 5, the primary comparison is exactly **F vs. B vs.
C vs. A** — D/E (Phase 3.2's raw-feature and failure-history candidates)
are not re-evaluated here, to avoid unnecessary scope expansion.

| ID | Candidate | Reused from |
|---|---|---|
| A | No signal | Phase 3.1 baseline, unchanged |
| B | Calibrated confidence | Phase 3.1 baseline, unchanged |
| C | Original Phase 2 Failure Memory | Phase 3.1 baseline, unchanged |
| **F** | **Supervised Failure Risk** | Phase 3.2C Experiment B / Phase 3.3 frozen candidate, unchanged |

`benchmarks/phase3_5_attack_generalization.py` imports
`benchmarks.phase3_3_generalization`'s `_fit_frozen_candidate`,
`_reconstruct_regime2_with_confidences`, `_compute_condition_arrays`,
`_evaluate_one`, `_is_probability`, `_assert_no_regime2_leakage`, and
`BASELINES` **directly, unmodified** — F, B, and C are not reimplemented
for Phase 3.5, only re-scored against new conditions. A test
(`test_f_implementation_matches_phase3_3_frozen_candidate`) confirms F's
score on a held-out sample matches Phase 3.3's own computation exactly.

## 8. Training/fitting boundaries

For every seed: `build_system` fits the workload model (regime 0),
calibrator (regime 1), and original Failure Memory (regime 2) exactly as
every prior phase did. F is fit exactly once, on clean regime-2 data, via
the unmodified `Phase2RepresentationSupervisedRisk.fit()`. All four
candidates are then **frozen** and reused, unmodified, to score the clean
reference condition and all three attack conditions. No `.fit()` call
occurs anywhere in the per-condition scoring loop — checked at runtime,
not just asserted in prose (see section 9).

No hyperparameter, feature, regularization, calibration, PCA dimension,
or KMeans setting was changed from Phase 3.2C/3.3's frozen configuration.

## 9. Leakage audit

`benchmarks/phase3_5_leakage_audit.py`, run against seed 42 — **all 7
checks passed**:

| Check | Result |
|---|---|
| `training_evaluation_disjointness` | PASS |
| `attack_transforms_preserve_ground_truth` | PASS |
| `attack_transforms_actually_corrupt_context` | PASS |
| `attack_determinism` | PASS |
| `no_fit_calls_during_attack_scoring` | PASS |
| `attack_protocol_matches_frozen_file` | PASS |
| `duplicate_samples_across_attack_conditions` | PASS |

`all_passed: true` (`experiments/results/phase3_5/leakage_audit.json`).
No STOP condition was triggered.

## 10. Clean baseline results

Identical (up to the display-label rename `D_supervised_failure_risk` →
`F`) to Phase 3.4's frozen numbers — reused for consistency, not rerun
independently for this table:

| Candidate | AUROC | AUPRC | AURC |
|---|---|---|---|
| A — No signal | 0.5000 [0.5000, 0.5000] | 0.2806 | 0.2699 |
| C — Original Failure Memory | 0.5141 [0.4914, 0.5368] | 0.2971 | 0.2767 |
| **F — Supervised Failure Risk** | **0.6548 [0.6159, 0.6938]** | 0.3912 | 0.1972 |
| B — Calibrated confidence | 0.6599 [0.6185, 0.7013] | 0.3835 | 0.1941 |

## 11. Attack-condition results (cross-seed AUROC, 95% CI)

| Candidate | Clean | Mild noise (σ=0.5) | Severe noise (σ=1.5) | Feature dropout |
|---|---|---|---|---|
| A — No signal | 0.5000 [.5000,.5000] | 0.5000 [.5000,.5000] | 0.5000 [.5000,.5000] | 0.5000 [.5000,.5000] |
| C — Original Failure Memory | 0.5141 [.4914,.5368] | 0.5143 [.4942,.5343] | 0.5152 [.5008,.5296] | 0.4970 [.4677,.5264] |
| **F — Supervised Failure Risk** | **0.6548 [.6159,.6938]** | **0.6297 [.5959,.6635]** | **0.5502 [.5225,.5779]** | **0.5999 [.5483,.6516]** |
| B — Calibrated confidence | 0.6599 [.6185,.7013] | 0.6351 [.5971,.6732] | 0.5565 [.5284,.5845] | 0.6005 [.5472,.6539] |

## 12. Per-seed results

F vs. A / F vs. C / F vs. B win counts (of 6 seeds), AUROC:

| Condition | F beats A | F beats C | F beats B |
|---|---|---|---|
| clean | 6/6 | 6/6 | 1/6 |
| feature_noise_mild | 6/6 | 6/6 | 1/6 |
| feature_noise_severe | 6/6 | **5/6** | 0/6 |
| feature_dropout | 6/6 | 6/6 | **3/6** |

Full per-seed AUROC (F / B / C), every condition:

```
clean:                seed 1: F=0.6325 B=0.6302 C=0.5165   seed 2: F=0.6875 B=0.6917 C=0.5373
                       seed 3: F=0.7106 B=0.7208 C=0.4729   seed 4: F=0.6188 B=0.6251 C=0.5226
                       seed 5: F=0.6547 B=0.6628 C=0.5160   seed 42: F=0.6249 B=0.6289 C=0.5193

feature_noise_mild:    seed 1: F=0.6004 B=0.5976 C=0.5029   seed 2: F=0.6491 B=0.6521 C=0.5241
                       seed 3: F=0.6757 B=0.6867 C=0.4836   seed 4: F=0.6032 B=0.6089 C=0.5113
                       seed 5: F=0.6481 B=0.6602 C=0.5274   seed 42: F=0.6015 B=0.6052 C=0.5362

feature_noise_severe:  seed 1: F=0.5231 B=0.5234 C=0.5306   seed 2: F=0.5492 B=0.5525 C=0.5080
                       seed 3: F=0.5556 B=0.5711 C=0.5332   seed 4: F=0.5227 B=0.5350 C=0.5004
                       seed 5: F=0.5941 B=0.5988 C=0.5049   seed 42: F=0.5565 B=0.5579 C=0.5139

feature_dropout:       seed 1: F=0.5359 B=0.5364 C=0.4927   seed 2: F=0.5732 B=0.5728 C=0.5105
                       seed 3: F=0.6365 B=0.6432 C=0.4561   seed 4: F=0.6292 B=0.6237 C=0.5272
                       seed 5: F=0.6614 B=0.6653 C=0.5215   seed 42: F=0.5635 B=0.5619 C=0.4741
```

Every seed is reported — none hidden or excluded.

## 13. Cross-seed aggregates and CIs

See sections 10–11. As in Phase 3.4, n=6 is too small for a formal
significance test; every interval above is a descriptive Student-t
interval over the six per-seed point estimates, not a hypothesis test.

## 14. Within-seed bootstrap (primary seed 42, AUROC)

| Condition | F | B | C |
|---|---|---|---|
| clean | [0.6031, 0.6452] | [0.6069, 0.6484] | [0.4969, 0.5413] |
| feature_noise_mild | [0.5808, 0.6222] | [0.5843, 0.6260] | [0.5141, 0.5574] |
| feature_noise_severe | [0.5363, 0.5778] | [0.5371, 0.5789] | [0.4919, 0.5363] |
| feature_dropout | [0.5428, 0.5835] | [0.5422, 0.5826] | [0.4526, 0.4944] |

2000 resamples, percentile method, seed 0 — kept entirely separate from
the cross-seed intervals above; not combined.

## 15. AUROC comparison

F and B remain tightly coupled across every condition (within ~0.005–0.03
AUROC of each other), while both remain clearly separated from C and A in
every condition except that C briefly nudges ahead of F on one individual
seed under severe noise (section 23). No candidate's ranking relative to
the others reverses wholesale under any attack.

## 16. AUPRC comparison

**Caveat before reading this section:** unlike AUROC, AUPRC's baseline
depends on failure prevalence, and prevalence itself shifts under the
noise attacks (a noisier input makes the workload model wrong more
often, raising the empirical failure rate) — clean AUPRC and attacked
AUPRC are **not directly comparable** the way clean/attacked AUROC are.
With that caveat: AUPRC rises for every candidate under stronger attacks
(prevalence effect dominates), and F and B remain close to each other at
every condition (e.g. severe noise: F=0.426, B=0.429; dropout: F=0.427,
B=0.415 — F marginally ahead here).

## 17. Risk-coverage comparison (AURC)

| Candidate | Clean | Mild noise | Severe noise | Dropout |
|---|---|---|---|---|
| A | 0.2699 | 0.2961 | 0.3885 | 0.3618 |
| C | 0.2767 | 0.3030 | 0.3815 | 0.3539 |
| **F** | **0.1972** | **0.2330** | **0.3590** | **0.2919** |
| B | 0.1941 | 0.2286 | 0.3526 | 0.2907 |

AURC rises (worse) for every candidate under every attack — expected,
since the workload model itself gets less accurate. F and B remain the
two lowest (best) at every condition; the gap between {F, B} and {A, C}
narrows under severe noise (all four candidates converge toward ~0.35–0.39
as the attack overwhelms the failure signal) but does not close.

## 18. Precision/recall at fixed coverage

At 5% coverage (F vs. B):

| Condition | F precision | B precision | F recall | B recall |
|---|---|---|---|---|
| clean | 0.438 | 0.436 | 0.081 | 0.080 |
| feature_noise_mild | 0.442 | 0.457 | 0.073 | 0.075 |
| feature_noise_severe | 0.418 | 0.460 | 0.053 | 0.059 |
| **feature_dropout** | **0.486** | **0.448** | 0.071 | 0.065 |

At every other fixed coverage point (10/20/50%) F and B stay within ~1–2
points of each other in every condition (full detail in
`attack_generalization.json`). Feature dropout is the one condition where
F's low-coverage precision is *ahead* of B's, consistent with its 3/6
per-seed AUROC win count there — the closest the two candidates come to
diverging in F's favor anywhere in this study, but still not a
consistent or large enough margin to claim F is superior under dropout
(see section 30's comparison rules).

## 19. Calibration

ECE (meaningful only for A/B/F/C's probability-valued outputs; C's
Gaussian-kernel score is never reported — consistent with Phase 3.1's
finding that it is not a probability):

| Candidate | Clean | Mild noise | Severe noise | Dropout |
|---|---|---|---|---|
| F | 0.075 | 0.094 | 0.196 | 0.127 |
| B | 0.082 | 0.117 | 0.229 | 0.123 |

Both degrade (higher ECE = worse) under stronger attacks — expected,
since neither was recalibrated for the attacked distribution. F's ECE is
slightly better than B's at every condition except dropout, where they
are essentially tied (0.127 vs 0.123).

## 20. Robustness/degradation analysis

`excess_auroc_retention_ratio = (attack_auroc - 0.5) / (clean_auroc -
0.5)`, defined in the frozen protocol before evaluation. Undefined
(reported `null`, never fabricated) for A, whose clean AUROC is exactly
0.5.

| Condition | F retention | B retention | C retention |
|---|---|---|---|
| feature_noise_mild | 0.838 | 0.843 | 0.918 |
| feature_noise_severe | 0.325 | 0.352 | 0.315 |
| feature_dropout | 0.658 | 0.632 | 0.444 |

Reading this carefully: C's "high retention" at mild noise (0.918) and
low retention at severe noise (0.315) is a small-number artifact — C's
clean excess-AUROC (0.0141) is tiny, so its retention ratio is highly
sensitive to noise and not informative on its own; the raw AUROC values
(section 11) are the more trustworthy comparison for C. Between F and B
specifically: retention is within ~1–5 percentage points of each other at
every condition, alternating which one retains marginally more (B
retains slightly more under noise, F retains slightly more under
dropout). **Neither candidate collapses disproportionately relative to
the other under any tested attack.**

## 21. F vs calibrated confidence

Consistent with Phase 3.4: F tracks B closely in every attack condition
and does not establish a consistent advantage over it. F beats B on
AUROC in 1/6, 1/6, 0/6, and 3/6 seeds across clean/mild/severe/dropout
respectively — never a majority except nowhere. The gap between them is
small in absolute terms at every condition (typically <0.01–0.03 AUROC)
and both degrade by similar amounts under the same attack. **This
phase does not establish that F is more robust than B, nor that F is
less robust than B in any way that would change Phase 3.4's
conclusion** — the relationship between them (close, F slightly and
inconsistently behind) is stable across the clean condition and all
three attacks tested here.

## 22. F vs original Failure Memory

F clearly and consistently outperforms C at every condition except one
individual seed (section 23): 6/6 wins at clean, mild noise, and
dropout; 5/6 at severe noise. C itself stays close to no-signal (AUROC
0.497–0.515) at every condition, including one aggregate value
(feature_dropout: 0.4970) that is numerically *below* 0.5 — consistent
with Phase 3.1–3.4's finding that the original Failure Memory mechanism
carries little to no reliable signal, a finding that persists rather than
reverses under attack.

## 23. Failure cases

**Explicitly reported, not hidden, per the brief's section 29/31
requirement:**

- **Severe noise, seed 1**: C (0.5306) narrowly exceeds both F (0.5231)
  and B (0.5234) — the only seed/condition combination in this entire
  study where the original Failure Memory beats either supervised/
  calibrated candidate. Given C's aggregate AUROC across all 6 seeds at
  this condition (0.5152 [0.5008, 0.5296]) remains barely above 0.5 and
  its per-seed values elsewhere in this condition are unremarkable
  (0.508, 0.533, 0.500, 0.505, 0.514), this reads as ordinary per-seed
  noise around a near-null signal, not a systematic reversal — but it is
  reported as observed, not smoothed over.
- **Feature dropout is F's/B's weakest relative margin over C and also
  the condition where F comes closest to (and briefly exceeds) B**: F
  beats B on AUROC in 3/6 seeds here (vs. 0–1/6 everywhere else) and
  leads on precision@5%. This is the most "mixed" result in the study —
  reported as mixed, not selected as a headline win for F.
- **Severe noise degrades every candidate toward the no-signal floor**:
  F, B, and C are within 0.06 AUROC of each other and all much closer to
  0.5 than on clean data — the failure-detection task becomes
  substantially harder under strong input corruption for every method
  tested, including calibrated confidence.

No condition was removed or re-parameterized after seeing these results.

## 24. Limitations

- Only two attack mechanisms (additive noise at two severities, and a
  single fixed feature-dropout set) were tested — a small, predetermined
  matrix, not an exhaustive attack taxonomy. A wider corruption space
  (different feature subsets, structured/adversarial noise directions,
  combined noise+dropout) was not explored and is not claimed to be
  covered.
- AUPRC is not directly comparable across conditions due to
  prevalence shift (section 16) — reported for completeness, but not
  used as a primary robustness signal in this report's conclusions.
- The feature-dropout feature set (`f2`, `f4`) was chosen by a stated,
  non-adaptive rule, but it is still a single arbitrary choice among
  `C(5,2)=10` possible pairs; different pairs might show different
  degradation patterns and were not tested.
- Six seeds remain a small sample for cross-seed inference; several
  per-condition CIs (especially for C, whose signal is near-null
  throughout) are wide relative to the effect sizes being compared.

## 25. Threats to validity

- All four candidates share the same underlying calibrator and workload
  model; an attack that degrades the calibrator's input features
  necessarily degrades every downstream candidate that consumes
  calibrated confidence (B, and indirectly F, whose embedding uses it) —
  this is a structural reason F and B move together under attack, not
  necessarily evidence that they carry the same information in general
  (see Phase 3.4 section 12, still unresolved).
- The attacks are purely synthetic transforms of a synthetic benchmark;
  nothing here speaks to how a real telemetry pipeline would actually
  fail or be attacked.
- No adversarial (gradient-based, worst-case-search) attack was
  attempted — only random/structural corruption. A targeted adversarial
  perturbation against the workload model's decision boundary could
  behave very differently and was out of scope here.

## 26. What Phase 3.5 establishes

- F's predictive relationship to the three baselines (A, B, C) — clearly
  above A and C, closely tracking but not exceeding B — **persists
  across all three tested covariate-shift attack conditions**, not just
  the clean benchmark.
- Neither F nor B collapses disproportionately relative to the other
  under any tested attack; their degradation (AUROC delta, retention
  ratio, ECE increase) is of similar magnitude at every severity.
- The original Failure Memory (C) continues to show little to no
  reliable signal under attack, consistent with every prior phase.
- No leakage, refitting, or attack-parameter influence on any fitted
  model was found (7/7 runtime checks passed).
- The feature-dropout condition is the one place F's relative standing
  vs. B improves somewhat (3/6 seed wins, ahead on precision@5%) — a
  genuinely mixed result, reported honestly rather than as a headline.

## 27. What Phase 3.5 does NOT establish

- That F generalizes *better* than B under attack — not shown; the
  evidence is that they degrade similarly and remain close, not that
  either is clearly more attack-robust than the other.
- That F is complementary to B — this phase's core objective was attack
  generalization, not complementarity; the (unperformed) complementarity
  sub-experiment described in `configs/phase3_5_attack_protocol.json`
  remains a required, separate follow-up gate (per the brief section 23),
  not attempted here.
- Anything about real-world attack robustness or security — every
  condition here is a synthetic, deterministic transform of a synthetic
  benchmark.
- Robustness to attack types outside the tested matrix (adversarial
  perturbations, different feature subsets, combined attacks, concept
  -level attacks).
- Statistical significance in the classical sense — every interval here
  is descriptive (n=6 cross-seed, or single-seed bootstrap), not a
  hypothesis test.

## 28. Recommendation

**Formal status:**

# 🟢 GENERALIZATION SUPPORTED

*in the specific, narrow sense defined for this phase*: F demonstrates
consistent robustness under the three predefined, unseen covariate-shift
attack conditions — its clear advantage over no-signal and the original
Failure Memory persists, its degradation under attack is proportionate to
(not worse than) calibrated confidence's own degradation, and it never
collapses to an uninformative signal while other candidates remain
useful. It remains **competitive with, but not superior to**, calibrated
confidence at every tested severity — consistent with, not contradicting,
Phase 3.4's frozen 🟡 INCONCLUSIVE finding on the (different) question of
whether F beats or is complementary to B.

**Whether this justifies moving forward:** The evidence justifies
treating F as a candidate that does not become unreliable or dangerous
relative to the existing baselines under the tested attack conditions —
useful evidence for eventually considering it, but not authorization to
use it. Per the brief's gate (section 33), **before any autonomous
integration of Failure Risk**, the project still needs:

1. The complementarity sub-experiment (B alone vs. F alone vs. a simple,
   pre-specified B+F model) — explicitly deferred from Phase 3.5, not
   performed here.
2. Dedicated calibration/operational-risk analysis beyond the ECE numbers
   already reported.
3. A defined, tested policy for safe decision thresholds and downstream
   recovery consequences — none of which exists yet.

Phase 3.5 is evidence. It is not authorization. **No autonomous
integration, recovery, retraining, or deployment work is performed in
this phase**, and Phase 3.6 is explicitly not begun.
