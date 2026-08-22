# PHASE 3.5 — DISTRIBUTION-ROBUST UNCERTAINTY & SELECTIVE DECISION RESEARCH

## 1. Motivation

Phase 3.4 found that bootstrap/model-variability uncertainty was associated with prediction error, especially under temporal shift, but its first abstention policy failed on the canonical future boundary. Phase 3.5 tested whether that relationship is stable across multiple future regimes and whether one pre-registered policy can improve safety without sacrificing operational coverage.

## 2. Phase 3.4 evidence

Phase 3.4 rejected Platt calibration, rejected its 80%-coverage abstention policy, and rejected the combined layer. Bootstrap uncertainty remained an **INTERESTING FINDING**, not an accepted V1.1 component. V1 remains frozen and is the permanent control.

## 3. Multi-temporal fold design

The additional protocol used a 40% chronological warm-up followed by three contiguous 20% future evaluation regimes. Each fold trained on preceding rows, used the immediately preceding training tail for validation, and evaluated on the next future block. These folds are research-only and do not replace V1’s canonical random or temporal split.

## 4. Fold characteristics

| Fold | Train | Validation | Test | Temporal regime | Failure rate |
|---|---:|---:|---:|---|---:|
| Fold 1 | 3,200 | 800 | 2,000 | First future block after 40% warm-up | 0.1725 |
| Fold 2 | 4,800 | 1,200 | 2,000 | Second future block | 0.3175 |
| Fold 3 | 6,400 | 1,600 | 2,000 | Final future block | 0.3785 |

All folds contain meaningful sample sizes and both outcome classes. Chronological boundaries and raw time ranges are recorded in the A protocol and results artifacts.

## 5. Uncertainty methodology

The unchanged Phase 3.4-B method was used: nine bootstrap/model-variability V1-compatible logistic fits, trained only on each fold’s preceding training rows. Uncertainty is the standard deviation of decision-time predicted probabilities. The high and low strata were the upper and lower uncertainty quartiles, fixed before evaluation.

## 6. Cross-temporal uncertainty results

| Fold | V1 AUROC | V1 AUPRC | Mean uncertainty | High-uncertainty error | Low-uncertainty error | Difference | Ratio | Correlation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Fold 1 | 0.5902 | 0.2826 | 0.0139 | 0.3070 | 0.1350 | 0.1720 | 2.27 | recorded in artifact |
| Fold 2 | 0.7166 | 0.5266 | 0.0186 | 0.4770 | 0.1980 | 0.2790 | 2.41 | recorded in artifact |
| Fold 3 | 0.7717 | 0.5757 | 0.0210 | 0.2460 | 0.1020 | 0.1440 | 2.41 | 0.0164 |

High uncertainty separated more errors than low uncertainty on all three folds. This is a robust diagnostic relationship under the pre-registered criterion: positive separation on at least two folds, no reversal, and acceptable research computation cost.

## 7. Uncertainty stability analysis

The relationship is consistent in direction across the three regimes, with high-to-low error ratios above 2 on every fold. The magnitude varies, and the signal’s correlation with the binary error indicator is not itself a sufficient deployment criterion. The evidence supports **diagnostic robustness**, not automatic actionability.

## 8. Selective policy

Before evaluation, one policy was declared: abstain when uncertainty exceeds the fold-validation 80th percentile. The policy was not swept across multiple coverage targets. The minimum operational coverage gate was 0.50. The safety gate required candidate accepted-case risk to be lower than V1 on every fold.

## 9. Safety gate

The safety gate was not met. The policy improved accepted-case risk only on Fold 1 and degraded it on Folds 2 and 3. The worst-fold degradation was +0.0438 risk points. No unsafe execution was performed; the candidate remained an offline research policy.

## 10. Coverage gate

The coverage gate was met numerically on Folds 2 and 3 but not Fold 1. Fold 1 coverage was 0.2520, below the pre-registered 0.50 minimum. This is not a zero-coverage artifact; it is nevertheless operationally insufficient under the declared gate.

## 11. Per-fold results

