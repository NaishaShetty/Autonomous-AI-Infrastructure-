# Phase 3.3-A — Temporal Validation / Model Selection

## Research question

Does selecting logistic-model regularization using temporally structured validation improve future-distribution performance compared with ordinary random validation?

## Hypothesis and intervention

The hypothesis was that temporal validation might select a configuration that generalizes better to future workloads. The only intervention was the validation/model-selection strategy. Three predeclared logistic regularization values, C ∈ {0.1, 1.0, 10.0}, were compared by validation AUROC. The temporal future test was not used for selection, calibration, or threshold definition.

## Data and protocol

The experiment used the restored official Alibaba GPU2020 data, the 14 V1 pre-outcome numeric features, registered random-stratified and temporal splits, seed 42, validation-only isotonic calibration, and the locked threshold of 0.1. V1 remains the permanent control. The raw artifact and machine-readable protocol are in this directory.

## Results

Both selection strategies selected C=10. Random-validation selection achieved random-test AUROC 0.7194 and temporal-future AUROC 0.8323. Temporal-validation selection produced the same C and therefore the same predictions: random-test AUROC 0.7194, AUPRC 0.5377, Brier 0.1443, ECE 0.0219; temporal AUROC 0.8323, AUPRC 0.7467, Brier 0.2173, and ECE 0.2124. V1 reference AUROC values are 0.7201 random and 0.8302 temporal.

| Evaluation | V1 AUROC | Selected candidate AUROC | Candidate AUPRC | Candidate Brier | Candidate ECE |
|---|---:|---:|---:|---:|---:|
| Random-stratified | 0.7201 | 0.7194 | 0.5377 | 0.1443 | 0.0219 |
| Temporal future | 0.8302 | 0.8323 | 0.7467 | 0.2173 | 0.2124 |

The temporal result is directionally favorable but small. Coverage was 0.0140 on the temporal future set with selective risk 0.0571, so the result does not establish broad operational superiority.

## Safety and reproducibility

No safety policy, runtime, recovery behavior, or abstention engine was changed. Both model and calibrator reloads reproduced identical predictions, and no runtime training was used. The result is independently immutable and includes protocol, manifest, results, summary, artifacts, and final hashes.

## Decision

# HOLD

Hold this result as an interesting, non-integrated candidate. It does not justify replacing V1 because both selectors chose the same C and the measured temporal gain is small with low useful coverage. A future study may replicate the strategy across additional predeclared temporal windows, but it must be a new protocol and must not tune on the current locked future test.

## Limitations

This is one registered future window and one small predeclared C set. It does not identify causality, and the historical seven skipped test-node identities remain unrecovered from preserved evidence.
