# ACTIVE PHASE 4.3 — Recovery Learning & Evaluation

**Status: COMPLETE. Verdict: PASS — HYPOTHESIS NOT SUPPORTED (H3-SAFETY and
H3-UTILITY supported; H3 primary comparison not supported).**

This is one complete Active Phase 4.3 milestone (audit → protocol freeze →
controlled data → environment → baselines → proposed mechanism → tests →
leakage audit → experiments → ablations → final evaluation → this
document), not split into 4.3a/4.3b, per this milestone's own governing
instructions (which explicitly supersede the post-4.2 reassessment's
suggestion, in `README.md` §18, to split it that way).

---

## 1. Executive summary

Every real dataset in this project (`FailureExperience`, Active Phase 4.1)
has `RecoveryStatus.NOT_OBSERVED` / `ValidationResult.NOT_PERFORMED` for
effectively all records — a structural gap in the source data, not an
analysis limitation (§2 below). Phase 4.3 therefore built a **controlled,
frozen, synthetic** failure→recovery-action→validated-outcome dataset
(2,320 episodes across 4 scenario families) and evaluated whether a simple,
interpretable, context-aware recovery-selection mechanism
(`EmpiricalRecoveryPolicy`) selects better recovery actions than
fixed-policy baselines on a held-out frozen test split (n=720, run exactly
once).

**Result**: the proposed mechanism beat a random-valid-action baseline
overwhelmingly (54.2% vs 22.1% validated success, McNemar p≈1.6×10⁻⁴⁵) but
was **statistically indistinguishable from a fixed rule-based priority
baseline** (54.2% vs 53.2%, effect size 0.0097 — far below the pre-registered
minimum meaningful effect of 0.15, McNemar p=0.525, not significant after
Holm-Bonferroni correction). The mechanism never selected the one unsafe
action in the frozen vocabulary (0/720), and a dedicated safety ablation
that removed the safety mask confirmed the mask is load-bearing (unsafe
rate jumps to 8.9% and mean utility collapses from 0.561 to 0.021 without
it). Verdict: **PASS** as a valid, adequately powered, leak-free experiment
— **H3 (the primary success-rate hypothesis) is NOT SUPPORTED** by this
evidence. This is reported as a negative result, not reframed or hidden.

---

## 2. Historical context

```
Phase 1 (prototype audit) -> Phase 2 (migration/integration)
  -> Phase 3.1-3.6 (synthetic) -> FROZEN
  -> OLD Phase 4.0/4.1/4.2 (synthetic) -> FROZEN
       (4.1: H1 PARTIALLY SUPPORTED | 4.2: H2 INCONCLUSIVE)
  -> Real-data expansion (AgentRx, AIOps 2020, Alibaba GPU 2020)
  -> Revised real-data Phase 3.1-3.6 -> FROZEN
  -> ACTIVE Phase 4.1 (src/failure_experience/) -> PASS
  -> ACTIVE Phase 4.2 (src/failure_patterns/) -> INCONCLUSIVE
  -> Post-Phase-4.2 Reassessment (README.md, "Post-Phase-4.2 Reassessment" section)
  -> ACTIVE PHASE 4.3 (src/recovery/) -> THIS DOCUMENT  <-- WE ARE HERE
```

None of the historical artifacts above were modified to produce this
document (verified: §26 below). The consolidated historical record
(originally `docs/PROJECT_HISTORY.md`, merged into `README.md` in a prior
session step) is unmodified by this milestone; this document is additive.

## 3. Relationship to Active Phase 4.1

Active Phase 4.1 (PASS) built the canonical `FailureExperience`
representation and confirmed its schema already has `RecoveryInfo` /
`ValidationInfo` / `OutcomeInfo` slots ready for recovery/validation data —
a data-population gap, not a schema gap. Phase 4.3 reuses
`src.failure_experience.schema` unmodified via
`src/recovery/experience_bridge.py`; no second competing experience schema
was created.

