# Phase 4.6 — Real Local AI/ML Model + Multi-Task Uncertainty Foundation

**Run:** `experiments/results/phase4_6_to_4_10/20260824T133029Z/` (immutable; do not overwrite)
**Scope:** Priority 1 of the Phase 4.6–4.10 five-gap research plan. Retry/abstention policy calibration (Priority 2), the prediction re-evaluation (Priority 3), independent environments (Priority 4), and the full integrated loop (Priority 5) are explicitly **out of scope** here and covered in later checkpoints.

## 1. What was built

Two real, open-weight, locally-run Hugging Face models replace nothing — the existing synthetic arithmetic self-consistency agent (`src/phase4/agent_task.py`, Phase 4.5b) is retained **unchanged** as the controlled baseline family. Two new real-model task families are added alongside it:

| Task family | Mechanism | Model | Params | Weights source |
|---|---|---|---|---|
| Arithmetic reasoning (baseline, unchanged) | `self_consistency_disagreement` | none (deterministic simulated solver) | — | n/a |
| Sentiment classification | `softmax_margin_classification` | `distilbert-base-uncased-finetuned-sst-2-english` | 67M | Hugging Face Hub, revision `714eb0fa89d2f80546fda750413ed43d93601a13` |
| Extractive question answering | `softmax_span_confidence_qa` | `distilbert-base-cased-distilled-squad` | 66M | Hugging Face Hub, revision `564e9b582944a57a3e586bbb98fd6f0a4118db7f` |

Both models are real pretrained checkpoints downloaded once from the Hub and run locally on CPU (`torch==2.13.0+cpu`, `transformers==5.15.1`, fp32, `eval()` mode, no dropout) — not an API call to a hosted LLM, and not the synthetic agent relabeled. Full reproducibility manifest per model: `reproducibility/model.json`; environment/software versions: `reproducibility/environment.json`; corpus/dataset identity: `reproducibility/dataset.json`; seeds: `reproducibility/seeds.json`.

