# System-Level Evaluation Report

## Verdict

**C — FUNCTIONAL BUT MAJOR CAPABILITIES REMAIN UNVALIDATED.** The repository genuinely executes a project-owned local workload lifecycle, persists/replays events, detects two controlled process-failure classes, and produces temporally bounded deterministic diagnoses. That is useful engineering evidence, but it is one controlled local environment with three fresh runs and no demonstrated real recovery, live prediction, production telemetry, or end-to-end autonomous recovery.

## Repository state

- HEAD: `680a5614e641ba778210525ef995a3a6b53c69d8`
- branch: `main`
- origin/main: `680a5614e641ba778210525ef995a3a6b53c69d8`
- working tree before evaluation: `M src/phase4/diagnosis.py
 M tests/unit/test_phase37_candidate_discovery.py
 M tests/unit/test_phase43_diagnosis.py
?? experiments/results/system_evaluation/
?? scripts/run_system_evaluation.py`

## Project goal

The intended system observes ML workloads, detects/predicts failures, reasons about uncertainty, diagnoses safely, performs authorized recovery, validates the outcome, and learns from incidents. The current evidence does not establish the complete loop.

## Architecture evaluated

`local subprocess → canonical event store → rule monitoring/detection → deterministic diagnosis → [simulator-only planner/safety/recovery/validation/memory]`

The bracketed stages exist in the canonical simulator runtime but were not represented by the fresh process-runtime runs and must not be read as production recovery evidence.

## Capability matrix

| Capability | Exists | Actually works | Tested | Quantitatively evaluated | Evidence | Limitation |
|---|---|---|---|---|---|---|
| Workload lifecycle and event persistence | Yes | Yes | Yes | Yes, N=3 | Fresh controlled subprocess runs + SQLite restart replay | One project-owned local environment |
| Resource telemetry | Partial | Partial | Yes | Partial | RSS/CPU samples where /proc is available | GPU, scheduler, queue unavailable; Windows may yield null process telemetry |
| Failure detection | Yes | Yes | Yes | Yes, N=3 / failures N=2 | Actual exit-7 and killed timeout | Rule-based classes only; engineering validation |
| Anomaly detection | Partial | Not established | Yes | No | RSS rule implementation | No legitimate anomalous-success workload demonstrated |
| Failure prediction / early warning | Partial | Not established in runtime | Partial | Historical artifact only | Runtime defaults to unconfigured assessor | No current injected artifact or predictive-horizon evaluation |
| Diagnosis | Yes | Yes for two controlled failure classes | Yes | Yes, N=2 | Fresh deterministic diagnosis records | Failure-class explanation only; causal ground truth unavailable |
| Uncertainty / abstention | Yes | Partial | Yes | Not evaluated in process runtime | Default runtime abstains when unconfigured | No paired live workload evaluation |
| Failure memory | Yes | Yes in controlled simulator | Yes | Historical simulator evidence | Existing versioned simulator studies | Not evaluated against current subprocess failures |
| Recovery execution | Simulated | Yes in simulator | Yes | Not evaluated here | SimulatedRecoveryExecutor | No real infrastructure mutation or recovery claim |
| Independent recovery validation | Simulated | Yes in simulator | Yes | Not evaluated here | SignalRecoveryValidator | Not independent external environment |
| Learning from incidents | Yes | Controlled simulator only | Yes | Historical simulator evidence | Runtime learning manager | No production continual-learning evidence |
| Reproducibility | Partial | Yes for this run | Yes | Yes | New protocol, raw log, hashes | No Docker or CI workflow |
| Engineering quality gates | Partial | Test suite dependent | Yes | Full suite recorded | pytest result in this run | No CI/CD configuration discovered |


## Fresh experiments executed

1. Normal local subprocess: completed successfully.
2. Local subprocess exiting nonzero: exit 7, detected and diagnosed.
3. Local subprocess exceeding a 0.25-second deadline: actually killed, detected and diagnosed.
4. SQLite restart/replay and monitoring replay comparison.
5. Full repository test suite: `C:\Users\naish\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q`; status `PASSED`, exit `0`, duration 526.922 seconds. Raw output: `raw/full_pytest.log`. A nonzero exit is reported as **FULL SUITE = INCOMPLETE**, never as a test pass.

