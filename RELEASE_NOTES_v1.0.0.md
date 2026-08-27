# Autonomous AI Infrastructure — v1.0.0 Release Notes

## What this project is

A research-grade, self-healing AI/ML infrastructure system: it observes
workloads and real AI/ML agent output, estimates calibrated confidence,
predicts failures where evidence supports it, diagnoses failure class,
plans and safety-gates a recovery action, executes it against a real
controlled runtime, independently validates the outcome, and learns from
persistent failure memory. Built by auditing, not trusting, two
predecessor prototypes (AI-Abstention-Engine, Introspective Failure Memory
Model) and evaluated through six major research phases with a discipline
of reporting negative and underpowered results at the same volume as
positive ones.

## Capabilities (status, not a checklist)

See `README.md`'s capability table for the full list. Headline
demonstrated capabilities: confidence-calibrated abstention on arithmetic
self-consistency and extractive QA (both `UNDERPOWERED` at benchmark
sample size but with real point estimates: AUROC 0.955 / 0.938), a
zero-tolerance safety gate (0/6 and 0/16 incorrectly authorized across two
independent adversarial matrices), and a demonstrated (controlled)
memory-driven change in recovery behavior under real repeated failures.

## Dataset and benchmark (published)

- Dataset (3,106 records, CC BY 4.0): <https://huggingface.co/datasets/naishashetty/autonomous-ai-infrastructure-dataset>
- Benchmark (16 tasks / 8 tracks / 33 metrics, MIT): <https://huggingface.co/datasets/naishashetty/autonomous-ai-infrastructure-benchmark>
- Final benchmark capability matrix: **0 VALIDATED / 6 PARTIALLY_VALIDATED
  / 3 UNDERPOWERED / 0 NOT_VALIDATED / 7 NOT_EVALUABLE.**

## Major findings — positive

- Safety gating: 0 incorrectly authorized actions across two independent
  adversarial matrices (6-case, 16-case).
- Memory measurably changes recovery decisions under real repeated
  process restarts (retry->retry->reconfigure->recovered vs. retry x6).
- `RECONFIGURE` vs. `RETRY` on `RESOURCE_UNAVAILABLE`: 100% vs. 0%
  recovery (n=40 each, Wilson 95% CIs non-overlapping).
- `resource_unavailable` failure prediction: `STRONG_EVIDENCE` from a real
  pre-flight-probe mechanism (aggregate-level).
- OOM failure-ranking generalizes across environments (AUROC
  0.989/0.983/0.935, dev/held-out/robustness).
- An 18-configuration pre-registered grid found no decision-policy
  fragility within its tested range.

## Major findings — negative / limited (reported with equal weight)

- Sentiment uncertainty has a real, unfixable-by-calibration
  discrimination ceiling (AUROC 0.439–0.659 depending on scale).
- 3 of 4 failure-prediction classes (`cpu`, pooled `oom`, `flaky`) are
  `NOT VALIDATED` — an always-fires false-alarm-rate near 1.0 at any
  calibrated threshold tried.
- All 4 `PRED-*` benchmark tasks are `NOT_EVALUABLE` at record level (no
  per-episode join key in the canonical dataset).
- Diagnosis accuracy (1.0) always carries a false-causal-attribution-rate
  of 1.0 — no independent causal ground truth exists.
- Recovery success is 0/35 on the benchmark dataset slice — a genuine
  negative finding.
- Ranking generalization (real) is explicitly distinguished from
  operating-point generalization (does not transfer) — never merged.
- Memory adaptation and multi-environment generalization are
  `NOT_EVALUABLE` at benchmark scale (1 repeated-workload group, 1
  environment).
- Two consecutive controlled recovery-policy-learning phases (4.3, 4.4)
  produced "hypothesis not supported" verdicts.
- No model repository was published — no single trained-model artifact in
  this project is independently validated at record level.

## Reproducibility

Every phase has its own deterministic regeneration script. The benchmark
runner executes twice per invocation and reports a determinism check; the
release packages were independently clean-room reproduced with
byte-identical results (modulo run metadata).

## Known limitations

- Recovery executes against this project's own local controlled subprocess
  runtime, not a production fleet.
- No production authentication, rate limiting, or deployment hardening on
  the demo API.
- See `README.md`'s "Limitations vs. future work" section for the full,
  current list.

## What's new in this release (Phase 6 — productization)

Repository cleanup, 8 architecture diagrams, a full README rewrite, a
Dockerfile, GitHub Actions CI/CD workflows (fast + full-suite), a real CLI
demo script (`scripts/demo_autonomy_loop.py`), a 27-section research
write-up (`docs/paper/`), and a final independent system audit. **No new
experiments, no metric/threshold/label changes** — every number in this
release is unchanged from the frozen Phase 4/5 evidence.

## License / citation

MIT (code and benchmark package) / CC BY 4.0 (dataset package). See
`LICENSE` and `CITATION.cff`.

## This release is local-only

This tag and its commit(s) are created locally in this repository. **They
have not been pushed to any remote, and no GitHub release has been
created.** Pushing requires the repository owner's own separate,
explicit, real-time action.
