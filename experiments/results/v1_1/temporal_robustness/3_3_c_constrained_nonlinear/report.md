# Phase 3.3-C — Constrained Nonlinear Reliability Model

## Research question

Can limited nonlinear capacity capture useful interactions without reproducing the severe temporal failure observed with unrestricted Gradient Boosting?

## Hypothesis and intervention

The hypothesis was that a shallow, strongly regularized Random Forest could capture limited interactions while preserving more temporal robustness than Phase 3.1 Gradient Boosting. The only intervention was the model formulation: 25 trees, maximum depth 2, minimum leaf size 50, max_features 0.7, and random seed 42.

## Data and protocol

The candidate used the same 14 V1 pre-outcome numeric features, restored Alibaba GPU2020 data, canonical preprocessing, registered random and temporal splits, validation-only isotonic calibration, locked threshold, and evaluation metrics. V1 remained the control; Phase 3.1 GB was only a contextual rejected comparator.

## Results

| Evaluation | V1 AUROC | Candidate AUROC | Candidate AUPRC | Candidate Brier | Candidate ECE |
|---|---:|---:|---:|---:|---:|
| Random-stratified | 0.7201 | 0.7249 | 0.5750 | 0.1409 | 0.0073 |
| Temporal future | 0.8302 | 0.3204 | 0.4083 | 0.3299 | 0.2858 |

The candidate’s random result improved slightly, but its temporal AUROC fell by 0.5098 relative to V1. Temporal coverage was 0.0180 and the accepted subset had selective risk 0.0000, which reflects near-total abstention rather than useful broad reliability. Phase 3.1 GB was similarly unacceptable temporally at AUROC 0.3336, so constrained capacity did not solve the observed failure.

## Safety and reproducibility

The candidate was evaluated offline only. No runtime, recovery, diagnosis, memory, or safety policy was modified. Model and calibrator artifacts reload with identical predictions, and the result is immutable with recorded protocol and hashes.

## Decision

# REJECT

Reject the constrained nonlinear model. The slight random improvement is outweighed by severe temporal degradation, worsening temporal calibration, and negligible operational coverage. The finding strengthens the evidence that additional nonlinear capacity, even constrained, is not justified without a stronger temporal-robustness mechanism.

## Limitations

Only one constrained forest configuration was tested by design. The result does not rule out every structured nonlinear model, but future candidates require separately locked hypotheses. The historical seven skipped test-node identities remain unrecovered from preserved evidence.