## 4. Relationship to Active Phase 4.2

Active Phase 4.2 (COMPLETE, **INCONCLUSIVE**, unchanged by this milestone)
found real Alibaba data has a hard candidate-key cardinality ceiling, an
evidence-volume problem unrelated to recovery. Phase 4.3 does not attempt
to rescue that verdict, does not touch `src/failure_patterns/`,
`configs/phase4_2_active_pattern_protocol.json`, or
`experiments/results/phase4_2_active/`, and the leakage audit's check 9
(`historical_frozen_dirs_untouched`) confirms this at the file-hash level.

## 5. Research question (frozen)

> Given a controlled, frozen set of failure-scenario → recovery-action →
> validated-outcome episodes spanning scenario families analogous to those
> already represented (descriptively) in `FailureExperience`, can a
> context-aware recovery-selection mechanism choose actions that achieve a
> higher validated-recovery-success rate than fixed-policy baselines on
> held-out frozen test episodes, without exceeding a pre-registered
> unsafe-action-rate threshold?

Frozen in `configs/phase4_3_recovery_protocol.json` before any dataset
generation. Falsifiable (H3 could fail, and did, on the primary
comparison), measurable (validated success rate, unsafe rate, utility),
appropriately scoped to the controlled environment, and distinct from
Active Phase 4.1 (retrieval) and Active Phase 4.2 (context→rate-elevation
pattern discovery).

## 6. Hypotheses (frozen, NOT YET TESTED at freeze time)

| Hypothesis | Statement | Result |
|---|---|---|
| H3 | Proposed mechanism's validated success rate > best fixed-policy baseline, effect ≥ 0.15, statistically significant | **NOT SUPPORTED** (effect 0.0097, p=0.525) |
| H3-SAFETY | Proposed mechanism's unsafe-action rate ≤ 0.00 | **SUPPORTED** (0/720 = 0.000) |
| H3-UTILITY | Proposed mechanism's mean recovery utility ≥ best fixed-policy baseline's | **SUPPORTED** (0.5614 ≥ 0.5585) |

All three were labeled `NOT YET TESTED` in the frozen protocol until the
one-shot frozen-test run in `benchmarks/phase4_3_recovery_evaluate.py`.

## 7. Scenario taxonomy (frozen)

Four families (of the ~8 suggested), each mapped to a failure family
already descriptively present in real `FailureExperience` sources:

| Family | Real-data analogue | Hidden causes | Candidate actions |
|---|---|---|---|
| `resource_exhaustion` | Alibaba GPU 2020 (OOM/resource kills) | `memory_leak`, `transient_spike` | retry, restart, escalate, abstain |
| `transient_failure` | AIOps 2020 (transient onsets) | `network_blip`, `dependency_timeout` | retry, restart, escalate, abstain |
| `configuration_failure` | AgentRx (behavioral/config failure) | `bad_config`, `stale_config` | rollback, reconfigure, restart, escalate, abstain |
| `dependency_failure` | AIOps 2020 (cascading entity faults) | `downstream_outage`, `downstream_degraded` | retry, escalate, abstain, **force_restart (UNSAFE)** |

`infrastructure_failure`, `model_runtime_failure`, and a standalone
`agent/behavioral_failure` family were considered and excluded — each
would not have added a materially different recovery-action profile from
the four above. Each hidden cause produces a **noisy** decision-time
`symptom_pattern` (max 85% correlation, never deterministic — verified by
`test_symptom_pattern_is_not_a_deterministic_function_of_cause`) so the
taxonomy cannot be trivially "solved" by symptom lookup (brief's
"avoid baked-in answers" requirement).

Full taxonomy: `src/recovery/taxonomy.py` (`TAXONOMY_VERSION =
"phase4_3_taxonomy_v1"`).

## 8. Recovery action vocabulary (frozen)

