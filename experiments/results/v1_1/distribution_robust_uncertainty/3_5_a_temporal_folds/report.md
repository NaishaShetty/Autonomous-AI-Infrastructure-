# Experiment 3.5-A — Multi-Temporal-Fold Construction & Audit

Three research-only chronological folds were pre-registered after a 40% historical warm-up. Each fold uses only preceding rows for training and validation, followed by a contiguous future evaluation block. The canonical V1 random and temporal splits were not modified.

| Fold | Train | Validation | Test | Test time range | Failure rate |
|---|---:|---:|---:|---|---:|
| fold_1 | 3200 | 800 | 2000 | 3563831–4789055 | 0.1725 |
| fold_2 | 4800 | 1200 | 2000 | 4789772–5667324 | 0.3175 |
| fold_3 | 6400 | 1600 | 2000 | 5668729–6449460 | 0.3785 |

**Decision: ACCEPT for use as a research protocol only.** These folds do not replace the frozen V1 evaluation boundary.

Historical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.
