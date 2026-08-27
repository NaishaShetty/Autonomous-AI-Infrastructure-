# Final Weakness Register — Phase 4 Closure

Consolidates every weakness (P1–P5) from
`experiments/results/post_p5_remediation/20260825T064402Z/FINAL_POST_REMEDIATION_EVALUATION.md`
with the final status after the 5 post-P5 follow-ups
(`experiments/results/post_p5_remediation_followups/20260825T144031Z/FOLLOWUPS_SUMMARY.md`)
and this closure phase's own audit. Allowed statuses only: **FIXED**,
**STRONGLY DEMONSTRATED**, **PARTIALLY FIXED**, **INVESTIGATED / NOT
VALIDATED**, **ACCEPTED LIMITATION**, **NOT YET STARTED**, **OUT OF
SCOPE**, **NOT APPLICABLE**. Nothing is hidden; every unresolved item is
carried forward explicitly.

| ID | Weakness | Original status | Follow-up | Result | Final status | Evidence path |
|---|---|---|---|---|---|---|
| P1-W1 | Sentiment uncertainty AUROC ≈0.659 vs. arithmetic/QA ≈0.95/0.93 | ACCEPTED LIMITATION (post-remediation) | None in this phase | All 4 candidate estimators mathematically rank-equivalent; not a bug | **ACCEPTED LIMITATION** | `experiments/results/post_p5_remediation/20260825T064402Z/reports/P1_P2_AGENT_REMEDIATION_REPORT.md` |
| P1-W2 | Limited real-model coverage (3 local models) | ACCEPTED LIMITATION | None in this phase | No expansion attempted or justified | **ACCEPTED LIMITATION** | `experiments/results/phase4_6_to_4_10/20260824T133029Z/reports/PHASE4_6_REAL_AGENT_REPORT.md` |
| P1-W3 | Mechanism-aware uncertainty interface | FIXED (pre-existing, verified) | None in this phase | Unchanged | **FIXED** | Step 5 report, above |
| P1-W4 | Full-suite instability | FIXED (837 passed / 0 failed, isolated) | Follow-ups' own full-suite run | 837 passed, 0 failed (2076.80s), confirmed again after all 5 follow-ups | **FIXED** | `FOLLOWUPS_SUMMARY.md`; this closure phase's own run (see `FINAL_SYSTEM_AUDIT.md`) |
| P2-W1 | Expand held-out sample size | NOT YET STARTED | Follow-up 4 (2x held-out, 600 seeds) | Calibrated final accuracy 0.998 vs. generic 0.970 (CI [0.991,1.000] vs. [0.953,0.981]); retry recovery 95% (19/20) | **FIXED — VALIDATED (survives 2x expansion)** | `.../reports/` follow-up 4 report |
| P2-W2 | RETRY only where legitimate | FIXED (verified) | None in this phase | Unchanged | **FIXED** | Step 5 report |
| P2-W3 | Retry economics sensitivity sweep | NOT YET STARTED | Follow-up 4 (18-point pre-registered grid) | All 18 configurations byte-identical decisions/outcomes (final accuracy 1.000 in every configuration, 40-seed/3-wrong-episode grid) | **PARTIALLY FIXED — no fragility observed, limited statistical power (disclosed)** | follow-up 4 report |
| P3-W1 | Telemetry may be insufficient | FIXED (audit) / CONFIRMED (oom sub-finding) | None in this phase | Unchanged | **FIXED** | `audits/P3_PREDICTIVE_OBSERVABILITY_AUDIT.md` |
| P3-W2 | Expand legitimate decision-time telemetry | IMPROVED | None in this phase | Unchanged | **FIXED** | Step 2 report |
| P3-W3 | Determine real predictability | INVESTIGATED — mixed, per-family | Follow-ups 1 and 5 | `cpu`: real/shuffled gap widened (0.616 vs 0.389) but false-alarm rate still 1.00 — no change in verdict. `oom`≥2-sample: real ranking edge confirmed (AUROC 0.780 vs 0.625 shuffled) but false-alarm rate 1.00, specificity 0.179 — not a usable detector | **INVESTIGATED / NOT VALIDATED — final, no further iteration** (`cpu`, pooled `oom`, `flaky`, `oom`≥2-sample all disqualified by false-alarm rate); `resource_unavailable` remains the one exception (see P3-W2/Step 3) | follow-up 1 and 5 reports |
| P3-W4 | Simple-model-first methodology | FIXED | None in this phase | Unchanged | **FIXED** | Step 3 report |
| P3-W5 | Prevent "always fires" false predictor | FIXED | Follow-ups 1, 5 (re-applied) | Correctly disqualified `cpu` and `oom`≥2-sample again after re-measurement | **FIXED** | follow-up 1, 5 reports |
| P3-W6 | Rolling-checkpoint / lead-time evaluation | FIXED (verified) | None in this phase | Unchanged | **FIXED** | Step 3 report |
| P3-W7 | GPU probe nondeterminism | FIXED | None in this phase | Unchanged | **FIXED** | `src/phase4/gpu_probe.py` |
| P3-W8 | RNG/test-order defect (`hash()` seeding) | FIXED | None in this phase | Unchanged | **FIXED** | Step 1 report |
| P4-W1 | Environment generalization fails (OOM) | INVESTIGATED / IMPROVED | None in this phase | Unchanged | **FIXED for OOM** (root cause identified and resolved) | Step 4 report |
| P4-W2 | Environment-aware representations | FIXED for OOM | None in this phase | Unchanged | **FIXED for OOM** | Step 4 report |
| P4-W3 | Distribution-shift robustness testing | IMPROVED (partial) | None in this phase | Unchanged | **PARTIALLY FIXED** — threshold recalibration per target environment still not explored | Step 4 report |
| P4-W4 | Does environment conditioning solve it? | CONFIRMED for OOM | Follow-up 3 (extends to `resource_unavailable`) | Combining preflight + environment-aware features raised held-out AUROC to 0.916 (C) vs. 0.781 (A) vs. 0.743 (B) — a real ranking improvement — but false-alarm rate 1.00 for all three at their calibrated thresholds | **PARTIALLY FIXED for `resource_unavailable`** (ranking improved, operating point not usable); **CONFIRMED for OOM** (unchanged) | follow-up 3 report |
| P4-W5 | Containerized/production-scale environment scope | NOT ATTEMPTED (explicit boundary) | Explicitly named, not one of the 5 bounded follow-ups | Not attempted | **OUT OF SCOPE** | `FOLLOWUPS_SUMMARY.md` "what was explicitly NOT done" |
| P5-W1 | Memory ON/OFF showed no difference (confounded design) | FIXED — hypothesis confirmed | Follow-up 2 (re-run with timestamp-tie fix) | Qualitative finding survives; determinism directly verified (byte-identical decisions across 2 same-seed runs) | **FIXED — RE-CONFIRMED** | follow-up 2 report |
| P5-W2 | Memory persistence/restart/isolation | FIXED (verified under real restart) | None in this phase | Unchanged | **FIXED** | Step 6 report |
| P5-W3 | 3 full-suite failures need individual re-evaluation | FIXED (837/0, 2 more defects found+fixed) | Follow-ups' full-suite run | 837 passed, 0 failed, confirmed again | **FIXED** | `FOLLOWUPS_SUMMARY.md`; `FINAL_SYSTEM_AUDIT.md` |
| P5-W4 | Recovery/action taxonomy narrow | NOT YET STARTED | Explicitly named, not one of the 5 bounded follow-ups | Not attempted | **OUT OF SCOPE** | `FOLLOWUPS_SUMMARY.md` "what was explicitly NOT done" |
| P5-W5 (new, this phase) | P5's exact headline numbers (100%/0% accuracy) used the pre-timestamp-tie-fix code path | Flagged as needing re-confirmation (post-remediation) | Follow-up 2 | Calibrated final accuracy 0.997 (vs. generic 0.957); final error rate 0.0033 (vs. 0.0433); retry recovery 0.938 (15/16); 0 unsafe actions in every condition; byte-identical determinism confirmed | **FIXED — RE-CONFIRMED** (exact decimals superseded by a defect-free measurement; qualitative direction unchanged) | follow-up 2 report |
| ENG-1 (new, this phase) | `cpu`-family timing margin defect | Found and fixed in Step 7 | N/A (fixed pre-follow-ups) | Regression-tested | **FIXED** | `reports/ADDENDUM_CPU_TIMING_DEFECT.md` |
| ENG-2 (new, this phase) | Timestamp-tie nondeterminism in core agent-decision path (`<` vs `<=`) | Found and fixed in Step 7 | Follow-up 2 verified the fix in production use | 0 further occurrences; determinism directly demonstrated | **FIXED** | `reports/ADDENDUM_TIMESTAMP_TIE_DETERMINISM_DEFECT.md`; follow-up 2 report |
| ENG-3 (carried forward, not this phase's finding) | `LogisticRegression` unpinned `random_state` in `prediction_training.py` causing test-order/RNG-seed sensitivity | Documented, not fixed (Phase 4.8–4.10) | Not one of the 5 follow-ups; re-checked in this closure phase's own audit | See `FINAL_SYSTEM_AUDIT.md` item on test-order independence for whether it surfaced in this phase's own runs | **NOT YET STARTED** (fix not attempted; documented for a future session) | `PHASE4_10_FINAL_INTEGRATED_EVALUATION.md` §4, §8 |
| N/A | P4-W5-adjacent: real externally-hosted LLM evaluation | Never claimed as in scope | Not attempted | Not attempted | **OUT OF SCOPE** | README "Known Limitations"; Phase 4.5b report |

## Notes on the status assignments above

- **P3-W3's final status is "INVESTIGATED / NOT VALIDATED"** rather than a
  blanket negative, because it is genuinely mixed per family:
  `resource_unavailable` carries an **A** grade (strong evidence,
  unaffected by the follow-ups), while `cpu`, pooled `oom`, `flaky`, and
  the `oom`≥2-sample subset all remain disqualified by the "always fires"
  false-alarm-rate check even after the follow-ups' final, most-favorable
  re-measurement. Both are true at once; neither is softened.
- **No status in this table was ever loosened by this closure phase.**
  Every status above is either unchanged from `FINAL_POST_REMEDIATION_EVALUATION.md`,
  or updated strictly by the 5 follow-ups' own explicit, final verdicts —
  this closure phase did not re-run or re-interpret any of the bounded
  scientific work itself, per the instruction that those five follow-ups
  are already complete and not to be second-guessed.
- **ENG-3 is carried forward, not newly discovered by this phase.** It is
  included here because it is a real, still-open, documented engineering
  item that a future session should address (pin `random_state=` in
  `prediction_training.py`'s `LogisticRegression` fit); see
  `docs/MASTER_RECORD_CONTENT.md` §31 and §38 for the same item in context.
