"""Phase 4.0: episodic/incident data generation.

Builds temporally-ordered, recurring-incident streams on top of Phase 3's
frozen benchmark machinery, per ``configs/phase4_0_episodic_protocol.json``
(written and frozen before this module's output was first generated).

This module does NOT modify anything Phase 3 froze
(``docs/PHASE3_FREEZE.md``): it calls ``src.pipeline_builder.build_system``,
``src.data.synthetic.generate_regime_stream``,
``src.evaluation.attacks.{apply_feature_noise,apply_feature_dropout}``,
``src.evaluation.decision_policy.{TierThresholds,assign_tier,RiskTier,
TIER_ACTION}``, ``src.evaluation.diagnosis.diagnose``, and
``src.evaluation.recovery.attempt_recovery`` exactly as Phase 3.6's own
benchmark scripts do -- read-only reuse of already-frozen components, no
in-place edits.

What is genuinely new here (not present anywhere in Phase 3): multiple
independent "workload" identities (distinct trained systems), a fixed
vocabulary of recurring "conditions" applied to each workload's held-out
test stream, a deterministic recurrence/scheduling rule that spreads
occurrences across simulated time, a known/novel combo split with
ground-truth novelty labels, and a chronological train/validation/test
split per combo -- the structure Phase 4.1's memory, 4.2's pattern
learning, 4.3's recovery-strategy learning, 4.6's continual-learning
experiments, and 4.7's generalization evaluation all require and which
Phase 3's i.i.d. benchmark never provided.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from src.data.synthetic import FEATURE_NAMES, StreamSample, generate_regime_stream
from src.evaluation.attacks import apply_feature_dropout, apply_feature_noise
from src.evaluation.decision_policy import TIER_ACTION, RiskTier, TierThresholds, assign_tier
from src.evaluation.diagnosis import diagnose
from src.evaluation.recovery import RecoveryOutcome, attempt_recovery
from src.pipeline_builder import DEFAULT_REGIME_SIZES, TrainedSystem, build_system

PROTOCOL_PATH = Path(__file__).resolve().parents[2] / "configs" / "phase4_0_episodic_protocol.json"


def load_protocol(path: Path = PROTOCOL_PATH) -> dict:
    data = json.loads(path.read_text())
    if not data.get("_frozen"):
        raise ValueError(f"{path} is not marked frozen")
    return data


@dataclass(frozen=True)
class Combo:
    workload_id: str
    condition_id: str
    is_novel: bool


@dataclass
class EpisodeStep:
    """One scored sample within one incident occurrence. Field set matches
    docs/PHASE4_PLAN.md section 1's episode tuple: workload identity,
    timestamp, context, model prediction/confidence, decision, outcome,
    recovery action/result -- plus the ground-truth recurrence/novelty/
    split labels only this generator can attach (it knows which condition
    it applied and how many times)."""

    step: int
    occurrence_ordinal: int
    sample_index_in_occurrence: int
    workload_id: str
    condition_id: str
    is_novel_combo: bool
    split: str  # "train" | "validation" | "test"
    occurrence_count_for_combo: int  # 1-based: which occurrence of this exact combo this is

    context: dict
    true_label: int
    predicted_label: int
    confidence: float
    b_risk_score: float
    tier: str
    decision: str
    is_failure: bool
    outcome: str  # "CORRECT" | "INCORRECT"

    diagnosed_cause: Optional[str] = None
    recovery_attempted: bool = False
    recovery_action: Optional[str] = None
    recovery_outcome: Optional[str] = None
    recovery_correct: Optional[bool] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EpisodicDataset:
    protocol_version: str
    steps: list  # list[EpisodeStep]
    workload_ids: list
    known_combos: list
    novel_combos: list

    def to_records(self) -> list:
        return [s.to_dict() for s in self.steps]


def _sorted_combos(protocol: dict) -> tuple[list[Combo], list[Combo]]:
    workload_ids = sorted(w["workload_id"] for w in protocol["workloads"])
    condition_ids = sorted(c["condition_id"] for c in protocol["conditions"])
    novel_pairs = {(c["workload_id"], c["condition_id"]) for c in protocol["novel_combos"]}

    known, novel = [], []
    for w in workload_ids:
        for c in condition_ids:
            is_novel = (w, c) in novel_pairs
            combo = Combo(workload_id=w, condition_id=c, is_novel=is_novel)
            (novel if is_novel else known).append(combo)
    return known, novel


def _condition_by_id(protocol: dict, condition_id: str) -> dict:
    for c in protocol["conditions"]:
        if c["condition_id"] == condition_id:
            return c
    raise ValueError(f"unknown condition_id: {condition_id}")


def _apply_condition(
    samples: list[StreamSample], condition: dict, seed: int, attack_ordinal_override: Optional[int] = None,
) -> list[StreamSample]:
    mechanism = condition["mechanism"]
    if mechanism is None:
        return samples
    ordinal = attack_ordinal_override if attack_ordinal_override is not None else condition["attack_ordinal"]
    if mechanism == "feature_noise":
        return apply_feature_noise(
            samples, FEATURE_NAMES, std=condition["parameters"]["std"], seed=seed, attack_ordinal=ordinal,
        )
    if mechanism == "feature_dropout":
        return apply_feature_dropout(samples, FEATURE_NAMES, dropped_features=condition["parameters"]["dropped_features"])
    raise ValueError(f"unknown mechanism: {mechanism}")


def _build_workloads(protocol: dict) -> dict:
    """One TrainedSystem + B-score TierThresholds per workload, built via
    the unmodified, frozen ``build_system`` -- read-only reuse."""
    regime_sizes = tuple(protocol["regime_sizes"])
    n_clusters = protocol["n_clusters"]
    systems = {}
    for w in protocol["workloads"]:
        wid, wseed = w["workload_id"], w["seed"]
        system = build_system(regime_sizes=regime_sizes, n_clusters=n_clusters, seed=wseed)
        regime2_b_scores = _regime2_b_scores(wseed, regime_sizes, system)
        thresholds = TierThresholds.derive(regime2_b_scores)
        systems[wid] = {"system": system, "seed": wseed, "thresholds": thresholds}
    return systems


def _regime2_b_scores(seed: int, regime_sizes: tuple, system: TrainedSystem) -> np.ndarray:
    """Regenerates this workload's regime 2 (same deterministic call
    ``build_system`` makes internally -- same function, same seed -> the
    exact same samples, not new data) and computes B = 1 - calibrated
    confidence for each, for threshold derivation. Mirrors
    benchmarks/phase3_3_generalization.py's
    _reconstruct_regime2_with_confidences, specialized to B alone."""
    stream = generate_regime_stream(regime_sizes=regime_sizes, seed=seed)
    regime2 = [s for s in stream if s.regime == 2]
    scores = []
    for s in regime2:
        x = np.array([s.context[f] for f in FEATURE_NAMES], dtype=float)
        pred = system.workload_model.predict(x)
        calib_features = {**s.context, "predicted_proba": pred.predicted_proba, "margin": pred.margin, "entropy": pred.entropy}
        calib_result = system.calibrator.predict(calib_features)
        scores.append(1.0 - calib_result.calibrated_confidence)
    return np.array(scores)


def _score_sample(system: TrainedSystem, sample: StreamSample) -> tuple:
    x = np.array([sample.context[f] for f in FEATURE_NAMES], dtype=float)
    pred = system.workload_model.predict(x)
    calib_features = {**sample.context, "predicted_proba": pred.predicted_proba, "margin": pred.margin, "entropy": pred.entropy}
    calib_result = system.calibrator.predict(calib_features)
    b_score = 1.0 - calib_result.calibrated_confidence
    return pred, calib_result.calibrated_confidence, b_score


def _split_for_occurrence(occurrence_ordinal: int, is_novel: bool, known_occurrences: int) -> str:
    if is_novel:
        return "test"
    if occurrence_ordinal < known_occurrences - 2:
        return "train"
    if occurrence_ordinal == known_occurrences - 2:
        return "validation"
    return "test"


def generate_episode_stream(protocol: Optional[dict] = None) -> EpisodicDataset:
    protocol = protocol or load_protocol()
    known_combos, novel_combos = _sorted_combos(protocol)
    workloads = _build_workloads(protocol)

    known_occurrences = protocol["recurrence"]["known_combo_occurrences"]
    novel_occurrences = protocol["recurrence"]["novel_combo_occurrences"]
    batch_size = protocol["recurrence"]["batch_size"]
    retry_stride = protocol["generation_rules"]["retry_ordinal_stride"]
    n_known = len(known_combos)

    steps: list[EpisodeStep] = []

    def _emit(combo: Combo, occurrence_ordinal: int, combo_rank: int, base_step: int, n_occurrences_for_combo: int) -> None:
        wl = workloads[combo.workload_id]
        system: TrainedSystem = wl["system"]
        thresholds: TierThresholds = wl["thresholds"]
        condition = _condition_by_id(protocol, combo.condition_id)

        start = occurrence_ordinal * batch_size
        end = start + batch_size
        chunk = system.test_stream[start:end]
        if len(chunk) < batch_size:
            raise ValueError(
                f"workload {combo.workload_id} test_stream exhausted for combo {combo.condition_id} "
                f"occurrence {occurrence_ordinal} (needed rows {start}:{end}, have {len(system.test_stream)})"
            )

        # Each occurrence of a recurring condition draws its own
        # independent corruption realization (a fresh instance of the same
        # failure mode recurring, not a byte-identical repeat) -- distinct,
        # deterministic ordinal per occurrence, per configs/phase4_0_
        # episodic_protocol.json's generation_rules.retry_ordinal_stride.
        occurrence_ordinal_for_mechanism = (
            condition["attack_ordinal"] + occurrence_ordinal * retry_stride if condition["mechanism"] is not None else None
        )
        corrupted = _apply_condition(chunk, condition, seed=wl["seed"], attack_ordinal_override=occurrence_ordinal_for_mechanism)

        split = _split_for_occurrence(occurrence_ordinal, combo.is_novel, known_occurrences)
        step = base_step

        for i, sample in enumerate(corrupted):
            pred, confidence, b_score = _score_sample(system, sample)
            tier = assign_tier(b_score, thresholds)
            decision = TIER_ACTION[tier]
            is_failure = pred.predicted_label != sample.label
            outcome = "INCORRECT" if is_failure else "CORRECT"

            diagnosed_cause = None
            recovery_attempted = False
            recovery_action = None
            recovery_outcome = None
            recovery_correct = None

            if tier == RiskTier.CRITICAL:
                diagnosed_cause = diagnose(sample.context, FEATURE_NAMES)
                original_ordinal = (
                    occurrence_ordinal_for_mechanism if condition["mechanism"] == "feature_noise" else None
                )

                def _workload_predict(s: StreamSample):
                    return system.workload_model.predict(
                        np.array([s.context[f] for f in FEATURE_NAMES], dtype=float)
                    ).predicted_label

                def _b_score_fn(ctx: dict) -> float:
                    return _score_sample(system, StreamSample(context=ctx, label=0, regime=-1))[2]

                result = attempt_recovery(
                    sample,
                    original_score=b_score,
                    original_ordinal=original_ordinal,
                    seed=wl["seed"],
                    feature_names=FEATURE_NAMES,
                    workload_predict=_workload_predict,
                    score_fn=lambda ctx: _score_sample(system, StreamSample(context=ctx, label=0, regime=-1))[2],
                    b_score_fn=_b_score_fn,
                    thresholds=thresholds,
                    b_thresholds=thresholds,
                    condition_id=combo.condition_id,
                )
                recovery_attempted = True
                recovery_action = result.action_taken
                recovery_outcome = result.outcome.value
                recovery_correct = result.recovered_correct

            steps.append(
                EpisodeStep(
                    step=step,
                    occurrence_ordinal=occurrence_ordinal,
                    sample_index_in_occurrence=i,
                    workload_id=combo.workload_id,
                    condition_id=combo.condition_id,
                    is_novel_combo=combo.is_novel,
                    split=split,
                    occurrence_count_for_combo=occurrence_ordinal + 1,
                    context=dict(sample.context),
                    true_label=int(sample.label),
                    predicted_label=int(pred.predicted_label),
                    confidence=float(confidence),
                    b_risk_score=float(b_score),
                    tier=tier.value,
                    decision=decision.value,
                    is_failure=bool(is_failure),
                    outcome=outcome,
                    diagnosed_cause=diagnosed_cause,
                    recovery_attempted=recovery_attempted,
                    recovery_action=recovery_action,
                    recovery_outcome=recovery_outcome,
                    recovery_correct=recovery_correct,
                )
            )
            step += 1

    for combo_rank, combo in enumerate(known_combos):
        for occurrence_ordinal in range(known_occurrences):
            base_step = (occurrence_ordinal * n_known + combo_rank) * batch_size
            _emit(combo, occurrence_ordinal, combo_rank, base_step, known_occurrences)

    novel_base = known_occurrences * n_known * batch_size
    for novel_rank, combo in enumerate(novel_combos):
        for occurrence_ordinal in range(novel_occurrences):
            base_step = novel_base + novel_rank * batch_size
            _emit(combo, occurrence_ordinal, novel_rank, base_step, novel_occurrences)

    steps.sort(key=lambda s: s.step)

    return EpisodicDataset(
        protocol_version="phase4_0_episodic_protocol.json",
        steps=steps,
        workload_ids=sorted(workloads.keys()),
        known_combos=[asdict(c) for c in known_combos],
        novel_combos=[asdict(c) for c in novel_combos],
    )
