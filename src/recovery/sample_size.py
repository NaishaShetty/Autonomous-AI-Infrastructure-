"""FROZEN sample-size methodology for Active Phase 4.3 (brief section 21).

Frozen BEFORE final dataset generation. This module documents and computes
the minimum test-set size via a two-proportion power calculation; the
number actually generated (``src.recovery.splits.N_TEST_PER_FAMILY``) was
then set with headroom above this minimum, not below it. If a future
protocol version generated a dataset that fell below this minimum, the
correct response is to report INCONCLUSIVE (brief section 21), not to
lower the requirement.

Two-proportion, two-sided z-test power formula (conservative: this is the
*unpaired* formula; the actual analysis in
benchmarks/phase4_3_recovery_evaluate.py uses a paired McNemar test on the
same test episodes scored under both baseline and proposed policy, which is
strictly more powerful for a fixed n than the unpaired formula below -- so
using the unpaired minimum as the frozen floor is conservative, not
optimistic):

    n_per_arm = (z_alpha/2 * sqrt(2*pbar*(1-pbar)) + z_beta * sqrt(p1*(1-p1) + p2*(1-p2)))^2
                / (p1 - p2)^2

Assumptions (frozen, not fit to any observed data):
- p1 (expected proposed-policy validated success rate): 0.55
- p2 (expected baseline validated success rate): 0.40
- alpha = 0.05 (two-sided), power = 0.80
- minimum meaningful effect size: 0.15 (matches p1 - p2 above)
"""
from __future__ import annotations

import math

Z_ALPHA_2 = 1.959963985  # alpha=0.05, two-sided
Z_BETA = 0.841621234     # power=0.80

P1_EXPECTED = 0.55
P2_EXPECTED = 0.40


def minimum_n_per_arm(p1: float = P1_EXPECTED, p2: float = P2_EXPECTED,
                       z_alpha_2: float = Z_ALPHA_2, z_beta: float = Z_BETA) -> int:
    pbar = (p1 + p2) / 2.0
    numerator = (z_alpha_2 * math.sqrt(2 * pbar * (1 - pbar))
                 + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2)))
    n = (numerator ** 2) / ((p1 - p2) ** 2)
    return math.ceil(n)


MINIMUM_N_TEST_TOTAL = minimum_n_per_arm()  # ~173, the frozen floor
