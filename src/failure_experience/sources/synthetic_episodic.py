"""Adapter: Phase 4.0's frozen synthetic episode stream
(experiments/results/phase4_0/episodes.json) -> NormalizedRecord.

This is the ONLY source with a full observation->diagnosis->recovery->
validation->outcome chain already present (it was purpose-built for the old,
now-frozen Phase 4.1/4.2). It is read here strictly as DATA (read-only,
never modified) to exercise and test the new FailureExperience schema's
full field range -- the old src/experience/ code that originally consumed
this file is NOT imported or reused here; this adapter is independent.

``condition_id`` is Phase 4.0's generator ground truth for which failure
mechanism was injected -- evaluation-only information the original
generator recorded because it CHOSE the condition (see the frozen
docs/PHASE4_0_EPISODIC_DATA.md and docs/PHASE4_1_FAILURE_MEMORY.md for the
same rule applied there). It is used here ONLY inside ``validation_*``
fields (post-hoc / outcome-only), never as an observation or diagnosis
input -- consistent with that established rule.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ._util import synthetic_timestamp

EPISODES_PATH = Path(__file__).resolve().parents[3] / "experiments" / "results" / "phase4_0" / "episodes.json"

_RECOVERY_ACTION_TO_STATUS = {
    None: "not_attempted",
    "retry": "attempted",
    "reconfigure": "attempted",
    "rollback": "attempted",
}


def _dataset_content_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def load_records(path: Path = EPISODES_PATH, only_failures: bool = True) -> list[dict]:
    with open(path) as f:
        episodes = json.load(f)
    if only_failures:
        episodes = [e for e in episodes if e.get("is_failure")]
    return episodes


def to_normalized(episode: dict, dataset_content_hash: str) -> dict:
    step = episode["step"]
    workload_id = episode["workload_id"]
    key = f"phase4_0|{workload_id}|{step}"
    obs_ts = synthetic_timestamp(key)

    diagnosed = episode.get("diagnosed_cause") is not None
    recovered = episode.get("recovery_attempted", False)
    recovery_correct = episode.get("recovery_correct")
    validated = recovery_correct is not None

    # IMPORTANT (found by Experiment C, not assumed up front): in this
    # dataset every recovery attempt occurs on an episode whose `decision`
    # is ABSTAIN (recovery_attempted is only ever True when decision ==
    # "ABSTAIN" -- there are zero REVIEW/ANSWER + recovery_attempted rows).
    # Checking `decision == "ABSTAIN"` first would therefore label EVERY
    # recovery attempt "abstained" regardless of whether the recovery
    # succeeded or failed -- exactly the outcome-collapsing Task 4
    # prohibits. Recovery outcome must take priority over the decision
    # label whenever a recovery was actually attempted.
    if recovered:
        if recovery_correct is True:
            final_status = "success"
        elif recovery_correct is False:
            final_status = "failure"
        else:
            final_status = "unknown"  # attempted, outcome not (yet) validated
    elif episode["decision"] == "ABSTAIN":
        final_status = "abstained"
    else:
        final_status = "failure"

    temporal = {"observation_ts": obs_ts, "detection_ts": obs_ts}
    cursor = obs_ts
    if diagnosed:
        from datetime import timedelta
        cursor = cursor + timedelta(seconds=1)
        temporal["diagnosis_ts"] = cursor
    if recovered:
        from datetime import timedelta
        cursor = cursor + timedelta(seconds=1)
        temporal["recovery_decision_ts"] = cursor
        cursor = cursor + timedelta(seconds=1)
        temporal["recovery_execution_ts"] = cursor
    if validated:
        from datetime import timedelta
        cursor = cursor + timedelta(seconds=1)
        temporal["validation_ts"] = cursor
    from datetime import timedelta
    temporal["outcome_ts"] = cursor + timedelta(seconds=1)

    return {
        "source_dataset": "phase4_0_synthetic_episodic",
        "episode_id": f"episode_{step}",
        "occurrence_key": str(step),
        "observed_at": obs_ts,
        "workload_id": workload_id,
        "workload_type": "synthetic_classifier_workload",
        "environment": episode.get("split"),
        "runtime_context": {
            "occurrence_ordinal": episode.get("occurrence_ordinal"),
            "is_novel_combo": episode.get("is_novel_combo"),
            "tier": episode.get("tier"),
        },
        "telemetry": {k: float(v) for k, v in episode.get("context", {}).items()},
        "performance_metrics": {
            "confidence": float(episode["confidence"]),
            "b_risk_score": float(episode["b_risk_score"]),
        },
        "failure_type": "synthetic_injected_condition",
        "affected_component": workload_id,
        "failure_status": "closed" if validated else "open",
        "diagnosis_suspected_cause": episode.get("diagnosed_cause"),
        "diagnosis_confidence": None,
        "diagnosis_evidence": [f"tier={episode.get('tier')}", f"decision={episode.get('decision')}"],
        "diagnosis_method": "phase3_6_deterministic_diagnosis_rule" if diagnosed else None,
        "diagnosis_method_version": "phase3.6",
        "diagnosis_source": "automated_system" if diagnosed else "not_attempted",
        "recovery_status": _RECOVERY_ACTION_TO_STATUS.get(episode.get("recovery_action"), "not_attempted"),
        "recovery_candidate_actions": ["retry", "reconfigure", "rollback"] if recovered else [],
        "recovery_selected_action": episode.get("recovery_action"),
        "recovery_execution_result": episode.get("recovery_outcome"),
        "recovery_retry_count": 1 if recovered else 0,
        "recovery_policy_version": "phase3.6",
        "validation_result": ("passed" if recovery_correct is True else "failed" if recovery_correct is False else "not_performed"),
        "validation_residual_failure": (recovery_correct is False) if validated else None,
        # evaluation-only ground truth, used only post-hoc (see module docstring) -- never fed to diagnosis/recovery decision fields above.
        "validation_validated_cause": episode["condition_id"] if validated else None,
        "outcome_recovery_success": recovery_correct,
        "outcome_task_success": episode["outcome"] == "CORRECT",
        "outcome_attempts": 1 if recovered else 0,
        "outcome_final_status": final_status,
        "provenance_source_workload": workload_id,
        "provenance_detector_version": "phase3.6_b_risk_score",
        "provenance_diagnosis_component_version": "phase3.6_diagnosis_rule" if diagnosed else None,
        "provenance_recovery_policy_version": "phase3.6_recovery_policy" if recovered else None,
        "provenance_validation_component_version": "phase4_0_generator_ground_truth" if validated else None,
        "provenance_dataset_content_hash": dataset_content_hash,
        "provenance_experiment_id": "phase4_0_episodic_data",
        "provenance_raw_record_ref": {"step": step, "workload_id": workload_id, "split": episode.get("split")},
        "temporal": temporal,
    }


def load_normalized(path: Path = EPISODES_PATH, only_failures: bool = True) -> list[dict]:
    content_hash = _dataset_content_hash(path)
    return [to_normalized(e, content_hash) for e in load_records(path, only_failures=only_failures)]
