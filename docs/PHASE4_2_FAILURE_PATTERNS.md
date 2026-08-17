# Phase 4.2 — Failure Pattern Learning

**Status: COMPLETE.** This document is the Phase 4.2 deliverable, per
[`docs/PHASE4_PLAN.md`](PHASE4_PLAN.md) and the Phase 4.2 authorization.

Companion artifacts: [`configs/phase4_2_pattern_protocol.json`](../configs/phase4_2_pattern_protocol.json),
[`src/patterns/`](../src/patterns/),
[`benchmarks/phase4_2_pattern_evaluate.py`](../benchmarks/phase4_2_pattern_evaluate.py),
[`benchmarks/phase4_2_leakage_audit.py`](../benchmarks/phase4_2_leakage_audit.py),
[`experiments/results/phase4_2/`](../experiments/results/phase4_2/),
[`tests/unit/test_pattern_discovery.py`](../tests/unit/test_pattern_discovery.py),
[`tests/integration/test_phase4_2_patterns.py`](../tests/integration/test_phase4_2_patterns.py).

## 1. Hypothesis

**H2** (fixed before final evaluation, `configs/phase4_2_pattern_protocol.json`):
recurring failure patterns (condition recurrence, temporal clustering,
symptom→cause→outcome relationships) are detectable above chance in the
episode stream, and the system can correctly separate observed evidence
from inferred pattern from confirmed relationship from uncertain
hypothesis using four explicit confidence tiers.

Phase 4.2 is a distinct question from Phase 4.1: 4.1 asked whether a
*single* relevant prior incident can be retrieved; 4.2 asks whether a
*recurring relationship across multiple* incidents can be identified and
its strength graded.

## 2. Inspection performed before implementation (per the authorization's section 5)

Phase 4.0's generator (`src/data/episodic.py`) and dataset
(`experiments/results/phase4_0/episodes.json`), Phase 4.1's `src/experience/`
(schema/store/metrics/protocol/results), `src.failure_memory.embedding`,
the frozen Phase 3.6 diagnosis taxonomy (`src/evaluation/diagnosis.py`),
`docs/PHASE3_FREEZE.md`, `docs/PHASE4_PLAN.md`, and the Phase 4.1
completion report were all read before writing any Phase 4.2 code.

**Reuse decisions:**
- `diagnosed_cause` (Phase 4.0's per-row field, itself computed via the
  frozen, unmodified `src.evaluation.diagnosis.diagnose`) is used as the
  decision-time-observable "symptom" side of the pattern claim — not
  recomputed, not reimplemented.
- `condition_id` (Phase 4.0 ground truth) is reused as the discovery/
  evaluation-only ground truth, exactly as Phase 4.1 used it — never
  exposed through a live-query type.
- `src.failure_memory.embedding.FailureEmbedder`'s KMeans-style clustering
  (identified in `docs/PHASE4_PLAN.md` section 4.2 as a *candidate*
  pattern-detection primitive) was inspected and **not used**: with only
  28 train-split CRITICAL-failure rows total (§4), fitting any clustering
  model would be operating far below a sample size where cluster
  assignments could be trusted, and — more importantly — the actual
  pattern claim under test here (does a `diagnosed_cause` reliably map to
  one `condition_id`) is already a direct, interpretable frequency/purity
  question that clustering would not answer more directly. This is a
  documented "reuse is not automatically adequate" decision, not an
  oversight.
- Phase 4.1's structural pattern (a type — `PatternQuery` here, mirroring
  `DecisionTimeQuery` — that syntactically cannot carry ground truth) is
  reused as the design template for leakage prevention, applied fresh to
  the pattern-learning problem (`src/patterns/schema.py`), not copied
  code.
- No frozen Phase 3 file, Phase 4.0 dataset file, or Phase 4.1 result file
  was modified.

## 3. What is a "pattern"? (fixed before evaluation)

A pattern **candidate** is keyed by `(workload_id, diagnosed_cause)`. The
claim under test is a **symptom→cause relationship**: does this
`diagnosed_cause`, for this workload, reliably correspond to one
particular true `condition_id`? A key is a candidate at all only if it
recurs in the train split (`n_train >= 2`) — a singleton is not
recurrence by definition and is excluded entirely, not folded into the
lowest tier.

