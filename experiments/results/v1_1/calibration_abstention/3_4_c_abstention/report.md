# Experiment 3.4-C — Selective Prediction & Abstention

Thresholds were selected from validation uncertainty only, with an 80% coverage operating target declared before test evaluation.

| Split | V1 coverage | Candidate coverage | V1 selective risk | Candidate selective risk | Abstention rate |
|---|---:|---:|---:|---:|---:|
| random_stratified | 1.0000 | 0.8110 | 0.2588 | 0.2551 | 0.1890 |
| temporal_future | 1.0000 | 0.8860 | 0.4342 | 0.4639 | 0.1140 |

**Decision: REJECT.** Zero-risk/near-zero-coverage behavior would be operationally unusable and would be rejected.

Historical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.
