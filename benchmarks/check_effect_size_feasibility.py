"""Feasibility gate: run this BEFORE freezing a minimum-effect-size
threshold for any future recovery-learning phase (4.5+).

Usage:
    python benchmarks/check_effect_size_feasibility.py \\
        --baseline-rate 0.54 --oracle-rate 0.60 --required-effect 0.15

Exits non-zero if the threshold is not feasible, so it can be used as a
CI-style go/no-go check in a protocol-freezing script, not just read by
eye. See src/recovery/feasibility.py for the full rationale: Phase 4.3 and
4.4 both froze a 0.15 minimum effect without running this check first, and
in both cases the baseline was already within 0.03-0.06 of the oracle
bound -- the threshold was unreachable before a single episode was
generated. This script exists so that mistake has to be made on purpose
from here on, not by omission.

Also supports re-checking any already-frozen phase's numbers directly from
its results.json, for retrospective auditing:
    python benchmarks/check_effect_size_feasibility.py --from-results experiments/results/phase4_3/results.json \\
        --baseline-key baseline_fixed_priority --required-effect 0.15
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.recovery.feasibility import check_feasibility  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--baseline-rate", type=float, help="strongest non-learned baseline's validated success rate")
    parser.add_argument("--oracle-rate", type=float, help="oracle reference bound's validated success rate")
    parser.add_argument("--required-effect", type=float, required=True, help="pre-registered minimum meaningful effect size")
    parser.add_argument("--from-results", type=Path, help="path to a phase results.json to read baseline/oracle rates from instead of passing them directly")
    parser.add_argument("--baseline-key", type=str, help="aggregates key of the baseline policy when using --from-results")
    parser.add_argument("--oracle-key", type=str, default="oracle_reference_bound", help="aggregates key of the oracle policy when using --from-results")
    args = parser.parse_args()

    if args.from_results:
        if not args.baseline_key:
            parser.error("--baseline-key is required with --from-results")
        data = json.loads(args.from_results.read_text())
        agg = data["test_result"]["aggregates"]
        baseline_rate = agg[args.baseline_key]["validated_recovery_success_rate"]
        oracle_rate = agg[args.oracle_key]["validated_recovery_success_rate"]
    else:
        if args.baseline_rate is None or args.oracle_rate is None:
            parser.error("either --from-results, or both --baseline-rate and --oracle-rate, are required")
        baseline_rate, oracle_rate = args.baseline_rate, args.oracle_rate

    result = check_feasibility(baseline_rate=baseline_rate, oracle_rate=oracle_rate, required_min_effect=args.required_effect)
    print(result.summary())
    if not result.feasible:
        print(
            "\nDO NOT freeze this effect-size threshold as-is. Either: (a) lower the required effect to something "
            "<= the available headroom, (b) pick/design a weaker baseline so real headroom exists above it (while "
            "still keeping it a serious, non-strawman baseline), or (c) redesign the environment so the naive "
            "baseline isn't already this close to the oracle ceiling. Freezing anyway guarantees a 'not supported' "
            "verdict regardless of the proposed policy's quality."
        )
        sys.exit(1)
    print("\nThreshold is feasible given this baseline/oracle headroom. This does not guarantee a learnable "
          "signal exists -- it only confirms the experiment CAN, in principle, support the hypothesis.")


if __name__ == "__main__":
    main()