This is a narrower pattern definition than the full space section 8 of
the authorization lists (condition recurrence, temporal clustering,
symptom→cause, cause→outcome, combined chains). The primary
precision/recall-evaluated mechanism covers **condition recurrence +
symptom→cause** (A and C in that list). **Temporal clustering** (B) and
**cause→outcome** (D) are implemented as separate, descriptive-only
secondary analyses (§8), not folded into the same tiered
precision/recall machinery — combining five different pattern types into
one scored mechanism was judged to overreach the smallest-research-valid
version this dataset's size (§4) could actually support; the scope
narrowing is stated here, not silently absorbed.

## 4. Data used, and a real scope constraint

`diagnosed_cause` only exists on CRITICAL-tier rows (diagnosis, per the
frozen Phase 3.6 policy Phase 4.0 reuses unmodified, is only computed for
CRITICAL-tier samples). This shrinks the usable population sharply:

| Split | is_failure & diagnosed_cause-not-null rows |
|---|---|
| train | 28 |
| validation | 4 |
| test | 14 |

This is a real, load-bearing limitation, not a bug: Phase 4.0's dataset
was sized for its own Phase 4.0 purpose, and CRITICAL-tier diagnosis
availability was not specifically tuned for Phase 4.2's needs. It is
carried into every result below.

**Split usage**: train → candidate discovery (recurrence counts, mode
condition, train-purity). Validation → CONFIRMED-tier replication check
only (permitted per `docs/PHASE4_PLAN.md` section 3: "confidence-tier
calibration"). Test → final, one-time row-level evaluation only —
verified never to influence discovery (§7).

## 5. Methodological integrity disclosure

During protocol design, candidate feasibility was checked against
train/validation counts to confirm the chosen thresholds would produce a
non-degenerate tier distribution (permitted). While doing this, a small
number of test-split row values were also inadvertently reviewed during
interactive design-phase scoping, **before** `configs/phase4_2_pattern_protocol.json`
was frozen. No threshold, baseline, or acceptance criterion in that file
was chosen or adjusted based on that inadvertent observation — the tier
thresholds were fixed from train/validation reasoning alone, and the
`minimum_evaluable_n = 10` acceptance bar was set from a generic,
dataset-independent small-sample convention, not reverse-engineered from
the realized test count (which turned out to be 7, i.e. below that bar —
see §10). This is disclosed here rather than concealed, per the
research-integrity requirement to report irregularities honestly. No
result below was altered because of this; the concern is about the
*process*, and it is recorded so the reader can judge it independently.

## 6. The four evidence tiers

`src/patterns/schema.py`'s `EvidenceTier` (`OBSERVED`, `INFERRED`,
`CONFIRMED`, `UNCERTAIN`) and `src/patterns/discovery.py::assign_tier`,
applied in this precedence (from the frozen protocol):

1. `n_train < 2` → not a candidate (excluded).
2. `n_train ≥ 6` AND `purity_train ≥ 0.8` AND validation replicates
   (`n_validation ≥ 1` and `purity_validation ≥ 0.5`) → **CONFIRMED**.
3. `purity_train ≥ 0.6` → **INFERRED**.
4. `n_train < 3` → **UNCERTAIN**.
5. else → **OBSERVED** (recurs with trustworthy n, but purity below the
   INFERRED bar — recurrence without an established relationship).

## 7. Leakage/integrity audit — all 5 checks passed

`benchmarks/phase4_2_leakage_audit.py`:
`pattern_query_excludes_ground_truth_and_outcome_fields`,
`no_candidate_derived_only_from_test_split`,
`candidacy_rule_excludes_n_train_below_2`, `discovery_is_deterministic`,
`empty_candidate_or_row_set_handled_gracefully`. Result:
`experiments/results/phase4_2/leakage_audit.json`, `all_passed: true`.
An additional integration test
(`test_no_test_split_row_influences_candidate_discovery`) confirms the
check is not vacuous: deliberately contaminating train with test rows
*does* change the discovered candidates, proving the real (uncontaminated)
build is meaningfully test-blind, not just untested for it.

## 8. Discovered candidates (train + validation)

| Workload | Diagnosed cause | n_train | Mode condition (train) | Purity (train) | n_validation | Purity (validation) | Tier |
|---|---|---|---|---|---|---|---|
| workload_1 | clean | 2 | clean | 1.00 | 0 | — | INFERRED |
| workload_2 | clean | 4 | clean | 0.75 | 1 | — | INFERRED |
| workload_2 | feature_noise | 2 | feature_noise_severe | 1.00 | 0 | — | INFERRED |
| workload_3 | clean | 5 | clean | 0.60 | 0 | — | INFERRED |
| workload_3 | feature_dropout | 7 | feature_dropout | 1.00 | 1 | 1.00 | **CONFIRMED** |
| workload_4 | clean | 4 | clean | 1.00 | 1 | 1.00 | INFERRED |