| Fold | Temporal regime | V1 risk | Candidate coverage | Candidate risk | Risk delta, candidate minus V1 | Decision |
|---|---|---:|---:|---:|---:|---|
| Fold 1 | First future block | 0.1725 | 0.2520 | 0.1230 | -0.0495 | Improved risk, failed coverage |
| Fold 2 | Second future block | 0.3175 | 0.8075 | 0.3276 | +0.0101 | Degraded |
| Fold 3 | Final future block | 0.3785 | 0.7755 | 0.4223 | +0.0438 | Degraded |

## 12. Aggregate results

The mean risk delta was +0.0015, the median was +0.0101, and the standard deviation was 0.0381. One fold improved and two degraded. The mean result therefore hides a material temporal failure pattern; the per-fold evidence governs the decision.

## 13. Worst-case temporal behavior

Fold 3 was the worst regime: candidate selective risk was 0.4223 versus V1 risk of 0.3785, while coverage remained 0.7755. This is a direct safety regression at meaningful coverage and prevents acceptance.

## 14. Operational overhead

The uncertainty estimator requires nine fitted model artifacts per fold and is substantially more expensive than single-model V1 inference. Serialization and reload were supported for the research artifacts, but production latency and resource acceptance were not established.

## 15. Robustness classification

The uncertainty-error relationship is **ROBUST AS A DIAGNOSTIC SIGNAL**, but the selective policy is not robust. Under the required Phase 3.5 outcomes, the overall result is **NON-ACTIONABLE**: uncertainty predicts error, yet the tested rule does not provide a safe, useful control signal across future regimes.

## 16. Decision

**HOLD as a diagnostic/research finding; do not accept for V1.1 integration.** This is consistent with the required distinction that uncertainty may be genuinely predictive of error while uncertainty-based abstention is not yet useful.

## 17. Limitations

The research folds use one restored dataset and three contiguous regimes. They are additional research boundaries and do not replace the canonical V1 temporal future test. The bootstrap estimator is computationally costly. The historical aggregate V1 result of **507 passed / 7 skipped / 0 failed** is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.

## 18. V1 comparison

V1 remains unchanged, fully operational as the control, and the only production-eligible predictor. Phase 3.5 adds no runtime training, no new production threshold, no new feature set, and no automatic integration.

## 19. Phase 3.4 versus Phase 3.5 comparison

Phase 3.4 demonstrated the uncertainty-error finding on one future boundary and rejected a single 80%-coverage policy. Phase 3.5 showed that the error relationship remains directionally consistent across three research future regimes, while the single pre-registered selective policy fails coverage in one regime and safety in two regimes. The result is therefore stronger diagnostic evidence but no actionable V1.1 control.

## 20. Next research question

Can a separately pre-registered, safety-constrained decision rule combine uncertainty with calibrated risk across multiple forward folds without using any future regime for tuning, while meeting both a minimum coverage gate and a per-fold safety gate?

## Required final synthesis table

| Fold | Temporal Regime | V1 AUROC | V1 Risk | Mean Uncertainty | High-Uncertainty Error | Low-Uncertainty Error | Candidate Coverage | Candidate Risk | Decision |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Fold 1 | First future block | 0.5902 | 0.1725 | 0.0139 | 0.3070 | 0.1350 | 0.2520 | 0.1230 | Coverage gate failed |
| Fold 2 | Second future block | 0.7166 | 0.3175 | 0.0186 | 0.4770 | 0.1980 | 0.8075 | 0.3276 | Safety gate failed |
| Fold 3 | Final future block | 0.7717 | 0.3785 | 0.0210 | 0.2460 | 0.1020 | 0.7755 | 0.4223 | Safety gate failed |

**Mean:** risk delta +0.0015. **Median:** +0.0101. **Standard deviation:** 0.0381. **Worst fold:** Fold 3, +0.0438. **Best fold:** Fold 1, -0.0495. **Folds improved:** 1/3. **Folds degraded:** 2/3.

> **V1 remains the control. Phase 3.5 confirms that uncertainty can diagnose error across regimes, but it does not yet justify using that signal to control autonomous decisions.**
