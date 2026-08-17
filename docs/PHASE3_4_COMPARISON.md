# Phase 3.4 — Compare Everything Against the Same Baseline

**Status: COMPLETE.** This document is the Phase 3.4 deliverable. Phase 3.4
performs **no new model fitting, training, or tuning**. It consolidates
already-frozen results from Phase 3.1, Phase 3.2, and Phase 3.2C into one
comparison, under the same protocol, evaluated on the same seeds.

Companion artifacts:
- Script: [`benchmarks/phase3_4_compare.py`](../benchmarks/phase3_4_compare.py)
- Machine-readable output: [`experiments/results/phase3_4/comparison.json`](../experiments/results/phase3_4/comparison.json)
- Tests: [`tests/integration/test_phase3_4_compare_pipeline.py`](../tests/integration/test_phase3_4_compare_pipeline.py)

---

## 1. Objective

Given everything evaluated in Phase 3.1–3.3, how do the candidate
failure-risk systems compare when evaluated under the **same frozen
protocol** and the **same evaluation criteria**? This phase does not
develop new models; it answers ten specific questions (section 8 of the
Phase 3.4 brief) about the candidates already on record.

## 2. Frozen protocol reference

`configs/phase3_1_protocol.json` (unmodified). Key values, verified
identical across every source file this comparison reads from (Phase
3.1/3.2/3.2C `per_seed_results.json` and `aggregate_results.json` `meta.protocol_config`
blocks — checked programmatically by `phase3_4_compare.load_sources`,
which raises `ProtocolDiscrepancyError` on any mismatch; none was found):

- Seeds: `[1, 2, 3, 4, 5, 42]`; primary seed `42`
- Coverage operating points: `5%, 10%, 20%, 50%`
- AURC coverage grid: 5%–100% in 5% steps
- Calibration bins: 10
- Bootstrap: 2000 resamples, percentile method, seed 0, 95% CI
- Cross-seed CI: Student-t interval over the six per-seed point estimates
- Failure definition, preprocessing, and train/test separation: unchanged
  from Phase 3.1

Additionally verified: for every seed, `n_test_samples` and
`test_failure_prevalence` are byte-identical across the Phase
3.1/3.2/3.2C result files (`_assert_test_sets_aligned`). This is what
makes per-seed comparisons across those three phases validly **paired** —
same seed + same frozen protocol + deterministic `build_system` produce
the same regime-3/4 stream and the same `y_fail` vector, so the same-seed
row from each phase scores the exact same held-out samples.

## 3. Candidates compared

| ID | Label | Source | Source key |
|---|---|---|---|
| A | No signal | Phase 3.2 | `A_no_signal` |
| B | Calibrated confidence | Phase 3.2 | `B_calibrated_confidence` |
| C | Original Phase 2 Failure Memory | Phase 3.2 | `control_phase2_failure_memory` |
| D | Candidate B — raw structured features | Phase 3.2 | `candidate_raw_features` |
| E | Candidate C — failure-history representation + supervised classifier | Phase 3.2 | `candidate_failure_history` |
| E′ | Phase 3.2C Experiment C (positive control) | Phase 3.2C | `experiment_C_control` |
| F | **Supervised Failure Risk** (Phase 3.2C Experiment B, selected candidate) | Phase 3.2C | `experiment_B_old_repr_supervised` |

**E and E′ are the same implementation, not two independent systems.**
Phase 3.2C documented Experiment C as an unmodified reproduction of Phase
3.2's Candidate C, included as that ablation's positive control. This
comparison verifies that documented claim rather than assuming it: E and
E′ produce **identical per-seed AUROC on all 6 seeds**
(`_assert_duplicate_candidates_match`, `identical: true`, no mismatches).
Wherever this report counts "how many candidates ...", E and E′ are
counted once.

No new candidate was introduced. This is exactly the set named in section
9 of the Phase 3.4 brief.

## 4. Experimental lineage of each candidate

- **A (no signal)** — Phase 3.1 baseline A, unchanged constant score
  equal to empirical failure prevalence on regime 2.
- **B (calibrated confidence)** — Phase 3.1 baseline B,
  `1 - calibrated_confidence`. The strongest established reference prior
  to Phase 3.4.
- **C (original Failure Memory)** — Phase 3.1 baseline C / Phase 3.2
  control. Unmodified Phase 2 KMeans + Gaussian-kernel similarity.
