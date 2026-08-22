# Phase 3.2 Temporal Generalization Evidence

This directory contains the Stage A temporal-generalization audit and the single Stage B intervention selected from that audit.

| Artifact | Purpose |
|---|---|
| `stage_a_audit.json` | Population comparison, feature distribution shift, feature-target drift, V1/GB behavior, and error stratification |
| `PHASE32_TEMPORAL_GENERALIZATION_REPORT.md` | Complete report and final decision |
| `stable_feature_filtering_time_features/` | Immutable Stage B feature-stability-filter intervention |

The Stage B intervention removed only `job_start_time` and `mean_instance_start_time` after the Stage A audit found both strongly shifted. It used the established Alibaba GPU2020 data, V1 feature construction and registered splits, validation-only calibration, seed 42, and the locked threshold. The result was **REJECTED** because temporal AUROC, AUPRC, Brier score, ECE, and operational coverage all worsened relative to V1.

The frozen V1 control, the rejected Phase 3.1 Gradient Boosting result, and the Phase 3.0 reconciliation evidence are not modified. The historical seven skipped test-node identities remain unrecovered from preserved evidence and must not be inferred from current test counts.
