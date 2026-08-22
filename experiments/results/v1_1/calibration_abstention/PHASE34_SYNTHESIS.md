# PHASE 3.4 — CALIBRATION, UNCERTAINTY & ABSTENTION RESEARCH REPORT

## 1. Research question

Phase 3.4 asked whether the autonomous system could become safer and more operationally useful by improving calibration, uncertainty estimation, selective prediction, and abstention **around the frozen V1 predictor**, without changing V1 ranking, preprocessing, runtime, memory, diagnosis, recovery, or safety policy.

The governing objective was decision quality rather than AUROC maximization: avoid unsafe decisions, preserve trustworthy probabilities, retain useful coverage, preserve predictive utility, and minimize overhead.

## 2. Previous evidence from Phases 3.1–3.3

Phase 3.1 showed that Gradient Boosting improved random-stratified AUROC but collapsed on the temporal future population and was rejected. Phase 3.2 documented temporal shifts in clock-time and CPU-planning features; removing shifted clock-time features also reduced temporal performance and was rejected. Phase 3.3 tested temporal model selection, contextual representations, constrained nonlinear modeling, and naive drift-aware abstention. Temporal selection was held; the other three interventions were rejected. The frozen V1 control therefore remained the only production-eligible predictor.

## 3. V1 calibration/decision audit

The implementation audit inspected the actual code rather than relying on documentation. `src/reliability/risk_calibrator.py` implements an `IsotonicRiskCalibrator` whose calibration is fit on a disjoint validation set of predicted risks and labels. It clips calibrated risk to `[0, 1]`, derives calibrated confidence from the predicted label, and refuses inference before fitting. `src/reliability/calibrator.py` contains a separate confidence interface using a Gradient Boosting confidence model followed by isotonic calibration; it is not silently substituted for the Alibaba risk predictor.

V1 retains the registered model, feature definitions, splits, calibration boundary, threshold, and runtime. Phase 3.4 fitted no calibration, uncertainty, or abstention parameter on either locked test population.

## 4. 3.4-A methodology

Experiment 3.4-A audited V1 isotonic calibration and evaluated one predeclared alternative: Platt scaling. V1 and the candidate used identical V1-compatible risk scores; only the post-model probability mapping differed. The candidate calibrator was fitted on registered validation predictions and labels. Random-stratified and temporal future test results were then computed without changing V1.

## 5. 3.4-A results

| Split | V1 ranking AUROC | Candidate AUROC | V1 Brier | Candidate Brier | V1 ECE | Candidate ECE |
|---|---:|---:|---:|---:|---:|---:|
| Random-stratified | 0.7348 | 0.7348 | 0.1415 | 0.1609 | 0.0211 | 0.0783 |
| Temporal future | 0.7931 | 0.7931 | 0.2822 | 0.2837 | 0.2380 | 0.2439 |

The candidate preserved ranking mechanically but worsened probability quality on both populations. Temporal calibration remains materially worse than random calibration, indicating that the dominant issue is not solved by this calibration remapping.

**Decision: REJECT.** Platt scaling does not justify replacing V1’s current calibration behavior.

## 6. 3.4-B methodology

Experiment 3.4-B used one uncertainty method: nine bootstrap/model-variability fits of the V1-compatible logistic predictor. Each model was trained from resampled training rows. The uncertainty score was the standard deviation of the ensemble’s decision-time predicted failure probabilities. No future telemetry, future population statistics, labels, or post-decision outcomes were used to compute uncertainty at inference time.

## 7. 3.4-B results

| Split | Ensemble AUROC | Mean uncertainty | Error rate, high uncertainty | Error rate, low uncertainty |
|---|---:|---:|---:|---:|
| Random-stratified | 0.7339 | Measured in artifact | 0.3630 | 0.1664 |
| Temporal future | 0.7942 | Measured in artifact | 0.6448 | 0.2242 |

Higher bootstrap variability was associated with substantially higher classification error, especially on the temporal future population. This is evidence that the estimator contains decision-relevant information. It is not evidence that a particular abstention threshold is safe or operationally useful.

**Decision: INTERESTING FINDING.** Bootstrap variability is retained as a research component for downstream testing, but it is not accepted for integration by itself because the experiment did not establish an acceptable safety/coverage policy.

## 8. 3.4-C methodology

Experiment 3.4-C tested selective prediction using the strongest independently supported signal from 3.4-B. The abstention threshold was fixed before test evaluation as the 80th percentile of validation uncertainty, targeting approximately 80% coverage. The policy abstained when bootstrap uncertainty exceeded that threshold. No threshold was selected from temporal results.

## 9. 3.4-C results

| Split | V1 coverage | Candidate coverage | V1 selective risk | Candidate selective risk | Candidate abstention rate |
|---|---:|---:|---:|---:|---:|
| Random-stratified | 1.0000 | 0.8110 | 0.2588 | 0.2551 | 0.1890 |
| Temporal future | 1.0000 | 0.8860 | 0.4342 | 0.4639 | 0.1140 |

The policy produced a small random-population risk reduction but increased temporal accepted-case risk. It therefore failed the critical future-generalization boundary. Coverage remained meaningful, but the safety objective was not achieved.

**Decision: REJECT.** The uncertainty signal is promising, but this fixed policy is not a reliable selective decision rule.

