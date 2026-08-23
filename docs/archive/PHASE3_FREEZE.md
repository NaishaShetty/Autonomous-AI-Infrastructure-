<a id="phase3-freeze"></a>
# PHASE3 FREEZE
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_FREEZE.md`  
**Role:** Formal freeze declaration sealing Phase 3.1-3.6 (synthetic-data track) as historical baseline.

# Phase 3 Freeze

**Phase 3 (3.1 through 3.6) is COMPLETE and FROZEN as of this document.**

This freeze is a research-integrity and reproducibility measure. It does
**not** make the repository immutable. Future phases may introduce new
components, new datasets, new failure/recovery mechanisms, improved
representations, or replace existing components entirely — including
discovering that a component Phase 3 found weak becomes useful in a new
setting, or that a component Phase 3 found promising remains unnecessary.
Any such change is **new evidence**, evaluated on its own terms. What the
freeze prohibits is **silently altering the historical Phase 3 record** —
its protocols, results, or conclusions — to make later work look better
by comparison.

> Phase 3 is frozen. Future phases may build upon, replace, or extend its
> components, but Phase 3 protocols, results, and conclusions are
> preserved as the historical experimental baseline.

If a future phase modifies or replaces a component Phase 3 relied on
(e.g. `src/pipeline_builder.py`, `src/failure_memory/`, `src/reliability/`,
`src/evaluation/representations.py`), the **original implementation and
its Phase 3 results must be preserved** (e.g. under a version-tagged copy
or an explicit "superseded by" note), and the relationship between old
and new must be documented — not overwritten in place.

## What is frozen

**Protocols/configs** (do not edit values, thresholds, seeds, coverage
points, cost model, attack matrix, or diagnosis rule in these files):
- `configs/phase3_1_protocol.json`
- `configs/phase3_5_attack_protocol.json`
- `configs/phase3_6_decision_recovery_protocol.json`

**Benchmark/evaluation scripts** (Phase 3.1 → 3.6, do not modify fitting
procedures, seeds, or metric definitions):
- `benchmarks/phase3_1_evaluate.py`, `benchmarks/phase3_1_leakage_audit.py`
- `benchmarks/phase3_2_evaluate.py`
- `benchmarks/phase3_2c_ablation.py`
- `benchmarks/phase3_3_generalization.py`
- `benchmarks/phase3_4_compare.py`
- `benchmarks/phase3_5_attack_generalization.py`, `benchmarks/phase3_5_leakage_audit.py`
- `benchmarks/phase3_6_complementarity.py`, `benchmarks/phase3_6_decision_policy.py`, `benchmarks/phase3_6_diagnosis.py`, `benchmarks/phase3_6_recovery.py`, `benchmarks/phase3_6_leakage_audit.py`, `benchmarks/phase3_6_export_csv.py`
- `benchmarks/risk_coverage.py` (Phase 2 harness, reused unmodified by every Phase 3 script)

**Evaluation/source modules explicitly frozen during Phase 3** (each
phase's own docstrings/reports name these as unmodified — see each
`docs/PHASE3_*.md` for the specific "does not modify" list of that
phase):
- `src/evaluation/protocol.py`, `bootstrap.py`, `metrics.py`, `representations.py`
- `src/evaluation/attacks.py`, `complementarity.py`, `decision_policy.py`, `diagnosis.py`, `recovery.py`
- `src/pipeline_builder.py`
- `src/failure_memory/` (`memory.py`, `embedding.py`, `anticipatory.py`)
- `src/reliability/` (`workload_model.py`, `calibrator.py`)
- `src/data/synthetic.py`
- `src/decision/policy.py`
- `src/schema/events.py`

**Result artifacts** (never regenerate/overwrite to change a historical
number — a genuine reproducibility bug is grounds to STOP and document,
per every phase's own protocol, not to silently re-run):
- `experiments/results/phase3_1/`, `phase3_2/`, `phase3_2c/`, `phase3_3/`, `phase3_4/`, `phase3_5/`, `phase3_6/` (all files)

**Reports/documentation:**
- `docs/PHASE3_1_EVALUATION_PROTOCOL.md`
- `docs/PHASE3_2_REPRESENTATION_EXPERIMENTS.md`
- `docs/PHASE3_2C_CANDIDATE_ABLATION.md`
- `docs/PHASE3_3_GENERALIZATION.md`
- `docs/PHASE3_4_COMPARISON.md`
- `docs/PHASE3_5_ATTACK_GENERALIZATION.md`
- `docs/PHASE3_6_DIAGNOSIS_ABSTENTION_RECOVERY.md`

**Tests and leakage audits** (all Phase 3.x tests under `tests/unit/` and
`tests/integration/` matching `test_phase3_*.py`, plus the leakage-audit
scripts listed above) — do not weaken or delete these to make a future
change pass more easily.

## Frozen conclusions (the historical record)

- **Phase 3.1** established the frozen evaluation protocol and the three
  original baselines (no signal, calibrated confidence, original Failure
  Memory).
- **Phase 3.2 / 3.2C** established that the original Failure Memory
  mechanism was weak (AUROC ≈ 0.514, barely above no-signal), while a
  supervised classifier extracted a real but modest signal — and that the
  supervised *classifier*, not the richer hand-designed representation,
  was the mechanism responsible.
- **Phase 3.3** supported generalization within the documented synthetic
  concept-drift scope (fixed features, rotated label boundary).
- **Phase 3.4** established that Supervised Failure Risk (F) did not
  consistently outperform calibrated confidence (B) — 🟡 INCONCLUSIVE.
- **Phase 3.5** supported robustness/generalization under the
  specifically tested synthetic covariate-shift attacks (feature noise,
  feature dropout), but did not establish superiority over B — 🟢
  GENERALIZATION SUPPORTED, narrowly (relative standing preserved, not
  superiority).
- **Phase 3.6** established that B+F provided no measurable incremental
  value over B alone (paired AUROC diff CI included zero); that
  calibrated confidence was the strongest and most cost-efficient signal
  under the tested synthetic cost assumptions; that failure-cause
  diagnosis was only partially successful (perfect on structurally
  unambiguous corruption, unreliable on mild perturbations); that
  retry-based recovery was real but unsafe (~45% failure rate among
  attempted recoveries); and that reconfiguration-based recovery provided
  zero measured benefit in the tested setting (its fallback signal shared
  the same corruption as the signal it was replacing) — 🟡 INCONCLUSIVE.
- **Autonomous decision authority is NOT justified** by any Phase 3
  result. This conclusion stands until a later phase produces new,
  independently evaluated evidence addressing complementarity,
  operational risk, calibration, and recovery safety at a level Phase 3
  did not reach.

## Verification performed at freeze time

- All expected result files exist under `experiments/results/phase3_{1,2,2c,3,4,5,6}/` (verified by directory listing).
- Spot-checked key numbers (Phase 3.1 `C_failure_memory` AUROC, Phase 3.2C Experiment B AUROC, Phase 3.4 F AUROC, Phase 3.5 clean-condition F AUROC, Phase 3.6 BF-vs-B paired diff, Phase 3.6 retry failure rate) against their source JSON files and confirmed they match the corresponding `docs/PHASE3_*.md` reports exactly.
- Confirmed `.gitignore` does not exclude `experiments/results/`, `configs/`, or `docs/` — no Phase 3 result artifact is silently untracked.
- Confirmed no Phase 4 files, directories, or references exist anywhere in the repository.
- Full test suite: **231 passed, 0 failed** (`python -m pytest -q`).
