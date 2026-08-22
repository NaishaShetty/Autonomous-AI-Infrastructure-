# Phase 3.3-B — Stable Contextual Feature Representations

## Research question

Can decision-time workload-relative representations retain useful information while becoming more stable across workload regimes?

## Hypothesis and intervention

The hypothesis was that contextual ratios derived from fields already available at the reliability decision could preserve signal better than simply removing shifted raw features. The single intervention added six ratios: mean/max CPU, mean/max GPU, mean/max memory, tasks per instance, instances per distinct machine, and distinct task names per task. No future normalization statistics, labels, outcomes, or post-decision fields were used.

## Data and protocol

The experiment used the restored official Alibaba GPU2020 data, canonical preprocessing, seed 42, registered random and temporal splits, the baseline logistic model family, validation-only isotonic calibration, and the locked threshold. The raw V1 feature set was retained and the six representations were added; no model, threshold, abstention, runtime, or safety-policy changes were made.

## Results

| Evaluation | V1 AUROC | Candidate AUROC | Candidate AUPRC | Candidate Brier | Candidate ECE |
|---|---:|---:|---:|---:|---:|
| Random-stratified | 0.7201 | 0.7237 | 0.5422 | 0.1452 | 0.0186 |
| Temporal future | 0.8302 | 0.8231 | 0.7389 | 0.2215 | 0.2203 |

The candidate produced a small random AUROC improvement but a temporal AUROC decline of 0.0071, temporal AUPRC decline of 0.0075, Brier deterioration of 0.0030, and ECE deterioration of 0.0041. Temporal coverage was 0.0400 with selective risk 0.0800.

## Leakage, safety, and reproducibility

All ratios are computed from same-job fields available at decision time. The intervention did not use future population statistics or temporal labels. No runtime or safety policy was changed. Model and calibrator reloads reproduced identical outputs, and the complete result is immutable.

## Decision

# REJECT

Reject the representation set for V1.1 integration. The small random improvement did not translate to future improvement, and probabilistic temporal quality worsened. The result does not show that contextual representations are useless generally; it shows that this predeclared six-ratio representation is insufficient under the current locked protocol.

## Limitations

Only one representation family was tested. The ratios may be noisy or redundant with the raw fields. Further representation research would require a new protocol and must preserve the locked temporal test boundary. The historical seven skipped test-node identities remain unrecovered from preserved evidence.
