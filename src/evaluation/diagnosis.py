"""Phase 3.6.3: deterministic, zero-fitting failure-cause diagnosis.

See ``configs/phase3_6_decision_recovery_protocol.json.diagnosis_
taxonomy`` for the full rationale. This is condition ATTRIBUTION (which
known, self-generated corruption mechanism produced this failure), not
deep causal inference -- the taxonomy is grounded in ground truth this
project itself generates (Phase 3.5's attack transforms), not fabricated
categories.

No model is fit here. The rule's threshold (mean_sq > 2.0) is derived
from the generator's own algebra (features are N(0,1); feature_noise_mild
adds N(0, 0.25) independently, feature_noise_severe adds N(0, 2.25)) --
see the protocol file for the exact expected-value derivation. It is
fixed before any diagnosis result is computed.
"""
from __future__ import annotations

DIAGNOSIS_CLASSES = ["clean", "feature_noise", "feature_dropout"]

MEAN_SQ_THRESHOLD = 2.0


def diagnose(context: dict[str, float], feature_names: list[str]) -> str:
    """Returns one of DIAGNOSIS_CLASSES for a single sample's (possibly
    corrupted) context. Intended to be called only on samples already
    identified as failures (is_failure == 1) -- diagnosing a cause for a
    non-failure is not meaningful under this taxonomy and is not
    prevented here (callers are responsible for that filter, exactly as
    every other Phase 3.x metric function trusts its caller's data
    boundary)."""
    values = [context[f] for f in feature_names]
    n_zero = sum(1 for v in values if v == 0.0)
    if n_zero >= 2:
        return "feature_dropout"
    mean_sq = sum(v * v for v in values) / len(values)
    if mean_sq > MEAN_SQ_THRESHOLD:
        return "feature_noise"
    return "clean"


def condition_to_true_class(condition_id: str) -> str:
    """Ground-truth diagnosis label for a Phase 3.5 condition id -- this
    is data we generated ourselves (we chose which attack to apply), not
    an inferred or fabricated label."""
    if condition_id == "clean":
        return "clean"
    if condition_id in ("feature_noise_mild", "feature_noise_severe"):
        return "feature_noise"
    if condition_id == "feature_dropout":
        return "feature_dropout"
    raise ValueError(f"unknown condition id: {condition_id}")
