"""Phase 3.5 formal leakage audit of the attack-generalization pipeline.

Mirrors ``benchmarks/phase3_1_leakage_audit.py``'s approach (concrete,
runtime checks against real objects, not just re-read-the-source
reasoning) applied to the NEW surface Phase 3.5 introduces: attack
transforms applied to the held-out test stream. Does not touch or modify
``benchmarks/phase3_1_leakage_audit.py`` itself, or any Phase 3.1-3.4
source file.

Run: python benchmarks/phase3_5_leakage_audit.py
Writes: experiments/results/phase3_5/leakage_audit.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.synthetic import FEATURE_NAMES  # noqa: E402
from src.evaluation.attacks import apply_feature_dropout, apply_feature_noise  # noqa: E402
from src.evaluation.protocol import Phase31Protocol  # noqa: E402
from src.pipeline_builder import build_system  # noqa: E402

from benchmarks.phase3_3_generalization import _reconstruct_regime2_with_confidences  # noqa: E402
from benchmarks.phase3_5_attack_generalization import load_protocol35  # noqa: E402

RESULTS_DIR = ROOT / "experiments" / "results" / "phase3_5"
SEED = 42


def _row_hash(context: dict[str, float]) -> tuple:
    return tuple(round(context[f], 10) for f in FEATURE_NAMES)


def check_training_evaluation_disjointness(system, regime2) -> dict:
    """Attack conditions are built from system.test_stream (regimes 3+4)
    only. Confirms none of those samples' clean feature rows are present
    among the regime-2 rows used to fit the candidate."""
    test_hashes = {_row_hash(s.context) for s in system.test_stream}
    regime2_hashes = {_row_hash(c) for c in regime2["regime2_contexts"]}
    overlap = test_hashes & regime2_hashes
    return {
        "check": "training_evaluation_disjointness",
        "n_test_samples": len(system.test_stream),
        "n_regime2_samples": len(regime2["regime2_contexts"]),
        "overlap_count": len(overlap),
        "passed": len(overlap) == 0,
    }


def check_attack_transforms_preserve_ground_truth(system) -> dict:
    """Confirms every attack transform leaves label/regime byte-identical
    to the clean stream -- i.e. attacks corrupt observations only, never
    the ground truth the model is scored against."""
    clean = system.test_stream
    noisy = apply_feature_noise(clean, FEATURE_NAMES, std=0.5, seed=SEED, attack_ordinal=1)
    dropped = apply_feature_dropout(clean, FEATURE_NAMES, dropped_features=["f2", "f4"])

    def labels_regimes(stream):
        return [(s.label, s.regime) for s in stream]

    noisy_ok = labels_regimes(clean) == labels_regimes(noisy)
    dropped_ok = labels_regimes(clean) == labels_regimes(dropped)
    return {
        "check": "attack_transforms_preserve_ground_truth",
        "feature_noise_labels_regimes_unchanged": bool(noisy_ok),
        "feature_dropout_labels_regimes_unchanged": bool(dropped_ok),
        "passed": bool(noisy_ok and dropped_ok),
    }


def check_attack_transforms_actually_corrupt_context(system) -> dict:
    """An attack that silently no-ops would make the 'attack' condition
    identical to clean and invalidate any degradation claim. Confirms the
    context values genuinely change."""
    clean = system.test_stream
    noisy = apply_feature_noise(clean, FEATURE_NAMES, std=0.5, seed=SEED, attack_ordinal=1)
    dropped = apply_feature_dropout(clean, FEATURE_NAMES, dropped_features=["f2", "f4"])

    noisy_changed = any(
        any(abs(c.context[f] - n.context[f]) > 1e-9 for f in FEATURE_NAMES) for c, n in zip(clean[:50], noisy[:50])
    )
    dropped_are_zero = all(d.context["f2"] == 0.0 and d.context["f4"] == 0.0 for d in dropped[:50])
    dropped_others_unchanged = all(
        d.context[f] == c.context[f] for c, d in zip(clean[:50], dropped[:50]) for f in FEATURE_NAMES if f not in ("f2", "f4")
    )
    return {
        "check": "attack_transforms_actually_corrupt_context",
        "feature_noise_changed_values": bool(noisy_changed),
        "feature_dropout_zeroed_target_features": bool(dropped_are_zero),
        "feature_dropout_left_other_features_unchanged": bool(dropped_others_unchanged),
        "passed": bool(noisy_changed and dropped_are_zero and dropped_others_unchanged),
    }


def check_attack_determinism(system) -> dict:
    """Same seed + same attack_ordinal must reproduce byte-identical
    corrupted values (no uncontrolled randomness)."""
    a = apply_feature_noise(system.test_stream, FEATURE_NAMES, std=0.5, seed=SEED, attack_ordinal=1)
    b = apply_feature_noise(system.test_stream, FEATURE_NAMES, std=0.5, seed=SEED, attack_ordinal=1)
    identical = all(a_s.context == b_s.context for a_s, b_s in zip(a, b))
    c = apply_feature_noise(system.test_stream, FEATURE_NAMES, std=0.5, seed=SEED, attack_ordinal=2)
    different_ordinal_differs = any(
        any(abs(a_s.context[f] - c_s.context[f]) > 1e-9 for f in FEATURE_NAMES) for a_s, c_s in zip(a[:50], c[:50])
    )
    return {
        "check": "attack_determinism",
        "same_seed_same_ordinal_reproducible": bool(identical),
        "different_ordinal_gives_different_noise": bool(different_ordinal_differs),
        "passed": bool(identical and different_ordinal_differs),
    }


def check_no_fit_calls_during_attack_scoring() -> dict:
    """Static check: benchmarks/phase3_5_attack_generalization.py's
    scoring path (run_one_seed) must contain no .fit( call after the one
    frozen candidate.fit -- i.e. attack conditions are scored, never
    fit-on. Source-level check, cross-referenced against the runtime
    checks above."""
    src = (ROOT / "benchmarks" / "phase3_5_attack_generalization.py").read_text()
    condition_loop_start = src.index("for condition in all_conditions:")
    condition_loop_region = src[condition_loop_start:]
    no_fit_in_loop = ".fit(" not in condition_loop_region
    return {
        "check": "no_fit_calls_during_attack_scoring",
        "no_fit_call_inside_condition_loop": bool(no_fit_in_loop),
        "passed": bool(no_fit_in_loop),
    }


def check_attack_protocol_matches_frozen_file(protocol35: dict) -> dict:
    """Confirms the loaded protocol35 dict used by the evaluation script
    is byte-identical to a fresh read of configs/phase3_5_attack_protocol.json
    -- i.e. nothing in the running process silently diverged from the
    frozen file on disk."""
    fresh = json.loads((ROOT / "configs" / "phase3_5_attack_protocol.json").read_text())
    matches = fresh == protocol35
    return {
        "check": "attack_protocol_matches_frozen_file",
        "matches": bool(matches),
        "passed": bool(matches),
    }


def check_duplicate_samples_across_attack_conditions(system) -> dict:
    """The attack conditions are all derived from the SAME clean
    test_stream -- by design they share row identity (same underlying
    sample, corrupted differently). Confirms this is exactly true (each
    attacked stream has the same length/order as clean, one-to-one), not
    an accidental resampling or shuffle that could silently introduce
    duplicate or missing rows."""
    clean = system.test_stream
    noisy = apply_feature_noise(clean, FEATURE_NAMES, std=1.5, seed=SEED, attack_ordinal=2)
    dropped = apply_feature_dropout(clean, FEATURE_NAMES, dropped_features=["f2", "f4"])
    same_length = len(clean) == len(noisy) == len(dropped)
    same_order = all(c.label == n.label == d.label for c, n, d in zip(clean, noisy, dropped))
    return {
        "check": "duplicate_samples_across_attack_conditions",
        "same_length": bool(same_length),
        "same_row_order_by_label": bool(same_order),
        "passed": bool(same_length and same_order),
    }


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    protocol = Phase31Protocol.load()
    protocol35 = load_protocol35()
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=SEED)
    regime2 = _reconstruct_regime2_with_confidences(SEED, protocol, system)

    checks = [
        check_training_evaluation_disjointness(system, regime2),
        check_attack_transforms_preserve_ground_truth(system),
        check_attack_transforms_actually_corrupt_context(system),
        check_attack_determinism(system),
        check_no_fit_calls_during_attack_scoring(),
        check_attack_protocol_matches_frozen_file(protocol35),
        check_duplicate_samples_across_attack_conditions(system),
    ]

    report = {
        "seed": SEED,
        "checks": checks,
        "all_passed": all(c["passed"] for c in checks),
    }
    out_path = RESULTS_DIR / "leakage_audit.json"
    out_path.write_text(json.dumps(report, indent=2))

    print(f"Phase 3.5 leakage audit -- seed {SEED}")
    for c in checks:
        status = "PASS" if c["passed"] else "FAIL"
        print(f"  [{status}] {c['check']}")
    print(f"\nAll checks passed: {report['all_passed']}")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
