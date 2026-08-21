# Counterfactual Behavioral-Generalization Experiment

## Research question

Can the runtime produce useful validated behavior for an unseen manifestation of a known latent failure mechanism when the exact manifestation is absent from memory?

## Why the previous result was insufficient

The previous related-minus-exact result measured retrieval within a similarity neighborhood. It did not remove the exact supporting experience while preserving a separate latent mechanism, so it could not distinguish episodic transfer from behavioral generalization. This protocol hides the mechanism and evaluates A3/B3/C3 manifestations that are never inserted into memory.

## Latent mechanisms and observable manifestations

The simulator contains three latent mechanisms: resource pressure (A1 GPU queue, A2 memory bandwidth, unseen A3 thermal throttle), latency congestion (B1 queue latency, B2 timeout burst, unseen B3 retry storm), and configuration drift (C1 feature flag, C2 schema mismatch, unseen C3 rollout skew). The runtime sees only six observable telemetry-like features, generic failure evidence, and current safety constraints. It never receives the mechanism ID, optimal action, future outcome, or hidden action label.

## Baselines

| Baseline | Definition | Uses episodic FailureMemory |
|---|---|---|
| B0 | Fixed retry with no training data | No |
| B1 | Nearest declared training manifestation copies its action | No |
| B2 | Current FailureMemory + diagnosis + recovery planner | Yes |
| B3 | Observable action-centroid classifier | No |
## Hypotheses

H1: training memory improves validated behavior on exact training manifestations. H2: the improvement survives on unseen A3/B3/C3 manifestations if the runtime has learned a mechanism-level pattern rather than copied an episodic action. H3: nearest-neighbor transfer is weaker than the full planner. H4: negative transfer and safety conflict produce a safe alternative or abstention, never an executed unsafe action.

## Protocol and leakage controls

The protocol uses simulator `latent-mechanism-simulator-v1`, seeds `7, 11, 19, 23, 31`, fixed distance bands D0–D4, declared thresholds, fixed action probabilities, and a maximum of 1 attempts. The training set is fixed before evaluation. A3/B3/C3 never appear in training memory. Counterfactual pairs share the same seed, observation, simulator, action probabilities, safety constraints, and validation; only memory availability changes.

## Core results

| Comparison | Recovery success | Relevant retrieval | Diagnosis uncertainty | Interpretation |
|---|---:|---:|---:|---|
| B2 C0 no memory | 0.20 | 0.00 | 0.33 | no episodic evidence |
| B2 C1 training memory | 0.80 | 2.00 | 0.17 | A1+A2 / B1+B2 / C1+C2 available |
| B2 C3 exact removed | 0.80 | 1.67 | 0.13 | unseen manifestation absent from memory |

The counterfactual C1-minus-C0 success delta is `0.60`. The C3-minus-C1 delta is `0.00`. The clean C7 pair delta is `0.60` with memory availability as the only manipulated variable. A positive C1-minus-C0 value would indicate a memory effect; a positive C3-minus-C1 value would be evidence that the effect survives exact-memory removal. The experiment must be interpreted from the recorded values, not from retrieval alone.

## Negative transfer and safety

The negative-transfer manifestation B4 buffer release is not inserted into memory. Historical rollback succeeds for B1/B2, but rollback is ineffective for B4 and reconfigure is the simulator-optimal action. The report records whether each baseline transfers rollback, whether its first validation fails, and whether bounded replanning recovers. In the safety condition, rollback is marked unsafe in the current world; the expected invariant is zero unsafe actions and abstention or a safe alternative.

## Distance ladder

The result includes D0 exact, D1 near, D2 moderate unseen, D3 large shift, and D4 unrelated. Each band reports retrieval, similarity/distance, diagnosis confidence and uncertainty, action, recovery success, and abstention. The curve is descriptive; no threshold is tuned after observing evaluation results.

## Per-seed results

| Seed | Episodes | Mean success | Mean uncertainty | Mean attempts |
|---:|---:|---:|---:|---:|
| 11 | 93 | 0.37 | 0.2153846153846154 | 0.84 |
| 19 | 93 | 0.37 | 0.2153846153846154 | 0.84 |
| 23 | 93 | 0.00 | 0.2153846153846154 | 0.84 |
| 31 | 93 | 0.84 | 0.2153846153846154 | 0.84 |
| 7 | 93 | 0.37 | 0.2153846153846154 | 0.84 |

## Baseline comparison on training-memory condition

| Baseline | Success | Optimal-action rate | Abstention | Unsafe-action rate |
|---|---:|---:|---:|---:|
| B0_no_memory | 0.20 | 0.00 | 0.00 | 0.00 |
| B1_nearest_neighbor | 0.80 | 1.00 | 0.00 | 0.00 |
| B2_memory_planner | 0.80 | 1.00 | 0.00 | 0.00 |
| B3_observable_centroid | 0.80 | 1.00 | 0.00 | 0.00 |

## Interpretation rules

Retrieval is not called generalization. Action copying is not called reasoning. Simulator success is not called production recovery. If C3 does not improve over C0, the scientifically correct conclusion is failure to demonstrate genuine behavioral generalization. The current architecture may therefore demonstrate safe episodic transfer and local retrieval generalization without learning an abstract latent failure mechanism.

## Reproducibility and limitations

The exact base commit is `981725041ff301fea5d031a8c6b9e8b2375130f0`. Event IDs are deterministic hashes, Python's process-randomized hash is not used, and the experiment writes only to `experiments/results/counterfactual_generalization/`. The study is a controlled simulator evaluation with five seeds, not a statistically powered real-world study. Manifestations and probabilities are hand-designed, the observable baseline is simple, and the runtime model remains honestly unconfigured with risk 0.0. No production self-healing claim is made.