`retry, restart, rollback, reconfigure, escalate_to_human, abstain,
force_restart`. Only `force_restart` is classified `UNSAFE` (irreversible;
may destroy in-flight work on a dependency-degraded/outage path) — every
other action is `SAFE`/reversible. `reschedule` and a separate `no_action`
were considered and dropped as redundant with `restart`/`abstain` in this
single-decision environment. Full spec with reversibility, nominal
cost/latency: `src/recovery/actions.py`
(`ACTION_VOCABULARY_VERSION = "phase4_3_actions_v1"`).

## 9. Environment

**Chosen class: static labeled episodes over a deterministic
single-decision state-transition function** (`src/recovery/environment.py`)
— not a heavier interactive multi-step simulator, since nothing in the
frozen research question requires multi-step planning (brief §14/39,
"smallest environment that supports a valid experiment").
`generate_scenario(family, seed)` is deterministic and independent of any
policy; `transition(scenario, action)` is deterministic given
`(scenario.seed, action)` and is the **only** function in the package
allowed to read `scenario.hidden_cause`.

## 10. Validation model (frozen)

Outcome vocabulary: `SUCCESS, PARTIAL_SUCCESS, FAILURE, UNSAFE, TIMEOUT,
UNRECOVERABLE` (`src/recovery/validation.py`,
`VALIDATION_RULE_VERSION = "phase4_3_validation_v1"`). Recovery is never
`action executed == success` — every episode routes through
`scenario → action → transition() → outcome`, with a fixed 120s validation
window. `ESCALATE_TO_HUMAN` deterministically resolves to `TIMEOUT`
(automated window elapses before a human can plausibly close the
incident); any `UNSAFE`-classified action deterministically resolves to
`UNSAFE` regardless of what its "success chance" would otherwise have
been (safety classification, not success probability, drives this rule —
brief §12, valid ≠ safe). `UNRECOVERABLE` is reserved in the enum but does
not occur under this frozen ground-truth table — see Limitations (§28).

## 11. Decision-time information boundary

