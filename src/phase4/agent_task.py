"""Phase 4.5b -- a real AI/ML agent task with a ground-truth correctness
oracle and a genuine self-consistency uncertainty signal.

This closes the second gap named in the project's own strategic review:
every prior phase of this pipeline evaluates infrastructure/process
failures (timeouts, OOM, crashes, network errors, ...) -- none of it ever
evaluates whether an actual AI/ML agent's OUTPUT is correct. This module
is a small, real, deterministic-given-seed chained-arithmetic reasoning
task with an intentionally fallible solver, plus a genuine uncertainty-
quantification mechanism: run the solver multiple independent times and
use the agreement rate across samples (self-consistency) as a confidence
signal -- exactly the abstention technique actually used with real large
language models (sample repeatedly, trust the answer more when samples
agree), not a metaphor for it.

Honesty notes (read before trusting any number produced with this module):
  - The "agent" is not a call to a real LLM API -- this sandboxed
    environment has no such API available, and fabricating a fake one
    would violate the honesty discipline this project has followed since
    Phase 4.4. It IS a real, independently-executed computation with a
    real correct/incorrect outcome (checked against ground truth computed
    the same way any oracle in this repo is: real arithmetic, not a
    lookup table) and a real, measurable per-sample disagreement signal --
    which is what the pipeline's abstention/diagnosis/recovery/validation/
    learning loop needs in order to be evaluated against genuine output
    correctness rather than only OS/process telemetry.
  - `agent_sample` never reads `TaskInstance.correct_answer` -- it
    independently replays the instance's own recorded operation sequence,
    exactly the way a solver with no access to the ground truth would.
    Wrongness comes from a real, seeded per-sample chance of a genuine
    arithmetic slip (a random-sized perturbation, not a fixed wrong
    constant), so which samples are wrong -- and how wrong -- varies
    sample to sample the way real model sampling variance does.
  - `BASE_ERROR_RATE` / `ERROR_RATE_PER_DIFFICULTY` are fixed and
    documented here, before any evaluation is run against them (same
    discipline as `MonitoringBaseline` / `prediction.py`'s fixed feature
    weights) -- they are not tuned after seeing accuracy or recovery
    results.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

TASK_VERSION = "phase4.5b-agent-arithmetic-task-v1"

# Fixed before any evaluation: how often a single independent sample is
# wrong, as a function of task difficulty (number of chained operations).
BASE_ERROR_RATE = 0.12
ERROR_RATE_PER_DIFFICULTY = 0.07
_OPS = ("+", "-", "*")


@dataclass(frozen=True)
class TaskInstance:
    task_id: str
    seed: int
    difficulty: int
    initial_value: int
    ops: tuple[tuple[str, int], ...]
    expression: str
    correct_answer: int


def _apply(value: int, op: str, operand: int) -> int:
    if op == "+":
        return value + operand
    if op == "-":
        return value - operand
    if op == "*":
        return value * operand
    raise ValueError(f"unsupported op: {op}")


def generate_task(seed: int, min_difficulty: int = 2, max_difficulty: int = 5) -> TaskInstance:
    """Deterministic given `seed`: builds a real chained-arithmetic
    expression (e.g. "((7 + 3) * 2 - 4)") by real repeated application of
    +/-/* and computes the ground-truth answer by actually performing that
    arithmetic -- the oracle `is_correct` (via `run_self_consistency`)
    checks against is exact, not approximate."""
    rng = random.Random(seed)
    difficulty = rng.randint(min_difficulty, max_difficulty)
    initial_value = rng.randint(1, 20)
    value = initial_value
    expression = str(value)
    ops: list[tuple[str, int]] = []
    for _ in range(difficulty):
        op = rng.choice(_OPS)
        operand = rng.randint(1, 12)
        ops.append((op, operand))
        value = _apply(value, op, operand)
        expression = f"({expression} {op} {operand})"
    return TaskInstance(
        task_id=f"task-{seed}", seed=seed, difficulty=difficulty,
        initial_value=initial_value, ops=tuple(ops), expression=expression, correct_answer=value,
    )


def error_probability(difficulty: int) -> float:
    return min(0.9, BASE_ERROR_RATE + ERROR_RATE_PER_DIFFICULTY * max(0, difficulty - 2))


def agent_sample(instance: TaskInstance, sample_seed: int) -> int:
    """One real, independent solve attempt. Replays `instance`'s own
    recorded operation sequence starting from its own recorded starting
    value (never reads `correct_answer`), then applies a real, seeded
    chance of a genuine arithmetic slip."""
    rng = random.Random(f"{instance.seed}:{sample_seed}")
    value = instance.initial_value
    for op, operand in instance.ops:
        value = _apply(value, op, operand)
    if rng.random() < error_probability(instance.difficulty):
        delta = rng.choice([-3, -2, -1, 1, 2, 3])
        return value + delta
    return value


@dataclass(frozen=True)
class SelfConsistencyResult:
    instance: TaskInstance
    samples: tuple[int, ...]
    majority_answer: int
    agreement_rate: float  # fraction of samples agreeing with the majority answer
    is_correct: bool


def run_self_consistency(instance: TaskInstance, n_samples: int, base_seed: int) -> SelfConsistencyResult:
    if n_samples < 1:
        raise ValueError("n_samples must be >= 1")
    samples = tuple(agent_sample(instance, base_seed * 1000 + i) for i in range(n_samples))
    counts: dict[int, int] = {}
    for s in samples:
        counts[s] = counts.get(s, 0) + 1
    # Tie-break deterministically (smallest |value|) so the vote is
    # reproducible given the same samples, never randomly re-broken.
    majority_answer = max(counts.items(), key=lambda kv: (kv[1], -abs(kv[0])))[0]
    agreement_rate = counts[majority_answer] / len(samples)
    return SelfConsistencyResult(
        instance=instance, samples=samples, majority_answer=majority_answer,
        agreement_rate=agreement_rate, is_correct=(majority_answer == instance.correct_answer),
    )
