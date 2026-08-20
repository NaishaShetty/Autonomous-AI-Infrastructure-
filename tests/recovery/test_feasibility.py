"""Tests for src/recovery/feasibility.py -- the retroactive feasibility-gate
amendment (see that module's docstring for why it exists)."""
from __future__ import annotations

import pytest

from src.recovery.feasibility import check_feasibility, oracle_relative_effect


def test_infeasible_when_headroom_below_required_effect():
    # Phase 4.3's actual numbers: oracle=0.60, baseline=0.5403, required=0.15
    result = check_feasibility(baseline_rate=0.5403, oracle_rate=0.60, required_min_effect=0.15)
    assert result.feasible is False
    assert result.headroom == pytest.approx(0.0597, abs=1e-4)
    assert result.headroom_ratio < 1.0


def test_infeasible_phase_4_4_numbers():
    # Phase 4.4's actual numbers: oracle=0.78, baseline=0.7514, required=0.15
    result = check_feasibility(baseline_rate=0.7514285714285714, oracle_rate=0.78, required_min_effect=0.15)
    assert result.feasible is False
    assert result.headroom == pytest.approx(0.0286, abs=1e-4)


def test_feasible_when_headroom_covers_required_effect():
    result = check_feasibility(baseline_rate=0.40, oracle_rate=0.60, required_min_effect=0.15)
    assert result.feasible is True
    assert result.headroom == pytest.approx(0.20)
    assert result.headroom_ratio == pytest.approx(0.20 / 0.15)


def test_feasible_at_exact_boundary():
    result = check_feasibility(baseline_rate=0.40, oracle_rate=0.55, required_min_effect=0.15)
    assert result.feasible is True
    assert result.headroom_ratio == pytest.approx(1.0)


def test_rejects_oracle_below_baseline():
    with pytest.raises(ValueError):
        check_feasibility(baseline_rate=0.60, oracle_rate=0.50, required_min_effect=0.10)


def test_oracle_relative_effect_normalizes_by_headroom():
    # proposed captured 0.0111 of a 0.0597 headroom in 4.3 -> ~18.6%
    frac = oracle_relative_effect(baseline_rate=0.5403, proposed_rate=0.5514, oracle_rate=0.60)
    assert frac == pytest.approx(0.0111 / 0.0597, abs=1e-3)


def test_oracle_relative_effect_none_when_no_headroom():
    assert oracle_relative_effect(baseline_rate=0.5, proposed_rate=0.5, oracle_rate=0.5) is None


def test_oracle_relative_effect_can_exceed_one():
    frac = oracle_relative_effect(baseline_rate=0.50, proposed_rate=0.65, oracle_rate=0.60)
    assert frac == pytest.approx(1.5)
