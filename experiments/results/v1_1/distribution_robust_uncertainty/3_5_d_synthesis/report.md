# PHASE 3.5 — DISTRIBUTION-ROBUST UNCERTAINTY & SELECTIVE DECISION RESEARCH

## 1. Motivation

Phase 3.4 found that bootstrap/model-variability uncertainty was associated with prediction error, but its first abstention policy failed on the temporal boundary. Phase 3.5 tested whether that finding generalizes across multiple future regimes without tuning on favorable results.

## 2. Phase 3.4 evidence

The Phase 3.4 uncertainty finding was retained as a hypothesis only. V1 remains frozen and all previous evidence remains unchanged.

## 3. Multi-temporal fold design

A 40% chronological warm-up was followed by three contiguous 20% future regimes. Each fold trained only on preceding observations, used the immediately preceding block for validation, and evaluated on the next future block. The canonical V1 temporal split was not replaced.

## 4. Fold characteristics and 5. Uncertainty methodology

All three folds have 2,000 evaluation jobs and meaningful failure representation. The unchanged 9-member bootstrap/model-variability estimator used only fold training rows and decision-time features.

## 6. Cross-temporal uncertainty results and 7. Stability analysis

| Fold | AUROC | AUPRC | Mean uncertainty | High-error | Low-error | Difference | Candidate coverage | Candidate risk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fold_1 | 0.5902 | 0.2826 | 0.027350 | 0.2420 | 0.1220 | 0.1200 | 0.2520 | 0.1230 |
| fold_2 | 0.7166 | 0.5266 | 0.028420 | 0.3040 | 0.1560 | 0.1480 | 0.8075 | 0.3276 |
| fold_3 | 0.7717 | 0.5757 | 0.021002 | 0.2460 | 0.1020 | 0.1440 | 0.7755 | 0.4223 |

Positive high-low separation occurred on 3/3 folds; reversals occurred on 0/3 folds.

## 8. Selective policy, 9. Safety gate, and 10. Coverage gate

The single policy was fixed at the validation 80th percentile, with a minimum coverage of 0.50 and a requirement for lower candidate risk than V1 on every fold. These criteria were fixed before final evaluation.

## 11. Per-fold results and 12. Aggregate results

Mean, median, standard deviation, improved-fold count, degraded-fold count, and worst-fold delta are recorded in the C results artifact. No pooled result is used in place of per-fold evidence.

## 13. Worst-case temporal behavior

The worst fold is the fold with the maximum candidate-minus-V1 selective-risk delta recorded in `3_5_c_selective_policy/results.json`. Any reversal is preserved rather than averaged away.

## 14. Operational overhead

The estimator requires nine serialized V1-compatible fits per fold and therefore costs more than single-model V1 inference. This research cost was accepted for measurement only; production latency acceptance was not demonstrated.

## 15. Robustness classification

**NON-ACTIONABLE.** The classification distinguishes an uncertainty diagnostic from an actionable selective control. A signal may predict error while its abstention policy remains unsafe or operationally unsuitable.

## 16. Decision

**Decision: HOLD.** V1 remains the permanent control, and no Phase 3.5 component is automatically integrated.

## 17. Limitations and 18. V1 comparison

The three research folds are not a replacement for the canonical V1 random or temporal evaluation. The study uses one dataset and three contiguous research regimes. The historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.

## 19. Phase 3.4 versus Phase 3.5 comparison

Phase 3.4 established the uncertainty-error finding on a single temporal boundary and rejected one 80%-coverage policy. Phase 3.5 tests the same estimator across three pre-registered regimes and keeps the policy decision separate from the diagnostic result.

## 20. Next research question

If the signal is informative but the policy is rejected, the next question is whether a safety-constrained decision rule can use uncertainty jointly with calibrated risk without tuning on any future regime. Any such work requires a new experiment ID.
