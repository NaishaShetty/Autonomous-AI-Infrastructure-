"""Phase 3.5 attack/corruption transforms.

These functions operate ONLY on already-generated ``StreamSample`` objects
(typically ``system.test_stream``, regimes 3+4) -- they never touch
``src/data/synthetic.py``'s RNG stream or its label-generating mechanism.
Each transform replaces a sample's ``context`` with a corrupted version and
leaves ``label`` and ``regime`` untouched.

This makes every attack defined here a COVARIATE-shift condition: what the
system OBSERVES changes, but the true feature->label relationship that
produced the (untouched) label does not. This is the opposite axis from
Phase 3.3's ``drift_scale`` (concept drift: the label-generating boundary
rotates, features are unchanged) -- see
docs/PHASE3_5_ATTACK_GENERALIZATION.md section 4 for why this is a
genuinely distinct generalization axis, not a relabeled repeat of Phase
3.3.

Determinism: every source of randomness here is derived from
``(seed, attack_ordinal)`` via ``np.random.default_rng((seed,
attack_ordinal))`` -- NumPy's documented multi-value ``SeedSequence``
entropy input. Same seed + same attack ordinal always reproduces the exact
same corrupted values; no uncontrolled randomness is introduced.
"""
from __future__ import annotations

import numpy as np

from src.data.synthetic import StreamSample


def apply_feature_noise(
    samples: list[StreamSample],
    feature_names: list[str],
    std: float,
    seed: int,
    attack_ordinal: int,
) -> list[StreamSample]:
    """Adds i.i.d. N(0, std^2) noise to every feature of every sample's
    context (simulating corrupted/noisy telemetry reaching the deployed
    system). ``label`` and ``regime`` are copied unchanged -- the ground
    truth the workload model is judged against is NOT perturbed, only what
    it observes."""
    if std < 0:
        raise ValueError("std must be >= 0")
    rng = np.random.default_rng((seed, attack_ordinal))
    out = []
    for s in samples:
        noise = rng.normal(scale=std, size=len(feature_names))
        new_context = {f: float(s.context[f] + n) for f, n in zip(feature_names, noise)}
        out.append(StreamSample(context=new_context, label=s.label, regime=s.regime))
    return out


def apply_feature_dropout(
    samples: list[StreamSample],
    feature_names: list[str],
    dropped_features: list[str],
) -> list[StreamSample]:
    """Zeroes a fixed, predetermined subset of features in every sample's
    context (simulating a sensor/telemetry field going dark or being
    stripped by an attacker). Fully deterministic -- no randomness
    involved at all. ``label`` and ``regime`` are copied unchanged."""
    missing = set(dropped_features) - set(feature_names)
    if missing:
        raise ValueError(f"dropped_features not in feature_names: {sorted(missing)}")
    out = []
    for s in samples:
        new_context = {f: (0.0 if f in dropped_features else s.context[f]) for f in feature_names}
        out.append(StreamSample(context=new_context, label=s.label, regime=s.regime))
    return out
