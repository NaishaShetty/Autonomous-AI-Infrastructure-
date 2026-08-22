# Experiment 3.6-A — Data & Evaluation Forensics

This study compares the canonical random-stratified and temporal future populations without changing either split.

| Population | Test jobs | Failure rate | Training jobs | Training failure rate |
|---|---:|---:|---:|---:|
| random | 1503 | 0.2588 | 6999 | 0.2595 |
| temporal | 2499 | 0.4342 | 6177 | 0.2011 |

Feature-level SMD, KS, and Wasserstein statistics, univariate AUROC/AUPRC, missingness, duplicates, and categorical composition are recorded in `results.json`. Duplicate presence is forensic evidence only and is not called leakage.

**Conclusion: PARTIALLY EXPLAINED.** Population prevalence and feature-distribution effects are established; the data alone does not prove that future labels are intrinsically easier or that V1 robustness is an artifact.

Historical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.
