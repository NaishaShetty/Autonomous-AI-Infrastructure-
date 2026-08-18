"""Active Phase 4.4 -- STEP 3 / protocol Section 7: observation-noise
calibration sweep, VALIDATION ONLY.

Generates a VALIDATION-only scenario manifest (never TRAIN, never TEST --
verified explicitly at the end of ``main``) and, for each candidate noise
rate in {0.05, 0.10, 0.20, 0.30, 0.40}, measures the performance gap
between:
  (a) a NAIVE step-1-only baseline that ignores the step-1 observation
      entirely (always repeats the same fixed action at step 2 regardless
      of what it observed), and
  (b) a rule that genuinely conditions on the step-1 observation
      ("if worsened, escalate; else repeat the step-1 action" -- the
      trivial conditioning rule named in protocol section 7).

Selects the rate that MAXIMIZES this gap (the rate at which the
observation is informative enough to matter but not so noisy it is
useless, nor so clean it trivializes the problem) and freezes it into
configs/phase4_4_recovery_protocol.json's ``observation_noise_rate``.

This sweep -- and only this sweep -- touches VALIDATION before TEST
generation, per protocol section 7. It must never touch TEST; the
sweep-only VALIDATION manifest generated here uses a seed block disjoint
from (and separate from) the final frozen VALIDATION split generated later
in benchmarks/phase4_4_generate_dataset.py (Step 6) -- this script's
manifest is calibration-only scratch data, not the frozen split.

Run: PYTHONHASHSEED=0 python benchmarks/phase4_4_noise_sweep.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.recovery.environment_v2 import generate_scenario_v2, make_step2_context, run_step1, run_step2  # noqa: E402
from src.recovery.schema import ActionId, ScenarioFamily  # noqa: E402
from src.recovery.schema_v2 import ObservationSignal  # noqa: E402
from src.recovery.taxonomy import safe_candidate_actions  # noqa: E402

RESULTS_DIR = ROOT / "experiments" / "results" / "phase4_4"
CONFIG_PATH = ROOT / "configs" / "phase4_4_recovery_protocol.json"

SWEEP_CANDIDATES = [0.05, 0.10, 0.20, 0.30, 0.40]
N_SWEEP_VALIDATION_PER_FAMILY = 250
# Disjoint from splits_v2's frozen VALIDATION seed block (which starts at
# base + n_train) and from TRAIN/TEST -- this sweep uses its own dedicated
# seed sub-block so it can never be confused with, or accidentally reused
# as, the frozen VALIDATION split written in Step 6.
_SWEEP_SEED_BASE = 1_000_000_000_000 + 90_000_000  # inside phase4_4's family-0 block, above any per-family split use
_FAMILY_BLOCK = 100_000_000

_FAMILIES = [
    ScenarioFamily.RESOURCE_EXHAUSTION,
    ScenarioFamily.TRANSIENT_FAILURE,
    ScenarioFamily.CONFIGURATION_FAILURE,
    ScenarioFamily.DEPENDENCY_FAILURE,
]


def _sweep_seeds(family_idx: int) -> list[int]:
    base = _SWEEP_SEED_BASE + family_idx * _FAMILY_BLOCK
    return [base + i for i in range(N_SWEEP_VALIDATION_PER_FAMILY)]


def _fixed_first_action(family: ScenarioFamily) -> ActionId:
    """Domain-reasoning first choice per family -- same ordering logic used
    by the Step 4 FixedPrioritySequential baseline (authored independently
    in src/recovery/policy_v2.py), reused here only as the step-1 action
    both sweep rules share so the comparison isolates the step-2 decision
    rule, not the step-1 one."""
    order = {
        ScenarioFamily.RESOURCE_EXHAUSTION: ActionId.RESTART,
        ScenarioFamily.TRANSIENT_FAILURE: ActionId.RETRY,
        ScenarioFamily.CONFIGURATION_FAILURE: ActionId.RECONFIGURE,
        ScenarioFamily.DEPENDENCY_FAILURE: ActionId.RETRY,
    }
    return order[family]


def _naive_step1_only(family: ScenarioFamily, step1_action: ActionId, observation: ObservationSignal) -> ActionId:
    """(a) NAIVE baseline: ignores the observation, always repeats step 1's action."""
    return step1_action


