"""Run process-A/process-B restart validation with independent interpreters."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="alibaba-restart-") as tmp:
        tmp_path = Path(tmp)
        db = tmp_path / "restart.db"
        env = {**os.environ, "DATABASE_URL": f"sqlite:///{db.as_posix()}", "PYTHONPATH": str(ROOT)}
        outputs = []
        for mode in ("A", "B"):
            path = tmp_path / f"process_{mode}.json"
            subprocess.run([sys.executable, str(ROOT / "scripts/alibaba_restart_worker.py"), mode, str(path)], cwd=ROOT, env=env, check=True)
            outputs.append(json.loads(path.read_text()))
        a, b = outputs
        assert a["artifact_hash"] == b["artifact_hash"]
        assert a["model_version"] == b["model_version"]
        assert a["calibrator_version"] == b["calibrator_version"]
        assert a["model_predicted_label"] == b["model_predicted_label"]
        assert a["model_predicted_proba"] == b["model_predicted_proba"]
        assert b["memory_fitted"] is True
        assert b["memory_version"] >= 1
        result = {"process_a": a, "process_b": b, "same_artifact_output": True, "persisted_memory_reloaded": True, "process_b_retrieved_experiences": b["retrieved_experiences"], "runtime_training": False}
        out = ROOT / "experiments/results/alibaba_closed_loop_v1/logs/restart_validation.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
