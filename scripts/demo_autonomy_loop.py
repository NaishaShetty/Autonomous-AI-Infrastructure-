"""Phase 6 -- a small, honest, real CLI demo of the autonomy pipeline.

Drives ONE real episode through ``AutonomyPipeline.run_workload()``
(``src/phase4/pipeline.py``) against this project's own controlled
subprocess runtime, and prints each stage's real output as it happens:
observe -> detect -> predict -> decide/abstain -> diagnose -> plan ->
safety-gate -> execute -> independently validate -> learn.

This is a demonstration aid, not a new experiment: it does not change any
frozen result, does not tune any threshold, and does not cherry-pick a
scenario that is guaranteed to "succeed". The scenario mode is a
deliberately failing one (``mode="fail"``, matching the pattern used by
``scripts/run_phase4_5_pipeline_demo.py``'s own ``recurring_failure``
episodes), so this script's own printed final_state is whatever the
pipeline actually produces for that scenario -- if that is
``NOT_RECOVERED`` or ``ABSTAINED`` rather than ``RECOVERED``, that is
printed honestly, not hidden.

Usage:
    python scripts/demo_autonomy_loop.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.phase4.controlled_runtime import ControlledRuntime, RuntimeConfig  # noqa: E402
from src.phase4.observability import PersistentEventStore  # noqa: E402
from src.phase4.pipeline import AutonomyPipeline  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        store = PersistentEventStore(Path(tmp) / "demo_events.sqlite")
        runtime = ControlledRuntime(
            store, RuntimeConfig(timeout_seconds=0.3, telemetry_interval_seconds=0.02)
        )
        pipeline = AutonomyPipeline(runtime)

        workload_id = "demo-workload-01"
        params = {"mode": "fail"}

        print(f"[observe]   workload_id={workload_id} params={params}")
        result = pipeline.run_workload("fail", params, workload_id=workload_id)

        print(f"[state]     {' -> '.join(result.state_history)}")
        print(f"[predict]   prediction_score={result.prediction_score}")
        decision_value = result.decision.decision if result.decision else None
        print(f"[decide]    decision={decision_value}")
        if result.diagnosis is not None:
            print(
                f"[diagnose]  primary_hypothesis={result.diagnosis.primary_hypothesis.name} "
                f"confidence={result.diagnosis.confidence} "
                f"(class-matching only -- no independent causal ground truth)"
            )
        else:
            print("[diagnose]  no diagnosis produced")
        action_value = result.action.action_type if result.action else None
        print(f"[plan]      action={action_value}")
        print(
            f"[safety]    authorized={result.safety_authorized} reason={result.safety_reason}"
        )
        if result.execution is not None:
            run_status = getattr(result.execution.run_result, "status", None)
            exit_code = getattr(result.execution.run_result, "run_id", None)
            print(
                f"[execute]   real controlled-runtime execution: action_type={result.execution.action_type} "
                f"executed={result.execution.executed} run_status={run_status} "
                f"run_id={exit_code} note={result.execution.note}"
            )
        else:
            print("[execute]   not executed (safety gate rejected or decision abstained)")
        validation_value = result.validation.status if result.validation else None
        print(f"[validate]  independently-derived status={validation_value}")
        if result.learning is not None:
            print(
                f"[learn]     experience recorded={result.learning.recorded} "
                f"memory_version={pipeline.memory.memory_version}"
            )
        else:
            print("[learn]     no learning update produced")
        print(f"[final]     final_state={result.final_state}")

        store.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
