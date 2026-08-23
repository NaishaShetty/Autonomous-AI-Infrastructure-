# Phase 3.8 — Candidate C Screening Report

**Decision: REJECT**

## Protocol

The candidate was evaluated independently against the frozen V1 control on the canonical random-stratified population, canonical temporal population, and Phase 3.5 Folds 1–3. The exact matched 14-feature numeric contract, training-only fitting, validation-only isotonic calibration, deterministic seed, and no-search rules were preserved. Candidate A and Candidate C were not combined.

## V1 versus candidate results

| Population | V1 AUROC | Candidate AUROC | Delta | V1 AUPRC | Candidate AUPRC | Delta |
|---|---:|---:|---:|---:|---:|---:|
| canonical_temporal | 0.830205 | 0.830291 | 0.000086 | 0.746390 | 0.746432 | 0.000042 |
| fold_1 | 0.569811 | 0.569722 | -0.000089 | 0.220051 | 0.220684 | 0.000633 |
| fold_2 | 0.726916 | 0.726715 | -0.000202 | 0.549252 | 0.548203 | -0.001049 |
| fold_3 | 0.806628 | 0.806733 | 0.000106 | 0.668480 | 0.668533 | 0.000053 |
| random_stratified | 0.720135 | 0.729888 | 0.009753 | 0.539681 | 0.565095 | 0.025414 |

## Multi-temporal summary

Mean AUROC delta: **0.001931**  
Median AUROC delta: **0.000086**  
Worst AUROC delta: **-0.000202**  
Best AUROC delta: **0.009753**  
Wins: **3**; losses: **2**; ties: **0**.

## Decision analysis

Candidate C produced small mixed deltas: three AUROC wins and two losses across the five populations, with a positive mean driven primarily by the random population. It does not establish robust temporal benefit.

The candidate is not production-ready and does not authorize V1.1 integration. The complete per-population records and leakage audit are stored beside this report.