## 10. 3.4-D methodology

Experiment 3.4-D was run only after A, B, and C. It used exactly one combined policy: the Platt candidate from 3.4-A followed by the validation-locked uncertainty abstention policy from 3.4-C. No combination sweep, future-test threshold search, or coverage optimization was performed.

## 11. 3.4-D results

| Split | Calibrated AUROC | Calibrated Brier | Coverage | Selective risk |
|---|---:|---:|---:|---:|
| Random-stratified | 0.7348 | 0.1609 | 0.8110 | 0.2551 |
| Temporal future | 0.7931 | 0.2837 | 0.8860 | 0.4639 |

**Decision: REJECT.** The combined layer did not improve the temporal safety/usefulness tradeoff. It remains an isolated negative result and was not integrated into V1.

## 12. Random versus temporal analysis

The random-stratified population made all interventions appear more favorable than the temporal future population. Calibration degradation was visible in both settings and was more severe temporally. Bootstrap uncertainty separated errors in both settings, but the resulting fixed abstention rule did not transfer safely: it increased temporal selective risk despite retaining high coverage. This confirms that decision-time uncertainty is not automatically equivalent to future-shift detection.

## 13. Safety analysis

No Phase 3.4 component changed the frozen V1 safety path or executed autonomous actions. The candidate abstention layer did not achieve a defensible reduction in accepted temporal failure risk. The results therefore do not support automatic integration. The prior Phase 3.3-D result remains a separate warning that near-zero risk obtained through near-total abstention is operationally unusable.

## 14. Coverage/risk analysis

The 3.4-C and 3.4-D policies retained 81.1% random coverage and 88.6% temporal coverage, but temporal selective risk was 0.4639 compared with 0.4342 for V1 without abstention. Meaningful coverage alone is insufficient; the accepted population must also become safer. Conversely, a future policy that drives coverage close to zero would fail the operational usefulness rule even if its selective risk were zero.

## 15. Reproducibility

Each experiment has an independent protocol, results, summary, report, manifest, artifact directory where applicable, and SHA-256 immutable evidence record. Fitted calibration and bootstrap components were serialized with `joblib`. The protocol records the official Alibaba GPU2020 identity, registered splits, feature set, random seed, training/validation selection boundary, and locked temporal test boundary. V1 and all prior Phase 3 evidence were treated as read-only.

## 16. Limitations

The temporal population remains a single registered future boundary. Bootstrap variability is computationally more expensive than a single V1 inference and was evaluated as a research layer rather than a runtime integration. The current uncertainty experiment reports error stratification but does not establish a universally safe threshold. The historical aggregate V1 result of **507 passed / 7 skipped / 0 failed** is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence. That archival limitation is separate from the Phase 3.4 findings.

## 17. Final synthesis

| Experiment | Intervention | Random result | Temporal result | Calibration | Safety | Coverage | Decision |
|---|---|---|---|---|---|---|---|
| 3.4-A | Platt calibration around V1 | Brier/ECE worsened | Brier/ECE slightly worsened; ranking unchanged | Not improved | No demonstrated gain | 100% | **REJECT** |
| 3.4-B | Bootstrap model-variability uncertainty | High uncertainty marked more errors | Stronger separation of errors | Not applicable | Decision relevance demonstrated | 100% diagnostic | **INTERESTING FINDING** |
| 3.4-C | Validation-locked uncertainty abstention | Small risk reduction at 81.1% coverage | Risk increased at 88.6% coverage | Uses V1 risk | Failed temporal safety gate | Meaningful but unsafe | **REJECT** |
| 3.4-D | Platt risk plus uncertainty abstention | No useful combined gain | Risk increased at 88.6% coverage | Candidate worsened | Failed combined gate | Meaningful but unsafe | **REJECT** |

What worked was the empirical finding that bootstrap disagreement contains information about prediction error. What failed was converting that signal into a temporally safe abstention policy, and Platt scaling did not improve calibration. What remains uncertain is whether a richer but still strictly decision-time uncertainty model can transfer across future regimes without collapsing coverage or increasing accepted-case risk.

## 18. Accepted V1.1 candidates

No component is accepted for integration into V1. The bootstrap uncertainty result is an **interesting research finding**, not an accepted production candidate.

## 19. Rejected candidates

Platt calibration, the validation-locked bootstrap abstention rule, and the single combined reliability decision layer are rejected for integration. V1 itself is not rejected; it remains the control.

## 20. Held candidates

No component is held as a direct integration candidate. The uncertainty signal may be revisited in a new experiment with a separately declared policy and stronger temporal validation design.

## 21. Next research question

Can a decision-time, distribution-robust uncertainty score be validated across multiple forward temporal folds, with thresholds fixed before each evaluation and a predeclared minimum coverage/safety gate, rather than relying on one future boundary?

## 22. Next phase

Proceed to a multi-temporal-fold uncertainty and selective-risk study only if additional valid temporal partitions can be registered without modifying V1 or using future labels for tuning. Any successful component must remain an additive V1.1 candidate and undergo a separate consolidation experiment before integration.

> **V1 remains the control. Phase 3.4 teaches that knowing when to trust a prediction requires stronger temporal evidence than a single calibration remap or one uncertainty threshold.**
