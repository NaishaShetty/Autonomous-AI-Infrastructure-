"""Pre-registration feasibility gate for recovery-learning hypotheses.

WHY THIS EXISTS (retroactive amendment, written after Active Phase 4.4):
Both Phase 4.3 (H3) and Phase 4.4 (H4) pre-registered a minimum meaningful
effect size of 0.15 (proposed policy's validated success rate must beat the
strongest baseline by >= 15 percentage points) without first checking
whether 0.15 points of headroom actually existed between that baseline and
the environment's own oracle reference bound. It did not:

  Phase 4.3: oracle 0.6000 - baseline_fixed_priority 0.5403 = 0.0597 headroom
             available, against a 0.15 requirement (39.8% of what was asked
             for was even reachable by ANY policy, including a perfect one).
  Phase 4.4: oracle 0.7800 - baseline_fixed_priority_sequential 0.7514
             = 0.0286 headroom available, against the same 0.15 requirement
             (19.1% reachable).

In both cases the frozen fixed-priority baseline was already close enough
to the oracle ceiling that no policy -- however good -- could have cleared
the pre-registered bar. The resulting "hypothesis not supported" verdicts
are valid (the experiments were leak-free, adequately powered, and
correctly executed against their own pre-registration), but they conflate
"the environment left little room to improve on a strong heuristic" with
"the proposed mechanism doesn't work." This module lets that distinction be
checked BEFORE a threshold is frozen, for every future phase.

USAGE: call ``check_feasibility`` with the baseline and oracle rates
observed/estimated on VALIDATION (never TEST) before freezing
``min_effect_size`` in a new phase's protocol. If ``feasible`` is False,
the threshold must be lowered, the baseline reconsidered, or the
environment redesigned to leave real headroom -- freezing the threshold
anyway and running the experiment regardless is exactly the mistake this
module exists to prevent from repeating.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeasibilityResult:
    baseline_rate: float
    oracle_rate: float
    required_min_effect: float
    headroom: float
    headroom_ratio: float  # headroom / required_min_effect; >= 1.0 means feasible
    feasible: bool

    def summary(self) -> str:
        verdict = "FEASIBLE" if self.feasible else "NOT FEASIBLE"
        return (
            f"{verdict}: oracle={self.oracle_rate:.4f} - baseline={self.baseline_rate:.4f} "
            f"= headroom={self.headroom:.4f}, required_min_effect={self.required_min_effect:.4f} "
            f"(headroom covers {self.headroom_ratio:.1%} of what's required)"
        )


def check_feasibility(baseline_rate: float, oracle_rate: float, required_min_effect: float) -> FeasibilityResult:
    """Can the pre-registered minimum effect size ever be satisfied, given
    the gap between the strongest non-learned baseline and the oracle
    reference bound? This is a NECESSARY (not sufficient) condition: a
    feasible headroom does not guarantee a learnable signal exists, but an
    infeasible headroom guarantees the hypothesis cannot be supported
    regardless of policy quality, and the threshold (or the environment)
    must be revisited before freezing anything.
    """
    if oracle_rate < baseline_rate:
        raise ValueError(
            f"oracle_rate ({oracle_rate}) < baseline_rate ({baseline_rate}) -- the oracle must be a valid "
            "upper bound; check that the baseline being compared is itself restricted to safe actions "
            "the way the oracle is, or that the oracle computation is not buggy."
        )
    headroom = oracle_rate - baseline_rate
    headroom_ratio = headroom / required_min_effect if required_min_effect > 0 else float("inf")
    return FeasibilityResult(
        baseline_rate=baseline_rate,
        oracle_rate=oracle_rate,
        required_min_effect=required_min_effect,
        headroom=headroom,
        headroom_ratio=headroom_ratio,
        feasible=headroom_ratio >= 1.0,
    )


def oracle_relative_effect(baseline_rate: float, proposed_rate: float, oracle_rate: float) -> float | None:
    """Normalize an observed effect (proposed - baseline) against the
    headroom that actually existed (oracle - baseline), i.e. what fraction
    of the reachable improvement the proposed policy captured. Returns
    ``None`` when there was no headroom to capture (oracle == baseline);
    the raw effect is reported separately in that degenerate case instead.
    Can exceed 1.0 if the proposed policy beats the oracle's TEST-set
    performance by chance (the oracle is a reference bound computed the
    same stochastic way as any other policy, not a hard ceiling on every
    individual draw) -- this is expected and should be reported, not
    clipped.
    """
    headroom = oracle_rate - baseline_rate
    if headroom == 0:
        return None
    return (proposed_rate - baseline_rate) / headroom