- **D (raw structured features)** — Phase 3.2 Candidate B:
  `RawFeatureFailureRisk`, KMeans directly on raw structured features
  (not a probability — `is_probability=False`).
- **E / E′ (failure-history + supervised)** — Phase 3.2 Candidate C /
  Phase 3.2C Experiment C: `FailureHistoryRiskModel`, rich k-NN
  failure-history features + logistic regression.
- **F (Supervised Failure Risk)** — Phase 3.2C Experiment B:
  `Phase2RepresentationSupervisedRisk`, the **old Phase 2 PCA
  representation** + logistic regression. Phase 3.2C's ablation isolated
  the supervised classifier (not the richer representation) as the
  mechanism that mattered, and Phase 3.3 froze this exact candidate for
  generalization testing.

## 5. Aggregate results (cross-seed, 6 seeds, Student-t 95% CI)

| Candidate | AUROC | AUPRC | AURC (↓ better) | ECE |
|---|---|---|---|---|
| A — No signal | 0.5000 [0.5000, 0.5000] | 0.2806 | 0.2699 | 0.0653 |
| C — Original Failure Memory | 0.5141 [0.4914, 0.5368] | 0.2971 | 0.2767 | not meaningful (similarity score) |
| D — Raw structured features | 0.5308 [0.5018, 0.5598] | 0.3088 | 0.2655 | not meaningful (similarity score) |
| E/E′ — Failure-history + supervised | 0.5809 [0.5472, 0.6146] | 0.3376 | 0.2327 | 0.1109 |
| **F — Supervised Failure Risk (selected)** | **0.6548 [0.6159, 0.6938]** | 0.3912 | **0.1972** | 0.0753 |
| B — Calibrated confidence | 0.6599 [0.6185, 0.7013] | 0.3835 | 0.1941 | 0.0823 |

All numbers reproduced exactly (to float precision) from Phase 3.2 /
Phase 3.2C `aggregate_results.json`; `phase3_4_compare.py` independently
recomputes each aggregate from per-seed values with the same `_t_interval`
helper Phase 3.1 defined, and raises on any disagreement with the stored
files. None occurred.

**Ranking by AUROC:** B > F > E ≈ E′ > D > C > A.
**Ranking by AURC (lower = better):** B < F < E ≈ E′ < D < A < C — the same
ordering, with the notable exception that C (original Failure Memory)
falls *below* the no-signal baseline on AURC despite a marginally higher
AUROC mean.

## 6. 95% confidence intervals

Two distinct sources of uncertainty are reported and never combined:

- **Cross-seed variability** (table above): Student-t interval over the
  six per-seed point estimates. This is the uncertainty that matters for
  "would this hold on a different training draw."
- **Within-seed bootstrap uncertainty** (primary seed 42 only): percentile
  bootstrap over resamples of that one seed's held-out rows. Reported
  only for AUROC/AUPRC (the only metrics the Phase 3.1/3.2/3.2C scripts
  bootstrapped). Example, primary seed 42, AUROC:
  - F (Supervised Failure Risk): [0.6031, 0.6452]
  - B (calibrated confidence): [0.6069, 0.6484]
  - C (original Failure Memory): [0.4969, 0.5413]

  These intervals are narrower than the cross-seed intervals and answer a
  different question (sampling noise within one test set, not
  seed-to-seed variability) — they are not interchangeable, and this
  report does not average or otherwise merge them.

## 7. Per-seed paired comparisons

For every candidate, versus each of the three established baselines
(no signal, original Failure Memory, calibrated confidence), computed
per-seed on the exact same 6 held-out test sets:

| Candidate | Beats no-signal | Beats orig. Failure Memory | Beats calibrated confidence |
|---|---|---|---|
| C — Original Failure Memory | 1/6 | — | 0/6 |
| D — Raw structured features | 6/6 | 5/6 | 0/6 |
| E/E′ — Failure-history + supervised | 6/6 | 6/6 | 0/6 |
| **F — Supervised Failure Risk** | **6/6** | **6/6** | 1/6 |
| B — Calibrated confidence | 6/6 | 6/6 | — |

Mean paired AUROC difference (Student-t 95% CI over the 6 paired
per-seed differences; **descriptive interval, not a significance test** —
see caveat below):