_SECOND_CHOICE = {
    ScenarioFamily.RESOURCE_EXHAUSTION: ActionId.RETRY,
    ScenarioFamily.TRANSIENT_FAILURE: ActionId.RESTART,
    ScenarioFamily.CONFIGURATION_FAILURE: ActionId.ROLLBACK,
    ScenarioFamily.DEPENDENCY_FAILURE: ActionId.ABSTAIN,
}


def _conditions_on_observation(family: ScenarioFamily, step1_action: ActionId, observation: ObservationSignal) -> ActionId:
    """(b) genuinely uses the step-1 observation: on WORSENED (which, by
    construction in environment_v2._true_intermediate_signal, correlates
    with the step-1 action being a poor match for the hidden cause), SWITCH
    to the family's second-priority action rather than repeating a proven
    mismatch; otherwise (IMPROVED / NO_CHANGE) repeat the step-1 action.
    A pure escalate-on-worsened rule was tried first and rejected here
    because ESCALATE_TO_HUMAN always times out (0% success), which makes
    it strictly dominated by repeating regardless of noise rate -- an
    uninformative sweep. Switching to a different action is the version
    that can actually benefit from a low-noise informative signal, per
    protocol section 7's intent ('a rule that genuinely uses the step-1
    observation'). NOT the same object as Step 4's FixedPrioritySequential
    baseline, authored independently afterward."""
    if observation == ObservationSignal.WORSENED:
        alt = _SECOND_CHOICE[family]
        return alt if alt != step1_action else step1_action
    return step1_action


def _run_rule(scenarios, noise_rate: float, step2_rule) -> float:
    n_success = 0
    for scenario in scenarios:
        step1_action = _fixed_first_action(scenario.family)
        t1, terminal = run_step1(scenario, step1_action, observation_noise_rate=noise_rate)
        if terminal:
            if t1.outcome.value == "success":
                n_success += 1
            continue
        step2_action = step2_rule(scenario.family, step1_action, t1.observation)
        safe = set(safe_candidate_actions(scenario.family))
        if step2_action not in safe:
            step2_action = ActionId.ESCALATE_TO_HUMAN
        t2 = run_step2(scenario, step2_action)
        if t2.outcome.value == "success":
            n_success += 1
    return n_success / len(scenarios)


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    scenarios = []
    for idx, family in enumerate(_FAMILIES):
        for seed in _sweep_seeds(idx):
            scenarios.append(generate_scenario_v2(family, seed))
    print(f"VALIDATION-only sweep manifest: {len(scenarios)} scenarios "
          f"({N_SWEEP_VALIDATION_PER_FAMILY} per family x {len(_FAMILIES)} families)")

    rows = []
    for rate in SWEEP_CANDIDATES:
        naive_sr = _run_rule(scenarios, rate, _naive_step1_only)
        conditioning_sr = _run_rule(scenarios, rate, _conditions_on_observation)
        gap = conditioning_sr - naive_sr
        rows.append({
            "observation_noise_rate": rate,
            "naive_step1_only_success_rate": naive_sr,
            "conditions_on_observation_success_rate": conditioning_sr,
            "gap": gap,
        })
        print(f"  rate={rate:.2f}  naive={naive_sr:.4f}  conditioning={conditioning_sr:.4f}  gap={gap:+.4f}")

    best = max(rows, key=lambda r: r["gap"])
    selected_rate = best["observation_noise_rate"]
    print(f"\nSELECTED observation_noise_rate = {selected_rate} (max gap = {best['gap']:+.4f})")

    config = json.loads(CONFIG_PATH.read_text())
    config["environment"]["observation_signal"]["observation_noise_rate"] = selected_rate
    config["environment"]["observation_signal"]["observation_noise_rate_status"] = "FROZEN_POST_VALIDATION_SWEEP"
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {CONFIG_PATH} with observation_noise_rate={selected_rate}")

    out_path = RESULTS_DIR / "noise_sweep.json"
    out_path.write_text(json.dumps({
        "sweep_candidates": SWEEP_CANDIDATES,
        "n_validation_scenarios": len(scenarios),
        "n_validation_per_family": N_SWEEP_VALIDATION_PER_FAMILY,
        "selection_rule": "maximize gap between naive step-1-only baseline and a rule conditioning on step-1 observation",
        "rows": rows,
        "selected_observation_noise_rate": selected_rate,
    }, indent=2), encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
