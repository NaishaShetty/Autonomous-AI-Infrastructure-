# Benchmark Card — Phase 5.3/5.4 Autonomous-Agent Capability Benchmark

benchmark_version: `phase5.3-benchmark-v1.0.0` | dataset_version:
`phase5.2-dataset-v1.0.0` | implementation_version:
`phase5.4-implementation-v1.0.0`

## What it measures

16 tasks across 8 tracks, each scoring a specific, narrow capability
claim against the Phase 5.2 canonical dataset (3,106 records: 3,060
agent-task episodes across 3 task families, 46 controlled-runtime failure/
recovery episodes). No single overall score is computed or should be
computed — see the capability matrix below.

## Capability matrix

| Track | Task | Status | Primary evidence | Sample size (test split unless noted) | Limitation |
|---|---|---|---|---|---|
| uncertainty | UNC-ARITH | UNDERPOWERED | AUROC 0.955, ECE raw 0.197→calibrated 0.083 | n=310 (min 500) | Below minimum-sample gate; point estimates are real, not a headline claim |
| uncertainty | UNC-SENT | UNDERPOWERED | AUROC 0.439 (near-chance) | n=113 (min 300) | Genuine discrimination ceiling, disclosed not "fixed" |
| uncertainty | UNC-QA | UNDERPOWERED | AUROC 0.938 | n=49 (min 300) | Below minimum-sample gate |
| abstention | ABST-ARITH | PARTIALLY_VALIDATED | Selective risk 0.0 at calibrated threshold | n=310 | SIMULATED_POLICY_EVALUATION — no realized ABSTAIN/RETRY episodes exist |
| abstention | ABST-SENT | PARTIALLY_VALIDATED | Selective risk 0.3125 | n=113 | same |
| abstention | ABST-QA | PARTIALLY_VALIDATED | Selective risk 0.03125 | n=49 | same |
| failure_prediction | PRED-RESOURCE-UNAVAILABLE | NOT_EVALUABLE | n/a (0 per-episode records with this label) | n=0 | STRONG_EVIDENCE verdict is aggregate-reference only (Phase 4) |
| failure_prediction | PRED-OOM | NOT_EVALUABLE | n/a | n=10 (min 300) | Aggregate AUROC 0.780 but always-fires (FAR=1.0); RANKING_SIGNAL, not a usable operating point |
| failure_prediction | PRED-CPU | NOT_EVALUABLE | n/a | n=1 (min 300) | Aggregate NOT_VALIDATED (always-fires) |
| failure_prediction | PRED-FLAKY | NOT_EVALUABLE | n/a | n=24 (min 300) | Aggregate NOT_VALIDATED |
| diagnosis | DIAG-EVAL | PARTIALLY_VALIDATED | Failure-class accuracy 1.0 (35/35) | n=35 | False-causal-attribution-rate = 1.0: every diagnosis names a cause while no independent causal ground truth exists in this dataset — accuracy is class-matching only, never a causal claim |
| recovery | REC-EVAL | PARTIALLY_VALIDATED | Recovery success rate 0.0 (0/35) | n=35 | Genuine negative finding on this dataset slice, not a benchmark defect |
| memory | MEM-EVAL | NOT_EVALUABLE | n/a | 1 repeated-workload group (3 records) | Far below any usable scale for a memory-adaptation claim |
| generalization | GEN-RANKING-CONTRACT | NOT_EVALUABLE | n/a | 1 environment in dataset | Phase 4's 0.989/0.983/0.935 OOM ranking numbers preserved as aggregate-reference only |
| generalization | GEN-OPERATING-POINT-CONTRACT | NOT_EVALUABLE | n/a | 1 environment | Phase 4's operating-point transfer failure preserved as aggregate-reference only |
| end_to_end | E2E-EVAL | PARTIALLY_VALIDATED | E2E recovery rate 0.0 | n=46 | Full 8-stage loop confined to controlled_runtime records only |

**Read this table left to right, never collapse it to one number.** A
task's "primary evidence" number is only meaningful together with its
status and limitation column.

## Baselines and ablations

Every scored track compares against explicit baselines, including
adversarial ones designed so a trivial policy cannot appear to win:
`BASE-ALWAYS-ABSTAIN` (flagged `ALWAYS_ABSTAIN_NOT_SUCCESSFUL`),
`BASE-ALWAYS-ANSWER`, `BASE-GENERIC-POLICY` (one pooled threshold across
families), `BASE-CALIBRATED-MECHANISM-AWARE` (per-family calibrated
threshold), `CTRL-RANDOM-POLICY`, `BASE-RANDOM`. 5 ablations are defined;
2 (`ABL-UNCERTAINTY-MECHANISM`, `ABL-CALIBRATED-VS-GENERIC-POLICY`) are
computable from this dataset; 3 (`ABL-MEMORY-ON-OFF`,
`ABL-PREDICTOR-ON-OFF`, `ABL-RETRY-ON-OFF`) are `AGGREGATE_REFERENCE_EVIDENCE`
only (not re-derivable at record level from the current dataset).

## Metrics

AUROC/AUPRC/Brier/ECE/risk-coverage (with bootstrap CIs, seeded), Wilson
CIs for binomial rates. Single-class AUROC/AUPRC returns
`NOT_DEFINED_SINGLE_CLASS` (never a fabricated 0.5). Zero-coverage
selective risk returns `UNDEFINED_ZERO_COVERAGE` (never 0). An
always-fires predictor (false-alarm-rate ≥ 0.99) is flagged
`RANKING_SIGNAL_BUT_OPERATIONALLY_INVALID` regardless of its AUROC. See
`PHASE5_3_METRIC_CATALOG.json` and `src/benchmark/metrics.py`.

## Leakage protection

12 leakage rules (L1–L12; see
`experiments/results/phase5_benchmark_specification/20260826T055915Z/PHASE5_3_LEAKAGE_POLICY.md`).
L1, L8, L10 are mechanically enforced at every run; L2–L7, L9, L11, L12
guard code paths not currently reachable (their corresponding tasks are
gated `NOT_EVALUABLE`) but are verified compliant by construction and
retained for when a future dataset revision makes those tasks evaluable.

## Determinism

The runner executes the full benchmark twice per invocation and reports
`determinism_check`; independently re-verified across separate process
invocations on different days with byte-identical results.

## What this benchmark cannot tell you

- Whether the underlying agent system is production-ready (it is a
  research evaluation harness, not a certification).
- Anything about environments other than the single one represented in
  this dataset.
- Anything about repeated-incident / memory-adaptation behavior at scale
  (1 group of 3 records exists; that is the entirety of the evidence).
- A causally-verified diagnosis (only failure-class matching is scored;
  causal ground truth does not exist in this dataset).
