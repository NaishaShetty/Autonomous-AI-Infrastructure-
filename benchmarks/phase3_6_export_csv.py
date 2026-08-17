"""Consolidates the four Phase 3.6 result JSONs into one per-seed CSV for
easy inspection/spreadsheet use. Reads already-written results; computes
nothing new.

Run: python benchmarks/phase3_6_export_csv.py (after the four phase3_6_*
scripts that produce complementarity.json / decision_policy.json /
diagnosis.json / recovery.json)
Writes: experiments/results/phase3_6/per_seed_results.csv
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RESULTS_DIR = ROOT / "experiments" / "results" / "phase3_6"


def main() -> None:
    comp = json.loads((RESULTS_DIR / "complementarity.json").read_text())
    decision = json.loads((RESULTS_DIR / "decision_policy.json").read_text())
    diag = json.loads((RESULTS_DIR / "diagnosis.json").read_text())
    recov = json.loads((RESULTS_DIR / "recovery.json").read_text())

    decision_by_seed = {row["seed"]: row for row in decision["per_seed"]}
    diag_by_seed = {row["seed"]: row for row in diag["per_seed"]}

    with (RESULTS_DIR / "per_seed_results.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "seed", "auroc_B", "auroc_F", "auroc_BF",
            "unsafe_rate_B_ratio5", "unsafe_rate_F_ratio5", "unsafe_rate_BF_ratio5", "unsafe_rate_no_risk_ratio5",
            "abstention_rate_B", "abstention_rate_F", "abstention_rate_BF",
            "diagnosis_accuracy", "diagnosis_macro_f1",
        ])
        for row in comp["per_seed"]:
            seed = row["seed"]
            d = decision_by_seed[seed]["policy_results"]
            g = diag_by_seed[seed]
            writer.writerow([
                seed,
                row["results"]["B_calibrated_confidence"]["auroc"],
                row["results"]["F_supervised_failure_risk"]["auroc"],
                row["results"]["BF_combined"]["auroc"],
                d["B_calibrated_confidence"]["metrics_by_cost_ratio"]["5.0"]["unsafe_action_rate"],
                d["F_supervised_failure_risk"]["metrics_by_cost_ratio"]["5.0"]["unsafe_action_rate"],
                d["BF_combined"]["metrics_by_cost_ratio"]["5.0"]["unsafe_action_rate"],
                d["no_risk_policy"]["metrics_by_cost_ratio"]["5.0"]["unsafe_action_rate"],
                d["B_calibrated_confidence"]["metrics_by_cost_ratio"]["5.0"]["abstention_rate"],
                d["F_supervised_failure_risk"]["metrics_by_cost_ratio"]["5.0"]["abstention_rate"],
                d["BF_combined"]["metrics_by_cost_ratio"]["5.0"]["abstention_rate"],
                g["accuracy"],
                g["macro_f1"],
            ])

    print(f"Wrote {RESULTS_DIR / 'per_seed_results.csv'}")


if __name__ == "__main__":
    main()
