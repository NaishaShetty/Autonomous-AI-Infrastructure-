import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments/results/v1_1/temporal_robustness"
EXPERIMENTS = [
    "3_3_a_temporal_validation/phase33_a_temporal_validation_model_selection",
    "3_3_b_contextual_features",
    "3_3_c_constrained_nonlinear",
    "3_3_d_drift_aware",
]


def test_four_experiments_are_independent_and_immutable():
    ids = set()
    for rel in EXPERIMENTS:
        p = BASE / rel
        protocol = json.loads((p / "protocol.json").read_text())
        summary = json.loads((p / "summary.json").read_text())
        marker = json.loads((p / ".finalized").read_text())
        ids.add(protocol["experiment_id"])
        assert summary["decision"] in {"ACCEPT", "REJECT", "HOLD", "INTERESTING FINDING"}
        assert len(summary["results"]) >= 2
        for name, expected in marker.items():
            assert hashlib.sha256((p / name).read_bytes()).hexdigest() == expected
    assert len(ids) == 4


def test_all_experiments_share_data_and_temporal_boundaries():
    for rel in EXPERIMENTS:
        p = BASE / rel
        protocol = json.loads((p / "protocol.json").read_text())
        assert "Alibaba GPU2020" in protocol["dataset"] or "alibaba_gpu2020" in protocol["dataset"]
        assert "temporal" in protocol["evaluation"].lower()


def test_decisions_preserve_no_automatic_integration():
    decisions = [json.loads((BASE / rel / "summary.json").read_text())["decision"] for rel in EXPERIMENTS]
    assert decisions == ["HOLD", "REJECT", "REJECT", "REJECT"]
