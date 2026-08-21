# Memory Composition and Planner Superiority Experiment

## Research question

Does the full FailureMemory + Diagnosis + RecoveryPlanner architecture provide decision-making capability beyond retrieving the nearest historical failure and copying its successful action?

## Motivation from B1 = B2

The prior counterfactual experiment found B1 nearest-neighbor success 0.80 and B2 full-planner success 0.80. The current protocol does not modify that result. It tests whether a deliberately compositional case, evidence ablation, negative transfer, diagnosis ablation, and planner ablation reveal additional value or a genuine limitation.

## Previous reporting ambiguities

The prior per-seed values aggregated every baseline, condition, distance band, and counterfactual row for a seed. They were not per-seed values for headline C0/C1/C3 conditions. This report uses condition-specific per-seed tables. The prior maximum-attempt value of 1 was intentional for action-selection isolation; this protocol declares the same one-attempt policy and makes no replanning claim.

## Simulator design and leakage controls

Three latent factors are declared: X resource pressure, Y latency congestion, and Z configuration drift. Training contains X-only, Y-only, Z-only, X+Y, and Y+Z experiences. The main evaluation case is the unseen X+Z combination. The runtime sees only the six observable features, generic failure evidence, and current safety constraints. It never receives factor IDs, optimal actions, action scores, or simulator probabilities. Training is fixed before evaluation and evaluation outcomes are never inserted before decision.

## Baselines

| Baseline | Definition |
|---|---|
| B0 | No memory; fixed retry |
| B1 | Single closest memory; copy only its action; same safety, execution, validation |
| B2 | Canonical FailureMemory + Diagnosis + RecoveryPlanner |
| B3 | Observable-feature action centroid |

## Discrimination check

The pre-evaluation discrimination check passed: `True`. It mechanically verifies that E1 alone, E3 alone, and the nearest individual experience are insufficient for the declared optimal action, while the full B2 path has the opportunity to select the optimal action. No hidden factor or optimal-action field enters the observation.

## Main results

| Condition | B0 success | B1 success | B2 success | B3 success | B2 optimal rate |
|---|---:|---:|---:|---:|---:|
| C0_no_memory | 0.2 | 0.2 | 0.2 | 0.2 | 0.0 |
| C1_nearest_only | 0.2 | 0.2 | 0.2 | 0.2 | 0.0 |
| C2_all_relevant | 0.2 | 0.2 | 0.0 | 0.2 | 1.0 |
| C3_full_with_irrelevant | 0.2 | 0.2 | 0.2 | 0.2 | 0.0 |
| C4_conflicting | 0.2 | 0.2 | 0.2 | 0.2 | 0.0 |
| C5_safety_conflict | 0.2 | 0.0 | 0.0 | 0.0 | 0.0 |
| C6_negative_outcome | 0.2 | 0.2 | 0.2 | 0.2 | 0.0 |

## Planner advantage

B2 minus B1 recovery-success advantage on C2 all-relevant is `-0.20`. The optimal-action advantage is `1.00`. A zero or negative result is preserved as a scientifically meaningful limitation rather than treated as a failure of the experiment.

## Evidence ablation

| Evidence | Success | Optimal rate | Uncertainty |
|---|---:|---:|---:|
| E1_only | 0.2 | 0.0 | 0.19999999999999996 |
| E3_only | 0.2 | 0.0 | 0.19999999999999996 |
| E1_plus_E3 | 0.0 | 1.0 | 0.19999999999999996 |
| none | 0.2 | 0.0 | 0.4 |

## Diagnosis and planner ablations

| Variant | Success | Optimal rate | Abstention |
|---|---:|---:|---:|
| diagnosis_direct | None | None | None |
| action_scoring | None | None | None |
| full | None | None | None |

## Ordering robustness

The deterministic ordering test produced decisions `['abstain', 'reconfigure', 'abstain', 'reconfigure']` and ordering invariance was `False`.

## Safety, negative transfer, and failure cases

Safety metrics separate proposed unsafe actions, rejected unsafe actions, and executed unsafe actions. The required invariant is zero executed unsafe actions. Negative-transfer results are reported without assuming that B2 must avoid a historical action; the simulator and planner limitations are part of the result.

