# Master Remediation Report — Post-P5 Remediation Phase

Run directory: `experiments/results/post_p5_remediation/20260825T064402Z/`
Scope: systematic, honest resolution (or explicit characterization) of
every weakness named in the Priorities 1-5 gap review, executed in the
required order (engineering → observability → predictability →
generalization → uncertainty/decision → memory → full re-evaluation).

This document is the entry point. It summarizes what each step found and
points to the full report for detail. It does not repeat every number —
see the linked reports for those.

## Reading order

1. `reports/ENGINEERING_FIXES_REPORT.md` — Step 1
2. `audits/P3_PREDICTIVE_OBSERVABILITY_AUDIT.md` — Step 2
3. `protocol/P3_STEP3_PROTOCOL.md` + `reports/P3_PREDICTABILITY_REMEDIATION_REPORT.md` — Step 3
4. `protocol/P4_STEP4_PROTOCOL.md` + `reports/P4_GENERALIZATION_REMEDIATION_REPORT.md` — Step 4
5. `protocol/P1_STEP5_SENTIMENT_UNCERTAINTY_PROTOCOL.md` + `reports/P1_P2_AGENT_REMEDIATION_REPORT.md` — Step 5
6. `protocol/P5_STEP6_MEMORY_PROTOCOL.md` + `reports/MEMORY_REMEDIATION_REPORT.md` — Step 6
7. `reports/ADDENDUM_CPU_TIMING_DEFECT.md` and
   `reports/ADDENDUM_TIMESTAMP_TIE_DETERMINISM_DEFECT.md` — two real
   defects found during Step 7 final verification, not during any earlier
   step (both engineering, not research-methodology, defects)
8. `audits/FINAL_SYSTEM_CHECK.md` — Step 7's mandatory checklist
9. `FINAL_POST_REMEDIATION_EVALUATION.md` — the final weakness-by-weakness
   table and per-capability grades (this run directory's top-level file)
10. `reports/WEAKNESS_REGISTER.md` — the complete, chronologically-updated
    running log every step wrote to as it went

## What this phase actually found, in one paragraph per priority

**P1 (uncertainty):** Sentiment's weak error-detection AUROC (~0.66 vs.
~0.95/~0.93 for arithmetic/QA) was investigated with 4 candidate
uncertainty estimators under a strict calibration/test split. All 4
produced mathematically identical AUROC — a real, explained negative
result (binary-classification confidence transforms are rank-equivalent),
not a bug. Temperature scaling did genuinely fix calibration (ECE
0.089→0.023) while leaving discrimination unchanged, an honest partial
win. RETRY availability and the mechanism-aware interface were both
verified already correct.

**P2 (decision):** Verified RETRY is correctly scoped only to the
arithmetic agent. Held-out-sample-size expansion and retry-economics
sensitivity sweeps were not performed this phase (logged as follow-ups).

**P3 (prediction) — highest priority:** A formal observability audit
(Step 2) found and fixed a real engineering defect — RSS telemetry was
silently broken (`None`) on Windows, zeroing out the OOM family's only
intended signal — before any model re-evaluation. Re-running P3's
predictability protocol (Step 3) with corrected telemetry found `cpu`,
pooled `oom`, and `flaky` NOT VALIDATED (an "always fires" false-alarm
pattern disqualified their nominal AUROC edge); `resource_unavailable`
showed STRONG EVIDENCE from a new, legitimate pre-flight probe; splitting
`oom` by observability confirmed the audit's own hypothesis about
temporal-resolution limits.

**P4 (generalization) — second priority:** The pre-remediation
0.678→0.506 OOM numbers did not replicate under corrected telemetry (honest
dev AUROC was only 0.434). Root-caused to a fixed, environment-independent
RSS normalization constant; building a real, environment-aware feature
(the run's own configured memory budget, exposed via new telemetry) raised
OOM AUROC to 0.989 (dev) with only 0.006-0.054 degradation to held-out/
robustness — a genuine, understood generalization result.

**P5 (final system):** A dedicated repeated-incident memory experiment
(same workload, real process restarts, memory ON vs. OFF) confirmed
memory changes real decisions exactly when and how expected. Persistence/
restart/isolation was verified directly. Step 7's final verification pass
then found and fixed two more genuine engineering defects beyond the
original 3 known full-suite failures — most significantly, real
nondeterminism in the core agent-uncertainty decision path itself (a
timestamp-tie bug that could silently flip ANSWER vs. REVIEW/ABSTAIN for
the highest-risk episodes). The final full-suite run is clean: 837
passed, 0 failed.

## What was explicitly NOT done (stated plainly, not hidden)

- Step 3's `cpu`-family AUROC numbers were measured before the Step 7
  timing-margin fix and are flagged as needing re-confirmation, not
  re-run in this phase (budget trade-off).
- P5's original headline numbers (100% accuracy, retry ablation) used the
  exact code path the timestamp-tie defect lived in; re-running them with
  the fix in place is recommended, not performed here.
- P2-W1/P2-W3 (held-out sample expansion, retry economics), P4-W5
  (containerized environments), P5-W4 (recovery taxonomy expansion) were
  not attempted this phase.
- No benchmark, dataset, or final model construction was started, per the
  master remediation register's own explicit boundary for this phase.

See `FINAL_POST_REMEDIATION_EVALUATION.md` for the complete
weakness-by-weakness table and capability grades.
