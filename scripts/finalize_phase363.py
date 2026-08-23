import hashlib,json,platform
from pathlib import Path
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'experiments/results/v1_1/v1_forensics/3_6_3_multi_temporal_validation';R=json.loads((D/'results.json').read_text());F=R['fold_results'];S=R['model_summary'];models=['v1_logistic','linear_c01','limited_interactions','constrained_rf','gradient_boosting'];labels=['V1','Linear C=.1','Interactions','RF','GB']
P=D/'plots';P.mkdir(exist_ok=True)
for name,metric,ylabel,title in [('per_fold_auroc','auroc','AUROC','Per-Fold AUROC'),('per_fold_auprc','auprc','AUPRC','Per-Fold AUPRC')]:
 plt.figure(figsize=(8,5));
 for m,l in zip(models,labels):plt.plot(range(1,4),[F[f][m][metric] for f in F],marker='o',label=l)
 plt.xticks([1,2,3],['Fold 1','Fold 2','Fold 3']);plt.xlabel('Chronological fold');plt.ylabel(ylabel);plt.title(title);plt.legend();plt.grid(alpha=.25);plt.tight_layout();plt.savefig(P/f'{name}.png',dpi=160);plt.close()
deltas=R['model_summary']['interaction_vs_v1']['fold_deltas'];plt.figure(figsize=(7,4.5));v=[x['auroc_delta'] for x in deltas];plt.axhline(0,color='black',lw=1);plt.bar(['Fold 1','Fold 2','Fold 3'],v,color=['#b45309' if x<0 else '#15803d' for x in v]);plt.ylabel('Interaction AUROC − V1 AUROC');plt.title('Interaction vs V1 Delta');plt.tight_layout();plt.savefig(P/'interaction_vs_v1_delta.png',dpi=160);plt.close()
plt.figure(figsize=(8,5));plt.bar(labels,[S[m]['min_auroc'] for m in models],color='#334155');plt.ylabel('Minimum fold AUROC');plt.title('Worst-Case Temporal Performance');plt.ylim(0,1);plt.tight_layout();plt.savefig(P/'worst_case_temporal_auroc.png',dpi=160);plt.close()
plt.figure(figsize=(8,5));plt.errorbar(labels,[S[m]['mean_auroc'] for m in models],yerr=[S[m]['std_auroc'] for m in models],fmt='o',capsize=5,color='#7c3aed');plt.ylabel('Fold AUROC (mean ± standard deviation)');plt.title('Performance Stability Across Three Folds');plt.ylim(0,1);plt.grid(alpha=.25);plt.tight_layout();plt.savefig(P/'performance_stability.png',dpi=160);plt.close()
# Full report
fold_rows=[]
for fid in F:
 for m,l in zip(models,labels):
  x=F[fid][m];fold_rows.append(f"| {fid.replace('_',' ').title()} | {l} | {x['auroc']:.4f} | {x['auprc']:.4f} | {x['brier']:.4f} | {x['ece']:.4f} |")
summary_rows=[]
for m,l in zip(models,labels):
 x=S[m]; summary_rows.append(f"| {l} | {x['mean_auroc']:.4f} | {x['median_auroc']:.4f} | {x['mean_auprc']:.4f} | {x['median_auprc']:.4f} | {'—' if m=='v1_logistic' else sum(F[f][m]['auroc']>F[f]['v1_logistic']['auroc'] for f in F)} | {'—' if m=='v1_logistic' else sum(F[f][m]['auroc']<F[f]['v1_logistic']['auroc'] for f in F)} |")