## Per-seed results

The per-seed table is condition-specific; it does not aggregate unrelated baselines or distance bands.

| Seed | Condition | Episodes | Success | Optimal rate | Uncertainty | Abstention | Attempts |
|---:|---|---:|---:|---:|---:|---:|---:|
| 11 | C0_no_memory | 4 | 0.0 | 0.0 | 0.4 | 0.0 | 1.0 |
| 11 | C1_nearest_only | 4 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 11 | C2_all_relevant | 4 | 0.0 | 0.25 | 0.19999999999999996 | 0.25 | 0.75 |
| 11 | C3_full_with_irrelevant | 4 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 11 | C4_conflicting | 4 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 11 | C5_safety_conflict | 4 | 0.0 | 0.0 | 0.19999999999999996 | 0.75 | 0.25 |
| 11 | C6_negative_outcome | 4 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 11 | ablation_E1_only | 1 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 11 | ablation_E1_plus_E3 | 1 | 0.0 | 1.0 | 0.19999999999999996 | 1.0 | 0.0 |
| 11 | ablation_E3_only | 1 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 11 | ablation_action_scoring | 1 | 0.0 | 0.0 | None | 0.0 | 1.0 |
| 11 | ablation_diagnosis_direct | 1 | 0.0 | 0.0 | None | 0.0 | 1.0 |
| 11 | ablation_full | 1 | 0.0 | 1.0 | 0.19999999999999996 | 1.0 | 0.0 |
| 11 | ablation_none | 1 | 0.0 | 0.0 | 0.4 | 0.0 | 1.0 |
| 19 | C0_no_memory | 4 | 0.0 | 0.0 | 0.4 | 0.0 | 1.0 |
| 19 | C1_nearest_only | 4 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 19 | C2_all_relevant | 4 | 0.0 | 0.25 | 0.19999999999999996 | 0.25 | 0.75 |
| 19 | C3_full_with_irrelevant | 4 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 19 | C4_conflicting | 4 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 19 | C5_safety_conflict | 4 | 0.0 | 0.0 | 0.19999999999999996 | 0.75 | 0.25 |
| 19 | C6_negative_outcome | 4 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 19 | ablation_E1_only | 1 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 19 | ablation_E1_plus_E3 | 1 | 0.0 | 1.0 | 0.19999999999999996 | 1.0 | 0.0 |
| 19 | ablation_E3_only | 1 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 19 | ablation_action_scoring | 1 | 0.0 | 0.0 | None | 0.0 | 1.0 |
| 19 | ablation_diagnosis_direct | 1 | 0.0 | 0.0 | None | 0.0 | 1.0 |
| 19 | ablation_full | 1 | 0.0 | 1.0 | 0.19999999999999996 | 1.0 | 0.0 |
| 19 | ablation_none | 1 | 0.0 | 0.0 | 0.4 | 0.0 | 1.0 |
| 23 | C0_no_memory | 4 | 0.0 | 0.0 | 0.4 | 0.0 | 1.0 |
| 23 | C1_nearest_only | 4 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 23 | C2_all_relevant | 4 | 0.0 | 0.25 | 0.19999999999999996 | 0.25 | 0.75 |
| 23 | C3_full_with_irrelevant | 4 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 23 | C4_conflicting | 4 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 23 | C5_safety_conflict | 4 | 0.0 | 0.0 | 0.19999999999999996 | 0.75 | 0.25 |
| 23 | C6_negative_outcome | 4 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 23 | ablation_E1_only | 1 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 23 | ablation_E1_plus_E3 | 1 | 0.0 | 1.0 | 0.19999999999999996 | 1.0 | 0.0 |
| 23 | ablation_E3_only | 1 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 23 | ablation_action_scoring | 1 | 0.0 | 0.0 | None | 0.0 | 1.0 |
| 23 | ablation_diagnosis_direct | 1 | 0.0 | 0.0 | None | 0.0 | 1.0 |
| 23 | ablation_full | 1 | 0.0 | 1.0 | 0.19999999999999996 | 1.0 | 0.0 |
| 23 | ablation_none | 1 | 0.0 | 0.0 | 0.4 | 0.0 | 1.0 |
| 31 | C0_no_memory | 4 | 1.0 | 0.0 | 0.4 | 0.0 | 1.0 |
| 31 | C1_nearest_only | 4 | 1.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 31 | C2_all_relevant | 4 | 0.75 | 0.25 | 0.19999999999999996 | 0.25 | 0.75 |
| 31 | C3_full_with_irrelevant | 4 | 1.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 31 | C4_conflicting | 4 | 1.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 31 | C5_safety_conflict | 4 | 0.25 | 0.0 | 0.19999999999999996 | 0.75 | 0.25 |
| 31 | C6_negative_outcome | 4 | 1.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 31 | ablation_E1_only | 1 | 1.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 31 | ablation_E1_plus_E3 | 1 | 0.0 | 1.0 | 0.19999999999999996 | 1.0 | 0.0 |
| 31 | ablation_E3_only | 1 | 1.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 31 | ablation_action_scoring | 1 | 1.0 | 0.0 | None | 0.0 | 1.0 |
| 31 | ablation_diagnosis_direct | 1 | 1.0 | 0.0 | None | 0.0 | 1.0 |
| 31 | ablation_full | 1 | 0.0 | 1.0 | 0.19999999999999996 | 1.0 | 0.0 |
| 31 | ablation_none | 1 | 1.0 | 0.0 | 0.4 | 0.0 | 1.0 |
| 7 | C0_no_memory | 4 | 0.0 | 0.0 | 0.4 | 0.0 | 1.0 |
| 7 | C1_nearest_only | 4 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 7 | C2_all_relevant | 4 | 0.0 | 0.25 | 0.19999999999999996 | 0.25 | 0.75 |
| 7 | C3_full_with_irrelevant | 4 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 7 | C4_conflicting | 4 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 7 | C5_safety_conflict | 4 | 0.0 | 0.0 | 0.19999999999999996 | 0.75 | 0.25 |
| 7 | C6_negative_outcome | 4 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 7 | ablation_E1_only | 1 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 7 | ablation_E1_plus_E3 | 1 | 0.0 | 1.0 | 0.19999999999999996 | 1.0 | 0.0 |
| 7 | ablation_E3_only | 1 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 | 1.0 |
| 7 | ablation_action_scoring | 1 | 0.0 | 0.0 | None | 0.0 | 1.0 |
| 7 | ablation_diagnosis_direct | 1 | 0.0 | 0.0 | None | 0.0 | 1.0 |
| 7 | ablation_full | 1 | 0.0 | 1.0 | 0.19999999999999996 | 1.0 | 0.0 |
| 7 | ablation_none | 1 | 0.0 | 0.0 | 0.4 | 0.0 | 1.0 |