- F vs. no signal: **+0.1548** [0.1159, 0.1938] — CI excludes 0.
- F vs. original Failure Memory: **+0.1407** [0.0865, 0.1950] — CI excludes 0.
- F vs. calibrated confidence: **−0.0051** [−0.0096, −0.0006] — CI excludes
  0, on the *negative* side. F is consistently, if narrowly, below
  calibrated confidence — this is not noise in either direction, it is a
  small but consistent gap.
- C (original Failure Memory) vs. no signal: +0.0141 [−0.0368, 0.0086] —
  CI includes 0. **C does not reliably beat no-signal on a per-seed
  basis**, consistent with Phase 3.1/3.2's conclusion that the original
  Failure Memory carries essentially no signal.

**Statistical caveat (explicit, per the Phase 3.4 brief section 11):**
with n=6 predetermined seeds, no formal hypothesis test (t-test, sign
test, Wilcoxon) has meaningful statistical power, and none is computed
here. The Student-t intervals above are reported as descriptive interval
estimates of the paired difference, exactly as the frozen protocol already
specifies for cross-seed aggregation — they are not being used as a
significance test, and "CI excludes 0" is reported as a consistency
signal, not as proof of a population-level effect.

## 8. AUROC comparison

Covered in section 5/7 above. F and B are clearly separated from
everything else (C, D, E/E′, A) by a wide margin (~0.07–0.16 AUROC), and
F and B are close to each other (~0.005 apart) but F is consistently
slightly below B, not above or indistinguishable.

## 9. AUPRC comparison

Same ordering as AUROC: A (0.281) < C (0.297) < D (0.309) < E/E′ (0.338) <
B (0.384) < F (0.391) — note F's AUPRC mean is actually marginally *above*
B's, unlike AUROC, though this was not paired/CI-tested here (AUPRC was
not part of the frozen per-seed paired-comparison scope, which the brief
specified for AUROC). This is worth flagging as a discrepancy in ranking
between the two ranking metrics but should not be over-read given the
absence of a paired CI for AUPRC specifically.

## 10. AURC comparison (risk-coverage)

Lower is better. B (0.1941) and F (0.1972) are the two best (i.e. lowest
average selective risk across the 5%–100% coverage grid), followed by
E/E′ (0.2327), then D (0.2655), then **A (0.2699) beats C (0.2767)** — the
original Failure Memory has *worse* risk-coverage behavior than doing
nothing and flagging a random subset by prevalence. This matches its weak
AUROC/near-1-vs-6-seeds-win record in section 7.

### Low-coverage precision/recall (the region autonomous abstention would use)

| Candidate | Prec@5% | Rec@5% | Prec@10% | Rec@10% | Prec@20% | Rec@20% | Prec@50% | Rec@50% |
|---|---|---|---|---|---|---|---|---|
| A — No signal | 0.262 | 0.048 | 0.257 | 0.094 | 0.263 | 0.190 | 0.271 | 0.488 |
| C — Failure Memory | 0.321 | 0.057 | 0.317 | 0.113 | 0.310 | 0.220 | 0.290 | 0.514 |
| D — Raw features | 0.346 | 0.061 | 0.352 | 0.127 | 0.320 | 0.230 | 0.297 | 0.530 |
| E/E′ — History+supervised | 0.376 | 0.068 | 0.378 | 0.138 | 0.361 | 0.261 | 0.322 | 0.579 |
| **F — Supervised Failure Risk** | **0.438** | **0.081** | **0.427** | **0.157** | **0.416** | **0.303** | 0.377 | 0.682 |
| B — Calibrated confidence | 0.436 | 0.080 | 0.440 | 0.162 | 0.416 | 0.302 | **0.378** | **0.685** |

At every fixed coverage point, the same two-tier structure holds: {B, F}
clearly ahead of {E/E′}, which is clearly ahead of {D, C, A}. F and B are
within ~1 percentage point of each other at every coverage level — an
autonomous system flagging its riskiest 5–20% of workloads would get
essentially the same precision/recall from either.

## 11. Calibration comparison

ECE is reported only for representations that were fit/designed as
probabilities (`is_probability=True` on the underlying representation
class — verified programmatically, not asserted): A, B, E/E′, F. **ECE is
explicitly "not meaningful" and not computed for C (original Failure
Memory) and D (raw structured features)** — both are Gaussian-kernel /
cluster-similarity scores, never calibrated as probabilities. Among the
probability-valued candidates, A (0.065, trivially — a constant score
equals its own empirical rate almost by construction) and F (0.075) have
the lowest ECE; B (0.082) and E/E′ (0.111) are less well calibrated. Lower
ECE is not the same as higher discriminative power — F has both a
reasonably low ECE *and* strong AUROC, which is a more meaningful
combination than A's near-zero ECE (a constant score is trivially
"calibrated" while providing no ranking information at all, AUROC=0.5).

