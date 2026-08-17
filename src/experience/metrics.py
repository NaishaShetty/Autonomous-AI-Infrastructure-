"""Phase 4.1.7: retrieval metrics.

Definitions fixed here, before evaluation, per
configs/phase4_1_experience_protocol.json.

**Relevance definition**: a stored experience is relevant to a query if it
shares the query's ground-truth ``condition_id`` (same underlying
corruption mechanism, or "clean") -- Phase 4.0's own generator ground
truth (docs/PHASE4_0_EPISODIC_DATA.md section 3). This is EVALUATION-ONLY
information: it is passed to these metric functions directly by the
benchmark script, never through a ``DecisionTimeQuery`` or any retrieval
function (see src/experience/schema.py module docstring and
src/experience/store.py's retrieve_* signatures, which only accept
DecisionTimeQuery).
"""
from __future__ import annotations

from typing import Optional

from .schema import Experience


def precision_at_k(retrieved: list[Experience], relevant_condition_id: str, k: int) -> Optional[float]:
    """(# retrieved among top-k sharing condition_id with the query) /
    (# actually retrieved, <= k). None if nothing was retrieved (empty
    store or k=0) -- not fabricated as 0.0, which would conflate "no
    signal" with "confirmed zero relevance"."""
    topk = retrieved[:k]
    if not topk:
        return None
    hits = sum(1 for e in topk if e.provenance.condition_id == relevant_condition_id)
    return hits / len(topk)


def recall_at_k(
    retrieved: list[Experience], relevant_condition_id: str, k: int, total_relevant_in_store: int
) -> Optional[float]:
    """(# retrieved among top-k sharing condition_id) / (total # store
    experiences sharing that condition_id). None if the store contains
    zero relevant experiences for this condition_id at all (undefined,
    not zero -- e.g. every occurrence of this exact condition_id was
    reserved as a novel combo and the store, built from train only,
    genuinely has none)."""
    if total_relevant_in_store == 0:
        return None
    topk = retrieved[:k]
    hits = sum(1 for e in topk if e.provenance.condition_id == relevant_condition_id)
    return hits / total_relevant_in_store


def same_workload_and_condition_rate(retrieved: list[Experience], workload_id: str, condition_id: str, k: int) -> Optional[float]:
    """Secondary diagnostic (not the primary metric): among the top-k
    retrieved, the fraction that match BOTH the query's workload_id AND
    condition_id -- distinguishes "found the right failure mode, any
    workload" from "found the right failure mode on the SAME workload"."""
    topk = retrieved[:k]
    if not topk:
        return None
    hits = sum(1 for e in topk if e.provenance.workload_id == workload_id and e.provenance.condition_id == condition_id)
    return hits / len(topk)


def count_relevant_in_store(store_experiences: list[Experience], condition_id: str) -> int:
    return sum(1 for e in store_experiences if e.provenance.condition_id == condition_id)
