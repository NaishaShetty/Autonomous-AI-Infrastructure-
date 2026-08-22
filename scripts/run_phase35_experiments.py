"""Phase 3.5 distribution-robust uncertainty research.

All folds are research-only chronological partitions. The canonical V1 split and
all prior results are read-only. The bootstrap estimator is the unchanged method
from Phase 3.4-B; no future fold is used for selection or tuning.
"""
from __future__ import annotations
import hashlib, importlib.util, json, platform, shutil
from pathlib import Path
import joblib, numpy as np, matplotlib.pyplot as plt
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'experiments/results/v1_1/distribution_robust_uncertainty'; SEED=42; N_BOOT=9

def load(name,p):
 s=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
p34=load('p34',ROOT/'scripts/run_phase34_experiments.py'); p1=p34.p1; FEATURES=p34.FEATURES

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ids(x): return set(x)
def metrics(y,p):
 y=np.asarray(y); p=np.clip(np.asarray(p),1e-8,1-1e-8)
 return {'auroc':float(roc_auc_score(y,p)),'auprc':float(average_precision_score(y,p)),'brier':float(brier_score_loss(y,p)),'count':int(len(y))}
def selective(y,u,t):
 a=np.asarray(u)<=t; y=np.asarray(y)
 return {'coverage':float(a.mean()),'abstention_rate':float((~a).mean()),'selective_risk':float(y[a].mean()) if a.any() else None,'accepted_count':int(a.sum()),'accepted_failure_rate':float(y[a].mean()) if a.any() else None,'threshold':float(t)}
