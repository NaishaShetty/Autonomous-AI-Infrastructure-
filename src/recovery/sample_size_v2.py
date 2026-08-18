"""FROZEN sample-size methodology for Active Phase 4.4.

Reuses the SAME two-proportion power-calculation formula Phase 4.3 froze
(``src.recovery.sample_size``, untouched, not imported here so this
module's minimum is derived independently rather than merely re-exported --
per protocol section 8: "recompute rather than reuse 4.3's literal
173/arm number, since the McNemar variance structure for a 2-step outcome
may differ").

Inputs (frozen, matching protocol section 8 / configs/phase4_4_recovery_protocol.json):
    p1 = 0.55, p2 = 0.40, alpha = 0.05 (two-sided), power = 0.80

Formula (identical unpaired two-proportion z-test form as 4.3 -- the actual
Step 9 analysis uses a paired McNemar test on 2-step episode outcomes,
which is strictly more powerful for a fixed n than this unpaired formula,
so using the unpaired minimum as the frozen floor is conservative here too,
exactly as in 4.3):

    n_per_arm = (z_alpha/2 * sqrt(2*pbar*(1-pbar)) + z_beta * sqrt(p1*(1-p1) + p2*(1-p2)))^2
                / (p1 - p2)^2
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


MINIMUM_N_TEST_TOTAL = minimum_n_per_arm()  # independently recomputed floor
