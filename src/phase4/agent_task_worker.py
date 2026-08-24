"""Phase 4.5b -- standalone subprocess entrypoint for `AgentTaskRuntime`.

Kept as a real, separately-invoked subprocess (mirroring
`controlled_runtime.py`'s discipline of real subprocess execution, never an
in-process shortcut) rather than importing `agent_task.py` in-process, so
the same "real, isolated execution" contract applies to agent-task
evaluation as it does to every other Phase 4 workload.

Usage: python3 agent_task_worker.py <seed> <min_difficulty> <max_difficulty> <n_samples> <base_seed>
Prints exactly one JSON object to stdout.
"""
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.phase4.agent_task import generate_task, run_self_consistency  # noqa: E402


def main() -> None:
    seed = int(sys.argv[1])
    min_difficulty = int(sys.argv[2])
    max_difficulty = int(sys.argv[3])
    n_samples = int(sys.argv[4])
    base_seed = int(sys.argv[5])

    instance = generate_task(seed, min_difficulty=min_difficulty, max_difficulty=max_difficulty)
    result = run_self_consistency(instance, n_samples=n_samples, base_seed=base_seed)

    print(json.dumps({
        "task_id": instance.task_id,
        "seed": instance.seed,
        "difficulty": instance.difficulty,
        "expression": instance.expression,
        "correct_answer": instance.correct_answer,
        "n_samples": n_samples,
        "samples": list(result.samples),
        "majority_answer": result.majority_answer,
        "agreement_rate": result.agreement_rate,
        "is_correct": result.is_correct,
    }))


if __name__ == "__main__":
    main()
