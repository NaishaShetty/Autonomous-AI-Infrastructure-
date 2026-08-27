# Phase 5.4 -- Limitations

Inherited from PHASE5_3_LIMITATIONS.md and PHASE5_2 limitations, restated
against the actual executed benchmark:

1. **failure_prediction** (4 tasks): NOT_EVALUABLE at record level. Every
   per-episode failure-class count in the canonical dataset (PROCESS_OOM=10,
   PROCESS_TIMEOUT_CPU=1, GENERIC_FAIL=13, NETWORK_FAILURE=11,
   resource_unavailable=0) is far below the 300-sample minimum. The
   STRONG_EVIDENCE / NOT_VALIDATED verdicts remain valid as
   AGGREGATE_REFERENCE_EVIDENCE, never recomputed as a record-level score.
2. **memory** (MEM-EVAL, ABL-MEMORY-ON-OFF): NOT_EVALUABLE. workloads=3104
   for episodes=3106 -- essentially no repeated-workload_id structure exists
   to measure adaptation.
3. **generalization** (2 tasks): NOT_EVALUABLE. All 3,106 records carry
   identity.environment_id == UNSPECIFIED_PRE_4_9; a single-environment
   dataset cannot support a generalization claim.
4. **abstention** (3 tasks): SIMULATED_POLICY_EVALUATION only. No ABSTAIN or
   RETRY decision episodes were ever realized in the ingested raw sources.
5. **diagnosis / recovery / end_to_end**: small samples (n=35 diagnosis-
   eligible, n=46 end-to-end, several failure classes n<30) -- per-class
   results below n=30 are UNDERPOWERED/DESCRIPTIVE_ONLY, not headline
   statistics. Recovery success rate is genuinely 0% on this dataset slice
   (0 of 35 failure episodes reach validation_status=RECOVERED) -- a real
   negative finding, not a benchmark defect.
6. **uncertainty**: the only FULLY_SUPPORTED track; UNC-SENT's near-chance
   AUROC (~0.66) is preserved and reported honestly, not merged into an
   aggregate "uncertainty works" claim.

## Disclosed specification tension (not silently resolved either way)

`PHASE5_3_DATASET_COVERAGE.json` asserts UNC-ARITH/UNC-SENT/UNC-QA's minimum
sample thresholds (500/300/300) are "met or exceeded" citing the FULL family
record counts (2,000/660/400). `PHASE5_3_SPLIT_POLICY.md` §4 separately
states: "A benchmark run that has fewer test-split instances than this
minimum for a given task MUST report that task's result as
UNDERPOWERED/DESCRIPTIVE ONLY." The actual `test`-split-only counts for these
three families are 310/113/49 -- all below their respective minimums. This
implementation follows the Split Policy's literal, benchmark-execution-level
rule (gating on test-split n, since final unfitted evaluation only ever uses
the test split) and therefore reports all three uncertainty tasks as
UNDERPOWERED at benchmark-run time, even though the underlying family-level
data volume is in fact ample. This is flagged here as a genuine tension
between two frozen Phase 5.3 documents -- it is not resolved by picking
whichever reading produces a better-looking capability matrix, and the raw
AUROC/AUPRC/Brier/ECE point estimates and their bootstrap CIs are reported in
full in PHASE5_4_BENCHMARK_RESULTS.json regardless of the UNDERPOWERED label,
so no information is lost, only the headline-statistic status is withheld
per the Split Policy's explicit instruction.
