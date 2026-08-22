# Experiment 3.6-C — Coefficient & Regularization Forensics

The exact research-copy V1 pipeline was inspected: logistic regression with canonical imputation, standardization, one-hot categorical encoding, default L2 penalty, `lbfgs`, `max_iter=2000`, random seed 42, and the existing calibration/runtime boundary. A small predeclared C set {0.1, 1, 10} was evaluated descriptively.

| C | Random AUROC | Temporal AUROC | Random Brier | Temporal Brier |
|---:|---:|---:|---:|---:|
| 0.1 | 0.7319 | 0.7939 | 0.1645 | 0.2705 |
| 1 | 0.7348 | 0.7931 | 0.1635 | 0.2706 |
| 10 | 0.7348 | 0.7913 | 0.1635 | 0.2710 |

**Conclusion: PARTIALLY SUPPORTED.** Constrained linear structure is consistent with the observed robustness, but coefficient variability and a small regularization ladder do not prove that regularization alone causes it. No C was selected or written back to V1.

Historical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.
