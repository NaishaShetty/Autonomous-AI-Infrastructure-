# Phase 3.8 — Candidate A Screening Report

**Decision: HOLD**

## Protocol

The candidate was evaluated independently against the frozen V1 control on the canonical random-stratified population, canonical temporal population, and Phase 3.5 Folds 1–3. The exact matched 14-feature numeric contract, training-only fitting, validation-only isotonic calibration, deterministic seed, and no-search rules were preserved. Candidate A and Candidate C were not combined.

## V1 versus candidate results

| Population | V1 AUROC | Candidate AUROC | Delta | V1 AUPRC | Candidate AUPRC | Delta |
|---|---:|---:|---:|---:|---:|---:|
| canonical_temporal | 0.830205 | 0.830205 | 0.000000 | 0.746390 | 0.746390 | 0.000000 |
| fold_1 | 0.569811 | 0.569811 | 0.000000 | 0.220051 | 0.220051 | 0.000000 |
| fold_2 | 0.726916 | 0.726916 | 0.000000 | 0.549252 | 0.549252 | 0.000000 |
| fold_3 | 0.806628 | 0.806628 | 0.000000 | 0.668480 | 0.668480 | 0.000000 |
| random_stratified | 0.720135 | 0.720135 | 0.000000 | 0.539681 | 0.539681 | 0.000000 |

## Multi-temporal summary

Mean AUROC delta: **0.000000**  
Median AUROC delta: **0.000000**  
Worst AUROC delta: **0.000000**  
Best AUROC delta: **0.000000**  
Wins: **0**; losses: **0**; ties: **5**.

## Decision analysis

Candidate A did not change V1 ranking metrics; it only added a deterministic evidence-request/escalation action layer. Its request rate and coverage must be judged as an operational tradeoff.

The candidate is not production-ready and does not authorize V1.1 integration. The complete per-population records and leakage audit are stored beside this report.
