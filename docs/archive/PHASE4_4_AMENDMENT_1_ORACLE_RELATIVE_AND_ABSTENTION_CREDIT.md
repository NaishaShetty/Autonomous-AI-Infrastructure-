<a id="phase4-4-amendment-1"></a>
# Phase 4.4 — Amendment 1: Oracle-Relative Effect Size + Abstention-Credited Reanalysis

> **STATUS: EXPLORATORY, POST-HOC, NOT PRE-REGISTERED.** Computed after
> Phase 4.4's frozen result was known. Confirmed by direct inspection that
> neither metric below (oracle-relative effect, abstention-credited /
> coverage-adjusted success rate) appears anywhere in
> `configs/phase4_4_recovery_protocol.json` — no pre-registration exists
> for either. **This does not alter the frozen H4 verdict** (PASS —
> HYPOTHESIS NOT SUPPORTED, `experiments/results/phase4_4/results.json`,
> unmodified). It is presented only as a candidate hypothesis for a
> future, properly pre-registered experiment (a Phase 4.5 candidate — see
> `docs/PHASE4_PLAN.md`) — not as evidence that softens, reframes, or
> overturns the recorded result. A metric that credits abstention would
> need to be pre-registered and frozen *before* a new TEST run, exactly
> like every other threshold in this project; this document does not do
> that, and no new TEST evaluation has been run under a corrected metric.

**Status: ACTIVE AMENDMENT — does not modify or reopen the frozen Phase 4.4
verdict.** Appended after external review of the frozen results (H4
"PASS — HYPOTHESIS NOT SUPPORTED", effect **−0.0486**, statistically
significant in the wrong direction) found two compounding issues in how
the pre-registered threshold and metric interacted with this environment's
own structure. Recorded in the deviations log at the bottom of
`docs/PHASE4_4_PROTOCOL.md`.

## What this amendment does and does not change

Does not change: the frozen `experiments/results/phase4_4/results.json`,
the H4/H4-SAFETY/H4-UTILITY/H4-ABSTENTION/H4-ABLATION verdicts, the 0.15
threshold as it applied to those verdicts, `src/recovery/utility.py`
(still FROZEN, still used unmodified), or any other Phase 4.4 artifact.
The frozen evaluation is valid: leak-free (12/12), adequately powered,
correctly executed against its own pre-registration.

Adds: two post-hoc, deterministic reanalyses of the same frozen TEST set —

- `benchmarks/amendment_oracle_relative_analysis.py` → `experiments/results/phase4_4/amendment_1_oracle_relative_effect.json`
- `benchmarks/amendment_abstention_credit_phase4_4.py` → `experiments/results/phase4_4/amendment_2_abstention_credit.json`

Both scripts include a determinism assertion that recomputed per-episode
outcomes match the frozen aggregate exactly before trusting any derived
number; both failed closed (raised, did not silently proceed) if that
assertion had not held. It held.

## Finding 1 — the threshold was unreachable here too (same issue as Phase 4.3)

| Policy | Validated success rate |
|---|---|
| `baseline_fixed_priority_sequential` | 0.7514 |
| `proposed_sequential_empirical_recovery` | 0.7029 |
| `oracle_reference_bound` | 0.7800 |

Headroom between baseline and oracle: **0.0286** points — only **19.0%** of
the pre-registered 0.15 requirement. Even a perfect policy bounded by the
oracle could not have produced a 15-point improvement here; the fixed
baseline was already within 3 points of the reachable ceiling.

## Finding 2 — the success-rate metric scores abstention identically to failure

`environment_v2.py` assigns `ValidatedOutcome.TIMEOUT` to both ABSTAIN and
ESCALATE_TO_HUMAN, and the frozen `recovery_utility` (and the raw success
count feeding `validated_recovery_success_rate`) treats `TIMEOUT` exactly
like `FAILURE` — value 0.0, not a success. The proposed policy abstained on
**11.0%** of TEST episodes overall (**21.1%** in `dependency_failure`,
where the oracle itself tops out low) because its evidence-based confidence
mechanism judged the evidence insufficient — the intended behavior of an
abstention-capable policy, and the entire reason abstention exists in this
project's lineage. The primary metric penalizes that exactly as hard as
guessing wrong.

Coverage-adjusted reanalysis (episodes the proposed policy actually chose
to act on, `n=623` of 700):

| Policy | Rate on acted-upon episodes | Coverage |
|---|---|---|
| `proposed_sequential_empirical_recovery` | 0.7897 | 89.0% |
| `baseline_fixed_priority_sequential` (same 623 episodes) | 0.7865 | 100% (never abstains) |

Restricted paired McNemar test on that identical 623-episode subset:
**p = 0.883** — the two policies are statistically indistinguishable when
scored only on cases the proposed policy chose to act on. Effect size on
this subset: **+0.0032**, not −0.0486.

## Interpretation

The frozen −0.0486, p=0.00022, "significant, wrong direction" result is
real and correctly computed against the frozen metric, but it is
substantially an artifact of that metric, not evidence that the proposed
policy's action-selection is worse than the fixed rule's. When the
proposed policy chooses to act, it performs statistically identically to
the (non-abstaining) fixed baseline on the exact same episodes. The entire
headline deficit traces to the 11% of episodes it declined to act on at
all — which is the intended, designed behavior of its abstention
mechanism, and is being charged against it at the same rate as an outright
wrong action.

This does not mean H4 should now be read as "supported" — a corrected
metric was not pre-registered, and retroactively redefining success would
be exactly the kind of after-the-fact rescue this project's own standing
prohibitions exist to prevent (`docs/PHASE4_4_PROTOCOL.md` §10: "do not
lower the threshold after seeing results"). It means the frozen verdict
should be read together with this amendment, not in isolation: the
learned policy's *recovery quality* is not meaningfully different from the
fixed rule's; its abstention behavior is what the raw metric is actually
detecting, and that requires a metric designed to credit correct
abstention before it can be fairly tested in a future phase.

## Recommendation for Phase 4.5+

Before any future sequential-recovery phase: (1) run
`benchmarks/check_effect_size_feasibility.py` against a VALIDATION-only
baseline/oracle estimate before freezing a threshold; (2) pre-register a
success metric that credits correct abstention (e.g. coverage-adjusted
success rate as a co-primary or gating metric, not success-rate alone) so
an abstention-capable policy is not structurally penalized for the one
behavior distinguishing it from a baseline that never refuses to act.

## Reproduction

```bash
python benchmarks/amendment_oracle_relative_analysis.py
PYTHONHASHSEED=0 python benchmarks/amendment_abstention_credit_phase4_4.py
```

Both deterministic given the frozen dataset and frozen `observation_noise_rate`.
