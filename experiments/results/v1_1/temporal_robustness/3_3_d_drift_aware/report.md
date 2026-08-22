# Phase 3.3-D — Drift-Aware Reliability + Abstention

## Research question

Can a reliability system detect when it operates outside the learned workload regime and use that information to make safer decisions while retaining useful coverage?

## Hypothesis and intervention

The hypothesis was that a decision-time standardized-distance drift signal could identify unfamiliar workloads and reduce unreliable accepted decisions. The only intervention was an additional abstention condition. The drift score is the standardized Euclidean distance from the training feature distribution, and its threshold is the 95th percentile of the validation drift scores. Future labels were not used to define the threshold.

## Data and protocol

The underlying risk model remained frozen V1: the same 14 features, preprocessing, logistic model, validation-only isotonic calibration, registered splits, threshold 0.1, and restored Alibaba GPU2020 data. The drift-aware layer was evaluated offline and did not rewrite the existing abstention engine or runtime.

## Results

Prediction metrics were identical to V1 by design because the intervention added only drift-aware abstention. On the random-stratified evaluation, drift-aware acceptance coverage was 0.0426 with selective risk 0.0625. On the temporal future evaluation, coverage was 0.0052 with selective risk 0.0000 and abstention rate 0.9948.

| Evaluation | V1 AUROC | Candidate AUROC | Candidate Brier | Candidate ECE | Drift-aware coverage | Drift-aware selective risk |
|---|---:|---:|---:|---:|---:|---:|
| Random-stratified | 0.7201 | 0.7201 | 0.1444 | 0.0215 | 0.0426 | 0.0625 |
| Temporal future | 0.8302 | 0.8302 | 0.2185 | 0.2162 | 0.0052 | 0.0000 |

The detector improves accepted-subset safety only by abstaining on nearly all future cases. It therefore fails the usefulness requirement even though its selective risk is low.

## Safety, leakage, and reproducibility

The threshold was selected from validation data only. The future test remained locked for final evaluation. The drift score uses only current decision-time feature values and training-derived mean/scale statistics. No future labels, recovery outcomes, or post-decision information were used. Serialization and reload reproduced identical predictions, no runtime training occurred, and the artifact set is immutable.

## Decision

# REJECT

Reject the drift-aware abstention layer for integration in its current form. It demonstrates a real safety-versus-coverage tradeoff but reduces temporal coverage to 0.52%, which is operationally unusable. A future drift-aware study may investigate a predeclared utility or coverage constraint, but that would be a new experiment and must not retune this locked future set.

## Limitations

Only one drift method and one validation percentile threshold were tested by design. The detector may be measuring the temporal boundary more than actionable epistemic uncertainty. No early-warning metric is reported because the established protocol does not support one. The historical seven skipped test-node identities remain unrecovered from preserved evidence.
