"""Post-P5 remediation, Step 6 (P5-W1, P5-W2) -- repeated-incident memory
evaluation. Implements exactly the protocol pre-registered in
``experiments/results/post_p5_remediation/<TIMESTAMP>/protocol/P5_STEP6_MEMORY_PROTOCOL.md``.

Usage:
    python scripts/run_p5_step6_memory_repeated_incident.py <run_dir>
"""
from __future__ import annotations

import json
import socket
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.phase4.controlled_runtime import ControlledRuntime, RuntimeConfig
from src.phase4.memory import FailureMemoryStore
from src.phase4.observability import PersistentEventStore
from src.phase4.pipeline import AutonomyPipeline

N_EPISODES = 6
WORKLOAD_ID = "post-p5-step6-incident-resource-unavailable"
ENVIRONMENT_ID = "post-p5-step6-environment"


def _hold_port() -> tuple[socket.socket, int]:
    """A real socket held in THIS process, independent of any
    ControlledRuntime instance -- models a genuinely externally-owned,
    still-down dependency that outlives every simulated 'restart'."""
    holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    holder.bind(("127.0.0.1", 0))
    holder.listen(1)
    port = holder.getsockname()[1]
    return holder, port


def _run_episode(memory_path, port, episode_index, tmp_dir):
    store = PersistentEventStore(Path(tmp_dir) / f"events-{episode_index}.sqlite")
    runtime = ControlledRuntime(store, RuntimeConfig(timeout_seconds=2.0, telemetry_interval_seconds=0.01, environment_id=ENVIRONMENT_ID))
    memory = FailureMemoryStore(path=memory_path)  # path=None (":memory:") for the OFF condition -- fresh, empty, every episode
    pipeline = AutonomyPipeline(runtime, memory=memory)
    result = pipeline.run_workload("resource_unavailable", {"mode": "resource_unavailable", "port": port}, workload_id=WORKLOAD_ID)
    outcome = {
        "episode": episode_index,
        "action": result.action.action_type if result.action else None,
        "validation_status": result.validation.status if result.validation else None,
        "memory_version_after": memory.memory_version,
    }
    memory.close()
    store.close()
    return outcome


def run_condition(condition_name, memory_path) -> list[dict]:
    holder, port = _hold_port()
    episodes = []
    try:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            for i in range(N_EPISODES):
                outcome = _run_episode(memory_path, port, i, tmp_dir)
                episodes.append(outcome)
                print(f"[{condition_name}] episode {i}: action={outcome['action']}, validation={outcome['validation_status']}")
    finally:
        holder.close()
    return episodes


def restart_persistence_check(run_dir: Path) -> dict:
    """P5-W2 standalone check: write, fully destroy every Python object,
    reopen the same file, verify retrieval/versioning/isolation."""
    db_path = run_dir / "raw" / "step6_persistence_check.sqlite"
    if db_path.exists():
        db_path.unlink()

    store1 = FailureMemoryStore(path=db_path)
    record = store1.add(
        workload_id="persistence-check-workload", environment_id="persistence-check-env",
        failure_class="RESOURCE_UNAVAILABLE", root_cause="TEST_ROOT_CAUSE", diagnosis_confidence="HIGH",
        source_run_id="run-1", source_diagnosis_id="diag-1", action_taken="reconfigure",
        validated_outcome="RECOVERED", recorded_at="2026-01-01T00:00:00Z", provenance={"source": "step6-check"},
    )
    version_before = store1.memory_version
    store1.close()
    del store1  # fully destroy the Python object; only the file remains

    store2 = FailureMemoryStore(path=db_path)  # simulated restart: reopen the same file
    version_after_restart = store2.memory_version
    retrieved = store2.retrieve(
        workload_id="persistence-check-workload", environment_id="persistence-check-env",
        failure_class="RESOURCE_UNAVAILABLE", exclude_run_id="run-other", at_or_before="2026-01-02T00:00:00Z",
    )
    cross_scope_retrieved = store2.retrieve(
        workload_id="a-different-workload", environment_id="persistence-check-env",
        failure_class="RESOURCE_UNAVAILABLE", exclude_run_id="run-other", at_or_before="2026-01-02T00:00:00Z",
    )
    store2.close()

    return {
        "record_written": record.memory_id, "memory_version_before_restart": version_before,
        "memory_version_after_restart": version_after_restart,
        "versions_match": version_before == version_after_restart,
        "retrieved_after_restart_count": len(retrieved),
        "retrieved_correctly": len(retrieved) == 1 and retrieved[0].record.memory_id == record.memory_id,
        "cross_scope_query_correctly_returned_nothing": len(cross_scope_retrieved) == 0,
    }


def main(run_dir: Path) -> None:
    (run_dir / "raw").mkdir(parents=True, exist_ok=True)

    print("=== Memory ON (file-persisted across simulated restarts) ===")
    on_db_path = run_dir / "raw" / "step6_memory_on.sqlite"
    if on_db_path.exists():
        on_db_path.unlink()
    on_episodes = run_condition("ON", on_db_path)

    print("=== Memory OFF (fresh :memory: store every episode) ===")
    off_episodes = run_condition("OFF", None)

    print("=== Restart/persistence/isolation check ===")
    persistence = restart_persistence_check(run_dir)
    print(persistence)

    on_actions = [e["action"] for e in on_episodes]
    off_actions = [e["action"] for e in off_episodes]
    first_change_on = next((i for i, a in enumerate(on_actions) if a != on_actions[0]), None)
    first_change_off = next((i for i, a in enumerate(off_actions) if a != off_actions[0]), None)

    results = {
        "workload_id": WORKLOAD_ID, "n_episodes": N_EPISODES,
        "memory_on": {"episodes": on_episodes, "actions": on_actions, "first_decision_change_episode": first_change_on},
        "memory_off": {"episodes": off_episodes, "actions": off_actions, "first_decision_change_episode": first_change_off},
        "restart_persistence_check": persistence,
        "verdict": {
            "memory_on_decision_changed": first_change_on is not None,
            "memory_off_decision_changed": first_change_off is not None,
            "hypothesis_confirmed": (first_change_on == 2) and (first_change_off is None),
        },
    }
    (run_dir / "raw" / "p5_step6_memory_results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print("verdict:", results["verdict"])
    print("wrote raw/p5_step6_memory_results.json")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
