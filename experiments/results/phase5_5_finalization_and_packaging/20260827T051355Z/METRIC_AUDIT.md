# Phase 5.5 — Metric Audit

Independent pathological-case test battery written and run in this phase
against the actual `src/benchmark/metrics.py` implementation (not against
any prior report's claims). All 17 cases passed.

| Case | Expected | Result |
|---|---|---|
| AUROC, all-positive labels | `NOT_DEFINED_SINGLE_CLASS`, value=None (never 0.5) | PASS |
| AUROC, all-negative labels | `NOT_DEFINED_SINGLE_CLASS` | PASS |
| AUPRC, single-class | `NOT_DEFINED_SINGLE_CLASS` | PASS |
| AUROC, empty input | `UNDEFINED_ZERO_DENOMINATOR` | PASS |
| Brier, empty input | `UNDEFINED_ZERO_DENOMINATOR` | PASS |
| ECE, empty input | `UNDEFINED_ZERO_DENOMINATOR` | PASS |
| ECE, constant predictor, correctly calibrated (p=1.0, all correct) | ECE ≈ 0 | PASS |
| ECE, constant predictor, miscalibrated (p=1.0, all wrong) | ECE = 1.0 | PASS |
| Selective risk, zero coverage (all-abstain) | `UNDEFINED_ZERO_COVERAGE` | PASS |
| Coverage metric, empty action list | `UNDEFINED_ZERO_DENOMINATOR` | PASS |
| Unnecessary-abstention, all-answer (n_abstain=0) | `UNDEFINED_ZERO_DENOMINATOR` | PASS |
| Final-correctness, all-abstain (n_resolved=0) | `UNDEFINED_ZERO_COVERAGE` | PASS |
| `rate(0, 35)` (zero recovery) | DEFINED, value=0.0 (not undefined) | PASS |
| `rate(35, 35)` (100% recovery) | DEFINED, value=1.0 | PASS |
| `rate(0, 0)` | `UNDEFINED_ZERO_DENOMINATOR` | PASS |
| Operating-point validity, always-fires (FAR=1.0, AUROC=0.99) | `RANKING_SIGNAL_BUT_OPERATIONALLY_INVALID`, `operationally_successful=False` — an always-fires predictor cannot appear to win regardless of AUROC | PASS |
| Risk-coverage, empty input | `UNDEFINED_ZERO_DENOMINATOR` | PASS |

## ECE binning

`ece()` uses `ECE_N_BINS=10` equal-width bins on `[0, 1]`; bin *i* is
`[i/10, (i+1)/10)` for `i < 9`, and the last bin is closed on both ends
(`[0.9, 1.0]`) so that a prediction of exactly `1.0` is not dropped.
Confirmed by direct code reading (`metrics.py` lines 141–166) and by the
constant-predictor test above (p=1.0 correctly lands in the last bin and
contributes to the ECE value rather than being silently excluded).
Documented explicitly in the `binning` field of every ECE result
(`"equal_width_[0,1]"`), so a benchmark consumer is never left guessing.

## Confidence intervals

- Binomial rates (coverage, abstention, recovery, precision/recall/etc.)
  use a closed-form Wilson score interval (`wilson_ci`), verified against
  the standard formula by direct code reading — no bootstrap noise is
  introduced for these.
- Ranking metrics (AUROC, AUPRC, Brier, ECE) use a nonparametric
  percentile bootstrap (`bootstrap_metric`), explicit seed
  (`BOOTSTRAP_SEED`), with degenerate resamples (e.g. a bootstrap draw
  that happens to be single-class) tracked in `n_degenerate_resamples`
  rather than silently dropped or coerced to a fabricated value.

## Always-fires / operational-validity protection

`operating_point_validity()` was specifically re-tested with an
adversarial input (AUROC=0.99, FAR=1.0) to confirm a naive "predict
failure always" policy cannot be reported as `operationally_successful` —
confirmed: it returns `RANKING_SIGNAL_BUT_OPERATIONALLY_INVALID` and
`operationally_successful: False` regardless of how high AUROC is. This
directly satisfies the "an always-abstain / always-fires policy cannot
appear to win" requirement for both the abstention and failure-prediction
tracks (the abstention track's own `BASE-ALWAYS-ABSTAIN` baseline is
independently flagged `ALWAYS_ABSTAIN_NOT_SUCCESSFUL` in
`tasks.py`/`baselines.py`, confirmed in the rerun's `baseline_results`).

## Finding

No metric implementation defect was found. `src/benchmark/metrics.py`
required no changes.
