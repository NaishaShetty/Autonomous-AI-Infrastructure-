# Phase 5.5 — Gate A Final Audit (Summary)

This document summarizes the full Gate A audit. Supporting detail lives in
the sibling documents in this directory:
`SPECIFICATION_RECONCILIATION.md`, `TASK_BY_TASK_AUDIT.md`,
`METRIC_AUDIT.md`, `LEAKAGE_AUDIT.md`, `DETERMINISM_AUDIT.md`,
`REPOSITORY_HEALTH_AUDIT.md`, `GATE_A_DECISION.md`,
`gate_a_independent_rerun/` (fresh benchmark artifacts),
`FULL_TEST_SUITE_OUTPUT.txt`.

## What was done, methodologically

Every headline number in this audit was **independently recomputed from
raw evidence in this phase**, not copied from a prior report:

1. Re-ran the full Phase 5.4 benchmark from scratch
   (`scripts/run_phase5_4_benchmark.py --out-dir .../gate_a_independent_rerun`),
   on a different day, in a fresh Python process, comparing byte-for-byte
   against the frozen `20260826T150824Z` artifact. Identical in every
   field.
2. Loaded `all_records.jsonl` (3,106 records) directly with a standalone
   script and recomputed: recovery population (n=35) and outcome (34
   NOT_RECOVERED + 1 UNKNOWN, 0 RECOVERED), diagnosis population (n=35)
   and false-causal-attribution count (35/35), repeated workload_id count
   (1 group of 3, not 0), and distinct environment count (1).
3. Wrote and ran a 17-case pathological-input test battery directly
   against `src/benchmark/metrics.py` (single-class AUROC/AUPRC, empty
   inputs, all-abstain, all-answer, zero/100% recovery rates,
   always-fires operating-point check).
4. Read `src/benchmark/leakage.py`, `tasks.py`, and `ablations.py` in full
   and traced every one of the 12 leakage rules to its actual (or absent)
   call site, rather than trusting the pre-existing leakage-scan status
   field.
5. Ran the benchmark-specific test file
   (`tests/unit/test_phase54_benchmark.py`, 41 passed) and the **entire
   repository test suite** (`python -m pytest tests/ -q`) to completion as
   a blocking foreground process (880 passed, 8 failed, 1338.76s),
   confirming the known 8-failure signature is reproducible right now, not
   assumed from a stale report.
6. Checked `git diff --stat` / `git log` against every frozen-boundary
   path (`src/phase4/`, `src/runtime/`, `src/recovery/`,
   `src/failure_experience/`, `src/decision/`, `docs/archive/`, the
   frozen Phase 5.1/5.2/5.3 output directories, `src/phase5/`) to confirm
   this phase's own work introduced zero changes to any of them.

## Key finding: the Phase 5.3 sample-size contradiction

`PHASE5_3_DATASET_COVERAGE.json` (full-family counts) and
`PHASE5_3_SPLIT_POLICY.md` §4 (test-split counts) give different
"adequately powered" verdicts for the uncertainty track. Resolved in favor
of the stricter, test-split-count reading (§4's literal, execution-time
MUST rule), applied uniformly. This reproduces Phase 5.4's original
UNDERPOWERED classification for UNC-ARITH (n_test=310<500), UNC-SENT
(n=113<300), UNC-QA (n=49<300). See `SPECIFICATION_RECONCILIATION.md` for
full reasoning. The benchmark implementation itself was already built this
way (`registry.may_execute` gates on catalog `eligibility_status`;
per-task code separately gates COMPLETED-vs-UNDERPOWERED on the actual
test-split `n` against `minimum_sample_requirement`) — no code change was
required.

## Key finding: minor documentation-precision correction (memory track)

Prior prose describing MEM-EVAL's evidence base said dataset construction
has "no repeated-workload_id structure" / "0 repeated workload_ids." Direct
recomputation from the raw dataset in this phase found this is not quite
literally true: one workload_id (`"workload-recurring"`) legitimately
repeats across 3 records (episode_ids `phase4.4-recurring_failure_1/2/3`,
all within `calibration_validation`, no split-crossing). The benchmark
implementation's own `evaluate_memory_task` already reports this correctly
(`"1 workload_ids appear more than once"` — the code was never wrong), only
some surrounding prose overstated the absence of any repetition. This does
not change MEM-EVAL's classification: one 3-record group is still far below
any usable sample size for a memory-adaptation claim, so NOT_EVALUABLE
stands. Corrected in `TASK_BY_TASK_AUDIT.md`.

## Key finding: 8 dead leakage-rule-check functions

`src/benchmark/leakage.py` implements callables for all 12 leakage rules,
but 8 (L2-L7, L9, L11, L12) are never invoked from `tasks.py`/`ablations.py`.
Investigated each: every rule's corresponding unsafe code path currently
does not exist (the tasks that would trigger it are gated NOT_EVALUABLE
before scoring, or the running code was independently verified compliant
by direct reading — e.g. recovery's `executor_self_report` never feeds the
`recovery_success_rate` label). Judged not a present defect; documented as
a forward-looking gap for whoever wires up PRED-*/MEM-EVAL under a future
dataset revision. See `LEAKAGE_AUDIT.md`.

## No stop condition triggered

None of data leakage, dataset corruption, benchmark/data mismatch, hidden
test-set tuning, post-hoc threshold tuning, aggregate-to-record
fabrication, missing provenance, undisclosed nondeterminism, an
unresolvable specification contradiction, a release dependency on
internal-only files, evidence of historical-result modification, or any
touch to frozen Phase 4 evidence was found.

## Result

**GATE A: PASS.** See `GATE_A_DECISION.md` for the itemized checklist.
