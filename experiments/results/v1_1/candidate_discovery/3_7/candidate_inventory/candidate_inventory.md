# Phase 3.7 Candidate Inventory

## Purpose and boundary

This inventory translates the Phase 3.0–3.6.3 evidence into a small set of V1.1 research directions. It is a design artifact, not a production change and not evidence that any candidate has been accepted. The canonical V1 control remains frozen at commit `d977a32c2f20efa5f8e0d0349d40b270ecabeca2`. No candidate in this inventory modifies the V1 predictor, features, preprocessing, calibration, threshold, runtime, memory, diagnosis, recovery, or safety policy.

The inventory is based on the actual Phase 3 protocols, reports, and immutable result records listed in the references. The central conclusion is that the most defensible opportunity is likely **around** the frozen predictor: V1 already demonstrates useful temporal predictive behavior, while uncertainty interpretation and operational decision handling remain incomplete.

## Evidence synthesis

| Evidence area | Observed result | Design implication |
|---|---|---|
| Flexible prediction | Gradient Boosting and constrained Random Forest achieved attractive or comparable random performance but collapsed on temporal evaluation. | Do not pursue unrestricted capacity or random-split gains. |
| Feature filtering and contextual representations | Removing shifted clock features and contextual representations did not establish a temporal improvement. | Do not repeat feature fishing or simple representation substitution. |
| Calibration | Platt scaling worsened calibration and temporal quality relative to the preserved isotonic path. | Calibration replacement is not the primary direction. |
| Uncertainty | High uncertainty was associated with higher error across multiple chronological folds, but a fixed abstention rule was not operationally acceptable. | Retain uncertainty as an internal signal; redesign how it informs decisions. |
| Complexity ladder | Three limited interactions improved the canonical temporal split but lost on two of three authoritative future folds. | Do not integrate the interaction candidate; require multi-temporal validation. |
| Existing architecture | V1 already separates risk prediction, uncertainty, abstention, memory, diagnosis, recovery, and safety gates. | The research opportunity is an additive, explicit decision layer rather than replacement of the predictor. |
| Data boundary | Alibaba GPU2020 is an evaluation source with a fixed 14-feature numeric contract; historical skipped-node identities remain unrecoverable. | Every candidate needs explicit provenance, leakage, fold, and reproducibility contracts. |

## Candidate matrix

| Candidate | Core idea | V1 preserved? | Expected benefit | Main risk | Existing evidence | Novelty versus prior phases | Priority |
|---|---|---:|---|---|---|---|---:|
| **A — Structured uncertainty and evidence-request policy** | Use V1 risk plus uncertainty and a bounded contextual evidence check to choose normal prediction, warning, or request-more-evidence; do not use a standalone uncertainty-abstain threshold. | Yes | Better decision safety and useful coverage on difficult cases while retaining V1 risk. | Policy may become an arbitrary threshold or reduce coverage without improving selective risk. | Uncertainty separates error-prone cases across Phases 3.4–3.5, but naive abstention failed. | Redesigns uncertainty into a validation-locked evidence-request policy rather than repeating threshold abstention. | **1** |
| **B — Distribution-context monitor** | Add a separate train-only reference-distance/drift context signal that modifies scrutiny or escalation, without replacing V1 predictions or blindly abstaining. | Yes | Detect operation outside familiar regimes and expose reliability context. | Drift may be confounded with prevalence, be unstable across folds, or trigger excessive escalation. | Distribution shift is material; prior drift-aware abstention had unusable coverage. | Separates drift measurement from an automatic abstention rule and treats it as diagnostic context. | 3 |
| **C — Provenance-aware failure-memory context** | Retrieve only temporally available, provenance-tagged historical failure episodes and expose a bounded memory context to the decision layer without contaminating V1 training or prediction. | Yes | Add operational context V1 does not use: recurring failure patterns, prior outcomes, and evidence provenance. | Retrieval leakage, sparse history, stale memory, or false similarity may create unjustified confidence. | V1 contains a failure-memory path and prior memory lifecycle/retrieval evidence; broader predictive benefit is not established. | Tests memory as decision context with strict temporal eligibility, not as predictor retraining. | **2** |
| **D — Constrained model disagreement** | Compare V1 with one predeclared, stable, linear complementary model and use disagreement only as a difficulty signal. | Yes | Identify cases where V1's confidence may be unreliable without replacing V1. | Correlated errors may make disagreement uninformative; interaction-like instability may recur. | Complexity and temporal studies caution against flexible secondary models; direct operational disagreement evidence is absent. | Uses a deliberately constrained secondary model and preserves V1 as the decision anchor. | 4 |
| **E — Explicit structured decision policy** | Keep V1 risk unchanged but map risk, uncertainty, context, memory, and safety state to explicit predict/warn/escalate/diagnose actions. | Yes | Improve operational usefulness and safety without chasing AUROC. | Policy can encode unsupported assumptions and may be difficult to evaluate fairly. | V1 already has abstention, diagnosis, recovery, and safety stages, but their research coupling is not yet isolated as a candidate. | Treats decision quality and safety as primary outcomes, with prediction held constant. | 5 |

