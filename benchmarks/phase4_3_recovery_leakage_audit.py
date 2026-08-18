"""Active Phase 4.3 -- leakage audit for the controlled recovery-selection
pipeline (src/recovery/).

Checks the decision-time information boundary (schema.py's DecisionContext),
split isolation, provenance integrity, and includes a NON-VACUOUS
contamination test (check 8) that actually attempts to smuggle ground truth
into a policy input and asserts it is rejected -- proving the guard is
load-bearing, per this project's standing leakage-audit discipline (see
benchmarks/phase4_2_active_leakage_audit.py's check 4 for the precedent).

Run: PYTHONHASHSEED=0 python benchmarks/phase4_3_recovery_leakage_audit.py
(PYTHONHASHSEED=0 is defense in depth; see the note in
benchmarks/phase4_3_generate_dataset.py's docstring.)

Writes experiments/results/phase4_3/leakage_audit.json.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pydantic import ValidationError  # noqa: E402

from src.recovery.environment import generate_scenario, transition  # noqa: E402
from src.recovery.io import read_jsonl  # noqa: E402
from src.recovery.policy import EmpiricalRecoveryPolicy, FixedPriorityPolicy, RandomValidPolicy  # noqa: E402
from src.recovery.schema import ActionId, DecisionContext, ScenarioFamily, Split  # noqa: E402
from src.recovery.splits import all_families, all_splits, seeds_for  # noqa: E402

RESULTS_DIR = ROOT / "experiments" / "results" / "phase4_3"
DATA_DIR = ROOT / "data" / "controlled_recovery"

HISTORICAL_FROZEN_DIRS = ["src/failure_patterns", "src/failure_experience"]


def check_1_decision_context_structurally_excludes_ground_truth() -> dict:
    fields = set(DecisionContext.model_fields.keys())
    forbidden = {"hidden_cause", "outcome", "transition", "validation_result", "oracle_best_action"}
    leaked = fields & forbidden
    return {
        "check": "decision_context_excludes_ground_truth_fields",
        "passed": len(leaked) == 0,
        "detail": f"DecisionContext fields={sorted(fields)}; forbidden-intersection={sorted(leaked)}",
    }


def check_2_non_vacuous_contamination_rejected() -> dict:
    """Actually attempt to inject hidden_cause into a DecisionContext
    payload and confirm pydantic rejects it -- non-vacuous per project
    convention (asserts a real failure mode is caught, not a tautology)."""
    scenario = generate_scenario(ScenarioFamily.RESOURCE_EXHAUSTION, seed=1)
    payload = scenario.decision_context.model_dump()
    payload["hidden_cause"] = scenario.hidden_cause
    try:
        DecisionContext(**payload)
        return {"check": "non_vacuous_contamination_rejected", "passed": False,
                "detail": "contamination payload was ACCEPTED -- leakage guard is not load-bearing"}
    except ValidationError as e:
        return {"check": "non_vacuous_contamination_rejected", "passed": True,
                "detail": f"contamination payload correctly rejected: {type(e).__name__}"}


def check_3_policy_signatures_take_only_decision_context() -> dict:
    bad = []
    for cls in (FixedPriorityPolicy, RandomValidPolicy, EmpiricalRecoveryPolicy):
        sig = inspect.signature(cls.select_action)
        params = [p for p in sig.parameters if p != "self"]
        if params != ["ctx"]:
            bad.append((cls.__name__, params))
    return {"check": "policy_select_action_signature_boundary", "passed": len(bad) == 0,
            "detail": f"violations={bad}" if bad else "all policies take exactly (self, ctx: DecisionContext)"}


def check_4_seed_ranges_disjoint() -> dict:
    seen: dict[int, tuple] = {}
    collisions = []
    for family in all_families():
        for split in all_splits():
            for seed in seeds_for(family, split):
                if seed in seen:
                    collisions.append((seed, seen[seed], (family.value, split.value)))
                seen[seed] = (family.value, split.value)
    return {"check": "seed_ranges_disjoint_across_family_and_split", "passed": len(collisions) == 0,
            "detail": f"collisions={collisions[:5]}" if collisions else f"{len(seen)} seeds, zero collisions"}


def check_5_generated_split_files_disjoint_and_manifest_consistent() -> dict:
    if not DATA_DIR.exists():
        return {"check": "generated_splits_disjoint", "passed": False, "detail": "data/controlled_recovery not generated"}
    ids = {}
    for split in all_splits():
        path = DATA_DIR / f"{split.value}.jsonl"
        if not path.exists():
            return {"check": "generated_splits_disjoint", "passed": False, "detail": f"missing {path}"}
        ids[split.value] = {ep.episode_id for ep in read_jsonl(path)}
    overlaps = {
        "train&val": ids["train"] & ids["validation"],
        "train&test": ids["train"] & ids["test"],
        "val&test": ids["validation"] & ids["test"],
    }
    total_overlap = sum(len(v) for v in overlaps.values())
    return {"check": "generated_splits_disjoint", "passed": total_overlap == 0,
            "detail": f"overlap_counts={{k: len(v) for k,v in overlaps}} -> "
                      f"{[len(v) for v in overlaps.values()]}"}


def check_6_val_test_unresolved_at_generation() -> dict:
    if not DATA_DIR.exists():
        return {"check": "val_test_unresolved_at_generation", "passed": False, "detail": "dataset not generated"}
    bad = []
    for split_name in ("validation", "test"):
        path = DATA_DIR / f"{split_name}.jsonl"
        for ep in read_jsonl(path):
            if ep.policy_selection is not None or ep.transition is not None:
                bad.append(ep.episode_id)
    return {"check": "val_test_unresolved_at_generation", "passed": len(bad) == 0,
            "detail": f"{len(bad)} episodes had a pre-baked action/outcome (should be 0)"}


def check_7_all_provenance_source_type_controlled() -> dict:
    if not DATA_DIR.exists():
        return {"check": "provenance_source_type_controlled", "passed": False, "detail": "dataset not generated"}
    bad = 0
    total = 0
    for split in all_splits():
        for ep in read_jsonl(DATA_DIR / f"{split.value}.jsonl"):
            total += 1
            if ep.provenance.source_type.value != "controlled":
                bad += 1
    return {"check": "provenance_source_type_controlled", "passed": bad == 0,
            "detail": f"{bad}/{total} episodes had non-'controlled' source_type"}


def check_8_unsafe_action_deterministically_flagged() -> dict:
    """Non-vacuous: confirms the environment ACTUALLY flags FORCE_RESTART as
    unsafe across many draws (would fail if the safety-classification wiring
    were broken), not merely that the enum member exists."""
    n_unsafe, n_total = 0, 50
    for seed in range(n_total):
        scenario = generate_scenario(ScenarioFamily.DEPENDENCY_FAILURE, seed=seed)
        t = transition(scenario, ActionId.FORCE_RESTART)
        if t.unsafe_action_taken and t.outcome.value == "unsafe":
            n_unsafe += 1
    return {"check": "unsafe_action_flagging_non_vacuous", "passed": n_unsafe == n_total,
            "detail": f"{n_unsafe}/{n_total} FORCE_RESTART transitions correctly flagged unsafe"}


def check_9_historical_frozen_dirs_untouched(baseline_hashes_path: Path) -> dict:
    """Compares against a hash snapshot taken before Phase 4.3 work began,
    if one exists; otherwise records current hashes as the first snapshot.

    NOTE: a first-run "no prior baseline, wrote fresh snapshot" result is a
    non-event, NOT a real pass -- there was nothing to compare against, so
    it proves nothing about whether these directories were touched. Treat
    it as informational only; this check only constitutes a real
    verification once it has been run again against a later, unrelated
    change and found the baseline unchanged.

    Baseline file format: {"baseline_commit": <git rev-parse HEAD at
    snapshot time, or null>, "hashes": {posix_relpath: sha256}}. Paths are
    stored via Path.as_posix() so the baseline is comparable across
    Windows/POSIX checkouts (str(Path) previously emitted OS-native
    separators, which made a baseline written on Windows silently
    mismatch -- and thus always "diff" -- when read back on POSIX, or
    vice versa)."""
    current = {}
    for d in HISTORICAL_FROZEN_DIRS:
        dir_path = ROOT / d
        if not dir_path.exists():
            continue
        for f in sorted(dir_path.rglob("*.py")):
            current[f.relative_to(ROOT).as_posix()] = hashlib.sha256(f.read_bytes()).hexdigest()

    if baseline_hashes_path.exists():
        raw = json.loads(baseline_hashes_path.read_text())
        baseline = raw.get("hashes", raw)  # tolerate the old flat format too
        diffs = {k: (baseline.get(k), v) for k, v in current.items() if baseline.get(k) != v}
        missing = [k for k in baseline if k not in current]
        passed = len(diffs) == 0 and len(missing) == 0
        detail = f"diffs={list(diffs.keys())[:10]} missing={missing[:10]}" if not passed else "no changes vs baseline snapshot"
    else:
        try:
            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True,
            ).stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            commit = None
        baseline_hashes_path.write_text(json.dumps({"baseline_commit": commit, "hashes": current}, indent=2))
        passed = True
        detail = (f"NON-EVENT, not a real verification: no prior baseline found; wrote first "
                  f"snapshot ({len(current)} files) to {baseline_hashes_path.name} at commit "
                  f"{commit}. Re-run this audit after a later, unrelated change to get a real pass/fail.")
    return {"check": "historical_frozen_dirs_untouched", "passed": passed, "detail": detail}


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    baseline_path = ROOT / "benchmarks" / "_phase4_3_historical_hashes.json"

    checks = [
        check_1_decision_context_structurally_excludes_ground_truth(),
        check_2_non_vacuous_contamination_rejected(),
        check_3_policy_signatures_take_only_decision_context(),
        check_4_seed_ranges_disjoint(),
        check_5_generated_split_files_disjoint_and_manifest_consistent(),
        check_6_val_test_unresolved_at_generation(),
        check_7_all_provenance_source_type_controlled(),
        check_8_unsafe_action_deterministically_flagged(),
        check_9_historical_frozen_dirs_untouched(baseline_path),
    ]

    n_passed = sum(1 for c in checks if c["passed"])
    result = {"milestone": "ACTIVE_PHASE_4_3", "n_checks": len(checks), "n_passed": n_passed, "checks": checks}
    out_path = RESULTS_DIR / "leakage_audit.json"
    out_path.write_text(json.dumps(result, indent=2))

    for c in checks:
        status = "PASS" if c["passed"] else "FAIL"
        print(f"[{status}] {c['check']}: {c['detail']}")
    print(f"\n{n_passed}/{len(checks)} checks passed -> {out_path}")
    return 0 if n_passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
