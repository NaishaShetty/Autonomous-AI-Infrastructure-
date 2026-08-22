# Experiment 3.5-C — Pre-Registered Selective Decision Policy

The single policy was locked before evaluation: abstain above the fold-validation 80th percentile of unchanged bootstrap uncertainty. The predeclared coverage gate was 0.50 and the safety gate required lower accepted-case risk than V1 on every fold; no operating-point sweep was run.

| Fold | V1 coverage | Candidate coverage | V1 risk | Candidate risk | Risk delta |
|---|---:|---:|---:|---:|---:|
| fold_1 | 1.0000 | 0.2520 | 0.1725 | 0.1230 | -0.0495 |
| fold_2 | 1.0000 | 0.8075 | 0.3175 | 0.3276 | 0.0101 |
| fold_3 | 1.0000 | 0.7755 | 0.3785 | 0.4223 | 0.0438 |

Improved folds: 1/3. Mean risk delta: 0.0015; median: 0.0101; standard deviation: 0.0386; worst fold: 0.0438. **Decision: REJECT.**

Historical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.
