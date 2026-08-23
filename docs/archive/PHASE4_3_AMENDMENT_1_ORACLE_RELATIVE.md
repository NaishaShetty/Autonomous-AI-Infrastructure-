<a id="phase4-3-amendment-1"></a>
# Phase 4.3 — Amendment 1: Oracle-Relative Effect Size Reanalysis

> **STATUS: EXPLORATORY, POST-HOC, NOT PRE-REGISTERED.** Computed after
> Phase 4.3's frozen result was known. Confirmed by direct inspection that
> this metric does not appear anywhere in
> `configs/phase4_3_recovery_protocol.json` — no pre-registration exists
> for it. **This does not alter the frozen H3 verdict** (PASS — HYPOTHESIS
> NOT SUPPORTED, `experiments/results/phase4_3/results.json`, unmodified).
> It is presented only as a candidate hypothesis for a future, properly
> pre-registered experiment (a Phase 4.5 candidate — see
> `docs/PHASE4_PLAN.md`) — not as evidence that softens, reframes, or
> overturns the recorded result.

**Status: ACTIVE AMENDMENT — does not modify or reopen the frozen Phase 4.3
verdict.** Appended after external review of the frozen results identified
that the pre-registered minimum effect size (0.15) was never checked
against the headroom actually available in the environment before being
frozen. See [`src/recovery/feasibility.py`](../src/recovery/feasibility.py)
for the reusable check this amendment is built on, and the corresponding
entry in `docs/PHASE4_3_RECOVERY_LEARNING.md`'s deviations record.

## What this amendment does and does not change

Does not change: the frozen `experiments/results/phase4_3/results.json`,
the H3 verdict (**PASS — HYPOTHESIS NOT SUPPORTED**), the 0.15 threshold as
it applied to that verdict, or any other Phase 4.3 artifact. The original
experiment was leak-free, adequately powered, and correctly evaluated
against its own pre-registration; that stands.

Adds: a second, headroom-normalized view of the same frozen numbers,
computed by `benchmarks/amendment_oracle_relative_analysis.py` and written
to `experiments/results/phase4_3/amendment_1_oracle_relative_effect.json`.

## The finding

The frozen numbers already in `results.json` are:

| Policy | Validated success rate |
|---|---|
| `baseline_fixed_priority` | 0.5403 |
| `proposed_empirical_recovery` | 0.5514 |
| `oracle_reference_bound` | 0.6000 |

Required minimum effect (H3, frozen): **0.15** absolute points.

Headroom actually available between baseline and oracle: **0.0597** points
(0.6000 − 0.5403) — i.e. **39.8%** of what H3 required. No policy, including
a hypothetically perfect one bounded by the oracle, could have produced a
0.15-point improvement over `baseline_fixed_priority` in this environment,
because the oracle itself is only 0.0597 points above it.

Of that 0.0597-point headroom, the proposed policy captured **0.0111**
points, i.e. **18.6%** of what was reachable (`oracle_relative_effect` =
0.0111 / 0.0597 ≈ 0.186).

## Interpretation

H3's "not supported" verdict is real and correctly derived from the frozen
protocol, but the protocol asked a question that was unanswerable in this
environment from the start: `baseline_fixed_priority` was already
capturing roughly 90% of the reachable success rate (0.5403 of 0.6000)
before any learning happened, leaving too little room for any mechanism —
proposed or otherwise — to clear a 15-point bar. Read on the
headroom-normalized scale, the proposed policy captured a modest but
non-trivial ~19% of the remaining gap; read on the absolute scale required
by H3, that is indistinguishable from zero and correctly reported as such.

Both readings are true simultaneously. The absolute-threshold framing
answers "did this clear a bar chosen without checking feasibility first";
the headroom-relative framing answers "did the proposed mechanism move the
needle at all, given how little needle there was to move." Future phases
should check feasibility (`benchmarks/check_effect_size_feasibility.py`)
*before* freezing a threshold, precisely so this ambiguity doesn't recur.

## Reproduction

```bash
python benchmarks/amendment_oracle_relative_analysis.py
```

Deterministic; reads only the already-frozen `results.json` files for
Phase 4.3 and 4.4, performs no new policy evaluation, and writes the two
`amendment_1_oracle_relative_effect.json` files alongside each phase's
frozen results.