6 candidates discovered; **0 landed in OBSERVED or UNCERTAIN** in this
run — every recurring key that met the candidacy floor (n≥2) happened to
also clear the 0.6 purity bar for INFERRED. This is a real, honest
property of this particular realization (not a design flaw): the
OBSERVED/UNCERTAIN tiers exist and are exercised by the unit tests
(`tests/unit/test_pattern_discovery.py`), but this specific dataset
happened not to produce any candidate landing there.

## 9. Row-level evaluation (test split, n=14 total, 7 covered)

Coverage: 7/14 (50%) — test rows whose exact `(workload_id,
diagnosed_cause)` key exists among the 6 discovered candidates.
7 test rows fall under 3 of the 6 candidates
(`workload_2/feature_noise` n=1, `workload_3/clean` n=2,
`workload_4/clean` n=4); the other 3 candidates (including the one
CONFIRMED candidate, `workload_3/feature_dropout`) have **zero** test
occurrences of their exact key, so nothing about them could be verified
against held-out data in this run.

| Method | n_flagged | Precision | Recall |
|---|---|---|---|
| A — no pattern learning | 0 | undefined (0 flagged) | 0.0 |
| B — naive frequency (n_train≥3) | 6 | **0.333** | 1.0 |
| **C1 — tiered (proposed)** | 7 | 0.286 | 1.0 |
| C2 — ablation, no tiering (purity≥0.6, any n) | 7 | 0.286 | 1.0 |

Full detail: `experiments/results/phase4_2/pattern_results.json`.

**Tier calibration** (true-structure rate by tier, test split): only
`INFERRED` has any covered rows in this run (n=7, true-structure rate
0.286); `CONFIRMED`, `OBSERVED`, `UNCERTAIN` all have n=0 covered test
rows. **The CONFIRMED > INFERRED > OBSERVED/UNCERTAIN ordering cannot be
checked at all in this run** — the one CONFIRMED candidate had no test
occurrences to verify against.

## 10. Is H2 supported? — Per the pre-registered acceptance criteria

`n_covered_test_rows = 7 < minimum_evaluable_n = 10`. Per
`configs/phase4_2_pattern_protocol.json`'s `acceptance_criteria`, this
alone determines the verdict:

# 🟡 H2: INCONCLUSIVE (evidence volume insufficient)

This is the pre-registered outcome for `n_covered < 10`, decided by the
rule fixed before evaluation (§5's disclosure notwithstanding — the rule
itself does not depend on the specific realized count). It would be
mandated regardless of which way the point estimates leaned.

**For the record, since the numbers exist and are not being suppressed**:
the point estimates in this run are directionally **unfavorable** to the
proposed tiered method — baseline B (naive frequency-count flagging)
achieved *higher* precision (0.333 vs. 0.286) than both the proposed C1
and its C2 ablation, at equal recall (1.0 for all three non-trivial
methods). The reason is specific and traceable (§12): C1's INFERRED tier
admitted a `workload_2/feature_noise` candidate with only `n_train=2`
(purity 1.0, but on just 2 observations), which turned out wrong on its
single test occurrence; baseline B's simpler `n_train ≥ 3` floor happened
to exclude that exact candidate. This is reported as a genuine
observation from an underpowered run, not evidence that tiering is
generally worse than frequency-flagging — 7 covered rows is nowhere near
enough to draw that conclusion either way.

## 11. Ablation: C1 (tiered) vs. C2 (no tiering)

**C1 and C2 produced numerically identical results in this run**
(precision 0.286, recall 1.0, n_flagged 7): every discovered candidate's
train-purity happened to be ≥ 0.6, so C2's flat-threshold rule and C1's
tiered rule agreed on every single candidate's flag/no-flag decision.
**The ablation is uninformative in this specific run** — it cannot show
whether the tier system's small-sample humility (the `UNCERTAIN`
n<3 carve-out) or its validation-replication requirement (the
`CONFIRMED` gate) contribute anything, because no candidate in this
realization was close enough to those boundaries to produce a different
decision between C1 and C2. This is reported as a limitation of this
run's specific candidate set, not evidence that the ablation factors are
inert in general.

## 12. Failure-case analysis

