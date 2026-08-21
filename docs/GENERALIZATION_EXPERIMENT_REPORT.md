# Generalization and Robustness Experiment Report

## Research question

Can validated prior failure and recovery experience help the autonomous runtime make better decisions when the future situation is **related to but not identical to** the training experience, when memories conflict, when actions have failed, and when safety uncertainty makes abstention preferable?

The experiment separates four effects:

| Effect | Question |
|---|---|
| Retrieval effect | Was the relevant historical experience retrieved? |
| Decision effect | Did evidence change diagnosis or action selection? |
| Performance effect | Did the resulting behavior improve validated outcome? |
| Safety effect | Did the runtime avoid unsafe action, including by abstaining? |

The previous learning-influence experiment remains frozen under `experiments/results/learning_influence/`. This report covers only the new experiment under `experiments/results/generalization/`.

## Protocol

The versioned protocol is [`configs/runtime_demo/generalization_protocol.json`](../configs/runtime_demo/generalization_protocol.json). It declares simulator version `simulator-v2`, five seeds (`7, 11, 19, 23, 31`), eight episodes per condition per seed, a fixed relevance threshold of `0.5`, four failure classes, stochastic action-outcome probabilities, fixed training experiences, shifted evaluation contexts, eight conditions, and a maximum of three recovery attempts.

There are **20 evaluation episodes per condition**: four failure classes across five seeds. Exact-match and related-match measurements use the same condition with two separate declared observation modes. The experiment is multi-seed and descriptive; it does not claim statistical significance because the episodes are controlled simulator trials rather than independent real-world incidents.

The training set includes both positive and negative evidence. For example, failure class A contains a successful `retry` and a failed `reconfigure`; class B contains a successful `reconfigure` and failed `retry`; class C contains a successful `rollback` and failed `reconfigure`; class D contains failures for all tested actions.

## Leakage controls

Training experiences are constructed before evaluation. Each condition and seed receives isolated memory and simulator state. Evaluation outcomes are not inserted into memory before the current decision, and they do not change thresholds, probabilities, diagnosis rules, or planning rules. The original learning-influence result is not rerun or overwritten. Real data and live telemetry are not used.

The manifest records the base repository commit `981725041ff301fea5d031a8c6b9e8b2375130f0`, protocol SHA256, seeds, simulator version, and the explicit no-leakage conditions.

## Condition results

| Condition | Relevant retrieval | Relevance precision | Relevance recall | Recovery success | Abstention | Mean attempts | Action distribution |
|---|---:|---:|---:|---:|---:|---:|---|
| C0 no memory | 0.00 | undefined | 0.00 | 0.65 | 0.00 | 1.85 | retry 10, rollback 7, reconfigure 3 |
| C1 related memory | 1.50 | 1.00 | 1.00 | 1.00 | 0.00 | 1.30 | retry 8, redeploy 8, reconfigure 4 |
| C2 irrelevant memory | 0.00 | undefined | 0.00 | 0.65 | 0.00 | 1.85 | retry 10, rollback 7, reconfigure 3 |
| C3 conflicting memory | 2.00 | 1.00 | 1.00 | 0.00 | **1.00** | 0.00 | abstain 20 |
| C4 negative experience | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 | 2.00 | rollback 4, reconfigure 8, redeploy 8; retry 0 |
| C5 safety conflict | 1.00 | 1.00 | 1.00 | 0.00 | **1.00** | 0.00 | abstain 20 |
| C6 multi-step | 0.00 | undefined | 0.00 | 0.65 | 0.00 | 1.85 | bounded fallback actions |
| C7 full closed loop | 1.50 | 1.00 | 1.00 | 1.00 | 0.00 | 1.30 | retry 8, redeploy 8, reconfigure 4 |

The precision metric is intentionally **undefined** when no relevant evidence is retrieved; it is not reported as a false perfect score. Recall is defined against the declared target failure class.

## Generalization result

| Match mode | Recovery success | Relevance recall |
|---|---:|---:|
| Exact memory | 1.00 | 1.00 |
| Related shifted memory | 1.00 | 1.00 |
| Related minus exact | 0.00 | 0.00 |

