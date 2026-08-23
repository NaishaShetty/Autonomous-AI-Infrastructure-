<a id="schema"></a>
# SCHEMA
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/SCHEMA.md`  
**Role:** The canonical ReliabilityEvent schema reference (still in active use, unmodified since Phase 1/2).

# Canonical Reliability/Failure Event Schema

Defined in [`src/schema/events.py`](../src/schema/events.py) as the pydantic
model `ReliabilityEvent`. This is the single representation shared by the
reliability (confidence) subsystem and the failure-memory subsystem — see
`PHASE1_AUDIT_REPORT.md` sections 2/3/8 for why the two source prototypes'
incompatible representations made this necessary.

## Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `event_id` | `str` | auto (uuid4 hex) | Primary key |
| `timestamp` | `datetime` (tz-aware, UTC) | auto | Coerced to UTC if naive |
| `workload_id` | `str` | yes | Identifies the monitored model/workload |
| `source` | `EventSource` enum | yes | `reliability_engine` \| `failure_memory` \| `benchmark` |
| `context` | `dict[str, float]` | yes | Structured numeric feature vector describing the input. Canonical replacement for both source repos' ad-hoc feature representations. |
| `raw_confidence` | `float \| None` | no | Pre-calibration confidence, `[0.0, 1.0]` |
| `confidence` | `float` | yes | Calibrated confidence. **Always `[0.0, 1.0]`, never 0-100.** |
| `failure_risk` | `float \| None` | no | Failure-memory's similarity-based risk, `[0.0, 1.0]` |
| `decision` | `Decision` enum | yes | `ANSWER` \| `ABSTAIN` \| `REVIEW` |
| `abstained` | `bool` | yes | Must equal `decision != ANSWER` (validated) |
| `is_failure` | `bool` | default `False` | True only for confirmed wrong `ANSWER`s; failure-memory stores only these |
| `failure_cluster` | `int \| None` | no | Assigned by failure-memory clustering |
| `outcome` | `Outcome` enum | default `UNKNOWN` | `CORRECT` \| `INCORRECT` \| `UNKNOWN` |
| `metadata` | `dict` | default `{}` | Free-form provenance only — must never contain personal data (see `PHASE1_AUDIT_REPORT.md` section 5/11 on the `reliability.db` credential leak this project does not repeat) |

## Validation rules

- `confidence`, `raw_confidence`, `failure_risk` — must lie in `[0.0, 1.0]`. This is a regression guard for the Phase 1 `global_reliability_score: 189.61` bug: any code path that hands a 0-100-scale number to this model raises `ValidationError` immediately instead of silently corrupting an aggregate metric. See `tests/unit/test_schema.py::test_confidence_over_100_scale_is_rejected`.
- `abstained` must be consistent with `decision`.
- `timestamp` is normalized to UTC.
- The model is `extra="forbid"` — an unexpected field is a schema violation, not silently dropped or accepted.

## Presentation-layer conversion

`confidence_to_percent(confidence: float) -> float` is the *only* place a
0-1 confidence is converted to a 0-100 display value. Presentation code
(dashboards, reports) must call this rather than re-deriving the conversion.
