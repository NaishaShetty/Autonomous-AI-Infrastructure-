# Experiment 3.5-B — Cross-Temporal Uncertainty Stability

The Phase 3.4-B bootstrap/model-variability estimator was reused without modification.

| Fold | AUROC | AUPRC | Mean uncertainty | High-error | Low-error | Difference | Ratio | Correlation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fold_1 | 0.5902 | 0.2826 | 0.027350 | 0.2420 | 0.1220 | 0.1200 | 1.98 | 0.1346 |
| fold_2 | 0.7166 | 0.5266 | 0.028420 | 0.3040 | 0.1560 | 0.1480 | 1.95 | 0.1340 |
| fold_3 | 0.7717 | 0.5757 | 0.021002 | 0.2460 | 0.1020 | 0.1440 | 2.41 | 0.0164 |

Positive high-low separation occurred on 3/3 folds, with 0/3 reversals. **Decision: HOLD.**

Historical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.