- **Why C1 loses precision to B specifically**: `workload_2/feature_noise`
  (n_train=2, purity_train=1.0) is admitted by C1's INFERRED tier
  (purity ≥ 0.6 is checked before any n-floor in the frozen precedence —
  see §6 step 3 vs. step 4) but excluded by B's `n_train ≥ 3` floor. Its
  single test occurrence (`condition_id = feature_noise_mild`) did not
  match its train-derived mode (`feature_noise_severe`), so it
  contributed one false positive to C1/C2 that B never risked. This is
  exactly the kind of small-n instability the `UNCERTAIN` tier concept
  was designed to guard against — but the frozen precedence (purity check
  before the n-floor check, per the protocol as written) lets a high
  train-purity override the n-floor, so it didn't guard against it here.
  This is reported as a real, traceable finding about this specific
  tier-precedence design choice, not smoothed over.
- **Why CONFIRMED's tier-calibration claim can't be checked**: the one
  CONFIRMED candidate (`workload_3/feature_dropout`) simply has no test
  occurrence of that exact key — its test-split occurrence (§9's known
  combo, per Phase 4.0) either produced no CRITICAL-tier failure at all
  or one diagnosed as something else. Nothing about "does CONFIRMED
  actually mean higher precision" could be tested this round.
- **Sample size is the dominant explanation for all of the above** — not
  weak representation, not noisy diagnosis, not workload-specific
  effects. With 28 train / 4 validation / 14 test usable rows spread over
  potentially 16 (workload × diagnosed_cause) combinations, most cells
  are populated by 1-7 observations. This is consistent with, and does
  not contradict, Phase 4.1's own small-sample caution (`docs/PHASE4_1_FAILURE_MEMORY.md`
  section 12) — both subphases are bottlenecked by the same underlying
  Phase 4.0 dataset scale at the CRITICAL-tier population specifically.

## 13. Secondary analyses (descriptive, not part of H2's formal criteria)

**Temporal clustering (pattern type B)**: for all 12 known combos, the
inter-occurrence step gaps are **exactly constant** (gap variance = 0.0
in every case — e.g. `workload_1|clean`: gaps `[180, 180, 180, 180]`).
This is a direct, expected consequence of Phase 4.0's deterministic
round-robin scheduler (`src/data/episodic.py`), which spaces every
combo's occurrences evenly by construction. **No temporal clustering
(bursty recurrence) exists in this dataset, and none was expected** —
this is a property of the generator, not a finding about real-world
failure timing, and is reported as an honest null result rather than
omitted. `experiments/results/phase4_2/pattern_results.json`'s
`temporal_clustering` block has full detail for all 12 combos.

