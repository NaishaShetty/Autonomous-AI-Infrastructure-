import pytest

from src.decision.policy import DecisionMode, DecisionPolicy, PolicyConfig
from src.schema.events import Decision


def test_policy_config_validates_threshold_ordering():
    PolicyConfig(answer_threshold=0.7, abstain_threshold=0.4)  # ok
    with pytest.raises(ValueError):
        PolicyConfig(answer_threshold=0.3, abstain_threshold=0.5)


def test_policy_config_validates_risk_weight_range():
    with pytest.raises(ValueError):
        PolicyConfig(risk_weight=1.5)


def test_confidence_only_mode_ignores_risk():
    policy = DecisionPolicy(PolicyConfig(answer_threshold=0.7, abstain_threshold=0.4))
    decision, score = policy.decide(confidence=0.9, risk=1.0, mode=DecisionMode.CONFIDENCE_ONLY)
    assert decision == Decision.ANSWER
    assert score == 0.9


def test_confidence_only_requires_confidence():
    policy = DecisionPolicy()
    with pytest.raises(ValueError):
        policy.fuse(confidence=None, risk=0.5, mode=DecisionMode.CONFIDENCE_ONLY)


def test_risk_only_mode_ignores_confidence():
    policy = DecisionPolicy(PolicyConfig(answer_threshold=0.7, abstain_threshold=0.4))
    decision, score = policy.decide(confidence=0.1, risk=0.05, mode=DecisionMode.RISK_ONLY)
    assert decision == Decision.ANSWER  # low risk -> high trust score, regardless of confidence
    assert score == pytest.approx(0.95)


def test_combined_mode_discounts_confidence_by_risk():
    policy = DecisionPolicy(PolicyConfig(risk_weight=0.5))
    score = policy.fuse(confidence=0.8, risk=0.4, mode=DecisionMode.COMBINED)
    assert score == pytest.approx(0.6)  # 0.8 - 0.5*0.4


def test_decide_thresholds_produce_all_three_decisions():
    policy = DecisionPolicy(PolicyConfig(answer_threshold=0.7, abstain_threshold=0.4, risk_weight=0.0))
    assert policy.decide(confidence=0.9, risk=0.0, mode=DecisionMode.CONFIDENCE_ONLY)[0] == Decision.ANSWER
    assert policy.decide(confidence=0.55, risk=0.0, mode=DecisionMode.CONFIDENCE_ONLY)[0] == Decision.REVIEW
    assert policy.decide(confidence=0.1, risk=0.0, mode=DecisionMode.CONFIDENCE_ONLY)[0] == Decision.ABSTAIN


def test_fused_score_always_in_unit_interval():
    policy = DecisionPolicy(PolicyConfig(risk_weight=1.0))
    # confidence low, risk high -> would go negative without clipping
    score = policy.fuse(confidence=0.1, risk=0.9, mode=DecisionMode.COMBINED)
    assert 0.0 <= score <= 1.0
