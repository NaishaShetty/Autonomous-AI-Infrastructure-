"""Phase 4.5b -- unit coverage for the real AI/ML agent correctness task
and its genuine self-consistency uncertainty signal (src/phase4/agent_task.py).
"""
from src.phase4.agent_task import (
    agent_sample,
    error_probability,
    generate_task,
    run_self_consistency,
)


def test_generate_task_is_deterministic_given_seed_and_has_a_real_arithmetic_oracle():
    a = generate_task(42)
    b = generate_task(42)
    assert a == b
    # The oracle is real arithmetic, not a lookup table -- replaying the
    # instance's own recorded ops from its own recorded starting value
    # must reproduce the recorded correct_answer exactly.
    value = a.initial_value
    for op, operand in a.ops:
        if op == "+":
            value += operand
        elif op == "-":
            value -= operand
        else:
            value *= operand
    assert value == a.correct_answer


def test_generate_task_varies_with_seed():
    tasks = {generate_task(s).expression for s in range(30)}
    assert len(tasks) > 1


def test_agent_sample_never_reads_the_ground_truth_directly():
    """A real independent solver derives its answer from the instance's
    own operation trace, never from `correct_answer` -- verified by
    corrupting `correct_answer` on a copy and confirming samples are
    unaffected (they are computed from `initial_value`/`ops` alone)."""
    import dataclasses

    instance = generate_task(7)
    tampered = dataclasses.replace(instance, correct_answer=-999999)
    samples_real = [agent_sample(instance, i) for i in range(20)]
    samples_tampered = [agent_sample(tampered, i) for i in range(20)]
    assert samples_real == samples_tampered


def test_error_probability_increases_with_difficulty_and_is_bounded():
    rates = [error_probability(d) for d in range(2, 10)]
    assert all(0.0 <= r <= 0.9 for r in rates)
    assert rates == sorted(rates)  # monotonically non-decreasing, fixed formula


def test_run_self_consistency_majority_vote_and_agreement_rate_are_consistent():
    instance = generate_task(1)
    result = run_self_consistency(instance, n_samples=9, base_seed=1)
    assert len(result.samples) == 9
    majority_count = sum(1 for s in result.samples if s == result.majority_answer)
    assert result.agreement_rate == majority_count / 9
    assert result.is_correct == (result.majority_answer == instance.correct_answer)


def test_more_samples_measurably_improves_majority_vote_accuracy():
    """The real, measured claim this whole recovery mechanism rests on:
    more independent samples improve accuracy via majority-vote averaging.
    Not asserted to hit an exact number -- just the real, expected
    direction, over enough seeds to not be noise."""
    n = 400
    correct_1 = sum(run_self_consistency(generate_task(s), n_samples=1, base_seed=s).is_correct for s in range(n))
    correct_5 = sum(run_self_consistency(generate_task(s), n_samples=5, base_seed=s).is_correct for s in range(n))
    assert correct_5 > correct_1, f"expected majority-vote-at-5 to beat single-sample accuracy: {correct_5} vs {correct_1} (n={n})"


def test_agreement_rate_is_a_real_usable_uncertainty_signal():
    """High agreement must correlate with correctness for this to be a
    genuine, non-fabricated uncertainty signal (the whole basis of
    AgentUncertaintyPredictor)."""
    n = 400
    high, low = [], []
    for s in range(n):
        r = run_self_consistency(generate_task(s), n_samples=5, base_seed=s)
        (high if r.agreement_rate >= 0.8 else low).append(r.is_correct)
    assert high and low, "expected both high- and low-agreement cases in this sample"
    high_acc = sum(high) / len(high)
    low_acc = sum(low) / len(low)
    assert high_acc > low_acc, f"expected high-agreement accuracy ({high_acc}) > low-agreement accuracy ({low_acc})"
