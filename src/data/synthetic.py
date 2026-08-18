"""Synthetic workload data generator with regime drift.

Migrates the concept validated as reusable in Phase 1
(``synthetic_failure_dataset.py`` -- "Reuse", PHASE1_AUDIT_REPORT.md
section 7): multiple regimes, later regimes shift the true
feature->label relationship so a model trained on early data accumulates
failures on later data. This is what makes a "failure memory" meaningful to
evaluate at all -- without drift, a well-calibrated confidence signal alone
would already be sufficient and there would be no historical-failure
pattern for failure-memory to find.

This is still explicitly synthetic data (as the Phase 1 audit noted about
the source), used to produce a controlled, reproducible benchmark, not a
claim about real-world model behavior.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

FEATURE_NAMES = ["f1", "f2", "f3", "f4", "f5"]
N_FEATURES = len(FEATURE_NAMES)


@dataclass
class StreamSample:
    context: dict[str, float]
    label: int
    regime: int


def generate_regime_stream(
    regime_sizes: tuple[int, ...] = (2000, 2000, 2000, 2000, 2000),
    drift_scale: float = 0.35,
    seed: int = 42,
) -> list[StreamSample]:
    """Generate a stream of samples across ``len(regime_sizes)`` regimes.
    Regime 0 is the "training" distribution; each subsequent regime's true
    decision boundary is rotated away from regime 0's by an amount
    proportional to ``drift_scale * regime_index``, so a model fit only on
    regime 0 degrades on later regimes -- deterministic given ``seed``.
    """
    rng = np.random.default_rng(seed)
    base_w = rng.normal(size=N_FEATURES)

    samples: list[StreamSample] = []
    for regime_idx, size in enumerate(regime_sizes):
        drift = rng.normal(scale=drift_scale * regime_idx, size=N_FEATURES)
        w = base_w + drift
        X = rng.normal(size=(size, N_FEATURES))
        logits = X @ w
        p = 1.0 / (1.0 + np.exp(-logits))
        y = (rng.random(size) < p).astype(int)
        for j in range(size):
            samples.append(
                StreamSample(
                    context={FEATURE_NAMES[k]: float(X[j, k]) for k in range(N_FEATURES)},
                    label=int(y[j]),
                    regime=regime_idx,
                )
            )
    return samples