rep=f'''# PHASE 3.6.3 — MULTI-TEMPORAL INDUCTIVE-BIAS VALIDATION

## 1. Executive Summary

This validation study evaluated the frozen Phase 3.6.2 model ladder across the three authoritative Phase 3.5 chronological future folds. The exact 14-feature base contract, predeclared interactions, model definitions, train-only preprocessing, validation-only calibration, and fold boundaries were preserved. No model, fold, threshold, or acceptance criterion was selected after observing future-fold results.

## 2. Research Question and Hypothesis

The primary question was whether the three-interaction model that reached 0.8439 AUROC on the canonical temporal test would continue to outperform frozen V1 across multiple independent chronological future regimes. The preregistered hypothesis was deliberately non-directional: the interaction model could win, lose, or show regime sensitivity.

## 3. Fold Contract

The existing Phase 3.5 folds were reused without redesign: expanding historical training populations, immediately preceding validation populations, and contiguous future evaluation populations. Fold 1, Fold 2, and Fold 3 contain 2,000 future evaluation rows each. Their definitions, row hashes, temporal bounds, and no-overlap checks are recorded under `fold_definitions/` and `results.json`.

## 4. Matched Feature and Model Contract

All models used the exact 14 numeric V1 features, in canonical order, with training-fitted median imputation and standardization. Model definitions were frozen from Phase 3.6.2. The only derived representation was the unchanged three-interaction candidate: `n_tasks × mean_plan_cpu`, `n_tasks × mean_plan_gpu`, and `mean_plan_cpu × mean_plan_gpu`. No categorical, drift, contextual, uncertainty, or additional interaction feature was used.

## 5. Calibration and Metrics

Each fold/model fit isotonic calibration on that fold's historical validation population only. AUROC and AUPRC are the primary metrics; Brier and ECE are secondary and use the common declared calibration path. Future-fold predictions were never used for calibration or selection.

## 6. Required Per-Fold Results

| Fold | Model | AUROC | AUPRC | Brier | ECE |
|---|---|---:|---:|---:|---:|
{''.join(fold_rows)}

## 7. Model Summary

| Model | Mean AUROC | Median AUROC | Mean AUPRC | Median AUPRC | Folds beating V1 | Folds losing to V1 |
|---|---:|---:|---:|---:|---:|---:|
{''.join(summary_rows)}

The model summaries also record minimum, maximum, standard deviation, and range. The worst future regime is retained rather than averaged away.

## 8. Interaction Primary Test

Interaction-minus-V1 AUROC deltas were: Fold 1 **{deltas[0]['auroc_delta']:.4f}**, Fold 2 **{deltas[1]['auroc_delta']:.4f}**, and Fold 3 **{deltas[2]['auroc_delta']:.4f}**. The interaction model beat V1 on **{S['interaction_vs_v1']['wins_auroc']}/3 folds**, lost on **{S['interaction_vs_v1']['losses_auroc']}/3 folds**, had mean delta **{S['interaction_vs_v1']['mean_auroc_delta']:.4f}**, median delta **{S['interaction_vs_v1']['median_auroc_delta']:.4f}**, worst delta **{S['interaction_vs_v1']['worst_auroc_delta']:.4f}**, and best delta **{S['interaction_vs_v1']['best_auroc_delta']:.4f}**.

![Interaction versus V1 delta](plots/interaction_vs_v1_delta.png)

## 9. Temporal Robustness and Failure Consistency

V1 mean AUROC was **{S['v1_logistic']['mean_auroc']:.4f}**, with worst fold **{S['v1_logistic']['min_auroc']:.4f}**. The interaction model mean was **{S['limited_interactions']['mean_auroc']:.4f}**, with worst fold **{S['limited_interactions']['min_auroc']:.4f}**. RF and GB were lower and comparatively unstable or weak across the folds. The interaction model is **regime-sensitive**: it was close to V1 on Fold 1, materially worse on Fold 2, and better on Fold 3. RF is consistently low in this replay; GB is comparatively stable around a low AUROC, but neither is a reliable competitor to V1.

![Per-fold AUROC](plots/per_fold_auroc.png)

![Per-fold AUPRC](plots/per_fold_auprc.png)

![Worst-case temporal performance](plots/worst_case_temporal_auroc.png)

![Performance stability](plots/performance_stability.png)

## 10. Generalization Analysis

The preserved canonical random-stratified evaluation is not a fold-specific random reference for these forward folds. Therefore no fabricated fold-level random-minus-future comparison is reported. The scientific comparison here is strictly across the authoritative future regimes.

## 11. Decision

**Outcome D — Interaction Instability / Partial Validation.** The Phase 3.6.2 interaction advantage did not persist consistently: it won one of three folds and lost two, including a −0.0718 AUROC loss on Fold 2. The result is therefore **promising but uncertain at most, and practically dataset/regime-sensitive**, not a strong candidate for integration. No unfavorable fold was removed.

## 12. Tree and Linear Interpretation

The RF and GB results provide additional support for the earlier observation that flexible tree models can fail under changing future distributions, although the three-fold evidence is descriptive and dataset-bounded. The C=0.1 linear model remains close to V1, supporting a broader constrained-linear stability hypothesis without proving that V1's exact parameterization is optimal.

## 13. Limitations

Only three chronological folds are available. This is insufficient for universal superiority claims or causal identification. The data is one restored Alibaba GPU2020 dataset, and fold-level estimates can vary with regime composition. The exact seven historical skipped test-node identities remain unrecoverable from preserved evidence.

## 14. V1 and Integration Status

V1 remains **FROZEN**. There is **no V1.1 integration, replacement, modification, threshold change, calibration change, runtime change, or safety-policy change**. This phase is validation evidence only.

## 15. Final Questions

**Does complexity hurt temporal generalization? YES — PARTIAL EVIDENCE.** The tree-based flexible models show the expected failure pattern, but the limited-interaction model is not uniformly worse and the relationship is not monotonic.

**Does the interaction model consistently outperform V1 across multiple future folds? NO.** It beats V1 on one fold and loses on two.

**Does constrained linear structure explain part of V1's temporal robustness? PARTIALLY SUPPORTED.** V1 and the nearby linear variant are comparatively stable, while the tree models are weak; however, the interaction model's mixed results prevent a stronger claim.

## 16. Next Research Question

A future study should predeclare additional forward folds or a second compatible dataset and evaluate the same frozen ladder with descriptive uncertainty intervals. Any candidate interaction model would require a new phase with broader safety, calibration, coverage, and operational analysis; it must not be integrated from this study.
'''
(D/'report.md').write_text(rep)
# hash all artifacts last
files=sorted(p for p in D.rglob('*') if p.is_file() and p.name not in {'manifest.json','finalized.json','.finalized'})
manifest={'experiment_id':'phase363_multi_temporal_inductive_bias_validation','phase':'3.6.3','fold_source':'Phase 3.5 authoritative fold manifest','feature_contract':json.loads((D/'protocol.json').read_text())['feature_contract'],'interaction_set':json.loads((D/'protocol.json').read_text())['interaction_set'],'artifact_hashes':{str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'software_version':platform.python_version()}
(D/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');files=sorted(p for p in D.rglob('*') if p.is_file() and p.name not in {'finalized.json','.finalized'});h={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files};(D/'finalized.json').write_text(json.dumps({'immutable':True,'files':h},indent=2,sort_keys=True)+'\n');(D/'.finalized').write_text(json.dumps(h,sort_keys=True)+'\n');print('finalized',len(h))
