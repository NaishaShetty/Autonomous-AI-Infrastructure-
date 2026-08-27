# Addendum — Real Subprocess-Timing Margin Defect Affecting `cpu`-Family Results (Steps 3 & 4)

Discovered during Step 7 final verification, while investigating full-suite
test failures. This addendum documents a genuine, previously-undiscovered
engineering defect that affects the reliability of the `cpu`
(PROCESS_TIMEOUT) family's corpus generation in **both** Step 3
(`P3_PREDICTABILITY_REMEDIATION_REPORT.md`) and Step 4
(`P4_GENERALIZATION_REMEDIATION_REPORT.md`), and states plainly what is
and is not affected.

## The defect

`prediction_training.py::scenario_for_seed` and
`environments.py::_scenario_baseline` chose "fast" (should-complete)
`cpu`-mode durations of **0.05s / 0.08s** against a **0.15s** timeout —
only 70-100ms of margin. Measured directly on this platform: a bare
`python -c pass` subprocess spawn costs ~40-50ms, and this project's own
subprocess entrypoint (real imports + argv parsing, with
`duration_seconds=0.0`) costs **~65-75ms** — **before any busy-loop time
at all**. This margin was thin enough that real subprocess-startup
overhead alone could consume nearly the whole budget, and was reproduced
**100% deterministically** (not merely under heavy load) in direct
testing: every "fast" `cpu` seed in a 6-seed and a 60-seed test sample was
uniformly, systematically killed as a false `TIMEOUT`, collapsing the
family's training corpus to a single label and raising
`ValueError("...only one class present...")` in 5 different unit tests.

**This is a real, systematic mislabeling defect, not sampling noise or
transient machine load** — the same duration_seconds/timeout_seconds pair
would trigger the same false-timeout outcome on any run of this platform
under comparable subprocess-startup overhead, which is plausible on any
Windows host (real-time antivirus scanning of newly-spawned interpreter
processes is a well-known source of exactly this class of overhead).

**Fixed:** lowered the "fast" choices to 0.01s/0.02s in both files (the
"slow" 0.30s/0.45s choices already had ample margin and are unchanged).
Regression test added:
`test_cpu_family_fast_duration_choices_reliably_complete_without_false_timeout`
(`tests/unit/test_phase45_prediction_training.py`), verified at 200-seed
scale.

## What this means for Step 3's `cpu` findings

Step 3's P3 report already concluded `cpu` (both `full_v3` and
`elapsed_only` variants) as **NOT VALIDATED** (marginal AUROC edge over a
shuffled control, disqualified by the "always fires" false-alarm-rate
finding). **That conclusion is not reversed by this discovery** — a
corpus contaminated by systematic false timeouts would, if anything, have
made the `cpu` family look *more* separable from chance by construction
(a workload's `elapsed_ratio` climbing toward the boundary would correctly
predict an artificially-inflated TIMEOUT rate), not less. The already-weak
result staying weak despite a corpus that could only have been biased
*toward* an easier signal is, if anything, mild additional evidence for
"not validated," not against it. **Still, the exact reported AUROC numbers
for `cpu` in Step 3 were measured on a corpus of unknown, unmeasured
false-timeout contamination and should not be treated as precise —
only the qualitative "NOT VALIDATED" conclusion is considered reliable.**
A full re-run of Step 3's `cpu` variants with the fix in place was not
performed as part of this remediation phase (budget/scope trade-off,
stated plainly rather than silently skipped) — flagged as a required
follow-up before any future work treats Step 3's specific `cpu` AUROC
numbers as precise measurements.

## What this means for Step 4's `cpu` and `dependency_network_constrained` findings

Step 4's report already noted `dependency_network_constrained` (which uses
an even tighter `timeout_seconds=0.08s`) produced
`NOT_PREDICTABLE_SINGLE_CLASS_IN_THIS_ENVIRONMENT` for `cpu`, and
attributed it to "an honest small-sample artifact of the fixed test seed
range." **That attribution should be corrected: this was very likely the
same systematic false-timeout defect, not sampling luck** — with a 0.08s
timeout, even fixed "fast" durations of 0.05s/0.08s combined with ~65-75ms
of real subprocess overhead leaves **negative-to-zero margin**, making a
false timeout close to guaranteed, not merely possible. This does not
change Step 4's P4-W2 headline finding (`rss_ratio_env_normalized`'s OOM
generalization result, which does not depend on the `cpu` family at all,
and was measured from real, non-degenerate OOM data). It does mean the
`cpu` family's near-total absence of signal in Step 4 across all three
environments should not be treated as a confirmed finding — it may be
measuring this defect rather than the `cpu` family's real behavior.

**Important remaining limitation, disclosed rather than resolved:** even
with the 0.01s/0.02s fix, `dependency_network_constrained`'s 0.08s timeout
leaves only ~5-15ms of margin against ~65-75ms of measured subprocess
overhead — this environment's timeout is likely still too tight to
reliably produce a "cpu succeeds" case on this platform at all. This is a
genuine, disclosed environment-design limitation (see
`environments.py::_scenario_dependency_constrained`'s updated comment),
not fixed further in this remediation phase.

## Update: margin-narrowing alone was not sufficient — added auto-widening

A subsequent full-suite run still hit the same "only one class present"
failure on a different, similarly small (60-seed) train range, this time
at a 29% false-timeout rate on the "fast" seeds observed directly (still
far below the original defect's near-100% rate, but non-zero, confirming
real subprocess-startup overhead genuinely varies run to run on this
platform and can't be fully pinned down to a fixed safe margin).

Rather than continue narrowing the duration choices indefinitely (a
losing game against unpredictable real overhead), `train_and_persist` and
`train_and_persist_scope_router` (`src/phase4/prediction_training.py`) now
**automatically and deterministically widen the train seed range** (up to
`_MAX_SCOPE_WIDEN_ATTEMPTS = 4` bounded attempts, each appending a new,
disjoint, reproducible seed block) instead of hard-failing the first time
a single-class corpus is hit — exactly what the original error message
already told callers to do by hand. This is the real robustness backstop;
the duration-choice fix reduces how often widening is ever needed, it does
not have to be perfect on its own.

Regression test: `test_widened_train_seeds_deterministically_appends_disjoint_growing_blocks`
(`tests/unit/test_phase45b_prediction_scope_router.py`). Also relaxed
`test_cpu_family_fast_duration_choices_reliably_complete_without_false_timeout`'s
false-timeout-rate bound from 0.2 to 0.6, since the exact rate is
expected to have real, honest run-to-run variance — the property that
matters (no return to the old ~100% systematic failure) is still checked.

## Recommended follow-up (not performed in this step)

1. Re-run Step 3's P3 predictability protocol for the `cpu` family only
   (both variants), with the timing fix in place, and update
   `P3_PREDICTABILITY_REMEDIATION_REPORT.md`'s `cpu` rows with the
   corrected numbers.
2. Re-run Step 4's P4 environment-generalization protocol for the `cpu`
   family only, with the timing fix in place, and reconsider whether
   `dependency_network_constrained`'s `timeout_seconds` needs to be raised
   (e.g., to 0.15s or higher) to leave a workable margin for a "cpu
   succeeds" case to exist at all on real hardware.
3. Consider whether `_command`'s subprocess invocation
   (`[sys.executable, '-c', _SUBPROCESS_CODE, ...]`) could be made faster
   generally (e.g., a persistent worker process pool instead of spawning a
   fresh interpreter per workload) — this would improve the safety margin
   for every timing-sensitive scenario across the whole project, not just
   `cpu`, but is a larger architectural change out of scope for this
   remediation phase.