## 12. Comparison with calibrated confidence (section 15 of the brief)

**How close are they?** Very close in aggregate (0.6548 vs. 0.6599 AUROC,
a 0.0051 gap) and close per-seed (F beats B on only 1 of 6 seeds; the mean
paired difference's 95% CI is entirely negative and does not cross zero).

**Does Failure Risk consistently track confidence?** Yes — at every fixed
coverage point (5/10/20/50%) their precision and recall are within ~1
point of each other, and their AUROC/AUPRC/AURC orderings are adjacent
across every metric in this report.

**Does Failure Risk add information beyond confidence, or provide
complementary information?** **Not established by Phase 3.4.** This phase
did not run an experiment designed to answer that question — e.g. it did
not fit a model using calibrated confidence as an input feature alongside
Failure Risk, did not test a combined/ensembled score, and did not measure
residual correlation between the two scores' errors. The consistent
per-seed AUROC gap in F's favor over the *original* Failure Memory (0/6
losses) combined with its consistent shortfall against calibrated
confidence (1/6 wins) is most consistent with an interpretation that
**Candidate F is learning a signal that substantially overlaps with what
calibrated confidence already captures**, rather than an independent
signal — but this is an interpretation of the pattern already visible in
this report's numbers, not a tested claim, and should not be reported as
established.

## 13. Comparison with original Failure Memory

F (and its precursor E/E′) clearly and consistently outperform the
original Phase 2 Failure Memory: 6/6 seeds on AUROC, mean paired AUROC
difference +0.14 with a 95%-CI entirely above zero, and a materially
better AURC (0.197 vs. 0.277 — the original Failure Memory's AURC is
worse than doing nothing). The original Failure Memory itself does not
reliably beat no-signal on a per-seed basis (1/6 seeds), consistent with
Phase 3.1's original finding that it carries essentially no usable
predictive signal on this benchmark.

## 14. Risk-coverage interpretation

At low coverage (5–10%, the region most relevant to an autonomous system
that can only afford to review/abstain on a small fraction of workloads),
F and B both roughly double the precision of the original Failure Memory
and roughly 1.4x the precision of the best non-selected candidate
(E/E′). C (original Failure Memory) is the only candidate whose AURC is
worse than the no-signal baseline across the full 5–100% grid — it would
be actively counterproductive to use for coverage-based triage, not just
unhelpful.

## 15. Limitations

- Six seeds is a small sample for cross-seed inference; the Student-t CIs
  reported here are wide relative to the AUROC gaps being compared for
  the mid-tier candidates (C, D, E/E′), and several pairwise CIs
  (C vs. no-signal, D vs. C) include zero — those comparisons are
  genuinely inconclusive at this seed count, not just "small but real."
- All results are on a single synthetic benchmark
  (`src/data/synthetic.generate_regime_stream`) with a fixed drift
  mechanism; Phase 3.3 tested three drift_scale conditions but Phase 3.4
  compares only the original benchmark condition (`drift_scale=0.35`) —
  it does not re-run this consolidated comparison across Phase 3.3's
  generalization conditions, which was out of this phase's scope.
- AUPRC is reported per-candidate but was not part of the frozen
  per-seed-paired-comparison protocol scope (which specified AUROC for
  win-count/CI purposes); its ranking (F slightly above B) should be
  read as descriptive only.
- ECE for candidate F/E — while "meaningful" by the `is_probability` flag
  — reflects an isotonic/logistic-regression-style calibration that was
  never explicitly re-checked with a dedicated calibration-curve
  diagnostic beyond the 10-bin ECE already computed in Phase 3.2/3.2C.

## 16. Threats to validity

- **Shared feature generator across candidates.** Every candidate in this
  comparison other than B was fit on data derived from the exact same
  `src.pipeline_builder.build_system` call per seed; a systematic property
  of that generator that happens to make calibrated confidence strong
  would propagate identically into every representation-based candidate's
  ceiling.
