# Memory Composition v2: Order-Invariant Planning and Ablation Audit

## Research question

Can the current FailureMemory + Diagnosis + RecoveryPlanner pipeline make a stable decision from a historical evidence set independently of arbitrary memory ordering?

## Root cause found in v1

V1 iterated relevant memories in retrieval order and accumulated action scores with ordinary floating-point addition. It then selected the maximum using exact equality. Equally relevant opposing actions therefore produced tiny order-dependent score differences; the result was a first/ordering-sensitive winner rather than a mathematically resolved tie. V1 also rendered its ablation table from the wrong summary namespace: stored rows used `baseline` values `B2_diagnosis_direct`, `B2_action_scoring`, and `B2_full` with condition `ablation_C2_all_relevant`, while the report looked up condition-only keys. The stored values were present; the report lookup was wrong.

## Runtime fix

The planner now stores signed evidence contributions per action, computes each action score with `math.fsum` over contributions sorted only for numerical reproducibility, and treats scores within a declared numerical tolerance as an unresolved tie that abstains. Event IDs are not decision evidence; they only make floating-point summation reproducible. This is a real aggregation fix because the decision is based on the commutative sum and tolerance-aware equivalence, not on choosing the first event or arbitrarily sorting the memories.

## Abstention semantics

Recovery success remains unchanged: it means validated workload recovery. V2 separately reports optimal decision rate, safe decision rate, abstention correctness, unsafe proposal rate, and unsafe execution rate. Thus B2 may have recovery success 0 while optimal decision rate and abstention correctness are 1 and unsafe execution is 0.

## B1 versus B2

| Metric | B1 nearest-only | B2 full planner | B2 - B1 |
|---|---:|---:|---:|
| Recovery success | 0.2 | 0.0 | -0.2 |
| Optimal decision rate | 0.0 | 1.0 | 1.0 |
| Abstention correctness | 0.0 | 1.0 | 1.0 |
| Safe decision rate | 1.0 | 1.0 | 0.0 |
| Unsafe execution rate | 0.0 | 0.0 | 0.0 |

## Corrected ablation results

| Variant | Recovery success | Optimal decision | Abstention correctness | Unsafe execution | Uncertainty |
|---|---:|---:|---:|---:|---:|
| diagnosis_direct | 0.2 | 0.0 | 0.0 | 0.0 | None |
| action_scoring | 0.2 | 0.0 | 0.0 | 0.0 | None |
| full | 0.0 | 1.0 | 1.0 | 0.0 | 0.19999999999999996 |

The corrected values are generated from the stored ablation rows and no values are fabricated. Diagnosis contribution is represented by the difference between `diagnosis_direct` and `full`; planner contribution is represented by `nearest`/B1 versus `action_scoring` versus `full` in the records and summary.

## Ordering and tie handling

V1 before-fix decisions were `['abstain', 'reconfigure', 'abstain', 'reconfigure']` with invariance `False`. V2 enumerated all 2 permutations and produced decisions `['abstain', 'abstain']` with invariance `True` and stability `1.0`. The explicit equal-similarity tie test produced `['abstain', 'abstain']` with invariance `True`. The valid result for unresolved equal evidence is abstention.

## Safety and negative experience

Safety remains authoritative. Proposed unsafe actions, rejected unsafe actions, final decisions, and executed actions are separate fields; the executed unsafe-action count is zero in the safety condition. Negative evidence remains outcome-signed and is reported with confidence, uncertainty, action, abstention, recovery, and optimality rather than being counted as positive memory.

## Per-seed results

Per-seed values are condition-specific and correspond directly to one baseline/condition group; they do not aggregate unrelated conditions.

