"""Integration tests for Phase 3.6.2/3.6.4: threshold derivation isolation
(regime-2 only, never test), deterministic tier assignment, cost-model
correctness, and metric-formula sanity checks."""
from __future__ import annotations

import numpy as np
import pytest

from src.evaluation.decision_policy import (
    DEFAULT_COST_MODEL,
    RiskTier,
    TierThresholds,
    assign_tier,
    decide_all,
    decision_metrics,
    sample_cost,
)
from src.schema.events import Decision


def test_tier_thresholds_derive_from_percentiles():
    scores = np.arange(0, 100)  # 0..99, percentiles are exact
    t = TierThresholds.derive(scores)
    assert t.t_50 == pytest.approx(49.5)
    assert t.t_80 == pytest.approx(79.2)
    assert t.t_95 == pytest.approx(94.05)


def test_assign_tier_boundaries():
    t = TierThresholds(t_50=0.5, t_80=0.8, t_95=0.95)
    assert assign_tier(0.1, t) == RiskTier.LOW
    assert assign_tier(0.5, t) == RiskTier.MEDIUM
    assert assign_tier(0.8, t) == RiskTier.HIGH
    assert assign_tier(0.95, t) == RiskTier.CRITICAL
    assert assign_tier(0.99, t) == RiskTier.CRITICAL


def test_tier_action_mapping_reuses_existing_decision_enum():
    from src.evaluation.decision_policy import TIER_ACTION
    assert TIER_ACTION[RiskTier.LOW] == Decision.ANSWER
    assert TIER_ACTION[RiskTier.MEDIUM] == Decision.REVIEW
    assert TIER_ACTION[RiskTier.HIGH] == Decision.ABSTAIN
    assert TIER_ACTION[RiskTier.CRITICAL] == Decision.ABSTAIN


def test_decide_all_deterministic():
    t = TierThresholds(t_50=0.5, t_80=0.8, t_95=0.95)
    scores = np.array([0.1, 0.6, 0.85, 0.99])
    tiers_a, actions_a = decide_all(scores, t)
    tiers_b, actions_b = decide_all(scores, t)
    assert tiers_a == tiers_b
    assert actions_a == actions_b


def test_sample_cost_ordering_matches_frozen_rationale():
    cm = DEFAULT_COST_MODEL
    # abstain_would_have_been_incorrect < abstain_would_have_been_correct < answer_incorrect
    assert cm["abstain_would_have_been_incorrect"] < cm["abstain_would_have_been_correct"] < cm["answer_incorrect"]
    assert sample_cost(Decision.ANSWER, 0, cm) == cm["answer_correct"]
    assert sample_cost(Decision.ANSWER, 1, cm) == cm["answer_incorrect"]
    assert sample_cost(Decision.ABSTAIN, 1, cm) == cm["abstain_would_have_been_incorrect"]
    assert sample_cost(Decision.ABSTAIN, 0, cm) == cm["abstain_would_have_been_correct"]


def test_decision_metrics_no_risk_policy_matches_raw_prevalence():
    y_fail = np.array([1, 0, 1, 0, 0])
    actions = [Decision.ANSWER] * 5
    m = decision_metrics(actions, y_fail, DEFAULT_COST_MODEL)
    assert m["unsafe_action_rate"] == pytest.approx(0.4)
    assert m["abstention_rate"] == 0.0
    assert m["utility_retention"] == 1.0


def test_decision_metrics_all_abstain_gives_full_failure_recall():
    y_fail = np.array([1, 0, 1, 0, 0])
    actions = [Decision.ABSTAIN] * 5
    m = decision_metrics(actions, y_fail, DEFAULT_COST_MODEL)
    assert m["failure_recall_among_abstained"] == 1.0
    assert m["utility_retention"] == 0.0
    assert m["unsafe_action_rate"] is None  # no ANSWER/REVIEW decisions made


def test_decision_metrics_false_abstention_rate_formula():
    y_fail = np.array([0, 0, 1])  # 2 non-failures, 1 failure, all abstained
    actions = [Decision.ABSTAIN] * 3
    m = decision_metrics(actions, y_fail, DEFAULT_COST_MODEL)
    assert m["false_abstention_rate"] == pytest.approx(2 / 3)


def test_review_counted_separately_from_answer_and_abstain():
    y_fail = np.array([0, 1, 0])
    actions = [Decision.ANSWER, Decision.REVIEW, Decision.ABSTAIN]
    m = decision_metrics(actions, y_fail, DEFAULT_COST_MODEL)
    assert m["n_answer"] == 1
    assert m["n_review"] == 1
    assert m["n_abstain"] == 1
    assert m["utility_retention"] == pytest.approx(2 / 3)  # answer+review attempted


def test_cost_model_frozen_file_matches_default():
    import json
    from pathlib import Path
    protocol36 = json.loads((Path(__file__).resolve().parents[2] / "configs" / "phase3_6_decision_recovery_protocol.json").read_text())
    assert protocol36["cost_model"]["base_costs"] == DEFAULT_COST_MODEL


def test_sensitivity_ratios_frozen():
    import json
    from pathlib import Path
    protocol36 = json.loads((Path(__file__).resolve().parents[2] / "configs" / "phase3_6_decision_recovery_protocol.json").read_text())
    assert protocol36["cost_model"]["sensitivity_analysis_ratios"] == [2.0, 5.0, 10.0]


def test_decision_policy_pipeline_thresholds_derived_from_regime2_only():
    from src.evaluation.protocol import Phase31Protocol
    from src.pipeline_builder import build_system
    from benchmarks.phase3_3_generalization import _fit_frozen_candidate, _reconstruct_regime2_with_confidences
    from benchmarks.phase3_6_complementarity import CANDIDATES, _fit_combined
    from benchmarks.phase3_6_decision_policy import _regime2_scores

    protocol = Phase31Protocol.load()
    protocol.regime_sizes = (300, 150, 150, 150, 150)
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=1)
    regime2 = _reconstruct_regime2_with_confidences(1, protocol, system)
    candidate_f = _fit_frozen_candidate(regime2, 1)
    combined = _fit_combined(regime2, candidate_f, 1)
    scores = _regime2_scores(regime2, candidate_f, combined)
    for name in CANDIDATES:
        assert len(scores[name]) == protocol.regime_sizes[2]