**New modules:** `src/phase4/real_model_runtime.py` (model loading + manifest), `src/phase4/classification_task.py`, `src/phase4/qa_task.py`, `src/phase4/uncertainty_eval.py` (task-family-agnostic metrics harness, preserves each family's own `mechanism` label rather than forcing one uncertainty signal onto all three families).

## 2. Honesty notes (read before trusting any number below)

- **No standard benchmark dataset (GLUE/SST-2, SQuAD) was downloaded.** The model-weight download already required one explicit user sign-off; a second dataset download would have needed a separate one. Instead, both evaluation corpora (`data/real_model_tasks/sentiment_eval.json`, `qa_eval.json`) are generated deterministically by `data/real_model_tasks/generate_corpora.py` (seeded, reproducible byte-for-byte) from templates whose correctness is guaranteed **by construction**: every sentiment example's true label is fixed by its template semantics (not by which words appear), and every QA gold answer is asserted to be a verbatim substring of its own context at generation time. This is real, objective, unambiguous ground truth over synthetic *inputs* — not a fabrication of model outputs or of labels.
- **First corpus draft was too easy.** An initial "easy" tier alone (400 sentiment / 160 QA examples) produced **100% accuracy on both new families**, which makes error-detection AUROC mathematically undefined (no error class present) — reported honestly rather than suppressed. A "hard" tier was then added (sarcasm/negation/mixed-clause sentiment; multi-entity and ordinal-position-reference QA distractors) to produce a realistic mix of correct and incorrect model outputs, which is what makes the uncertainty/calibration metrics below meaningful. The hard-tier templates were fixed and the corpus regenerated **before** re-running the evaluation script that produced the numbers below — no metric was inspected and then used to cherry-pick easier/harder examples after the fact.
- The three task families use **three genuinely different uncertainty mechanisms** (self-consistency agreement / softmax margin / span-logit confidence), per the instruction not to force one signal onto every family. `mechanism` is recorded per-record and never collapsed.
- Every metric in this report was produced in one run of `scripts/run_phase4_6_real_agent_evaluation.py`; no threshold or corpus content was tuned against these specific output numbers afterward.

## 3. Results

N is always reported; metrics unavailable for a family are `null`, never fabricated as 0.

| Family | N | Accuracy | Error rate | AUROC (error detection) | AUPRC (error detection) | Brier | ECE |
|---|---|---|---|---|---|---|---|
| Arithmetic (baseline) | 2000 | 0.956 | 0.044 | 0.953 | 0.459 | 0.079 | 0.185 |
| Sentiment classification | 660 | 0.909 | 0.091 | 0.659 | 0.467 | 0.088 | 0.089 |
| Extractive QA | 400 | 0.823 | 0.178 | 0.934 | 0.625 | 0.082 | 0.048 |

**Risk-coverage / selective accuracy** (confidence-ranked; keeping only the most-confident fraction of predictions):

- Arithmetic: accuracy at full coverage 0.956 → 1.000 by 70% coverage (the model's own self-consistency signal fully separates its errors once the least-confident 30% is set aside).
- Classification: 0.909 at full coverage → 0.945 at 80% coverage, degrading to 0.818 at the most-confident 10% slice (the softmax-margin signal is directionally useful — confirmed by AUROC 0.659, meaningfully above the 0.5 chance line — but far weaker than the other two families; see §4).
- Extractive QA: 0.823 at full coverage → 1.000 by 60% coverage (span-confidence cleanly separates the ordinal-position-distractor failures introduced by the hard tier).

Full curves: `evaluation/uncertainty_metrics.json`. Per-example raw outputs: `raw/episodes/arithmetic_episodes.json`, `raw/predictions/classification_predictions.json`, `raw/predictions/qa_predictions.json`.

## 4. Interpretation

- The arithmetic and QA families show strong error-detection discrimination (AUROC 0.93–0.95) — their respective uncertainty mechanisms (self-consistency disagreement; span-logit confidence) are genuinely informative about correctness on this evaluation set.
- The classification family's softmax-margin signal is weaker (AUROC 0.659) — better than chance but not strong. This is plausible and not suppressed: DistilBERT-SST2 is a confidently-calibrated model on in-distribution movie/product-review-style text, and the hard-tier sarcasm/negation examples it gets wrong, it often gets wrong **confidently** (a known failure mode of shallow lexical cues in sentiment models), which flattens the margin signal's ability to separate its errors. This is a real, measured limitation of the classification family's uncertainty mechanism, reported as found.
- These numbers are **not comparable in magnitude** to the arithmetic-only figures from Phase 4.5b (AUC 0.636/0.857) — different task, different mechanism, different corpus. Priority 3 will re-evaluate infrastructure-failure prediction on its own terms.

## 5. Test coverage

New tests (22, all passing): `tests/unit/test_real_model_runtime.py` (4), `tests/unit/test_classification_task.py` (5), `tests/unit/test_qa_task.py` (4), `tests/unit/test_uncertainty_eval.py` (7), `tests/integration/test_phase46_integration.py` (2).

```
python -m pytest tests/unit/test_real_model_runtime.py tests/unit/test_classification_task.py \
  tests/unit/test_qa_task.py tests/unit/test_uncertainty_eval.py tests/integration/test_phase46_integration.py -q
22 passed
```

## 6. Full repository regression check

Full suite (`python -m pytest`, Python 3.12.13, pytest 9.1.1): **753 passed, 21 failed, 823.91s**.

All 21 failures were **verified pre-existing on unmodified `main` (commit `8086e71`)** — confirmed by `git stash`-ing the only tracked-file change made in this priority (`requirements.txt`, additive `torch`/`transformers` lines only) and re-running the affected files, which failed identically. They fall into two unrelated, Phase-4.6-independent categories:
1. **Windows file-lock flakiness** (`tests/unit/test_phase45b_agent_runtime.py`, `test_phase45b_agent_recovery.py`, parts of `test_phase45b_agent_pipeline.py`): `tempfile.TemporaryDirectory.cleanup()` racing an open SQLite handle (`PermissionError: [WinError 32]`) — a Windows-specific temp-file-handle timing issue, not present in the pipeline logic itself.
2. **Deterministic but environment-sensitive assertions** (`test_phase44_pipeline.py::test_abstention_path_is_reachable_when_predicted_risk_is_high`, several `test_phase45_pipeline_extensions.py` / `test_phase45b_prediction_scope_router*.py` cases): real-subprocess-timing-dependent risk scores landing in a different decision band (`REVIEW` vs `ABSTAIN`) on this machine than whatever machine these tests were authored/last verified on.

No Phase 4.6 code path is implicated in any of the 21 failures (none touch `agent_task.py`, `classification_task.py`, `qa_task.py`, `real_model_runtime.py`, or `uncertainty_eval.py`). These are flagged here rather than silently ignored, per the project's audit discipline, and are carried forward as a known item for the Priority 5 complete-system audit rather than fixed opportunistically now (fixing them is out of Priority 1's scope and risks touching frozen/near-frozen Phase 4.4/4.5 code without the full audit context).

## 7. What Priority 1 does not claim

- Not evidence about infrastructure failure prediction (unchanged from Phase 4.5b; Priority 3).
- Not evidence about retry/abstain/review policy behavior for the new task families (Priority 2 — no `DecisionPolicy` wiring exists yet for classification/QA).
- Not evidence of generalization across environments (Priority 4 — everything above ran in one local CPU environment).
- The classification/QA corpora are templated and hand-designed, not a standard external benchmark; absolute accuracy/AUROC numbers should not be compared to published GLUE/SQuAD leaderboard figures.