| Seed | Condition | Episodes | Recovery | Optimal decision | Abstention correctness | Uncertainty | Unsafe execution |
|---:|---|---:|---:|---:|---:|---:|---:|
| 7 | C0_no_memory | 4 | 0.0 | 0.0 | 0.0 | 0.4 | 0.0 |
| 7 | C1_nearest_only | 4 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 7 | C2_all_relevant | 7 | 0.0 | 0.2857142857142857 | 0.2857142857142857 | 0.19999999999999996 | 0.0 |
| 7 | C3_full_with_irrelevant | 4 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 7 | C4_conflicting | 4 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 7 | C5_safety_conflict | 4 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 7 | C6_negative_outcome | 4 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 7 | ablation_E1_only | 1 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 7 | ablation_E1_plus_E3 | 1 | 0.0 | 1.0 | 1.0 | 0.19999999999999996 | 0.0 |
| 7 | ablation_E3_only | 1 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 7 | ablation_none | 1 | 0.0 | 0.0 | 0.0 | 0.4 | 0.0 |
| 11 | C0_no_memory | 4 | 0.0 | 0.0 | 0.0 | 0.4 | 0.0 |
| 11 | C1_nearest_only | 4 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 11 | C2_all_relevant | 7 | 0.0 | 0.2857142857142857 | 0.2857142857142857 | 0.19999999999999996 | 0.0 |
| 11 | C3_full_with_irrelevant | 4 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 11 | C4_conflicting | 4 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 11 | C5_safety_conflict | 4 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 11 | C6_negative_outcome | 4 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 11 | ablation_E1_only | 1 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 11 | ablation_E1_plus_E3 | 1 | 0.0 | 1.0 | 1.0 | 0.19999999999999996 | 0.0 |
| 11 | ablation_E3_only | 1 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 11 | ablation_none | 1 | 0.0 | 0.0 | 0.0 | 0.4 | 0.0 |
| 19 | C0_no_memory | 4 | 0.0 | 0.0 | 0.0 | 0.4 | 0.0 |
| 19 | C1_nearest_only | 4 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 19 | C2_all_relevant | 7 | 0.0 | 0.2857142857142857 | 0.2857142857142857 | 0.19999999999999996 | 0.0 |
| 19 | C3_full_with_irrelevant | 4 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 19 | C4_conflicting | 4 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 19 | C5_safety_conflict | 4 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 19 | C6_negative_outcome | 4 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 19 | ablation_E1_only | 1 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 19 | ablation_E1_plus_E3 | 1 | 0.0 | 1.0 | 1.0 | 0.19999999999999996 | 0.0 |
| 19 | ablation_E3_only | 1 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 19 | ablation_none | 1 | 0.0 | 0.0 | 0.0 | 0.4 | 0.0 |
| 23 | C0_no_memory | 4 | 0.0 | 0.0 | 0.0 | 0.4 | 0.0 |
| 23 | C1_nearest_only | 4 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 23 | C2_all_relevant | 7 | 0.0 | 0.2857142857142857 | 0.2857142857142857 | 0.19999999999999996 | 0.0 |
| 23 | C3_full_with_irrelevant | 4 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 23 | C4_conflicting | 4 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 23 | C5_safety_conflict | 4 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 23 | C6_negative_outcome | 4 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 23 | ablation_E1_only | 1 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 23 | ablation_E1_plus_E3 | 1 | 0.0 | 1.0 | 1.0 | 0.19999999999999996 | 0.0 |
| 23 | ablation_E3_only | 1 | 0.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 23 | ablation_none | 1 | 0.0 | 0.0 | 0.0 | 0.4 | 0.0 |
| 31 | C0_no_memory | 4 | 1.0 | 0.0 | 0.0 | 0.4 | 0.0 |
| 31 | C1_nearest_only | 4 | 1.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 31 | C2_all_relevant | 7 | 0.7142857142857143 | 0.2857142857142857 | 0.2857142857142857 | 0.19999999999999996 | 0.0 |
| 31 | C3_full_with_irrelevant | 4 | 1.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 31 | C4_conflicting | 4 | 1.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 31 | C5_safety_conflict | 4 | 0.25 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 31 | C6_negative_outcome | 4 | 1.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 31 | ablation_E1_only | 1 | 1.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 31 | ablation_E1_plus_E3 | 1 | 0.0 | 1.0 | 1.0 | 0.19999999999999996 | 0.0 |
| 31 | ablation_E3_only | 1 | 1.0 | 0.0 | 0.0 | 0.19999999999999996 | 0.0 |
| 31 | ablation_none | 1 | 1.0 | 0.0 | 0.0 | 0.4 | 0.0 |

## Interpretation

The fixed planner is now order-invariant for this protocol. The result does not automatically establish planner superiority over nearest-neighbor transfer. It establishes that the v1 ordering defect was real, the safety/decision-quality distinction is measurable, and the ablations can be compared without a None-reporting artifact. Any remaining equality or negative recovery result is a limitation or a finding, not a reason to alter the simulator.

## Reproducibility and limitations

Protocol `memory-composition-v2`, simulator `latent-composition-simulator-v1`, protocol hash `56d47e28a1b817ab67ee33d9bceba026ad348b0d2521631b9325da46ada02cfe`, fixed seeds `[7, 11, 19, 23, 31]`, deterministic event IDs, fixed training/evaluation data, and explicit memory permutations were used. The study remains a small, hand-designed simulator with one attempt per episode. It does not establish production self-healing or statistical significance. Reliability-model integration remains out of scope and the default runtime remains honestly unconfigured.