## Hypothesis conclusions

H1 memory versus no memory is read from C0 versus C1/C2. H2 multiple relevant experiences outperform one nearest experience only if C2 exceeds C1. H3 full diagnosis and planning outperform nearest-neighbor only if B2 exceeds B1. H4 ablation deltas show whether each experience is necessary. H5 is supported only when executed unsafe actions remain zero. H6 is supported when conflict increases uncertainty or abstention. The experiment does not engineer any target outcome.

## Limitations

This is a hand-designed, deterministic, multi-seed simulator study with one attempt per episode. It cannot establish production self-healing, real-world generalization, causal superiority beyond the declared worlds, or statistical significance. The current reliability model remains honestly unconfigured with risk 0.0. If B2 ties B1, the correct conclusion is that this architecture did not demonstrate measurable planner advantage under this protocol.

## Reproducibility

Protocol version: `memory-composition-v1`. Simulator version: `latent-composition-simulator-v1`. Base commit: `981725041ff301fea5d031a8c6b9e8b2375130f0`. Protocol SHA-256: `3c72ca46ac3237a07d9172a4e4b4ea26eddbdb900ed4e2cb7586f58ebe19be53`. Deterministic event IDs, fixed seeds, fixed training/evaluation sets, and explicit ordering permutations are used. Outputs are isolated under `experiments/results/memory_composition/`.
