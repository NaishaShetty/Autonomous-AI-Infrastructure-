"""Post-P5 remediation, Step 5 (P1-W1) -- unit coverage for the sentiment
uncertainty-candidate comparison's split and temperature-fitting logic."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import torch

from scripts.run_p1_step5_sentiment_uncertainty import _fit_temperature, _stable_split


def test_stable_split_is_deterministic_and_roughly_matches_the_configured_fraction():
    ids = [f"sent-{i:04d}" for i in range(2000)]
    splits = [_stable_split(i) for i in ids]
    # deterministic: same id always gets the same split
    assert all(_stable_split(i) == s for i, s in zip(ids, splits))
    calibration_fraction = sum(1 for s in splits if s == "calibration") / len(splits)
    assert 0.35 <= calibration_fraction <= 0.45  # target is 0.4; allow real sampling slack


def test_stable_split_only_produces_the_two_named_splits():
    ids = [f"x-{i}" for i in range(200)]
    assert {_stable_split(i) for i in ids} <= {"calibration", "test"}


def test_fit_temperature_recovers_a_high_temperature_for_overconfident_logits():
    # Construct synthetic logits that are perfectly separable but wildly
    # overconfident (huge magnitude) relative to a modest true error rate --
    # temperature scaling should push T well above 1 to soften them.
    torch.manual_seed(0)
    logits = []
    labels = []
    for i in range(60):
        correct_class = i % 2
        wrong_class = 1 - correct_class
        vec = torch.zeros(2)
        vec[correct_class] = 20.0  # extreme, overconfident logit gap
        vec[wrong_class] = -20.0
        logits.append(vec)
        # inject some real label noise so perfect confidence is miscalibrated
        labels.append(correct_class if i % 5 != 0 else wrong_class)
    t = _fit_temperature(logits, labels, n_iters=100, lr=0.05)
    assert t > 1.0, f"expected temperature scaling to soften overconfident logits (T>1), got T={t}"


def test_fit_temperature_returns_a_positive_finite_value():
    torch.manual_seed(1)
    logits = [torch.randn(2) for _ in range(40)]
    labels = [i % 2 for i in range(40)]
    t = _fit_temperature(logits, labels, n_iters=50)
    assert t > 0 and t == t and t != float("inf")  # positive, not NaN, not inf
