# Experiment 3.4-A — Calibration Audit & Improvement

V1 calibration implementation was audited: frozen V1 uses an isotonic risk calibrator fit on validation risk values, with clipped [0,1] output and the existing threshold/runtime untouched. The candidate was one predeclared Platt scaling layer fit on validation predictions only.

| Split | V1 AUROC | Candidate AUROC | V1 Brier | Candidate Brier | V1 ECE | Candidate ECE |
|---|---:|---:|---:|---:|---:|---:|
| random_stratified | 0.7348 | 0.7348 | 0.1415 | 0.1609 | 0.0211 | 0.0783 |
| temporal_future | 0.7931 | 0.7931 | 0.2822 | 0.2837 | 0.2380 | 0.2439 |

**Decision: REJECT.** Calibration must be judged jointly with temporal behavior, ranking, and downstream selectivity; no V1 behavior was changed.

Historical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.
