# Experiment 3.4-D — Combined Reliability Decision Layer

D was run only after A, B, and C. It used exactly one policy: the predeclared Platt candidate plus the validation-locked uncertainty threshold.

| Split | Calibrated AUROC | Calibrated Brier | Coverage | Selective risk |
|---|---:|---:|---:|---:|
| random_stratified | 0.7348 | 0.1609 | 0.8110 | 0.2551 |
| temporal_future | 0.7931 | 0.2837 | 0.8860 | 0.4639 |

**Decision: REJECT.** The layer is not integrated into V1; any future integration requires a separate consolidation experiment.

Historical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.