`src.recovery.schema.DecisionContext` (pydantic `extra="forbid"`) is the
**only** type any policy's `select_action` may read: `scenario_id,
episode_id, family, symptom_pattern (noisy), severity (noisy),
workload_type, candidate_actions`. It has no `hidden_cause` field, no
outcome field, no validation-result field — structurally, not just by
convention. Every policy's `select_action(self, ctx)` signature is
asserted (via `inspect.signature`) to take exactly `ctx: DecisionContext`
in both `tests/recovery/test_leakage.py` and
`benchmarks/phase4_3_recovery_leakage_audit.py`. `oracle_best_action()`
reads `hidden_cause` directly and is used **only** as a reference upper
bound, never as a policy input or a competing baseline.

## 12. Dataset generation & provenance

`benchmarks/phase4_3_generate_dataset.py`. TRAIN episodes are generated as
a **resolved historical corpus**: a dedicated uniform-random exploration
policy selects an action per scenario and the environment resolves the
outcome — this is what `EmpiricalRecoveryPolicy.fit()` learns from, playing
the role a logged `FailureExperience` corpus would play in production.
VALIDATION and TEST are generated as **unresolved scenario-only
manifests** — no action/outcome is baked in at generation time; each
candidate policy configuration selects its own action against these
frozen scenarios at evaluation time, and the environment resolves the
outcome then. Every episode carries `RecoveryProvenance` with
`source_type=CONTROLLED` (permanently — the schema has no "real" member at
all), plus generator/taxonomy/action-vocabulary/validation-rule/protocol
versions, split, seed, and creation timestamp (`src/recovery/provenance.py`,
`src/recovery/schema.py`).

## 13. Split methodology (frozen)

Grouping unit: scenario (1:1 with episode). Disjoint **seed ranges** per
`(family, split)`, fixed before generation (`src/recovery/splits.py`,
`SPLIT_METHODOLOGY_VERSION = "phase4_3_splits_v1"`) — structurally
impossible to duplicate a scenario across splits, verified by
`check_5_generated_split_files_disjoint_and_manifest_consistent` (0/0/0
overlaps) and `check_4_seed_ranges_disjoint` (2,320 seeds, zero
collisions).

## 14. Sample-size methodology (frozen)

Two-proportion, two-sided z-test power calculation
(`src/recovery/sample_size.py`): p1=0.55, p2=0.40, α=0.05, power=0.80 →
minimum n per arm ≈ **173** (conservative floor; the actual analysis uses
the strictly more powerful paired McNemar test on the same episodes). The
generated test set (720 total, 180/family) exceeds this floor with a
4.16× headroom ratio, comfortably satisfying per-family coverage too.

## 15. Exact dataset sizes

| Split | Total | Per family | Resolved at generation? |
|---|---|---|---|
| TRAIN | 1,200 | 300 | yes (exploration-policy corpus) |
| VALIDATION | 400 | 100 | no (scenario-only) |
| TEST | 720 | 180 | no (scenario-only, frozen, evaluated once) |

`data/controlled_recovery/{train,validation,test}.jsonl` +
`manifest.json` (per-split SHA-256 checksums, counts, versions).

## 16. Baselines

- **Baseline A — `FixedPriorityPolicy`**: fixed, non-learning, per-family
  priority order (frozen domain heuristic, e.g. `restart > retry >
  escalate > abstain` for `resource_exhaustion`), first safe candidate
  wins.
- **Baseline B — `RandomValidPolicy`**: uniform-random among safe candidate
  actions (deterministic given episode id, for reproducibility).
- **Oracle reference bound** — `oracle_best_action()`, uses `hidden_cause`
  directly; reported for context, never scored as a competitor.

## 17. Proposed recovery-selection mechanism

`EmpiricalRecoveryPolicy` (`src/recovery/policy.py`): an experience-based
empirical success-rate lookup with a 3-level retrieval backoff
(`(family, symptom_pattern, severity, action)` → `(family, symptom_pattern,
action)` → `(family, action)`), Laplace-smoothed, ranking safe candidate
actions by estimated expected utility. Deliberately the **simplest**
mechanism judged scientifically meaningful — no reinforcement learning, no
neural network (brief §39/23).

## 18. Uncertainty & abstention

Confidence = supporting TRAIN example count (`n`) in the most specific
non-empty retrieval bucket, normalized by `min_evidence`. Below
`min_evidence`, the policy abstains (or escalates if `ABSTAIN` is not a
candidate) rather than guessing. `min_evidence` was swept on **VALIDATION
only** over `{2, 3, 5, 8, 12, 20}` and frozen at **2** (the sweep showed
success rate strictly decreasing as `min_evidence` rose past 2 — on this
generated TRAIN corpus, evidence was already abundant enough at the
lowest swept value that raising the threshold only cost coverage, never
bought safety: `unsafe_action_rate` was 0.000 at every swept value). Because
the frozen value produced ~0% abstention on VALIDATION, the "no-abstention"
ablation (§21) is **identical** to the proposed policy on TEST — an honest
limitation of this specific frozen selection, not a hidden result (§28).

## 19. Recovery utility (frozen)

`src/recovery/utility.py`: `utility = outcome_value − 0.02×cost −
0.001×latency`, with `SUCCESS=+1.0, PARTIAL_SUCCESS=+0.5, FAILURE/TIMEOUT/
UNRECOVERABLE=0.0, UNSAFE=−5.0`. Weights chosen so no cost/latency saving
can flip an UNSAFE action above a safe FAILURE, and cost/latency only
break ties within the same outcome class (derivation and worst-case bound
in the module docstring).

## 20. Primary metrics (frozen)

`validated_recovery_success_rate`, `unsafe_action_rate`,
`recovery_utility_mean` (all primary); `abstention_rate,
partial_recovery_rate, recovery_latency_mean_seconds,
recovery_cost_mean, regret_vs_oracle` (secondary). Exact formulas in
`configs/phase4_3_recovery_protocol.json`.

## 21. Statistical methodology & results

Primary comparison: **paired McNemar exact test** (proposed vs. each
baseline, same 720 test episodes scored under both policies), **Wilson 95%
CI** per policy's success rate, **paired bootstrap 95% CI** (n=2,000) on
the success-rate difference, **Holm-Bonferroni** correction across the 2
pairwise comparisons.

| Comparison | Proposed | Baseline | Effect | McNemar p | Holm-sig? | 95% CI on diff |
|---|---|---|---|---|---|---|
| vs. `baseline_fixed_priority` | 0.5417 | 0.5319 | **0.0097** (< 0.15 required) | 0.525 | **No** | [−0.015, +0.035] |
| vs. `baseline_random_valid` | 0.5417 | 0.2208 | 0.3208 | 1.6×10⁻⁴⁵ | **Yes** | [+0.279, +0.361] |

Wilson 95% CI, proposed success rate: [0.505, 0.578]. Wilson 95% CI, fixed-
priority: [0.495, 0.568] — the two intervals overlap substantially,
consistent with the non-significant McNemar result.

## 22. Full policy comparison (frozen TEST, n=720, run exactly once)

| Policy | Success | Unsafe | Utility (mean) | Abstain | Partial |
|---|---|---|---|---|---|
| `baseline_fixed_priority` | 0.5319 | 0.0000 | 0.5585 | 0.000 | 0.158 |
| `baseline_random_valid` | 0.2208 | 0.0000 | 0.1487 | 0.000 | 0.071 |
| **`proposed_empirical_recovery`** | **0.5417** | **0.0000** | **0.5614** | 0.000 | 0.147 |
| `ablation_frequency_only` | 0.3653 | 0.0000 | 0.3235 | 0.000 | 0.117 |
| `ablation_no_abstention` | 0.5417 | 0.0000 | 0.5614 | 0.000 | 0.147 |
| `ablation_family_only` | 0.5514 | 0.0000 | 0.5555 | 0.000 | 0.140 |
| `ablation_unmasked_utility` | 0.5319 | **0.0889** | **0.0215** | 0.000 | 0.133 |
| `oracle_reference_bound` | 0.6014 | 0.0000 | 0.6168 | — | 0.125 |

Per-family breakdown (proposed / fixed / oracle): `resource_exhaustion`
0.700 / 0.667 / 0.761; `configuration_failure` 0.689 / 0.667 / 0.856;
`transient_failure` 0.489 / 0.506 / 0.506; `dependency_failure` 0.289 /
0.289 / 0.283 (all n=180/family). `dependency_failure` is the hardest
family for every policy including the oracle (max achievable ~28%) because
its non-outage-avoiding safe actions genuinely have low ground-truth
success probability against `downstream_outage` — a deliberate "no strong
safe recovery exists" case in the frozen taxonomy (§7), not a bug.

## 23. Ablation results (pre-registered, brief §30)

- **A — memory vs. no memory**: `proposed_empirical_recovery` (0.542) beats
  `baseline_random_valid` (0.221) overwhelmingly and is statistically tied
  with `baseline_fixed_priority` (0.532) — memory (§17) clearly beats
  *no* domain knowledge at all, but does not clearly beat *hand-written*
  domain knowledge here.
- **B — outcome-aware vs. frequency-only**: `proposed_empirical_recovery`
  (0.542) clearly beats `ablation_frequency_only` (0.365) — learning
  *which* action tends to succeed matters far more than just learning
  *which* action is tried most often. This is the cleanest positive
  finding of the milestone.
- **C — abstention vs. no abstention**: **identical on TEST** (0.542 vs.
  0.542) at the frozen `min_evidence=2` — an honest null result specific
  to this frozen hyperparameter value (§18/§28), not evidence that
  abstention never matters.
- **D — context vs. no context (family-only)**: `ablation_family_only`
  (0.551) is *marginally higher* than the full-context proposed policy
  (0.542) — the finer symptom/severity buckets did not help, and may have
  mildly hurt via smaller per-bucket sample sizes on this generated TRAIN
  corpus. A genuine negative/null finding, reported as such.
- **E — safety masking**: without the safety mask,
  `ablation_unmasked_utility` selects the UNSAFE `force_restart` action in
  8.9% of test episodes and mean utility collapses from 0.561 to 0.021 —
  direct evidence the safety mask (§11, `safe_candidate_actions`) is
  load-bearing, not decorative.

## 24. Leakage audit (9/9 passed)

`benchmarks/phase4_3_recovery_leakage_audit.py` →
`experiments/results/phase4_3/leakage_audit.json`: decision-context
ground-truth exclusion, **non-vacuous** contamination rejection (a
hand-crafted payload injecting `hidden_cause` into `DecisionContext` is
actually constructed and confirmed rejected, not merely asserted
impossible), policy-signature boundary, seed-range disjointness (2,320
seeds, 0 collisions), generated-split disjointness (0/0/0 overlaps),
VALIDATION/TEST unresolved-at-generation, universal `source_type=CONTROLLED`,
non-vacuous unsafe-action-flagging check (50/50), and a historical-frozen-
directory hash snapshot (`src/failure_experience/`, `src/failure_patterns/`
— first snapshot taken this run, 18 files, informational baseline for
future comparison). **9/9 passed.**

## 25. Known-answer environment validation

`tests/recovery/test_environment.py` (16 tests, all passing) validates the
environment BEFORE any policy result is trusted: determinism given seed,
determinism given (seed, action), `FORCE_RESTART` always → `UNSAFE`
(20/20 seeds), `ESCALATE_TO_HUMAN` always → `TIMEOUT` (all 4 families),
rejection of an action outside a family's candidates, `RESTART` beating
`RETRY` by >3× for `memory_leak` scenarios (matches the frozen 0.85 vs
0.05 ground truth), presence of `SUCCESS`/`PARTIAL_SUCCESS`/`FAILURE` all
occurring, oracle never selecting the unsafe action, symptom pattern
non-determinism per cause, and multiple-distinguishable-success-rates per
family (anti-baked-in-answer check).

## 26. Full test-suite results

- `tests/recovery/` (schema, environment, policy, leakage, integration):
  **38/38 passed**.
- Full repository suite (`pytest -q` from repo root): **425 passed, 0
  failed**, 4 pre-existing unrelated warnings (fastapi/sklearn
  deprecation notices, not touched by this milestone).
- Historical artifacts verified untouched: `git status` shows zero
  modifications to any tracked file under `src/failure_experience/`,
  `src/failure_patterns/`, `configs/phase4_2_active_pattern_protocol.json`,
  or `experiments/results/phase4_2_active/` — every Phase 4.3 file is new
  and additive. (`README.md`'s working-tree modification and
  `docs/PROJECT_HISTORY.md`'s deletion both predate this milestone's work
  and were not made by it.)

## 27. Important failures/bugs discovered during implementation

None required a design change to the frozen protocol. One implementation
detail worth flagging: the initial `min_evidence` sweep showed success
rate *strictly decreasing* as `min_evidence` increased (0.598 → 0.245
across the swept range) rather than the more typical "rises then
plateaus" shape one might expect from an abstention threshold — because on
this TRAIN corpus (uniform-random exploration, 300 episodes/family),
evidence accumulates quickly enough per bucket that raising the threshold
mainly just forces more abstentions (which are scored as `FAILURE`-
equivalent for success rate) without buying safety, since `unsafe_action_rate`
was already 0.000 at `min_evidence=2`. This is reported as-is (§18) rather
than treated as a bug, since it reflects a genuine property of this
generated corpus's evidence density, not an implementation error.

## 28. Real-vs-controlled evidence distinction

**Every number in this document is CONTROLLED/synthetic evidence.**
`src.recovery.schema.SourceType` has exactly one member (`CONTROLLED`) —
there is no code path in this package that can produce a "real" or
"observational" label, by construction. Nothing here demonstrates that any
recovery-selection mechanism works on real production failures; it
demonstrates that a specific, frozen, interpretable mechanism does or does
not outperform specific, frozen baselines under a specific, frozen,
documented set of controlled scenario/action/validation rules. Any future
claim about real-world autonomous recovery requires a separate,
observational milestone.

## 29. Limitations

1. **H3 not supported vs. the strongest baseline.** The proposed mechanism
   did not clear the pre-registered minimum effect size against
   `FixedPriorityPolicy` — a hand-written heuristic turned out to be a
   strong baseline on this taxonomy.
2. **Ablation C (abstention) was uninformative at the frozen
   hyperparameter** — `min_evidence=2` produced ~0% abstention, so the
   no-abstention ablation could not differ from the full mechanism on
   TEST. A future protocol version could pre-register a VALIDATION
   selection rule that trades some success rate for non-trivial
   abstention coverage, to make this ablation informative.
3. **`UNRECOVERABLE` is unused.** Reserved in the outcome enum for
   completeness but does not occur under this frozen ground-truth table —
   not backfilled with an artificial case merely for coverage appearance.
4. **`dependency_failure` has no strong automatable recovery** — even the
   oracle tops out near 28% success — a deliberate, honestly-reported
   "no safe recovery reliably works" scenario, not a data quality issue.
5. **Single-decision environment.** No multi-step/retry-sequence planning
   is modeled; a scenario where a first action's failure should inform a
   second action's choice is out of scope for this milestone (judged
   unnecessary for the frozen research question, brief §14/39).
6. **Ground-truth probabilities are hand-specified, not fit to any real
   distribution** — appropriate for a controlled methodological study, but
   means absolute success-rate numbers have no real-world calibration
   claim attached (§28).

## 30. Historical artifacts verified untouched

Confirmed in §26 and by leakage-audit check 9
(`historical_frozen_dirs_untouched`, `experiments/results/phase4_3/leakage_audit.json`).
Old Phase 4.1/4.2 (synthetic), revised real-data Phase 3, and Active Phase
4.1/4.2 verdicts (H1 PARTIALLY SUPPORTED, `INCONCLUSIVE`) are unchanged and
not reinterpreted anywhere in this document.

## 31. Reproducibility

All versions frozen and recorded in every episode's provenance and in
`configs/phase4_3_recovery_protocol.json`: `generator_version
=phase4_3_generator_v1`, `scenario_taxonomy_version=phase4_3_taxonomy_v1`,
`action_vocabulary_version=phase4_3_actions_v1`,
`validation_rule_version=phase4_3_validation_v1`,
`protocol_version=phase4_3_protocol_v1`,
`split_methodology_version=phase4_3_splits_v1`,
`schema_version=4.3.0-controlled`. `data/controlled_recovery/manifest.json`
carries per-split SHA-256 checksums and counts. Given the same protocol
version, `benchmarks/phase4_3_generate_dataset.py` regenerates an
identical byte-for-byte dataset (all randomness is seeded via
`random.Random(seed)`, never global state).

## 32. Final research interpretation

1. **Can the controlled environment represent meaningful recovery
   scenarios?** Yes — 4 families, 2 causes each, noisy non-deterministic
   symptoms, multiple actions with genuinely different success profiles,
   one unsafe action, one "no strong safe recovery" family.
2. **Can recovery outcomes be validated objectively?** Yes — deterministic
   given (scenario, action), a fixed validation window, and a closed
   6-value outcome vocabulary; verified by known-answer tests (§25).
3. **Can the proposed mechanism select recovery actions better than the
   baseline?** Better than a random baseline, decisively. **Not**
   detectably better than a well-designed fixed-priority heuristic
   baseline, on this taxonomy, at this sample size.
4. **Does memory improve recovery selection?** Compared to no memory at
   all (random), yes. Compared to hand-written domain-knowledge memory
   (fixed priority), not detectably.
5. **Does uncertainty-aware abstention improve safety?** Not measurable
   here — the frozen `min_evidence` produced near-zero abstention on this
   corpus (§18/§27), so the question remains open for a future protocol
   version.
6. **What happens on unseen scenarios?** All TEST scenarios are unseen by
   construction (disjoint seed ranges); the mechanism generalizes about as
   well as the fixed-priority baseline, not better.
7. **What happens when multiple actions are valid?** Every family but one
   action always has ≥2 safe candidate actions with different ground-truth
   success rates (§7); the mechanism correctly concentrates on the
   higher-success action for high-signal cases (e.g. `RESTART` for
   `memory_leak`, §25) but this did not translate into an aggregate edge
   over the simpler heuristic.
8. **What happens when no safe recovery exists?** `dependency_failure`
   `downstream_outage`: every policy, including the oracle, tops out
   under ~30% success; the mechanism did not attempt the unsafe action
   (0/720) and did not inflate its confidence in that regime.
9. **What are the failure modes of the recovery mechanism?** (a) It offers
   no advantage over a good hand-written heuristic when the heuristic
   already encodes the right domain knowledge; (b) its context buckets can
   mildly *underperform* a coarser family-level statistic when per-bucket
   evidence is thin (ablation D); (c) its abstention behavior is sensitive
   to a hyperparameter that, at its frozen value, rarely triggers on this
   corpus.
10. **Does the evidence justify moving toward autonomous recovery
    orchestration?** Not yet, and not on this evidence alone: the
    mechanism is safe (H3-SAFETY held) and utility-competitive
    (H3-UTILITY held), but has not demonstrated a success-rate advantage
    over a much simpler, cheaper, fully-interpretable fixed-priority
    policy. The strongest actionable finding is that a fixed, well-designed
    priority list is a genuinely strong, hard-to-beat baseline for
    single-decision recovery selection — worth stating plainly rather than
    downplaying because it is not the "learning wins" story.

## 33. What improved / what did not / what remains inconclusive

- **Improved (clearly)**: outcome-aware selection over frequency-only
  selection (ablation B); any-memory over no-memory (vs. random baseline);
  safety when the mask is applied (ablation E).
- **Did not improve**: validated success rate over a fixed-priority
  baseline (H3 primary); context-aware buckets over family-only buckets
  (ablation D, mild negative).
- **Remains inconclusive**: whether abstention meaningfully trades success
  for safety (ablation C was uninformative at the frozen hyperparameter,
  §27/§29).

## 34. Readiness for the next phase

Phase 4.3's infrastructure (`src/recovery/`, the frozen protocol, the
`FailureExperience` bridge) is reusable for a follow-on milestone that
either (a) re-runs this exact protocol with a richer/multi-step
environment if a future audit motivates one, or (b) revisits the
`min_evidence` freeze rule specifically to make the abstention ablation
informative, as a new pre-registered experiment — not a retrofit onto this
one's frozen TEST result. Per this project's standing discipline
(consistent with the post-4.2 reassessment, README.md §14), the honest
next step is a fresh, explicitly-labeled follow-up experiment, not
re-opening this frozen evaluation.

---

## Final verdict

**PASS — HYPOTHESIS NOT SUPPORTED.**

The Active Phase 4.3 experiment was valid (leakage audit 9/9, 425/425
repository tests green, known-answer environment checks passing,
no test-set tuning, sample size 4.16× the pre-registered floor,
one-shot frozen TEST evaluation), and sufficiently powered. H3-SAFETY and
H3-UTILITY were supported; H3 (the primary validated-success-rate
comparison against the fixed-priority baseline) was **not** supported at
the pre-registered minimum effect size. This is reported as a genuine,
negative, evidence-based research result, exactly as this project's
standing research-integrity discipline requires (README.md, Active Phase
4.2's INCONCLUSIVE verdict; this project's Phase 3 Freeze) — not adjusted,
reframed, or hidden.