**Cause→outcome (pattern type D)**, train-split CRITICAL-tier recovery
attempts, grouped by `diagnosed_cause` (descriptive only — **not** used
to make or evaluate any recovery decision; that is Phase 4.3's separate
objective, per the authorization's closing instruction):

| Diagnosed cause | Attempts | Recovered | Rolled back | Recovered correct | Recovered incorrect |
|---|---|---|---|---|---|
| clean | 29 | 0 | 29 | 0 | 0 |
| feature_dropout | 11 | 0 | 11 | 0 | 0 |
| feature_noise | 10 | 3 | 7 | 2 | 1 |

This closely **replicates Phase 3.6's frozen findings** (`docs/PHASE3_6_DIAGNOSIS_ABSTENTION_RECOVERY.md`
§16-17) on independently-generated Phase 4.0 data: `clean`-diagnosed
CRITICAL samples never attempt retry (matches Phase 3.6's structural
non-action finding exactly), `feature_dropout`-diagnosed samples recover
**0/11** via reconfigure (matches Phase 3.6's "reconfigure provides zero
measured benefit" finding), and `feature_noise`-diagnosed samples recover
a modest, imperfect fraction (3/10, of which 1/3 was actually incorrect).
This is stated as corroborating evidence on new data, not as a new
finding, and Phase 3.6's own frozen conclusion is not reopened or
restated as improved by it.

## 14. Limitations

- Pattern population is small (§4): 28/4/14 train/validation/test usable
  rows, a direct consequence of `diagnosed_cause` only existing on
  CRITICAL-tier rows. If more statistical power is needed for a future
  subphase, Phase 4.0's protocol would need a documented, pre-frozen
  revision (larger recurrence/batch parameters) — not attempted here,
  per the instruction not to modify Phase 4.0's frozen dataset.
- The pattern vocabulary evaluated with full precision/recall/tiering is
  narrower than the authorization's full list (§3) — temporal clustering
  and cause→outcome are descriptive-only secondary analyses, not scored.
- The tier precedence (purity check before the n-floor check) allows a
  high-purity, low-n candidate to reach INFERRED without ever passing
  through the n-floor gate that baseline B uses — this is exactly what
  the frozen protocol specifies, but §12 shows it has a real, traceable
  cost in this run; a future protocol revision could reorder this
  precedence, but that is a new experimental factor for a later
  subphase, not a change made here.
- The ablation (§11) is uninformative in this specific run because no
  discovered candidate sat near a tier boundary — this reflects the small
  candidate set, not a property of the tiering mechanism established one
  way or the other.
- "Novel" combinations (Phase 4.0's own documented scope) are not
  separately analyzed in Phase 4.2's row-level evaluation — with only 14
  test rows total and most falling in known combos by chance, splitting
  further by novelty would leave cells too small to report meaningfully;
  novelty-stratified pattern generalization remains primarily a Phase
  4.7 question, consistent with the authorization's section 14.
- §5's methodological disclosure: strict test-blindness during protocol
  design was not perfectly maintained; documented rather than concealed.

## 15. Progression note

Phase 4.1 (frozen): H1 **PARTIALLY SUPPORTED** — similarity retrieval
clears baselines only in the `known_combo_test, k=3` condition. Phase
4.2 (this document): H2 **INCONCLUSIVE**, evidence volume insufficient
(7 < 10 covered test rows), with directionally unfavorable-to-tiering
point estimates reported transparently. These are independent findings
about different mechanisms (single-incident retrieval vs.
multi-incident pattern/tier assignment) evaluated on overlapping but not
identical row populations. Neither result is rewritten by the other.
**Combined interpretation**: both Phase 4.1 and Phase 4.2, independently,
found that the smallest-valid mechanisms tested here provide at most
modest, inconsistent, sample-size-limited evidence of value on this
particular Phase 4.0 dataset scale — a pattern worth carrying into Phase
4.3's design (favor mechanisms and evaluations that are robust to, or
explicitly account for, this dataset's small CRITICAL-tier/failure
population), not a reason to abandon the overall Phase 4 research
program.

## 16. Deliverables checklist

1. Phase 4.2 implementation — done (`src/patterns/`).
2. Pattern representation/schema — done (`schema.py`: `EvidenceTier`, `PatternCandidate`, `PatternQuery`).
3. Pattern detection mechanism — done (`discovery.py::discover_candidates`, `assign_tier`).
4. Four-tier evidence mechanism — done (§6, exercised by unit tests for all 4 tiers).
5. Required baselines — done (A, B in `benchmarks/phase4_2_pattern_evaluate.py`).
6. Evaluation benchmark — done (`benchmarks/phase4_2_pattern_evaluate.py`).
7. Reproducible configuration — done (`configs/phase4_2_pattern_protocol.json`).
8. Leakage/integrity audit — done, 5/5 passed (§7).
9. Phase 4.2 tests — done, 14 unit + 9 integration = 23, all passing.
10. Full-suite test results — 285/285 (see completion report).
11. Pattern precision/recall results — done (§9).
12. Tier-level calibration results — done (§9, reported as unverifiable in this run — not fabricated).
13. Required ablation — done, reported as uninformative in this run (§11).
14. Failure-case analysis — done (§12).
15. Limitations — done (§14).
16. This document.
17. Formal completion record — §17 below.

## 17. Final status

# 🟡 INCONCLUSIVE

Implementation, evaluation, documentation, leakage audit, and
research-integrity checks are all complete, and every required mechanism
(4 evidence tiers, both baselines, the proposed method, the ablation, two
secondary pattern analyses) was built, tested, and evaluated. **H2 is
INCONCLUSIVE** — not because the mechanism failed to run, but because the
pre-registered minimum-evidence bar (10 covered test rows) was not met
(7 achieved), a direct consequence of Phase 4.0's CRITICAL-tier
population being small. The point estimates that do exist lean
unfavorably for the proposed tiered method relative to a naive
frequency-count baseline, for a specific, traced reason (§12) — reported
plainly rather than minimized. The cause→outcome secondary analysis did
independently replicate Phase 3.6's frozen recovery findings on new data,
which is a positive, if secondary, result. Per the completion rule,
"implementation success" and "hypothesis support" are reported as the
separate outcomes they are: implementation is a clean PASS; H2 support is
INCONCLUSIVE; the overall Phase 4.2 status is recorded as INCONCLUSIVE to
reflect the hypothesis-level result, not the implementation-level one.
