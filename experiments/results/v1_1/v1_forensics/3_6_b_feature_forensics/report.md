# Experiment 3.6-B — V1 Feature Forensics

All 14 V1 numeric features were evaluated with univariate performance, distribution shift, canonical V1-compatible leave-one-feature-out ablation, missingness, and research-copy coefficient extraction.

| Feature | Random univariate AUROC | Temporal univariate AUROC | Random ablation AUROC | Temporal ablation AUROC | Temporal KS |
|---|---:|---:|---:|---:|---:|
| job_start_time | 0.6143 | 0.7794 | 0.7143 | 0.7816 | 0.7265 |
| n_tasks | 0.5464 | 0.5653 | 0.7143 | 0.7816 | 0.0479 |
| n_distinct_task_names | 0.5464 | 0.5653 | 0.7143 | 0.7816 | 0.0479 |
| sum_inst_num | 0.5578 | 0.5865 | 0.7031 | 0.7673 | 0.0659 |
| mean_plan_cpu | 0.6424 | 0.8134 | 0.7143 | 0.7818 | 0.2368 |
| max_plan_cpu | 0.6524 | 0.8154 | 0.7152 | 0.7833 | 0.2369 |
| mean_plan_mem | 0.5495 | 0.5181 | 0.7151 | 0.7817 | 0.0465 |
| max_plan_mem | 0.5419 | 0.5040 | 0.7144 | 0.7833 | 0.0419 |
| mean_plan_gpu | 0.5660 | 0.6699 | 0.7143 | 0.7817 | 0.1595 |
| max_plan_gpu | 0.5660 | 0.6699 | 0.7143 | 0.7817 | 0.1595 |
| n_distinct_gpu_types | 0.5104 | 0.5094 | 0.7130 | 0.7834 | 0.0062 |
| n_instances | 0.5561 | 0.5879 | 0.7080 | 0.7759 | 0.0772 |
| n_distinct_machines | 0.5485 | 0.5812 | 0.7143 | 0.7839 | 0.0715 |
| mean_instance_start_time | 0.6142 | 0.7793 | 0.7143 | 0.7815 | 0.7265 |

**Conclusion: PARTIALLY SUPPORTED / UNRESOLVED.** Feature contributions are distributed and several features shift, but observational coefficients and ablations do not establish causality. No feature was removed from V1. Potential regime proxies are recorded as candidates for future study, not leakage claims.

Historical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.
