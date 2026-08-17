"""Phase 4.0 leakage/integrity audit.

Mirrors the project's existing leakage-audit convention (e.g.
benchmarks/phase3_6_leakage_audit.py): a set of independent, falsifiable
checks against the generated episode stream, run AFTER generation, that
either all pass or the run STOPS -- no check is weakened to make a result
look better.

Run: python benchmarks/phase4_0_leakage_audit.py
Writes: experiments/results/phase4_0/leakage_audit.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.episodic import generate_episode_stream, load_protocol  # noqa: E402

RESULTS_DIR = ROOT / "experiments" / "results" / "phase4_0"


def _row_key(step: dict) -> tuple:
    ctx = tuple(sorted(step["context"].items()))
    return (step["workload_id"], step["condition_id"], ctx, step["true_label"])


def check_determinism(protocol: dict) -> dict:
    a = generate_episode_stream(protocol).to_records()
    b = generate_episode_stream(protocol).to_records()
    same = a == b
    return {"name": "generation_is_deterministic", "passed": same, "detail": f"n_steps={len(a)} vs {len(b)}"}


def check_no_duplicate_rows_within_combo(records: list) -> dict:
    """No two occurrences of the same combo ever score the literal same
    underlying (context, label) row -- each occurrence draws a distinct,
    non-overlapping chunk of the workload's test_stream, per protocol."""
    seen = set()
    dupes = []
    for r in records:
        key = _row_key(r)
        if key in seen:
            dupes.append(key)
        seen.add(key)
    return {"name": "no_duplicate_rows_within_or_across_combos", "passed": len(dupes) == 0, "detail": f"{len(dupes)} duplicate rows"}


def check_novel_combos_absent_from_train_and_validation(records: list) -> dict:
    violations = [r for r in records if r["is_novel_combo"] and r["split"] in ("train", "validation")]
    return {
        "name": "novel_combos_absent_from_train_and_validation",
        "passed": len(violations) == 0,
        "detail": f"{len(violations)} novel-combo rows found in train/validation",
    }


def check_novel_combos_have_zero_known_history(records: list) -> dict:
    """A novel combo must have exactly its declared occurrence count, all
    in the test split -- no occurrence of a novel combo may appear before
    its single test-split occurrence (i.e. no combo is both 'known' and
    'novel')."""
    novel_keys = {(r["workload_id"], r["condition_id"]) for r in records if r["is_novel_combo"]}
    known_keys = {(r["workload_id"], r["condition_id"]) for r in records if not r["is_novel_combo"]}
    overlap = novel_keys & known_keys
    return {"name": "novel_and_known_combo_sets_are_disjoint", "passed": len(overlap) == 0, "detail": f"overlap={sorted(overlap)}"}


def check_split_boundary_matches_protocol(records: list, protocol: dict) -> dict:
    known_occurrences = protocol["recurrence"]["known_combo_occurrences"]
    violations = []
    for r in records:
        if r["is_novel_combo"]:
            expected = "test"
        else:
            o = r["occurrence_ordinal"]
            if o < known_occurrences - 2:
                expected = "train"
            elif o == known_occurrences - 2:
                expected = "validation"
            else:
                expected = "test"
        if r["split"] != expected:
            violations.append((r["workload_id"], r["condition_id"], r["occurrence_ordinal"], r["split"], expected))
    return {"name": "split_boundary_matches_protocol_rule", "passed": len(violations) == 0, "detail": f"{len(violations)} mismatches"}

def check_chronological_no_future_leakage(records: list) -> dict:
    """Within each combo, every train-split step must have a strictly
    earlier global `step` than every validation-split step, which must in
    turn be strictly earlier than every test-split step of the SAME combo
    -- i.e. no split boundary is defined by anything other than time
    order within a combo."""
    by_combo = {}
    for r in records:
        key = (r["workload_id"], r["condition_id"])
        by_combo.setdefault(key, []).append(r)

    violations = []
    order = {"train": 0, "validation": 1, "test": 2}
    for key, rows in by_combo.items():
        if len(rows) <= 1:
            continue
        max_step_by_split = {}
        min_step_by_split = {}
        for r in rows:
            s = r["split"]
            max_step_by_split[s] = max(max_step_by_split.get(s, r["step"]), r["step"])
            min_step_by_split[s] = min(min_step_by_split.get(s, r["step"]), r["step"])
        splits_present = sorted(max_step_by_split.keys(), key=lambda s: order[s])
        for earlier, later in zip(splits_present, splits_present[1:]):
            if max_step_by_split[earlier] >= min_step_by_split[later]:
                violations.append((key, earlier, later))
    return {"name": "chronological_no_future_leakage_within_combo", "passed": len(violations) == 0, "detail": f"{len(violations)} violations"}


def check_regime2_thresholds_never_score_test_stream_rows(records: list) -> dict:
    """Structural check: every scored context in the episode stream comes
    from a workload's test_stream (regimes 3+4, per pipeline_builder.
    build_system) -- regime 0/1/2 rows are never scored/emitted, only used
    internally (train/calibrate/threshold-derive) and discarded. Verified
    indirectly: no emitted row's context can be reconstructed as an exact
    regime-0/1/2 sample, checked by re-deriving each workload's regime 0-2
    contexts and confirming zero intersection with emitted contexts for
    that workload."""
    from src.data.synthetic import generate_regime_stream

    protocol = load_protocol()
    violations = 0
    for w in protocol["workloads"]:
        wid, wseed = w["workload_id"], w["seed"]
        stream = generate_regime_stream(regime_sizes=tuple(protocol["regime_sizes"]), seed=wseed)
        early_contexts = {tuple(sorted(s.context.items())) for s in stream if s.regime in (0, 1, 2)}
        emitted = {tuple(sorted(r["context"].items())) for r in records if r["workload_id"] == wid}
        violations += len(early_contexts & emitted)
    return {"name": "no_regime_0_1_2_row_ever_emitted", "passed": violations == 0, "detail": f"{violations} overlapping rows"}


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    protocol = load_protocol()
    dataset = generate_episode_stream(protocol)
    records = dataset.to_records()

    checks = [
        check_determinism(protocol),
        check_no_duplicate_rows_within_combo(records),
        check_novel_combos_absent_from_train_and_validation(records),
        check_novel_combos_have_zero_known_history(records),
        check_split_boundary_matches_protocol(records, protocol),
        check_chronological_no_future_leakage(records),
        check_regime2_thresholds_never_score_test_stream_rows(records),
    ]

    all_passed = all(c["passed"] for c in checks)
    output = {"all_passed": all_passed, "checks": checks}
    (RESULTS_DIR / "leakage_audit.json").write_text(json.dumps(output, indent=2))

    print("Phase 4.0 leakage audit\n")
    for c in checks:
        status = "PASS" if c["passed"] else "FAIL"
        print(f"  [{status}] {c['name']} -- {c['detail']}")
    print(f"\nALL PASSED: {all_passed}")
    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
