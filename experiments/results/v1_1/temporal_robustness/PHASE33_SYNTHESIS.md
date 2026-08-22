# PHASE 3.3 — TEMPORAL ROBUSTNESS & DRIFT-AWARE RELIABILITY SYNTHESIS

**Decision:** Keep frozen V1 as the operating control. No Phase 3.3 intervention is accepted for automatic integration.

## Scope and control

Four experiments were run independently against the frozen V1 control using the same restored official Alibaba GPU2020 data, canonical preprocessing, registered splits, validation-only isotonic calibration, seed 42, and locked threshold. The prior Phase 3.1 Gradient Boosting rejection and Phase 3.2 feature-removal rejection were preserved and were not overwritten. No intervention was selected by comparing the four temporal test results; each protocol was predeclared and each decision was made independently.

> The historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.

## Results

| Experiment | Intervention | Random result | Temporal result | Safety / operations | Decision |
|---|---|---|---|---|---|
| 3.3-A | Validation strategy: random versus temporal model selection over predeclared logistic C values | Temporal-selected C=10 had AUROC 0.7194 on random test versus V1 0.7201 | AUROC 0.8323 versus V1 0.8302; AUPRC 0.7467 versus 0.7464; Brier 0.2173 versus 0.2185 | Slight temporal gains, but small effect and low coverage; no evidence of broad superiority | **HOLD** |
| 3.3-B | Six decision-time contextual workload-relative representations | AUROC 0.7237 versus V1 0.7201 | AUROC 0.8231 versus V1 0.8302; Brier 0.2215 versus 0.2185 | Coverage 0.0400 and selective risk 0.0800, but temporal ranking and calibration worsened | **REJECT** |
| 3.3-C | Shallow, regularized Random Forest | AUROC 0.7249 versus V1 0.7201 | AUROC 0.3204 versus V1 0.8302; Brier 0.3299 versus 0.2185 | Temporal failure repeats the nonlinear-capacity warning | **REJECT** |
| 3.3-D | Validation-only standardized-distance drift-aware abstention | Prediction metrics equal V1 by design | Prediction metrics equal V1; drift-aware coverage 0.0052 and selective risk 0.0000 | Nearly universal abstention; safety improves only by making the system operationally unusable | **REJECT** |

## Accepted, rejected, held, and interesting findings

No intervention is accepted. Experiment 3.3-A is held because temporal-validation selection produced a small, directionally favorable future result without demonstrating meaningful superiority or robustness across operational dimensions. Experiments 3.3-B, 3.3-C, and 3.3-D are rejected for the reasons recorded in their independent reports. The most important interesting finding is that the temporal-selection candidate and contextual representations both remain close to V1, while the constrained nonlinear model still collapses temporally; limited nonlinear capacity alone is not a sufficient robustness intervention. The drift-aware detector identifies a large safety/coverage tradeoff but, with the validation 95th-percentile threshold, abstains on almost all future cases.

## Final operating decision

V1 remains unchanged and remains the only production-eligible control. No interventions are combined. The held 3.3-A result requires a separately predeclared replication or statistical-power study before any integration consideration. Any future integration must be a new experiment evaluated against V1, not an automatic combination of independent candidates.

## Unresolved questions

The next research question is whether a predeclared distribution-aware training procedure can improve future calibration and decision coverage while retaining V1’s temporal ranking, without using the future test labels for model selection or threshold definition. A separate question is whether the 3.3-A small temporal gain persists across additional legitimate temporal windows; such a study must be locked before inspection of new future test outcomes.

## References

[1]: https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-/blob/main/docs/V1_REPRODUCIBILITY_BOUNDARY_FINAL_READINESS.md "V1 reproducibility boundary"

[2]: https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-/blob/main/experiments/results/v1_1/reliability_model/gradient_boosting_same_features_v1/report.md "Phase 3.1 rejected Gradient Boosting result"

[3]: https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-/blob/main/experiments/results/v1_1/temporal_generalization/PHASE32_TEMPORAL_GENERALIZATION_REPORT.md "Phase 3.2 temporal feature-stability result"

[4]: https://github.com/alibaba/clusterdata/tree/master/cluster-trace-gpu-v2020 "Official Alibaba GPU2020 source"
