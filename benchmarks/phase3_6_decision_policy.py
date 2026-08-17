"""Phase 3.6.2 (decision thresholds/cost model) and 3.6.4 (abstention).

Derives risk-tier thresholds from regime-2 data ONLY (never test), applies
them to the held-out test stream, and reports decision metrics (unsafe
action rate, abstention rate, expected cost, utility retention, ...) for
four policies: no-risk-policy (always ANSWER), B-based, F-based, and
BF_combined-based. Also reports abstention safety/utility at the frozen
Phase 3.1 coverage points by reusing ``precision_recall_at_coverage``
directly.

Reuses ``benchmarks.phase3_6_complementarity``'s fitting/scoring
functions so B/F/BF_combined are scored identically to 3.6.1 (same
fitted objects, same regime-2 data) -- not refit or rescored differently
here.

Run: python benchmarks/phase3_6_decision_policy.py
Writes: experiments/results/phase3_6/decision_policy.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.decision_policy import (  # noqa: E402
    DEFAULT_COST_MODEL,
    TierThresholds,
    decide_all,
    decision_metrics,
)
from src.evaluation.metrics import precision_recall_at_coverage  # noqa: E402
from src.evaluation.protocol import Phase31Protocol  # noqa: E402
from src.pipeline_builder import build_system  # noqa: E402
from src.schema.events import Decision  # noqa: E402

from benchmarks.phase3_1_evaluate import _t_interval  # noqa: E402
from benchmarks.phase3_3_generalization import (  # noqa: E402
    _fit_frozen_candidate,
    _reconstruct_regime2_with_confidences,
)
from benchmarks.phase3_6_complementarity import CANDIDATES, _compute_test_arrays, _fit_combined  # noqa: E402

RESULTS_DIR = ROOT / "experiments" / "results" / "phase3_6"
POLICIES = ["no_risk_policy"] + CANDIDATES
SENSITIVITY_RATIOS = [2.0, 5.0, 10.0]


def _regime2_scores(regime2: dict, candidate_f, combined) -> dict:
    b_scores = np.array([1.0 - c for c in regime2["regime2_confidences"]])
    f_scores = np.array([candidate_f.risk(ctx, conf) for ctx, conf in zip(regime2["regime2_contexts"], regime2["regime2_confidences"])])
    bf_scores = np.array([combined.risk(b, f) for b, f in zip(b_scores, f_scores)])
    return {"B_calibrated_confidence": b_scores, "F_supervised_failure_risk": f_scores, "BF_combined": bf_scores}


def run_one_seed(seed: int, protocol: Phase31Protocol) -> dict:
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=seed)
    regime2 = _reconstruct_regime2_with_confidences(seed, protocol, system)
    candidate_f = _fit_frozen_candidate(regime2, seed)
    combined = _fit_combined(regime2, candidate_f, seed)

    regime2_scores = _regime2_scores(regime2, candidate_f, combined)
    thresholds = {name: TierThresholds.derive(regime2_scores[name]) for name in CANDIDATES}

    test_arrays = _compute_test_arrays(system, candidate_f, combined)
    y_fail = test_arrays["y_fail"]

    policy_results = {}
    for name in CANDIDATES:
        tiers, actions = decide_all(test_arrays["scores"][name], thresholds[name])
        metrics = {ratio: decision_metrics(actions, y_fail, _scaled_cost_model(ratio)) for ratio in SENSITIVITY_RATIOS}
        policy_results[name] = {
            "thresholds": thresholds[name].__dict__,
            "tier_counts": {t.value: sum(1 for x in tiers if x == t) for t in set(tiers)},
            "metrics_by_cost_ratio": metrics,
        }

    no_risk_actions = [Decision.ANSWER] * len(y_fail)
    policy_results["no_risk_policy"] = {
        "thresholds": None,
        "tier_counts": None,
        "metrics_by_cost_ratio": {ratio: decision_metrics(no_risk_actions, y_fail, _scaled_cost_model(ratio)) for ratio in SENSITIVITY_RATIOS},
    }

    abstention = {}
    for name in CANDIDATES:
        score = test_arrays["scores"][name]
        abstention[name] = [precision_recall_at_coverage(y_fail, score, c) for c in protocol.coverage_operating_points]

    return {"seed": seed, "n_test_samples": int(len(y_fail)), "policy_results": policy_results, "abstention": abstention}


def _scaled_cost_model(ratio: float) -> dict:
    cm = dict(DEFAULT_COST_MODEL)
    cm["answer_incorrect"] = ratio * cm["abstain_would_have_been_correct"]
    cm["review_incorrect"] = cm["answer_incorrect"] + cm["review_correct"]
    return cm


def aggregate_across_seeds(per_seed: list[dict], protocol: Phase31Protocol) -> dict:
    agg = {"policies": {}, "abstention": {}}
    metric_names = [
        "unsafe_action_rate", "accepted_task_success_rate", "abstention_rate", "review_rate",
        "false_abstention_rate", "failure_recall_among_abstained", "expected_decision_cost", "utility_retention",
    ]
    for policy in POLICIES:
        agg["policies"][policy] = {}
        for ratio in SENSITIVITY_RATIOS:
            agg["policies"][policy][ratio] = {}
            for m in metric_names:
                values = [row["policy_results"][policy]["metrics_by_cost_ratio"][ratio][m] for row in per_seed]
                values = [v for v in values if v is not None]
                agg["policies"][policy][ratio][m] = _t_interval(values, 0.95) if values else {"mean": None, "n": 0}

    for name in CANDIDATES:
        agg["abstention"][name] = []
        for i, cov in enumerate(protocol.coverage_operating_points):
            precisions = [row["abstention"][name][i]["precision"] for row in per_seed]
            recalls = [row["abstention"][name][i]["recall"] for row in per_seed]
            agg["abstention"][name].append(
                {"coverage": cov, "precision": _t_interval(precisions, 0.95), "recall": _t_interval(recalls, 0.95)}
            )
    return agg


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    protocol = Phase31Protocol.load()

    per_seed = [run_one_seed(seed, protocol) for seed in protocol.seeds]
    aggregate = aggregate_across_seeds(per_seed, protocol)

    output = {
        "meta": {"protocol": protocol.raw, "cost_model_base": DEFAULT_COST_MODEL, "sensitivity_ratios": SENSITIVITY_RATIOS},
        "per_seed": per_seed,
        "aggregate": aggregate,
    }
    (RESULTS_DIR / "decision_policy.json").write_text(json.dumps(output, indent=2))

    print("Phase 3.6.2/3.6.4 decision policy (base ratio=5.0)\n")
    print(f"{'Policy':<28} {'Unsafe rate':>12} {'Abstain rate':>13} {'Exp. cost':>10} {'Utility ret.':>13}")
    for policy in POLICIES:
        m = aggregate["policies"][policy][5.0]
        u = m["unsafe_action_rate"]["mean"]
        ab = m["abstention_rate"]["mean"]
        c = m["expected_decision_cost"]["mean"]
        ut = m["utility_retention"]["mean"]
        print(f"{policy:<28} {u if u is None else round(u,4):>12} {ab if ab is None else round(ab,4):>13} {c if c is None else round(c,4):>10} {ut if ut is None else round(ut,4):>13}")

    print(f"\nWrote results to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
