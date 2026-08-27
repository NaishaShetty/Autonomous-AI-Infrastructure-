"""Phase 5.2 canonical dataset construction (main entry point).

Pure, deterministic function of the frozen Gen-3 evidence sources listed in
`sources.py`. No step here writes to any frozen path; output is written only
under the caller-supplied output directory
(experiments/results/phase5_dataset_construction/<timestamp>/).

Determinism discipline (Phase 5.1 Open Question 3):
- every source file is read once, its exact bytes hashed (sha256) for
  provenance/record_id lineage;
- every iteration order is an explicit `sorted(..., key=...)` over a
  source-intrinsic natural key (never raw dict/list iteration order,
  never os.listdir()/glob() order);
- record_id is computed by src.phase5.record_id (sha256-based, no
  hash()/id()/random/wall-clock dependence);
- the only timestamp fields written anywhere are copied from source data
  (there are none in the current sources at record granularity) or are
  explicitly `None`/`TIMESTAMP_UNKNOWN` -- `generated_at` in
  dataset_metadata.json is deliberately EXCLUDED from anything that
  participates in record_id, split assignment, or ordering, precisely so
  two separate invocations of this script (run at different wall-clock
  times) produce byte-identical dataset content.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from . import sources as src
from .record_id import compute_record_id, compute_record_id_full, sha256_of_file
from .failure_mapping import infer_failure_class

DATASET_VERSION = "phase5.2-dataset-v1.0.0"
SCHEMA_VERSION = "phase5.1-schema-v1.0.0"
GENERATION_SPEC_VERSION = "phase5.2-generation-spec-v1"

# Documented, disclosed family-level AUROC numbers already published in the
# frozen record (docs/MASTER_RECORD_CONTENT.md / SRC-018
# uncertainty_eval.py). Attached to per-episode agent_output prediction
# blocks purely as CONTEXT (auroc_family_level), never as a per-episode
# ground-truth label -- consistent with the Prediction schema block's own
# comment ("family-level metric, attached for context; not a per-episode
# ground truth").
AGENT_FAMILY_AUROC = {
    "arithmetic_self_consistency": 0.953,
    "sentiment_softmax_margin": 0.659,
    "extractive_qa_span_logit": 0.934,
}

RECOVERY_ACTION_MAP = {
    "retry": "RETRY",
    "restart": "RESTART",
    "reconfigure": "RECONFIGURE",
    "rollback": "ROLLBACK",
    "escalate": "ESCALATE",
    "abstain": "ABSTAIN",
    None: None,
}


def _hash_bytes(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\x1f")
    return h.hexdigest()


class SourceHashCache:
    """Computes and memoizes sha256(file_bytes) for each frozen source file,
    read once, in a fixed (sorted) order."""

    def __init__(self):
        self._cache: dict[str, str] = {}
        for p in sorted(src.ALL_SOURCE_FILES, key=lambda p: str(p)):
            self._cache[str(p)] = sha256_of_file(str(p))

    def get(self, path: Path) -> str:
        return self._cache[str(path)]

    def as_dict(self) -> dict:
        # Keys relativized and sorted for deterministic, portable output.
        out = {}
        for k, v in self._cache.items():
            rel = str(Path(k).resolve().relative_to(src.REPO_ROOT)).replace("\\", "/")
            out[rel] = v
        return dict(sorted(out.items()))


def _split_bucket(group_key: str) -> str:
    """Deterministic hash-partition of a group_key into
    train(70%)/calibration_validation(15%)/test(15%).

    Resolution of Phase 5.1 Open Question 2's disclosed limitation: the
    original historical exact seed lists used to fit/calibrate/test
    TrainedRiskPredictor / PredictionScopeRouter / AgentDecisionCalibration
    Profile in the frozen Phase 4 runs are NOT recoverable from the raw
    per-episode evidence actually available to this construction (see
    PHASE5_2_DATASET_CONSTRUCTION_REPORT.md and PHASE5_2_DATASET_AUDIT.md,
    "Question 2" sections, for the full disclosure). Per the explicit
    instruction not to invent historical seed lists, this dataset instead
    assigns splits using the strongest reproducible grouping key actually
    available -- `workload_id` (`group_key`) -- via a deterministic
    (non-random-module, non-wall-clock) SHA-256 hash partition. This is a
    NEW split assignment for this dataset release; it is not a claim to
    reproduce the original Phase 4 training/calibration/test partition.
    """
    digest = hashlib.sha256(group_key.encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) / 0xFFFFFFFF
    if bucket < 0.70:
        return "train"
    elif bucket < 0.85:
        return "calibration_validation"
    else:
        return "test"


def _outcome_class(failure_class: str, validation_status: str | None, decision_action: str | None) -> str:
    if failure_class == "NONE":
        return "NO_FAILURE"
    if validation_status == "RECOVERED":
        return "RECOVERED"
    if validation_status == "NOT_RECOVERED":
        return "NOT_RECOVERED"
    if decision_action == "ABSTAIN":
        return "ABSTAINED"
    return "UNKNOWN"


def build_controlled_runtime_records(hashcache: SourceHashCache) -> list[dict]:
    records: list[dict] = []

    # --- Phase 4.4 (6 episodes) ---
    src_hash_44 = hashcache.get(src.PHASE4_4_RESULTS)
    for seq, ep in enumerate(src.iter_phase4_4_episodes()):
        run_id = ep["run_id"]
        episode_local_id = ep["episode"]
        episode_id = f"phase4.4-{episode_local_id}"
        workload_id = ep["workload_id"]
        diagnosis_hypothesis = ep.get("diagnosis_hypothesis")
        failure_class, unmapped = infer_failure_class(diagnosis_hypothesis, workload_id)
        validation_status = ep.get("validation")
        if validation_status is None:
            validation_status_norm = "UNKNOWN"
        else:
            validation_status_norm = validation_status
        decision_action = ep.get("decision")
        group_key = workload_id
        record_id = compute_record_id(
            DATASET_VERSION, src_hash_44, run_id, episode_id, "controlled_runtime_episode", seq,
        )
        record_id_full = compute_record_id_full(
            DATASET_VERSION, src_hash_44, run_id, episode_id, "controlled_runtime_episode", seq,
        )
        rec = {
            "identity": {
                "dataset_version": DATASET_VERSION,
                "schema_version": SCHEMA_VERSION,
                "source_artifact_version": "phase4.5-controlled-runtime-v2",
                "record_id": record_id,
                "record_id_full_digest": record_id_full,
                "track": "controlled_runtime",
                "environment_id": "UNSPECIFIED_PRE_4_9",
                "environment_role": "UNSPECIFIED",
                "workload_id": workload_id,
                "run_id": run_id,
                "episode_id": episode_id,
                "seed": None,
                "group_key": group_key,
            },
            "provenance": {
                "source": "experiments/results/phase4_4_autonomy_pipeline/results.json",
                "source_version": "phase4.4-autonomy-pipeline",
                "source_record_id": run_id,
                "extraction_method": "direct_telemetry_read",
                "transformation": "identity",
                "transformation_version": None,
                "timestamp_quality": "UNKNOWN",
                "checksum": src_hash_44,
                "evidence_class": 2,
                "frozen_run_dir": "experiments/results/phase4_4_autonomy_pipeline",
            },
            "experimental_boundary": "controlled_runtime_evidence",
            "evidence_class": 2,
            "temporal": {
                "observation_time": None,
                "decision_time": "1970-01-01T00:00:00Z",
                "failure_time": None,
                "recovery_start_time": None,
                "validation_time": None,
                "learning_write_time": None,
                "availability_of_this_record": "TIMESTAMP_UNKNOWN",
                "phase_of_episode": "post_recovery" if ep.get("action") else "post_failure",
            },
            "workload": {
                "workload_type": workload_id,
                "scenario_mode": workload_id.replace("workload-", ""),
                "scenario_parameters": {},
                "runtime_config": {},
            },
            "observations": [],
            "agent_output": None,
            "failure": {
                "failure_class": failure_class,
                "failure_detected": failure_class != "NONE",
                "failure_detected_time": None,
                "ground_truth_source": "real_subprocess_exit_semantics" if failure_class != "NONE" else "NOT_APPLICABLE",
            },
            "prediction": {
                "prediction_id": None,
                "score": ep.get("prediction_score"),
                "model_artifact_version": None,
                "predictability_status": "NOT_EVALUATED",
                "auroc_family_level": None,
                "false_alarm_rate_family_level": None,
                "label_type": "MODEL_PREDICTION",
            } if ep.get("prediction_score") is not None else None,
            "decision": {
                "decision_id": f"{episode_id}-decision",
                "action": decision_action,
                "policy_profile": "generic",
                "safety_status": "AUTHORIZED" if ep.get("safety_authorized") else ("DENIED" if ep.get("safety_authorized") is False else "NOT_EVALUATED"),
                "rationale": "",
                "label_type": "MODEL_PREDICTION",
            } if decision_action is not None else None,
            "diagnosis": {
                "diagnosis_id": f"{episode_id}-diagnosis",
                "suspected_cause": diagnosis_hypothesis,
                "alternative_causes": [],
                "confidence": ep.get("diagnosis_confidence"),
                "causal_status": "OBSERVED" if diagnosis_hypothesis else "UNKNOWN",
                "memory_informed": bool(ep.get("memory_used")),
                "label_type": "MODEL_DIAGNOSIS",
            } if diagnosis_hypothesis is not None or ep.get("action") else None,
            "recovery": {
                "action_id": f"{episode_id}-action",
                "action_type": RECOVERY_ACTION_MAP.get(ep.get("action"), ep.get("action")),
                "reversible": None,
                "authorization_required": True,
                "authorized": ep.get("safety_authorized"),
                "executed": ep.get("action") is not None,
                "executor_self_report": ep.get("validation"),
                "recovery_success_rate_family_level": None,
            } if ep.get("action") is not None else None,
            "safety": {
                "safety_gate_evaluated": ep.get("safety_authorized") is not None,
                "unsafe_authorization": False,
                "circuit_breaker_triggered": False,
            },
            "validation": {
                "validation_status": validation_status_norm,
                "validator": "SignalRecoveryValidator_independent_rederivation",
                "label_type": "OBSERVED_OUTCOME_VALIDATED",
            } if ep.get("action") is not None else None,
            "memory_interaction": {
                "memory_id_written": None,
                "memory_version_at_write": None,
                "memory_matches_read": [],
                "scope_key": f"{workload_id}|UNSPECIFIED_PRE_4_9|{failure_class}",
            } if ep.get("memory_used") is not None else None,
            "generalization": None,
            "labels": [
                {
                    "label_type": "DERIVED_LABEL",
                    "value": failure_class,
                    "origin_record_id": record_id,
                    "is_ground_truth_eligible": False,
                },
                {
                    "label_type": "OBSERVED_OUTCOME_VALIDATED",
                    "value": validation_status_norm,
                    "origin_record_id": record_id,
                    "is_ground_truth_eligible": True,
                } if ep.get("action") is not None else None,
            ],
            "split_assignment": _split_bucket(group_key),
            "capability_grade_context": "NOT_GRADED",
            "outcome_class": _outcome_class(failure_class, validation_status_norm if ep.get("action") is not None else None, decision_action),
            "final_state": ep.get("final_state"),
            "state_history": ep.get("state_history", []),
            "learning_recorded": ep.get("learning_recorded"),
            "memory_used": ep.get("memory_used"),
            "failure_class_mapping_fallback_used": unmapped,
        }
        rec["labels"] = [l for l in rec["labels"] if l is not None]
        records.append(rec)

    # --- Phase 4.5 continuous-mode (40 episodes) ---
    src_hash_45 = hashcache.get(src.PHASE4_5_CONTINUOUS)
    for seq, ep in enumerate(src.iter_phase4_5_continuous_episodes()):
        run_id = ep["run_id"]
        episode_local_id = ep["episode"]
        episode_id = f"phase4.5-continuous-{episode_local_id}"
        workload_id = ep["workload_id"]
        workload_type = ep.get("workload_type", "")
        diagnosis_hypothesis = ep.get("diagnosis_hypothesis")
        failure_class, unmapped = infer_failure_class(diagnosis_hypothesis, workload_type)
        validation_status = ep.get("validation")
        validation_status_norm = "UNKNOWN" if validation_status is None else validation_status
        action = ep.get("action")
        group_key = workload_id
        record_id = compute_record_id(
            DATASET_VERSION, src_hash_45, run_id, episode_id, "controlled_runtime_episode", seq,
        )
        record_id_full = compute_record_id_full(
            DATASET_VERSION, src_hash_45, run_id, episode_id, "controlled_runtime_episode", seq,
        )
        rec = {
            "identity": {
                "dataset_version": DATASET_VERSION,
                "schema_version": SCHEMA_VERSION,
                "source_artifact_version": "phase4.5-controlled-runtime-v2",
                "record_id": record_id,
                "record_id_full_digest": record_id_full,
                "track": "controlled_runtime",
                "environment_id": "UNSPECIFIED_PRE_4_9",
                "environment_role": "UNSPECIFIED",
                "workload_id": workload_id,
                "run_id": run_id,
                "episode_id": episode_id,
                "seed": None,
                "group_key": group_key,
            },
            "provenance": {
                "source": "experiments/results/phase4_5_autonomy_pipeline_at_scale/continuous_mode_metrics.jsonl",
                "source_version": "phase4.5-autonomy-pipeline-at-scale",
                "source_record_id": run_id,
                "extraction_method": "direct_telemetry_read",
                "transformation": "identity",
                "transformation_version": None,
                "timestamp_quality": "UNKNOWN",
                "checksum": src_hash_45,
                "evidence_class": 2,
                "frozen_run_dir": "experiments/results/phase4_5_autonomy_pipeline_at_scale",
            },
            "experimental_boundary": "controlled_runtime_evidence",
            "evidence_class": 2,
            "temporal": {
                "observation_time": None,
                "decision_time": "1970-01-01T00:00:00Z",
                "failure_time": None,
                "recovery_start_time": None,
                "validation_time": None,
                "learning_write_time": None,
                "availability_of_this_record": "TIMESTAMP_UNKNOWN",
                "phase_of_episode": "post_recovery" if action else "post_failure",
            },
            "workload": {
                "workload_type": workload_type,
                "scenario_mode": workload_type,
                "scenario_parameters": {"elapsed_seconds": ep.get("elapsed_seconds")},
                "runtime_config": {},
            },
            "observations": [],
            "agent_output": None,
            "failure": {
                "failure_class": failure_class,
                "failure_detected": failure_class != "NONE",
                "failure_detected_time": None,
                "ground_truth_source": "real_subprocess_exit_semantics" if failure_class != "NONE" else "NOT_APPLICABLE",
            },
            "prediction": None,
            "decision": None,
            "diagnosis": {
                "diagnosis_id": f"{episode_id}-diagnosis",
                "suspected_cause": diagnosis_hypothesis,
                "alternative_causes": [],
                "confidence": None,
                "causal_status": "OBSERVED" if diagnosis_hypothesis else "UNKNOWN",
                "memory_informed": False,
                "label_type": "MODEL_DIAGNOSIS",
            } if diagnosis_hypothesis is not None or action else None,
            "recovery": {
                "action_id": f"{episode_id}-action",
                "action_type": RECOVERY_ACTION_MAP.get(action, action),
                "reversible": None,
                "authorization_required": True,
                "authorized": None,
                "executed": action is not None,
                "executor_self_report": validation_status,
                "recovery_success_rate_family_level": None,
            } if action is not None else None,
            "safety": {
                "safety_gate_evaluated": False,
                "unsafe_authorization": False,
                "circuit_breaker_triggered": False,
            },
            "validation": {
                "validation_status": validation_status_norm,
                "validator": "SignalRecoveryValidator_independent_rederivation",
                "label_type": "OBSERVED_OUTCOME_VALIDATED",
            } if action is not None else None,
            "memory_interaction": None,
            "generalization": None,
            "labels": [
                {
                    "label_type": "DERIVED_LABEL",
                    "value": failure_class,
                    "origin_record_id": record_id,
                    "is_ground_truth_eligible": False,
                },
                {
                    "label_type": "OBSERVED_OUTCOME_VALIDATED",
                    "value": validation_status_norm,
                    "origin_record_id": record_id,
                    "is_ground_truth_eligible": True,
                } if action is not None else None,
            ],
            "split_assignment": _split_bucket(group_key),
            "capability_grade_context": "NOT_GRADED",
            "outcome_class": _outcome_class(failure_class, validation_status_norm if action is not None else None, None),
            "final_state": ep.get("final_state"),
            "elapsed_seconds": ep.get("elapsed_seconds"),
            "failure_class_mapping_fallback_used": unmapped,
        }
        rec["labels"] = [l for l in rec["labels"] if l is not None]
        records.append(rec)

    return records


def _agent_record_common(dataset_version, src_hash, source_path, source_version, task_family,
                          run_id, workload_id, seed, seq, is_correct, prediction_score, agent_output):
    episode_id = f"episode-{run_id}"
    group_key = workload_id
    record_id = compute_record_id(dataset_version, src_hash, run_id, episode_id, "agent_task_episode", seq)
    record_id_full = compute_record_id_full(dataset_version, src_hash, run_id, episode_id, "agent_task_episode", seq)
    failure_class = "NONE" if is_correct else "AGENT_INCORRECT_ANSWER"
    rec = {
        "identity": {
            "dataset_version": dataset_version,
            "schema_version": SCHEMA_VERSION,
            "source_artifact_version": "phase4.6-4.10-agent-task-evidence",
            "record_id": record_id,
            "record_id_full_digest": record_id_full,
            "track": "agent_task",
            "environment_id": "UNSPECIFIED_PRE_4_9",
            "environment_role": "UNSPECIFIED",
            "workload_id": workload_id,
            "run_id": run_id,
            "episode_id": episode_id,
            "seed": seed,
            "group_key": group_key,
        },
        "provenance": {
            "source": source_path,
            "source_version": source_version,
            "source_record_id": run_id,
            "extraction_method": "direct_telemetry_read",
            "transformation": "identity",
            "transformation_version": None,
            "timestamp_quality": "UNKNOWN",
            "checksum": src_hash,
            "evidence_class": 1,
            "frozen_run_dir": "experiments/results/phase4_6_to_4_10/20260824T133029Z",
        },
        "experimental_boundary": "research_evaluation_evidence",
        "evidence_class": 1,
        "temporal": {
            "observation_time": None,
            "decision_time": "1970-01-01T00:00:00Z",
            "failure_time": None,
            "recovery_start_time": None,
            "validation_time": None,
            "learning_write_time": None,
            "availability_of_this_record": "TIMESTAMP_UNKNOWN",
            "phase_of_episode": "post_failure" if not is_correct else "post_recovery",
        },
        "workload": {
            "workload_type": task_family,
            "scenario_mode": task_family,
            "scenario_parameters": {},
            "runtime_config": {},
        },
        "observations": [],
        "agent_output": agent_output,
        "failure": {
            "failure_class": failure_class,
            "failure_detected": failure_class != "NONE",
            "failure_detected_time": None,
            "ground_truth_source": "agent_oracle_mismatch",
        },
        "prediction": {
            "prediction_id": None,
            "score": prediction_score,
            "model_artifact_version": None,
            "predictability_status": "NOT_EVALUATED",
            "auroc_family_level": AGENT_FAMILY_AUROC.get(task_family),
            "false_alarm_rate_family_level": None,
            "label_type": "MODEL_PREDICTION",
        },
        "decision": None,
        "diagnosis": None,
        "recovery": None,
        "safety": {
            "safety_gate_evaluated": False,
            "unsafe_authorization": False,
            "circuit_breaker_triggered": False,
        },
        "validation": None,
        "memory_interaction": None,
        "generalization": None,
        "labels": [
            {
                "label_type": "OBJECTIVE_GROUND_TRUTH",
                "value": is_correct,
                "origin_record_id": record_id,
                "is_ground_truth_eligible": True,
            },
        ],
        "split_assignment": _split_bucket(group_key),
        "capability_grade_context": "NOT_GRADED",
        "outcome_class": "ANSWERED_CORRECT" if is_correct else "ANSWERED_INCORRECT",
        "final_state": "COMPLETED",
    }
    return rec


def build_agent_task_records(hashcache: SourceHashCache) -> list[dict]:
    records: list[dict] = []

    # Arithmetic self-consistency (2000)
    src_hash = hashcache.get(src.ARITHMETIC_EPISODES)
    for seq, row in enumerate(src.iter_arithmetic_task_records()):
        run_id = row["example_id"]
        seed = row.get("seed")
        workload_id = f"agent-arithmetic-seed-{seed}"
        agent_output = {
            "task_family": "arithmetic_self_consistency",
            "task_id": run_id,
            "difficulty": row.get("difficulty"),
            "expression": row.get("expression"),
            "samples": row.get("samples"),
            "majority_answer": row.get("majority_answer"),
            "agreement_rate": row.get("agreement_rate"),
            "correct_answer": row.get("correct_answer"),
            "is_correct": row.get("is_correct"),
        }
        rec = _agent_record_common(
            DATASET_VERSION, src_hash,
            "experiments/results/phase4_6_to_4_10/20260824T133029Z/raw/episodes/arithmetic_episodes.json",
            "phase4.6-4.10-arithmetic-episodes",
            "arithmetic_self_consistency", run_id, workload_id, seed, seq,
            row.get("is_correct"), row.get("agreement_rate"), agent_output,
        )
        records.append(rec)

    # Sentiment softmax-margin (660)
    src_hash = hashcache.get(src.CLASSIFICATION_PREDICTIONS)
    for seq, row in enumerate(src.iter_sentiment_task_records()):
        run_id = row["example_id"]
        workload_id = f"agent-sentiment-{run_id}"
        agent_output = {
            "task_family": "sentiment_softmax_margin",
            "model_checkpoint": "distilbert-base-uncased-finetuned-sst-2-english",
            "template_label": row.get("true_label"),
            "predicted_label": row.get("predicted_label"),
            "softmax_margin": row.get("margin"),
            "temperature_scaled": False,
            "is_correct": row.get("is_correct"),
        }
        rec = _agent_record_common(
            DATASET_VERSION, src_hash,
            "experiments/results/phase4_6_to_4_10/20260824T133029Z/raw/predictions/classification_predictions.json",
            "phase4.6-4.10-classification-predictions",
            "sentiment_softmax_margin", run_id, workload_id, None, seq,
            row.get("is_correct"), row.get("margin"), agent_output,
        )
        records.append(rec)

    # Extractive QA span-logit (400)
    src_hash = hashcache.get(src.QA_PREDICTIONS)
    for seq, row in enumerate(src.iter_qa_task_records()):
        run_id = row["example_id"]
        workload_id = f"agent-qa-{run_id}"
        gold_answers = row.get("gold_answers") or []
        agent_output = {
            "task_family": "extractive_qa_span_logit",
            "model_checkpoint": "distilbert-base-cased-distilled-squad",
            "gold_answer_span": gold_answers[0] if gold_answers else None,
            "predicted_span": row.get("predicted_answer"),
            "span_logit_confidence": row.get("span_confidence"),
            "is_correct": row.get("is_correct"),
        }
        rec = _agent_record_common(
            DATASET_VERSION, src_hash,
            "experiments/results/phase4_6_to_4_10/20260824T133029Z/raw/predictions/qa_predictions.json",
            "phase4.6-4.10-qa-predictions",
            "extractive_qa_span_logit", run_id, workload_id, None, seq,
            row.get("is_correct"), row.get("span_confidence"), agent_output,
        )
        records.append(rec)

    return records


def build_all_records() -> tuple[list[dict], SourceHashCache]:
    hashcache = SourceHashCache()
    records = []
    records.extend(build_controlled_runtime_records(hashcache))
    records.extend(build_agent_task_records(hashcache))
    # Final deterministic global ordering: by record_id (stable, content-derived).
    records.sort(key=lambda r: r["identity"]["record_id"])
    return records, hashcache