## Master metrics

| System capability | Metric | Result | N | Environment N | Evidence level | Limitation |
|---|---|---:|---:|---:|---|---|
| Observability | restart replay equality | True | 26 events | 1 | controlled-runtime validated | one local host |
| Failure detection | precision / recall / F1 | 1.00 / 1.00 / 1.00 | 3 runs; 2 failures | 1 | engineering validation only | deterministic two-class protocol |
| Failure detection | TP / FP / FN / TN | 2 / 0 / 0 / 1 | 3 | 1 | engineering validation only | no confidence interval at this N |
| Detection latency | rule-event latency | 0.0 seconds | 2 failures | 1 | implementation property | failure event is emitted at detection boundary |
| Anomaly detection | anomalous-success rate | NOT EVALUABLE | N/A | 1 | unavailable | no legitimate anomalous-success case was produced |
| Diagnosis | failure-class explanation accuracy | 1.00 | 2 | 1 | engineering validation only | causal/root-cause accuracy not computed |
| Diagnosis | UNKNOWN root-cause rate | 1.00 | 2 | 1 | controlled-runtime validated | does not prove causal reasoning |
| Recovery | validated recovery success | NOT EVALUABLE | N/A | 1 | unavailable | fresh process runtime has no authorized executor |
| End-to-end autonomy | success rate | NOT EVALUABLE | N/A | 1 | unavailable | full real loop absent |
| Leakage | post-boundary evidence / pre-failure detections | 0 / 0 | 2 failure boundaries | 1 | bounded code-path check | does not cover all historical data pipelines |
| Overhead | with-vs-without monitoring | NOT EVALUABLE | N/A | 1 | unavailable | no equivalent uninstrumented runtime baseline |

All perfect values above are small-N engineering checks, not statistical or generalization evidence. `N_ENVIRONMENTS = 1`.

## Baselines and ablations

No same-task, live process-runtime baseline exists for monitoring off, memory off, abstention off, or recovery off. Creating one post hoc would require defining a new protocol, so `BASELINE_COMPARISON` and `ABLATION_RESULTS` are intentionally **NOT EVALUABLE** here. Existing simulator studies remain separate, controlled evidence and are not merged with these measurements.

## Robustness and leakage

Restart/replay equality was tested once after the three runs. The fresh boundary check found 0 post-boundary diagnosis evidence records, 0 pre-failure detections, and 0 prior-run records when diagnosis was deliberately passed the complete replay. The post-fix incident boundary is enforced inside `DiagnosisEngine`; no historical-memory input was enabled. Missing/duplicate/malformed-event robustness, external environments, and train/evaluation-memory isolation were not comprehensively re-evaluated here.

## Critical gaps

1. **Critical — real recovery and independent validation:** only simulated recovery exists; no authorized infrastructure action was evaluated.
2. **Critical — operational telemetry:** no GPU/scheduler/queue telemetry and only one local environment.
3. **High — live predictive reliability integration:** the runtime's default assessor is intentionally unconfigured, so no current workload prediction or calibration claim is supported.
4. **High — memory usefulness on real incidents:** memory-on versus memory-off has simulator evidence only, not a valid live controlled-runtime comparison.
5. **High — evidence scale:** three runs and two failures cannot support statistical reliability claims.

## Direct research answers

1. Runtime observation: **yes, in the controlled local subprocess runtime**.
2. Controlled failures: **yes, for nonzero exit and timeout (N=2)**.
3. Anomaly adds information: **not established**.
4. Diagnosis beyond classification: **partially**; structured evidence/uncertainty is produced, causal diagnosis is not established.
5. Uncertainty: **implemented; not freshly evaluated on process runtime**.
6. Abstention under insufficient live evidence: **not established by this run**.
7. Memory improvement: **not established for current subprocess runtime**.
8. Genuine autonomous recovery: **no**.
9. End-to-end autonomy: **not yet evaluable**.
10. Strong research metrics: **none from the fresh N=3 evaluation**.
11. Engineering-only metrics: **detection, replay, and deterministic diagnosis checks**.
12. Unevaluable now: **real recovery, deployment, CI/CD, Dockerized reproducibility, external-environment generalization**.
