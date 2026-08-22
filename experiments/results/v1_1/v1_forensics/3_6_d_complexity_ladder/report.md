# Experiment 3.6-D — Model Complexity / Inductive-Bias Ladder

The controlled ladder contains an appropriate prevalence baseline, frozen-V1-compatible logistic regression, a minimally less-regularized linear copy, the previously tested constrained Random Forest, and the previously tested Gradient Boosting model. Models are retained even when poor; no temporal result was used for selection.

| Level | Random AUROC | Temporal AUROC | Random AUPRC | Temporal AUPRC | Random Brier | Temporal Brier |
|---|---:|---:|---:|---:|---:|---:|
| 0_prevalence | 0.5000 | 0.5000 | 0.2588 | 0.4342 | 0.1918 | 0.3000 |
| 1_v1_logistic | 0.7348 | 0.7931 | 0.5373 | 0.6354 | 0.1635 | 0.2706 |
| 2_less_regularized_linear | 0.7348 | 0.7913 | 0.5349 | 0.6334 | 0.1635 | 0.2710 |
| 3_constrained_rf | 0.7256 | 0.3325 | 0.5898 | 0.4142 | 0.1453 | 0.3130 |
| 4_gradient_boosting_prior | 0.8070 | 0.2294 | 0.7155 | 0.4039 | 0.1225 | 0.3426 |

**Conclusion: PARTIALLY SUPPORTED.** Increasing flexibility is associated with a strong random-versus-temporal failure pattern in this controlled set. V1 appears unusually robust relative to these alternatives, while the possibility that alternatives are unusually poor OOD models remains open.

Historical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.
