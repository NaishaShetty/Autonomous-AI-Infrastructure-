"""Offline reliability-model evaluation primitives.

These helpers operate on an explicit prepared dataset. They do not fetch data,
choose a split from evaluation outcomes, or train at runtime. A caller must
provide predeclared split/group assignments and labels available at the stated
prediction time.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score


class EvaluationProtocolError(ValueError):
    """Raised when a prepared dataset violates the declared evaluation protocol."""


def validate_group_disjointness(records: Sequence[Mapping[str, Any]], *, group_key: str = "group_id", split_key: str = "split") -> None:
    groups: dict[str, set[str]] = defaultdict(set)
    for record in records:
        split = str(record.get(split_key, ""))
        group = str(record.get(group_key, ""))
        if split not in {"train", "validation", "evaluation"} or not group:
            raise EvaluationProtocolError("every record needs a declared split and non-empty independent group")
        groups[group].add(split)
    overlap = {group: sorted(splits) for group, splits in groups.items() if len(splits) > 1}
    if overlap:
        raise EvaluationProtocolError(f"independent groups cross split boundaries: {overlap}")


def validate_feature_availability(records: Iterable[Mapping[str, Any]], *, feature_keys: Sequence[str], label_key: str = "label") -> None:
    for record in records:
        features = record.get("features")
        if not isinstance(features, Mapping):
            raise EvaluationProtocolError("each record needs a mapping of decision-time features")
        missing = [key for key in feature_keys if key not in features]
        if missing:
            raise EvaluationProtocolError(f"missing declared features: {missing}")
        if label_key not in record:
            raise EvaluationProtocolError("each record needs an explicit outcome label")
        if any(key in features for key in ("future_label", "post_failure", "outcome", "recovery_result")):
            raise EvaluationProtocolError("post-outcome fields cannot be used as decision-time features")


def _binary_metrics(labels: np.ndarray, risks: np.ndarray) -> dict[str, float | None]:
    if len(np.unique(labels)) < 2:
        return {"auroc": None, "auprc": None, "brier_score": brier_score_loss(labels, risks), "log_loss": None}
    return {
        "auroc": float(roc_auc_score(labels, risks)),
        "auprc": float(average_precision_score(labels, risks)),
        "brier_score": float(brier_score_loss(labels, risks)),
        "log_loss": float(log_loss(labels, np.clip(risks, 1e-7, 1 - 1e-7), labels=[0, 1])),
    }


def calibration_metrics(labels: Sequence[int], risks: Sequence[float], *, bins: int = 10) -> dict[str, Any]:
    y = np.asarray(labels, dtype=int)
    p = np.asarray(risks, dtype=float)
    if len(y) != len(p) or len(y) == 0:
        raise EvaluationProtocolError("labels and risks must be non-empty and have equal length")
    edges = np.linspace(0.0, 1.0, bins + 1)
    ece = 0.0
    rows: list[dict[str, float | int]] = []
    for index in range(bins):
        mask = (p >= edges[index]) & ((p < edges[index + 1]) if index < bins - 1 else (p <= edges[index + 1]))
        count = int(mask.sum())
        if count == 0:
            continue
        mean_prediction = float(p[mask].mean())
        observed_rate = float(y[mask].mean())
        ece += (count / len(y)) * abs(mean_prediction - observed_rate)
        rows.append({"bin": index, "count": count, "mean_prediction": mean_prediction, "observed_rate": observed_rate})
    return {
        "brier_score": float(brier_score_loss(y, p)),
        "expected_calibration_error": float(ece),
        "reliability_bins": rows,
    }


def abstention_metrics(labels: Sequence[int], risks: Sequence[float], *, accept_risk_threshold: float, abstain_uncertainty: Sequence[float] | None = None, uncertainty_threshold: float | None = None) -> dict[str, float | int | None]:
    y = np.asarray(labels, dtype=int)
    p = np.asarray(risks, dtype=float)
    if len(y) != len(p) or len(y) == 0:
        raise EvaluationProtocolError("labels and risks must be non-empty and have equal length")
    accepted = p < accept_risk_threshold
    if abstain_uncertainty is not None and uncertainty_threshold is not None:
        u = np.asarray(abstain_uncertainty, dtype=float)
        if len(u) != len(y):
            raise EvaluationProtocolError("uncertainty length must match labels")
        accepted &= u < uncertainty_threshold
    abstained = ~accepted
    accepted_count = int(accepted.sum())
    abstained_count = int(abstained.sum())
    return {
        "coverage": float(accepted.mean()),
        "selective_risk": float(y[accepted].mean()) if accepted_count else None,
        "abstention_rate": float(abstained.mean()),
        "accepted_failure_rate": float(y[accepted].mean()) if accepted_count else None,
        "abstained_failure_rate": float(y[abstained].mean()) if abstained_count else None,
        "accepted_count": accepted_count,
        "abstained_count": abstained_count,
        "accept_risk_threshold": float(accept_risk_threshold),
        "uncertainty_threshold": float(uncertainty_threshold) if uncertainty_threshold is not None else None,
    }


def evaluate_predictions(labels: Sequence[int], risks: Sequence[float]) -> dict[str, Any]:
    y = np.asarray(labels, dtype=int)
    p = np.asarray(risks, dtype=float)
    if len(y) != len(p) or len(y) == 0:
        raise EvaluationProtocolError("labels and risks must be non-empty and have equal length")
    return {"count": int(len(y)), **_binary_metrics(y, p), "calibration": calibration_metrics(y, p)}