- **Reused calibrator.** Candidate F, E/E′, and Candidate B's own score
  all depend on the same underlying `ConfidenceCalibrator` — D depends on
  it in the KMeans-similarity mechanism, and F's classifier is trained on
  features that include or derive from calibrated confidence. This is a
  structural reason to expect F and B to be correlated, independent of
  whether F is "actually the same signal" — again, not something Phase
  3.4 tested directly (see section 12).
- **No independent replication benchmark.** All comparisons here are
  within one synthetic benchmark family; nothing in Phase 3.4 speaks to
  real-world transfer.

## 17. What Phase 3.4 establishes

- Under the frozen protocol and all six predetermined seeds, **F
  (Supervised Failure Risk) and B (calibrated confidence) are the two
  strongest candidates on every metric evaluated** (AUROC, AUPRC, AURC,
  precision/recall at every fixed coverage point), clearly separated from
  the original Failure Memory, raw-feature, and failure-history
  candidates.
- **F consistently and substantially outperforms both no-signal (6/6
  seeds) and the original Phase 2 Failure Memory (6/6 seeds)**, with
  cross-seed and paired-difference confidence intervals that exclude
  zero in both cases.
- **F does not consistently outperform calibrated confidence** (1/6
  seeds; paired-difference CI is entirely negative) — the aggregate gap is
  small (~0.005 AUROC) but not in F's favor and not indistinguishable from
  zero in this data.
- **The original Phase 2 Failure Memory does not reliably beat no-signal
  on a per-seed basis** (1/6 seeds) and has the worst AURC of any
  candidate compared, including no-signal — reaffirming Phase 3.1/3.2's
  conclusion, now under a direct multi-candidate comparison rather than
  in isolation.
- **Candidate C (Phase 3.2) and Experiment C (Phase 3.2C) are verified
  byte-identical per-seed**, confirming the ablation's documented claim
  that Experiment C is an exact reproduction, not merely a similar result.

## 18. What Phase 3.4 does NOT establish

- Whether Failure Risk (F) adds information *complementary* to calibrated
  confidence, or is learning a largely overlapping signal — **not
  established**; no experiment here tested combined/ensembled scoring or
  residual correlation (see section 12).
- Whether F would remain competitive with calibrated confidence under
  Phase 3.3's unseen-drift conditions when compared to calibrated
  confidence *in this same consolidated multi-metric format* — Phase 3.3
  already reported per-condition AUROC for both, but Phase 3.4 did not
  re-run the full comparison table (AUPRC/AURC/coverage/ECE/paired
  per-seed) across those conditions.
- Any claim of real-world generalization — this remains a synthetic
  benchmark result.
- Statistical significance in the classical sense for any comparison —
  every interval reported here is a descriptive Student-t or bootstrap
  interval at n=6 or n=1-seed-resampled, explicitly not a hypothesis test.

## 19. Explicit recommendation for Phase 3.5

The evidence here does **not** by itself justify claiming Failure Risk
(F) is ready to replace or augment calibrated confidence in an autonomous
decision path — it tracks confidence closely but has not been shown to
add value beyond it. Before any such use is considered (and before Phase
3.5's attack-generalization work, which this document does not begin):

1. A dedicated complementarity test (does F improve on B when combined,
   e.g. via a simple two-feature model or residual-correlation check) is
   the most direct way to resolve section 12/18's open question, and is
   recommended as a candidate follow-up — **not performed here**, per the
   Phase 3.4 brief's explicit prohibition on new model development inside
   this phase.
2. If Phase 3.5 proceeds with attack/generalization analysis using F, it
   should carry calibrated confidence (B) alongside it as a co-equal
   comparison baseline, not treat B as already-surpassed — this report's
   own numbers do not support that framing.

---

## 20. Formal Phase 3.4 assessment

# 🟡 INCONCLUSIVE

The evidence clearly and consistently supports that the selected
Supervised Failure Risk candidate (F) outperforms the weaker baselines —
no signal and the original Phase 2 Failure Memory — on every metric and
essentially every seed. It does **not** establish that F provides value
beyond the strongest existing reference, calibrated confidence: F tracks
confidence closely but sits slightly and consistently below it on AUROC,
and whether the two carry complementary information was not tested. The
comparison is useful and honest evidence that the supervised-classifier
mechanism (isolated in Phase 3.2C) is real and reproducible relative to
Failure Memory — but it is not evidence that this specific candidate is
"clearly supported" as an improvement over the strongest baseline already
on record.