Under this protocol, the related contexts remained within the fixed relevance boundary and achieved the same simulator success rate as exact contexts. This is evidence of **generalization within the tested neighborhood**, not broad generalization. The evaluation distribution is deliberately small and synthetic.

## Negative experience result

In C4, relevant failed `retry` experience is retrieved, but `retry` is not selected in any of the 20 episodes. The runtime chooses bounded alternatives and records multi-step attempts. This supports the narrower claim that negative experience can reduce selection of the failed action in sufficiently similar exact contexts. It does not establish that the policy learns an optimal alternative across all contexts.

## Conflicting memory result

In C3, two equally relevant positive experiences recommend different actions. The planner abstains in **20/20** cases rather than selecting the latest memory. This is the intended uncertainty behavior for unresolved conflict.

## Safety result

In C5, a relevant experience supports `reconfigure`, but the current environment marks `reconfigure` unsafe. The runtime abstains in **20/20** cases and records zero unsafe actions. This directly tests **safety precedence over historical preference**.

## Multi-step recovery result

C6 uses stochastic outcomes and a maximum of three attempts. The controller records action history, validation history, execution outcome probabilities, random draws, seed, and simulator version. Across the 20 episodes, 50% required more than one attempt, the mean attempts was 1.85, and the maximum was bounded by three. Failed attempts trigger replanning with the failed action excluded rather than reusing the same plan indefinitely.

## Interpretation

The results support four distinct statements.

**The system can learn:** the runtime records positive and negative recovery outcomes as failure experiences and uses scored relevant evidence in diagnosis and planning.

**The system learns something useful:** in this controlled simulator, related-memory and full-loop conditions achieve 1.00 recovery success, while the no-memory and irrelevant-memory conditions achieve 0.65. This is a simulator-specific performance effect, not a production claim.

**The system generalizes:** the shifted related contexts in this protocol retain 1.00 relevance recall and 1.00 recovery success, matching the exact condition. This demonstrates local generalization within the declared feature neighborhood, not broad or real-world generalization.

**The system is safe:** conflicting evidence and unsafe historical preferences produce abstention, with zero unsafe actions in the tested conditions.

None of these statements means that the system works in real infrastructure. Recovery remains simulated, model risk remains unconfigured, and no live telemetry or production executor is present.

## Reliability model integration boundary

A separate audit found no protocol-valid persisted workload model and calibrator artifact. The repository’s existing model and calibrator are in-memory research objects without a versioned artifact boundary and independent leakage manifest. The default runtime therefore remains an honest neutral abstainer with risk 0.0. Details are in [`docs/RELIABILITY_MODEL_INTEGRATION_AUDIT.md`](RELIABILITY_MODEL_INTEGRATION_AUDIT.md) and [`configs/runtime_demo/model_config.json`](../configs/runtime_demo/model_config.json).

## Reproducibility

Run:

```bash
PYTHONPATH=. python3 scripts/run_generalization.py
pytest -q tests/runtime/test_generalization.py
```

The output is written only to `experiments/results/generalization/`. Repeating the same protocol with the same seed list reproduces the stochastic draws and aggregate results. The original `experiments/results/learning_influence/` files remain unchanged.

## Limitations and negative findings

The simulator has four hand-specified failure classes and four tested actions, while real infrastructure has far broader context and action spaces. The action policies remain interpretable heuristics. `redeploy` and other fallback actions are simulator-level labels, not real executors. The current experiment does not estimate confidence intervals, test causal effects on independent real-world incidents, or integrate a persisted reliability model. The C6 no-memory condition demonstrates bounded stochastic recovery rather than memory-driven recovery. These limitations are part of the result rather than reasons to inflate the claim.

## Final validation checkpoint

The final repository suite after this phase reports **453 passed, 17 skipped, 0 failed, and 1 warning** in 212.41 seconds. The remaining warning is the external Starlette/httpx deprecation. Compilation of `src/runtime`, `src/failure_memory`, `scripts`, and `tests/runtime` passed, and `git diff --check` passed.

The generalization protocol was run twice with the same seed list and produced byte-identical `generalization_results.json`, `summary.json`, and `manifest.json` outputs. The frozen learning-influence files were not modified. All new results remain isolated under `experiments/results/generalization/`.
