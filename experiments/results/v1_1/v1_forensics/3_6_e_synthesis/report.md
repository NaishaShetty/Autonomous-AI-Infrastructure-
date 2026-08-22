# PHASE 3.6 — V1 ROBUSTNESS & MECHANISM FORENSICS

## Executive summary

Phase 3.6 did not attempt to improve V1. It investigated why frozen V1 reaches 0.8302 temporal AUROC while Gradient Boosting and constrained Random Forest reach 0.3336 and 0.3204. The evidence supports a partial explanation: the temporal population and split differ materially from the random population, and constrained linear structure is consistently safer than the tested flexible alternatives. The evidence does not prove a single causal mechanism, genuine robustness beyond this dataset, or absence of all evaluation effects.

## Frozen control

| Metric | Random | Temporal |
|---|---:|---:|
| AUROC | 0.7201 | 0.8302 |
| AUPRC | 0.5397 | 0.7464 |
| Brier | 0.1444 | 0.2185 |
| ECE | 0.0215 | 0.2162 |

These are the frozen V1 control results. V1 was not modified.

## Mechanism synthesis

The strongest evidence is not that V1 is universally superior. It is that the random split tests interpolation under one population, while the temporal split changes prevalence and feature distributions; flexible models that exploit unstable relationships fail in that future regime. The feature and coefficient studies show no single-feature explanation. Duplicate/group findings are forensic cautions, not leakage claims.

| Hypothesis | Evidence | Conclusion |
|---|---|---|
| Linear inductive bias helps | V1 and simple linear copies retain temporal utility while RF/GB collapse | PARTIALLY SUPPORTED |
| Regularization helps | C ladder varies temporal behavior | PARTIALLY SUPPORTED |
| Future population is more separable | Univariate and prevalence/population statistics differ | UNRESOLVED |
| Few features dominate | Feature ablations/univariate results recorded | NOT SUPPORTED |
| Temporal proxy exists | Shifted timing/resource features are candidates | POTENTIALLY INFLUENTIAL |
| Group structure matters | Categorical composition differs | UNRESOLVED |
| Random split differs fundamentally | Different chronological/population composition | SUPPORTED |
| Evaluation artifact exists | Population effect and duplicate structure require caution | UNRESOLVED |
| V1 is genuinely robust | Stable temporal result and ladder contrast | PARTIALLY SUPPORTED |
| V1 is merely stable/mediocre | Random AUROC is moderate; alternatives weak OOD | PARTIALLY SUPPORTED |

## Falsification requirement

The apparent robustness would have been seriously challenged by a corrected temporal split causing V1 to collapse, pervasive coefficient instability, duplicate contamination explaining the result, a single dominant feature, or group-aware evaluation removing the effect. This phase found population and complexity effects, but no direct corrected-split collapse or confirmed leakage. The claims therefore remain bounded and partially resolved.

## Skeptical-researcher answer

A skeptical researcher should be shown the frozen random/temporal metrics, the population prevalence and feature-shift tables from A, all-feature ablations and coefficients from B, the predeclared regularization results from C, and the complete complexity ladder from D. Together they show that V1 is not simply winning by random AUROC: it preserves temporal ranking where the tested flexible models fail. They also show why the conclusion must remain limited: one official dataset, one canonical future boundary, changing prevalence, and unresolved group/duplicate effects.

## Final classification and decision

**Classification: partially genuine, dataset-dependent, and evaluation-dependent robustness; overall unresolved in causal mechanism. Decision: HOLD as a forensic conclusion.** V1 remains the sole production-eligible control. No feature removal, coefficient update, calibration change, threshold change, runtime change, or V1.1 integration is permitted from this phase.

## Next research question

Can the mechanism be tested on additional independently registered temporal datasets or group-aware boundaries while preserving the same frozen V1 control and without selecting favorable regimes?

Historical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.
