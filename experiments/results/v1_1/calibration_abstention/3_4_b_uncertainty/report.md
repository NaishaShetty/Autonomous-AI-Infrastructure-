# Experiment 3.4-B — Uncertainty Estimation

The sole uncertainty method was bootstrap/model variability. Every ensemble member used only training rows and uncertainty was computed from decision-time features.

| Split | AUROC | AUPRC | Mean uncertainty | High-uncertainty error | Low-uncertainty error |
|---|---:|---:|---:|---:|---:|
| random_stratified | 0.7339 | 0.5350 | 0.014161 | 0.3630 | 0.1664 |
| temporal_future | 0.7942 | 0.6370 | 0.012628 | 0.6448 | 0.2242 |

**Decision: INTERESTING FINDING.** The signal is retained only as a research finding unless it demonstrates a useful downstream safety/coverage tradeoff.

Historical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.