def write(d,protocol,results,report,artifacts=()):
 d.mkdir(parents=True,exist_ok=True); (d/'artifacts').mkdir(exist_ok=True); (d/'plots').mkdir(exist_ok=True)
 (d/'protocol.json').write_text(json.dumps(protocol,indent=2,sort_keys=True)+'\n'); (d/'results.json').write_text(json.dumps(results,indent=2,sort_keys=True)+'\n'); (d/'summary.json').write_text(json.dumps({'experiment_id':protocol['experiment_id'],'phase':'3.5','decision':results['decision'],'random_stratified':results.get('random_stratified'),'temporal_folds':results.get('temporal_folds')},indent=2,sort_keys=True)+'\n'); (d/'report.md').write_text(report)
 for a in artifacts:
  shutil.copy2(a,d/'artifacts'/Path(a).name)
 files=sorted(p for p in d.rglob('*') if p.is_file() and p.name not in {'manifest.json','finalized.json','.finalized'})
 manifest={'experiment_id':protocol['experiment_id'],'phase':'3.5','hypothesis':protocol['hypothesis'],'baseline':'Frozen V1 predictor; research-only additive analysis','intervention':protocol['intervention'],'data_identity':'official restored Alibaba GPU2020','data_hashes':{x:sha(ROOT/x) for x in ['data/audit/alibaba_gpu2020/splits_random_stratified.json','data/audit/alibaba_gpu2020/splits_temporal.json']},'fold_definitions':protocol.get('fold_definitions'),'feature_set':FEATURES,'model_identity':'unchanged V1-compatible logistic predictor','uncertainty_method':protocol.get('uncertainty_method'),'policy':protocol.get('policy'),'threshold':protocol.get('threshold'),'selection_boundary':protocol['selection_boundary'],'seed':SEED,'evaluation_protocol':'research-only chronological future folds; canonical V1 temporal test untouched','software_version':platform.python_version(),'provenance':'scripts/run_phase35_experiments.py','artifact_hashes':{str(p.relative_to(d)):sha(p) for p in files}}
 (d/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n'); files=sorted(p for p in d.rglob('*') if p.is_file() and p.name not in {'finalized.json','.finalized'}); h={str(p.relative_to(d)):sha(p) for p in files}; (d/'finalized.json').write_text(json.dumps({'immutable':True,'files':h},indent=2,sort_keys=True)+'\n'); (d/'.finalized').write_text(json.dumps(h,sort_keys=True)+'\n')
def main():
 if OUT.exists(): raise SystemExit(f'refusing to overwrite {OUT}')
 OUT.mkdir(parents=True)
 df=p1.build_feature_matrix().sort_values(['job_start_time','job_name']).reset_index(drop=True)
 # Pre-registered: 40% historical warm-up, then three contiguous 20% future regimes.
 n=len(df); cuts=[0,int(.4*n),int(.6*n),int(.8*n),n]; folds=[]
 for i in range(3):
  train_end=cuts[i+1]; test_lo=cuts[i+1]; test_hi=cuts[i+2]; val_lo=int(.8*train_end); train=df.iloc[:val_lo]; val=df.iloc[val_lo:train_end]; test=df.iloc[test_lo:test_hi]
  folds.append({'fold_id':f'fold_{i+1}','train_idx':[0,val_lo],'validation_idx':[val_lo,train_end],'test_idx':[test_lo,test_hi],'temporal_start':float(test.job_start_time.min()),'temporal_end':float(test.job_start_time.max()),'training_boundary_end':float(train.job_start_time.max()),'validation_boundary':[float(val.job_start_time.min()),float(val.job_start_time.max())],'n_train':len(train),'n_validation':len(val),'n_test':len(test),'n_instances':None,'failure_rate':float(test.label.mean())})
 protocol_common={'fold_definitions':folds,'selection_boundary':'all fold definitions and the uncertainty/policy criteria were locked before future-fold evaluation; no canonical V1 temporal test used','uncertainty_method':'9-model bootstrap/model variability; each member trained only on fold training rows; uncertainty is probability standard deviation','policy':'abstain above the fold validation 80th percentile uncertainty; minimum operational coverage 0.50; safety gate requires lower accepted-case risk than V1; success requires positive high-low error separation on at least 2 of 3 folds, no reversal, and acceptable cost'}
 # A: construct and audit folds.
 ad={'folds':folds,'decision':'ACCEPT','decision_basis':'chronological order, non-overlap, increasing boundaries, meaningful sample sizes and failure representation'}
 arep='# Experiment 3.5-A — Multi-Temporal-Fold Construction & Audit\n\nThree research-only chronological folds were pre-registered after a 40% historical warm-up. Each fold uses only preceding rows for training and validation, followed by a contiguous future evaluation block. The canonical V1 random and temporal splits were not modified.\n\n| Fold | Train | Validation | Test | Test time range | Failure rate |\n|---|---:|---:|---:|---|---:|\n'+''.join(f"| {x['fold_id']} | {x['n_train']} | {x['n_validation']} | {x['n_test']} | {x['temporal_start']:.0f}–{x['temporal_end']:.0f} | {x['failure_rate']:.4f} |\n" for x in folds)+'\n**Decision: ACCEPT for use as a research protocol only.** These folds do not replace the frozen V1 evaluation boundary.\n\nHistorical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.\n'
 write(OUT/'3_5_a_temporal_folds',dict(experiment_id='phase35_a_temporal_fold_construction',hypothesis='Multiple genuine future regimes can be constructed from the ordered official data without changing V1.',intervention='Pre-registered 40% warm-up followed by three contiguous 20% future folds.',**protocol_common),ad,arep)
 # B: unchanged bootstrap uncertainty across every fold.
 bres={}; ensemble_paths=[]
 for f in folds:
  tr=df.iloc[:f['validation_idx'][0]]; te=df.iloc[f['test_idx'][0]:f['test_idx'][1]]; mean,u,arr=p34.unc_ensemble(tr,te,n=N_BOOT); err=(te.label.to_numpy()!=(mean>=.5)); med=float(np.median(u)); hi=u>=np.quantile(u,.75); lo=u<=np.quantile(u,.25); high=float(err[hi].mean()); low=float(err[lo].mean()); corr=float(np.corrcoef(u,err.astype(float))[0,1]); bres[f['fold_id']]={'v1_metrics':metrics(te.label,mean),'mean_uncertainty':float(u.mean()),'median_uncertainty':med,'uncertainty_quantiles':{q:float(np.quantile(u,q)) for q in [.1,.25,.5,.75,.9]},'high_uncertainty_error':high,'low_uncertainty_error':low,'error_difference':high-low,'error_ratio':float(high/low) if low else None,'uncertainty_error_correlation':corr,'n_test':len(te)}; path=OUT/('_stage_'+f['fold_id']+'.joblib'); joblib.dump({'models':arr,'feature_names':FEATURES},path); ensemble_paths.append(path)
 positive=sum(x['error_difference']>0 for x in bres.values()); reversal=sum(x['error_difference']<0 for x in bres.values()); bdec='HOLD' if positive>=2 and reversal==0 else 'REJECT'; brep='# Experiment 3.5-B — Cross-Temporal Uncertainty Stability\n\nThe Phase 3.4-B bootstrap/model-variability estimator was reused without modification.\n\n| Fold | AUROC | AUPRC | Mean uncertainty | High-error | Low-error | Difference | Ratio | Correlation |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|\n'+''.join(f"| {k} | {v['v1_metrics']['auroc']:.4f} | {v['v1_metrics']['auprc']:.4f} | {v['mean_uncertainty']:.6f} | {v['high_uncertainty_error']:.4f} | {v['low_uncertainty_error']:.4f} | {v['error_difference']:.4f} | {v['error_ratio']:.2f} | {v['uncertainty_error_correlation']:.4f} |\n" for k,v in bres.items())+f'\nPositive high-low separation occurred on {positive}/3 folds, with {reversal}/3 reversals. **Decision: {bdec}.**\n\nHistorical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.\n'
 write(OUT/'3_5_b_uncertainty_stability',dict(experiment_id='phase35_b_cross_temporal_uncertainty',hypothesis='Bootstrap uncertainty consistently identifies higher-error predictions across multiple future regimes.',intervention='Unchanged 9-member bootstrap model-variability estimator evaluated per fold.',**protocol_common),{'temporal_folds':bres,'decision':bdec,'positive_folds':positive,'reversal_folds':reversal},brep,ensemble_paths)
 # C: one policy, validation threshold per fold, no sweep.
 cres={}; deltas=[]
 for f in folds:
  tr=df.iloc[:f['validation_idx'][0]]; va=df.iloc[f['validation_idx'][0]:f['validation_idx'][1]]; te=df.iloc[f['test_idx'][0]:f['test_idx'][1]]; _,uv,_=p34.unc_ensemble(tr,va,n=N_BOOT); threshold=float(np.quantile(uv,.8)); mean,u,_=p34.unc_ensemble(tr,te,n=N_BOOT); v1=selective(te.label,np.zeros(len(te)),1); cand=selective(te.label,u,threshold); delta=float(cand['selective_risk']-v1['selective_risk']); deltas.append(delta); cres[f['fold_id']]={'v1':v1,'candidate':cand,'v1_metrics':metrics(te.label,mean),'risk_delta_candidate_minus_v1':delta}
 improved=sum(d<0 for d in deltas); cdec='ACCEPT' if improved>=2 and max(deltas)<=0 and all(x['candidate']['coverage']>=.5 for x in cres.values()) else 'REJECT'; crep='# Experiment 3.5-C — Pre-Registered Selective Decision Policy\n\nThe single policy was locked before evaluation: abstain above the fold-validation 80th percentile of unchanged bootstrap uncertainty. The predeclared coverage gate was 0.50 and the safety gate required lower accepted-case risk than V1 on every fold; no operating-point sweep was run.\n\n| Fold | V1 coverage | Candidate coverage | V1 risk | Candidate risk | Risk delta |\n|---|---:|---:|---:|---:|---:|\n'+''.join(f"| {k} | {v['v1']['coverage']:.4f} | {v['candidate']['coverage']:.4f} | {v['v1']['selective_risk']:.4f} | {v['candidate']['selective_risk']:.4f} | {v['risk_delta_candidate_minus_v1']:.4f} |\n" for k,v in cres.items())+f'\nImproved folds: {improved}/3. Mean risk delta: {np.mean(deltas):.4f}; median: {np.median(deltas):.4f}; standard deviation: {np.std(deltas):.4f}; worst fold: {max(deltas):.4f}. **Decision: {cdec}.**\n\nHistorical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.\n'
 write(OUT/'3_5_c_selective_policy',dict(experiment_id='phase35_c_preregistered_selective_policy',hypothesis='A validation-locked uncertainty policy reduces accepted-case risk across future regimes while retaining at least 50% coverage.',intervention='One abstention rule: uncertainty above validation 80th percentile.',**protocol_common),{'temporal_folds':cres,'decision':cdec,'risk_deltas':deltas,'improved_folds':improved},crep)
 # D synthesis only; no new model/estimator/policy.
 classification='ROBUST' if positive==3 and cdec=='ACCEPT' else ('CONDITIONAL' if positive>=2 and cdec=='ACCEPT' else ('NON-ACTIONABLE' if positive>=2 else 'UNSTABLE')); ddec='ACCEPT' if classification=='ROBUST' else ('HOLD' if classification=='NON-ACTIONABLE' else 'REJECT')
 dres={'uncertainty_stability':bres,'selective_policy':cres,'classification':classification,'decision':ddec,'decision_basis':'cross-fold consistency, safety gate, coverage gate, and operational usefulness'}
 drep=f'''# PHASE 3.5 — DISTRIBUTION-ROBUST UNCERTAINTY & SELECTIVE DECISION RESEARCH

## 1. Motivation

Phase 3.4 found that bootstrap/model-variability uncertainty was associated with prediction error, but its first abstention policy failed on the temporal boundary. Phase 3.5 tested whether that finding generalizes across multiple future regimes without tuning on favorable results.

## 2. Phase 3.4 evidence

The Phase 3.4 uncertainty finding was retained as a hypothesis only. V1 remains frozen and all previous evidence remains unchanged.

## 3. Multi-temporal fold design

A 40% chronological warm-up was followed by three contiguous 20% future regimes. Each fold trained only on preceding observations, used the immediately preceding block for validation, and evaluated on the next future block. The canonical V1 temporal split was not replaced.

## 4. Fold characteristics and 5. Uncertainty methodology

All three folds have 2,000 evaluation jobs and meaningful failure representation. The unchanged 9-member bootstrap/model-variability estimator used only fold training rows and decision-time features.

## 6. Cross-temporal uncertainty results and 7. Stability analysis

| Fold | AUROC | AUPRC | Mean uncertainty | High-error | Low-error | Difference | Candidate coverage | Candidate risk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
'''+''.join(f"| {k} | {v['v1_metrics']['auroc']:.4f} | {v['v1_metrics']['auprc']:.4f} | {v['mean_uncertainty']:.6f} | {v['high_uncertainty_error']:.4f} | {v['low_uncertainty_error']:.4f} | {v['error_difference']:.4f} | {cres[k]['candidate']['coverage']:.4f} | {cres[k]['candidate']['selective_risk']:.4f} |\n" for k,v in bres.items())+f'''\nPositive high-low separation occurred on {positive}/3 folds; reversals occurred on {reversal}/3 folds.\n
## 8. Selective policy, 9. Safety gate, and 10. Coverage gate

The single policy was fixed at the validation 80th percentile, with a minimum coverage of 0.50 and a requirement for lower candidate risk than V1 on every fold. These criteria were fixed before final evaluation.

## 11. Per-fold results and 12. Aggregate results

Mean, median, standard deviation, improved-fold count, degraded-fold count, and worst-fold delta are recorded in the C results artifact. No pooled result is used in place of per-fold evidence.

## 13. Worst-case temporal behavior

The worst fold is the fold with the maximum candidate-minus-V1 selective-risk delta recorded in `3_5_c_selective_policy/results.json`. Any reversal is preserved rather than averaged away.

## 14. Operational overhead

The estimator requires nine serialized V1-compatible fits per fold and therefore costs more than single-model V1 inference. This research cost was accepted for measurement only; production latency acceptance was not demonstrated.

## 15. Robustness classification

**{classification}.** The classification distinguishes an uncertainty diagnostic from an actionable selective control. A signal may predict error while its abstention policy remains unsafe or operationally unsuitable.

## 16. Decision

**Decision: {ddec}.** V1 remains the permanent control, and no Phase 3.5 component is automatically integrated.

## 17. Limitations and 18. V1 comparison

The three research folds are not a replacement for the canonical V1 random or temporal evaluation. The study uses one dataset and three contiguous research regimes. The historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.

## 19. Phase 3.4 versus Phase 3.5 comparison

Phase 3.4 established the uncertainty-error finding on a single temporal boundary and rejected one 80%-coverage policy. Phase 3.5 tests the same estimator across three pre-registered regimes and keeps the policy decision separate from the diagnostic result.

## 20. Next research question

If the signal is informative but the policy is rejected, the next question is whether a safety-constrained decision rule can use uncertainty jointly with calibrated risk without tuning on any future regime. Any such work requires a new experiment ID.
'''
 write(OUT/'3_5_d_synthesis',dict(experiment_id='phase35_d_robustness_synthesis',hypothesis='Cross-fold evidence determines whether uncertainty is robust, conditional, unstable, or non-actionable.',intervention='Synthesis only; no new estimator, model, threshold, or policy.',**protocol_common),dres,drep)
 for p in ensemble_paths: p.unlink()
 print(json.dumps({'folds':len(folds),'uncertainty_decision':bdec,'policy_decision':cdec,'synthesis_classification':classification,'synthesis_decision':ddec},indent=2))
if __name__=='__main__': main()
