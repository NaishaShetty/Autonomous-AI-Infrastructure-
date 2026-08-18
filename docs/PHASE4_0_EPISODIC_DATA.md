<a id="phase4-0-episodic-data"></a>
# PHASE4 0 EPISODIC DATA
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE4_0_EPISODIC_DATA.md`  
**Role:** Old Phase 4.0: synthetic episodic incident-stream generator.

# Phase 4.0 — Episodic Incident Data Generator

**Status: COMPLETE.** This document is the Phase 4.0 deliverable, per
[`docs/PHASE4_PLAN.md`](PHASE4_PLAN.md) section 1.

Companion artifacts: [`configs/phase4_0_episodic_protocol.json`](../configs/phase4_0_episodic_protocol.json),
[`src/data/episodic.py`](../src/data/episodic.py),
[`benchmarks/phase4_0_generate_episodes.py`](../benchmarks/phase4_0_generate_episodes.py),
[`benchmarks/phase4_0_leakage_audit.py`](../benchmarks/phase4_0_leakage_audit.py),
[`experiments/results/phase4_0/`](../experiments/results/phase4_0/),
[`tests/integration/test_phase4_0_episodic.py`](../tests/integration/test_phase4_0_episodic.py).

## 1. Objective

Phase 3's benchmark (`src/data/synthetic.py`) generates i.i.d. classification
samples under a single regime-drift condition — no recurring workload
identity, no incident recurrence over simulated time, no known/novel
ground truth. Phase 4.1 (failure memory), 4.2 (pattern learning), 4.3
(recovery strategy learning), 4.6 (continual learning), and 4.7
(generalization) all require exactly that structure. Phase 4.0 builds it,
without touching anything Phase 3 froze.

## 2. What is reused, unmodified, read-only

Per `docs/PHASE3_FREEZE.md` and the approved integration boundary
(`docs/PHASE4_PLAN.md` review decisions): `src.pipeline_builder.build_system`
(one call per workload seed), `src.data.synthetic.generate_regime_stream`
(regime-2 reconstruction for threshold derivation, exactly as
`benchmarks/phase3_3_generalization.py`'s `_reconstruct_regime2_with_confidences`
does), `src.evaluation.attacks.{apply_feature_noise,apply_feature_dropout}`,
`src.evaluation.decision_policy.{TierThresholds,assign_tier,RiskTier,
TIER_ACTION}`, `src.evaluation.diagnosis.diagnose`, and
`src.evaluation.recovery.attempt_recovery`. No new module wraps or edits
any of these in place; `src/data/episodic.py` is new, additive code that
calls them.

**Acting candidate: B (calibrated confidence) alone.** Phase 3.6 (frozen)
established B is the strongest, cheapest signal at every tested axis; F/BF
add no measured value. Driving the episodic stream's tiering/decision/
recovery off B alone is therefore the research-justified minimal choice,
not an arbitrary simplification — see
`configs/phase4_0_episodic_protocol.json.acting_candidate`. F/BF-driven
episode variants are explicitly deferred to a later subphase if a
`src/experience/` component needs them, not silently dropped.

## 3. What is genuinely new

- **4 independent "workloads"** (`workload_1..4`, seeds 101–104, disjoint
  from Phase 3's frozen seed list `[1,2,3,4,5,42]`) — each a distinct
  `build_system` call, i.e. a structurally different decision boundary
  (`base_w`), not a relabeling of one shared model.
- **A fixed condition vocabulary** (`clean`, `feature_noise_mild`,
  `feature_noise_severe`, `feature_dropout`) reusing Phase 3.5's frozen
  attack parameters verbatim (`configs/phase3_5_attack_protocol.json`),
  applied to each workload's own held-out `test_stream` (regimes 3+4,
  never used in that workload's own training).
- **Recurrence**: each known (workload, condition) combo occurs 5 times,
  each occurrence drawing a distinct 15-row chunk of that workload's
  `test_stream` and (for noise conditions) an independently-drawn
  corruption realization per occurrence (`attack_ordinal + occurrence_ordinal
  * 1000` — a genuinely new realization per recurrence, not a byte-identical
  repeat), so retry-recovery's re-roll is also unique per occurrence.
- **Known/novel combo split, fixed before generation**: 12 known combos
  recur across train/validation/test; 4 combos (`workload_4 ×
  {feature_noise_mild, feature_noise_severe, feature_dropout}` and
  `workload_1 × feature_dropout`) are entirely novel — zero occurrences
  before their single, frozen-test-only appearance. This gives two
  distinct, labeled generalization axes for Phase 4.7: a wholly unseen
  workload facing known condition families, and a well-known workload
  facing a condition it has never encountered.
- **Deterministic round-robin scheduling** across a global `step` index,
  so occurrences interleave through simulated time instead of bunching by
  combo, with novel combos scheduled strictly after every known-combo
  occurrence.
- **Per-combo chronological train/validation/test split**: occurrences
  0–2 → train, occurrence 3 → validation, occurrence 4 (chronologically
  last) → test — no combo's test occurrence ever precedes its own
  train/validation occurrences in `step` order.

## 4. Output schema (`EpisodeStep`)

One record per scored sample: `step`, `occurrence_ordinal`,
`sample_index_in_occurrence`, `workload_id`, `condition_id`,
`is_novel_combo`, `split`, `occurrence_count_for_combo`, `context`,
`true_label`, `predicted_label`, `confidence`, `b_risk_score`, `tier`,
`decision`, `is_failure`, `outcome`, and (CRITICAL-tier rows only)
`diagnosed_cause`, `recovery_attempted`, `recovery_action`,
`recovery_outcome`, `recovery_correct`. This is the full episode tuple
`docs/PHASE4_PLAN.md` section 1 specified, generated by scoring the new
incident structure through Phase 3.6's frozen decision/diagnosis/recovery
machinery — not a duplicate schema.

Information available at decision time vs. only after outcome: `context`,
`confidence`, `b_risk_score`, `tier`, `decision`, `diagnosed_cause`,
`recovery_action` are all knowable before the true label is checked;
`true_label`, `predicted_label` correctness, `outcome`, `is_failure`, and
`recovery_correct` are only knowable after — this distinction matters for
Phase 4.1's memory (which may only condition retrieval on pre-outcome
fields when simulating a live decision) and is preserved by keeping both
groups as separate, clearly-named fields rather than collapsing them.

## 5. Generated dataset (primary run, `configs/phase4_0_episodic_protocol.json` as committed)

| Metric | Value |
|---|---|
| Total steps | 960 |
| Workloads | 4 |
| Known combos | 12 |
| Novel combos | 4 |
| Train / Validation / Test rows | 540 / 180 / 240 |
| CRITICAL-tier rows | 109 |
| Recovery attempts | 109 |
| Recovered (RECOVERED outcome) | 9 |
| Content hash (SHA-256) | `c69a87ee877ed6090ed7e8d648d9da24fb8090fbb667b070724fe5d983f2057a` |

Regenerating with the same protocol reproduces this hash exactly (verified
by the leakage audit's `generation_is_deterministic` check and by manual
re-run during development). Full per-step records:
`experiments/results/phase4_0/episodes.json`; summary + environment
provenance: `experiments/results/phase4_0/manifest.json`.

The low recovered count (9/109 CRITICAL rows) is consistent with, not a
regression from, Phase 3.6's frozen finding that recovery only clears the
risk threshold for a modest minority of CRITICAL samples, and that
reconfigure recovers ~0% under `feature_dropout` — nothing here overrides
or is compared against that frozen result; the same recovery mechanics are
simply reused on a new incident stream.

## 6. Leakage/integrity audit — all 7 checks passed

`benchmarks/phase4_0_leakage_audit.py`:
`generation_is_deterministic`, `no_duplicate_rows_within_or_across_combos`,
`novel_combos_absent_from_train_and_validation`,
`novel_and_known_combo_sets_are_disjoint`,
`split_boundary_matches_protocol_rule`,
`chronological_no_future_leakage_within_combo`,
`no_regime_0_1_2_row_ever_emitted`. Result:
`experiments/results/phase4_0/leakage_audit.json`, `all_passed: true`. No
STOP condition triggered.

## 7. Tests

`tests/integration/test_phase4_0_episodic.py` — 13 tests, all passing:
the 7 leakage-audit checks run directly (not re-described), plus
structural assertions (expected combo/split row counts derived
arithmetically from the protocol, every context has exactly the 5 expected
feature keys, `decision` always matches `tier` via the frozen
`TIER_ACTION` mapping, recovery is attempted if and only if `tier ==
CRITICAL`, and `outcome`/`is_failure` are consistent with
`predicted_label` vs. `true_label`).

## 8. Limitations

- Only the B-alone acting candidate is used to drive tiering/decision/
  recovery in this generator; an F- or BF-driven episodic variant is not
  produced and would need its own protocol addendum if a later subphase
  needs it (unlikely, given Phase 3.6's finding that B alone is sufficient
  and cheapest).
- The condition vocabulary is exactly Phase 3.5's 3 attacks + clean — no
  new corruption mechanism is introduced; "novel condition" in this
  dataset always means a known mechanism applied to an unfamiliar
  workload/combo, not a mechanism the system has literally never seen in
  any form. This is a real scope limit for Phase 4.7's generalization
  claims and must be stated there, not overclaimed.
- Recurrence count (5 known-combo occurrences) and batch size (15) are
  small by design (fast, deterministic, inspectable smallest-valid-version
  choices per the Implementation Rule) — if Phase 4.6's continual-learning
  experiments need finer-grained checkpoints or more statistical power,
  this protocol's `recurrence` block would need a documented, pre-frozen
  revision (a new protocol version, not a silent edit of this one) before
  that experiment runs.
- Workload identity here is entirely synthetic (a different `base_w`
  decision boundary per seed) — it stands in for "a different deployed
  model/workload" structurally, not for any claim about real-world
  workload diversity.

## 9. What Phase 4.0 establishes

- A deterministic, reproducible, leakage-audited episodic incident
  generator exists and is tested — the structural prerequisite Phase 4.1
  through 4.7 needed and Phase 3's benchmark did not provide.
- Known-history and entirely-novel (workload, condition) combos are both
  represented in the frozen test split, with machine-checked disjointness
  from train/validation — Phase 4.7's generalization evaluation has real,
  labeled novel cases to test against, not an assumed novelty.
- All of this was built without editing any file `docs/PHASE3_FREEZE.md`
  lists as frozen, verified structurally (the `no_regime_0_1_2_row_ever_
  emitted` and `generation_is_deterministic` checks) rather than only by
  code inspection.

## 10. Next step

Per the frozen Phase 4 sequence, Phase 4.1 (Failure Memory & Experience
Learning) may now begin, using this episodic dataset's `train` split for
memory population and `validation`/`test` splits reserved per
`docs/PHASE4_PLAN.md` section 3's isolation protocol.
