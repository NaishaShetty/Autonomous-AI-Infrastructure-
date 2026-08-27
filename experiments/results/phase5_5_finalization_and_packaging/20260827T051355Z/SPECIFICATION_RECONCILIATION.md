# Phase 5.5 — Specification Reconciliation

## The contradiction

`PHASE5_3_DATASET_COVERAGE.json` classifies the uncertainty track as
`FULLY_SUPPORTED`, citing full-family record counts (2,000 arithmetic + 660
sentiment + 400 QA) against the minimum-sample thresholds (500/300/300) —
"met or exceeded."

`PHASE5_3_SPLIT_POLICY.md` §4 states, unconditionally: "A benchmark run
that has fewer test-split instances than this minimum for a given task
MUST report that task's result as `UNDERPOWERED/DESCRIPTIVE ONLY`, never as
a headline statistic."

The actual `test`-split-only counts for the three uncertainty families are
310 (arithmetic), 113 (sentiment), 49 (QA) — all below their respective
minimums (500/300/300). Phase 5.4's implementation used the test-split
count and classified all three as `UNDERPOWERED`.

## Resolution

**Decision: the test-split (Split Policy §4) reading is the operative,
scientifically defensible rule. It is applied uniformly to every task in
this phase.**

Justification:

1. **§4's text is unambiguous and specific.** It says "test-split
   instances," not "family" or "dataset" instances, and it is written as a
   binding MUST for "a benchmark run" — i.e. an execution-time gate, not a
   dataset-scoping heuristic. `PHASE5_3_DATASET_COVERAGE.json`'s own
   `_meta.method` field describes itself as reasoning from
   `dataset_coverage_status` cross-referenced against
   `dataset_statistics.json` — a *scoping* document written before any
   split-level execution occurred, not a benchmark-run gating
   determination.
2. **A benchmark's headline claim is only ever supported by what it holds
   out for final, unfitted evaluation.** `PHASE5_3_SPLIT_POLICY.md` §3
   itself restricts `test`-split use to "final, unfitted evaluation." A
   metric with a nominal 95% CI computed on n=49 test rows is not rendered
   adequately powered by the fact that a further 351 rows exist in
   `train`/`calibration_validation` — those rows were spent on fitting, not
   evaluation, and reusing them for the power claim would itself violate
   L6/L11.
3. **The stricter reading is the one that cannot be gamed.** Accepting the
   full-family reading would let any task look adequately powered by
   shrinking its test split and growing train/calibration — exactly the
   kind of post-hoc flattery this phase's stop conditions warn against.
   Preferring the strictest defensible reading when two frozen documents
   disagree is the correct default absent a tie-breaker in either document.
4. **This reproduces, not contradicts, Phase 5.4's own conclusion.**
   Phase 5.4 already implemented and reported the test-split reading
   (`PHASE5_4_LIMITATIONS.md`, "Disclosed specification tension" section)
   and flagged the tension explicitly rather than silently picking a side.
   This phase's independent audit (see `TASK_BY_TASK_AUDIT.md`,
   `METRIC_AUDIT.md`) reproduces the same UNDERPOWERED classification for
   UNC-ARITH/UNC-SENT/UNC-QA from a fresh, independent re-run
   (`gate_a_independent_rerun/PHASE5_4_BENCHMARK_RESULTS.json`), confirmed
   byte-identical to the frozen Phase 5.4 artifact. **This is a legitimate
   outcome, not a failure to find a new answer** — the audit's job was to
   determine which reading is correct, and the answer is the one already
   in force.

## Scope of the decision and what is NOT changed

- `PHASE5_3_DATASET_COVERAGE.json` and `PHASE5_3_SPLIT_POLICY.md`
  themselves are **not modified** (per this phase's absolute boundaries —
  Phase 5.3 specification files are frozen). The contradiction is resolved
  by choosing an interpretation for benchmark execution, not by editing
  either frozen document.
- The full-family record counts (2,000/660/400) are not lost: they remain
  visible in `PHASE5_3_DATASET_COVERAGE.json` as a dataset-scoping
  statement about the *existence* of enough raw material for a future
  larger test split, which is a true and useful fact distinct from "this
  benchmark run's test-split evaluation is adequately powered."
- The decision applies **uniformly** to every task re-evaluated in this
  phase: uncertainty (UNC-*), abstention (ABST-*, gated on the same
  test-split n), diagnosis (DIAG-EVAL, gated on n=35 selected records,
  which for that task's `all_matching` split definition is itself the
  effective evaluation population), recovery (REC-EVAL, n=35), and memory
  (MEM-EVAL, gated on repeated-workload_id count at any split). No task
  was evaluated against a more lenient standard than another.
- The raw point estimates, confidence intervals, and per-family breakdowns
  are reported in full in `PHASE5_4_BENCHMARK_RESULTS.json` / this phase's
  rerun regardless of the UNDERPOWERED label — only the headline-statistic
  status is withheld, per Split Policy §4's own instruction ("never as a
  headline statistic," not "never reported at all").