## Candidate-level research definitions

### Candidate A — Structured uncertainty and evidence-request policy

**Hypothesis:** A structured uncertainty signal can improve decision safety when combined with bounded additional contextual evidence rather than used as a standalone abstention threshold. The candidate is falsifiable: it must improve a predeclared decision-safety score or selective-risk profile without catastrophic future-fold degradation or unjustified coverage loss.

The research copy would consume frozen V1 calibrated risk, a frozen uncertainty estimator, and a fixed evidence-request action. The evidence request must be deterministic, bounded, and evaluated as an action with latency and coverage consequences. No future-fold results may alter the policy thresholds.

### Candidate B — Distribution-context monitor

**Hypothesis:** A separate distribution-context detector can identify reliability degradation without replacing V1's prediction and can improve escalation or diagnostic targeting. Drift is context, not an automatic abstention command. The detector must be fitted only on the training boundary and evaluated on the canonical temporal test plus all three Phase 3.5 folds.

### Candidate C — Provenance-aware failure-memory context

**Hypothesis:** Temporally eligible, provenance-tagged historical failure memory can improve current risk interpretation without modifying the frozen V1 predictor. Memory retrieval must be strictly prior-only, auditable, and allowed to return no result. The candidate must be evaluated against a no-memory decision-layer control and must report memory overhead and leakage checks.

### Candidate D — Constrained model disagreement

**Hypothesis:** Disagreement between V1 and a predeclared complementary but constrained linear model identifies failure-prone cases that V1 alone cannot distinguish. The candidate is not a replacement ensemble and cannot use RF, GB, or any unregistered flexible model.

### Candidate E — Explicit structured decision policy

**Hypothesis:** An explicit, validation-locked operational policy can improve safety or escalation quality without requiring a more complex predictor. The policy must declare action states, costs, gates, coverage requirements, and failure behavior before evaluation.

## Selection outcome

At most two candidates are eligible for future experimental screening under this discovery phase: **Candidate A** and **Candidate C**. They were selected because they address capabilities V1 does not presently provide, are supported by prior positive-but-incomplete evidence, preserve the V1 predictor, are meaningfully different from rejected interventions, and can be evaluated across the frozen future-fold boundary.

No candidate is accepted by this inventory. Phase 3.7 therefore ends with **V1.1 DIRECTION IDENTIFIED — NO CANDIDATE YET** until candidate-specific experiments are executed under the protocols in `candidate_protocols/`.

## References to repository evidence

1. `docs/PHASE3_BASELINE_AUDIT.md`
2. `experiments/results/v1_1/calibration_abstention/`
3. `experiments/results/v1_1/distribution_robust_uncertainty/`
4. `experiments/results/v1_1/temporal_robustness/`
5. `experiments/results/v1_1/v1_forensics/3_6_1_baseline_reconciliation/`
6. `experiments/results/v1_1/v1_forensics/3_6_2_matched_complexity/`
7. `experiments/results/v1_1/v1_forensics/3_6_3_multi_temporal_validation/`
8. `docs/FAILURE_MEMORY_LIFECYCLE_RECONCILIATION.md`
