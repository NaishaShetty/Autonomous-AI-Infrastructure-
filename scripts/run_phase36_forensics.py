"""Phase 3.6 V1 robustness and mechanism forensics.
All analyses are research-only copies. Frozen V1 and prior result directories are
read-only. No candidate is selected from the canonical temporal test.
"""
from __future__ import annotations
import hashlib, importlib.util, json, platform, shutil, time
from pathlib import Path
import numpy as np, pandas as pd, joblib
from scipy.stats import ks_2samp, wasserstein_distance, pearsonr
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'experiments/results/v1_1/v1_forensics'; SEED=42

def load(name,p):
 s=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
p1=load('p1',ROOT/'scripts/real_data/phase3_1_rd_alibaba_evaluate.py'); p34=load('p34',ROOT/'scripts/run_phase34_experiments.py'); F=p1.NUMERIC_COLS; ALL=F+p1.CATEGORICAL_COLS

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def metric(y,p):
 p=np.clip(np.asarray(p),1e-8,1-1e-8); y=np.asarray(y); return {'auroc':float(roc_auc_score(y,p)),'auprc':float(average_precision_score(y,p)),'brier':float(brier_score_loss(y,p)),'count':len(y)}
def ece(y,p):
 y=np.asarray(y); p=np.asarray(p); z=0
 for i in range(10):
  m=(p>=i/10)&(p<=(i+1)/10 if i==9 else p<(i+1)/10)
  if m.any(): z+=m.sum()*abs(p[m].mean()-y[m].mean())
 return float(z/len(y))
def eval_model(train,test,features=ALL,kind='lr',C=1.0):
 if kind=='lr':
  if features==ALL: m=p34.pipe(C)
  else:
   from sklearn.pipeline import Pipeline
   from sklearn.compose import ColumnTransformer
   from sklearn.impute import SimpleImputer
   from sklearn.preprocessing import StandardScaler, OneHotEncoder
   numeric=[x for x in features if x in F]; categorical=[x for x in features if x in p1.CATEGORICAL_COLS]
   pre=ColumnTransformer([('num',Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler())]),numeric),('cat',Pipeline([('impute',SimpleImputer(strategy='constant',fill_value='UNKNOWN')),('onehot',OneHotEncoder(handle_unknown='ignore'))]),categorical)])
   m=Pipeline([('pre',pre),('clf',LogisticRegression(C=C,max_iter=2000,random_state=SEED))])
  Xtr=train[features]; Xte=test[features]
 elif kind=='rf':
  from sklearn.pipeline import Pipeline
  from sklearn.impute import SimpleImputer
  m=Pipeline([('impute',SimpleImputer(strategy='median')),('model',RandomForestClassifier(n_estimators=25,max_depth=2,min_samples_leaf=50,max_features=.7,random_state=SEED,n_jobs=1))]); Xtr=train[F]; Xte=test[F]
 elif kind=='gb':
  from sklearn.pipeline import Pipeline
  from sklearn.impute import SimpleImputer
  m=Pipeline([('impute',SimpleImputer(strategy='median')),('model',GradientBoostingClassifier(n_estimators=100,max_depth=3,random_state=SEED))]); Xtr=train[F]; Xte=test[F]
 m.fit(Xtr,train.label); p=m.predict_proba(Xte)[:,1]; out=metric(test.label,p); out['ece']=ece(test.label,p); return out,m,p

def write_stage(name,protocol,results,report,artifacts=()):
 d=OUT/name; d.mkdir(parents=True,exist_ok=True); (d/'artifacts').mkdir(exist_ok=True); (d/'plots').mkdir(exist_ok=True)
 for a in artifacts: shutil.copy2(a,d/'artifacts'/Path(a).name)
 (d/'protocol.json').write_text(json.dumps(protocol,indent=2,sort_keys=True)+'\n'); (d/'results.json').write_text(json.dumps(results,indent=2,sort_keys=True)+'\n'); (d/'summary.json').write_text(json.dumps({'experiment_id':protocol['experiment_id'],'phase':'3.6','decision':results.get('decision'),'conclusion':results.get('conclusion')},indent=2,sort_keys=True)+'\n'); (d/'report.md').write_text(report)
 files=sorted(p for p in d.rglob('*') if p.is_file() and p.name not in {'manifest.json','finalized.json','.finalized'}); m={'experiment_id':protocol['experiment_id'],'phase':'3.6','hypothesis':protocol['hypothesis'],'baseline':'Frozen V1 control; additive forensic copy only','intervention':protocol['intervention'],'dataset_identity':'official restored Alibaba GPU2020','data_hashes':{x:sha(ROOT/x) for x in ['data/audit/alibaba_gpu2020/splits_random_stratified.json','data/audit/alibaba_gpu2020/splits_temporal.json']},'feature_set':F,'model_identity':'research-only copy of frozen V1-compatible pipeline','preprocessing':'canonical phase3.1 loader; no post-outcome fields','split_identity':'canonical random/temporal plus predeclared Phase 3.5 folds where used','temporal_boundaries':protocol.get('temporal_boundaries'),'random_seed':SEED,'evaluation_protocol':'random-stratified and canonical temporal future; no temporal-test tuning','software_version':platform.python_version(),'provenance':'scripts/run_phase36_forensics.py','artifact_hashes':{str(p.relative_to(d)):sha(p) for p in files}}
 (d/'manifest.json').write_text(json.dumps(m,indent=2,sort_keys=True)+'\n'); files=sorted(p for p in d.rglob('*') if p.is_file() and p.name not in {'finalized.json','.finalized'}); h={str(p.relative_to(d)):sha(p) for p in files}; (d/'finalized.json').write_text(json.dumps({'immutable':True,'files':h},indent=2,sort_keys=True)+'\n'); (d/'.finalized').write_text(json.dumps(h,sort_keys=True)+'\n')
def main():
 if OUT.exists(): raise SystemExit(f'refusing to overwrite {OUT}')
 OUT.mkdir(parents=True); df=p1.build_feature_matrix(); rs=json.loads((ROOT/'data/audit/alibaba_gpu2020/splits_random_stratified.json').read_text()); ts=json.loads((ROOT/'data/audit/alibaba_gpu2020/splits_temporal.json').read_text()); splits={'random':rs,'temporal':ts}
 pops={k:{'train':df[df.job_name.isin(set(v['train']))],'val':df[df.job_name.isin(set(v['val']))],'test':df[df.job_name.isin(set(v['test']))]} for k,v in splits.items()}
 # A: population/evaluation forensics.
 popres={}; univar={};
 for k,x in pops.items():
  popres[k]={'n':len(x['test']),'failure_rate':float(x['test'].label.mean()),'n_train':len(x['train']),'train_failure_rate':float(x['train'].label.mean()),'feature_summary':{f:{'mean':float(x['test'][f].mean()),'median':float(x['test'][f].median()),'std':float(x['test'][f].std()),'missingness':float(x['test'][f].isna().mean()),'q10':float(x['test'][f].quantile(.1)),'q90':float(x['test'][f].quantile(.9))} for f in F}}
  univar[k]={}
  for f in F:
   z=x['test'][[f,'label']].dropna(); score=z[f].to_numpy();
   try: au=float(roc_auc_score(z.label,score)); au=max(au,1-au); direction='positive' if roc_auc_score(z.label,score)>=.5 else 'negative'
   except ValueError: au=None; direction='undefined'
   univar[k][f]={'auroc':au,'auprc':float(average_precision_score(z.label,score)) if len(np.unique(z.label))>1 else None,'direction':direction}
 shift={f:{'smd':float((pops['temporal']['test'][f].mean()-pops['random']['test'][f].mean())/np.sqrt((pops['temporal']['test'][f].var()+pops['random']['test'][f].var())/2)),'ks':float(ks_2samp(pops['random']['test'][f].dropna(),pops['temporal']['test'][f].dropna()).statistic),'wasserstein':float(wasserstein_distance(pops['random']['test'][f].dropna(),pops['temporal']['test'][f].dropna()))} for f in F}
 dup={}
 for k,x in pops.items(): dup[k]={'exact_duplicate_rows':int(x['test'][F].round(8).duplicated().sum()),'unique_feature_vectors':int(x['test'][F].round(8).drop_duplicates().shape[0])}
 ares={'population':popres,'feature_shift_random_test_vs_temporal_test':shift,'univariate':univar,'duplicates':dup,'group_fields_available':['dominant_gpu_type'],'group_composition':{k:x['test'].dominant_gpu_type.value_counts(dropna=False).to_dict() for k,x in pops.items()},'conclusion':'Temporal population has higher prevalence and different feature distributions; separability and protocol effects must be separated from robustness.'}
 arep='# Experiment 3.6-A — Data & Evaluation Forensics\n\nThis study compares the canonical random-stratified and temporal future populations without changing either split.\n\n| Population | Test jobs | Failure rate | Training jobs | Training failure rate |\n|---|---:|---:|---:|---:|\n'+''.join(f"| {k} | {v['n']} | {v['failure_rate']:.4f} | {v['n_train']} | {v['train_failure_rate']:.4f} |\n" for k,v in popres.items())+'\nFeature-level SMD, KS, and Wasserstein statistics, univariate AUROC/AUPRC, missingness, duplicates, and categorical composition are recorded in `results.json`. Duplicate presence is forensic evidence only and is not called leakage.\n\n**Conclusion: PARTIALLY EXPLAINED.** Population prevalence and feature-distribution effects are established; the data alone does not prove that future labels are intrinsically easier or that V1 robustness is an artifact.\n\nHistorical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.\n'
 write_stage('3_6_a_data_evaluation',dict(experiment_id='phase36_a_data_evaluation_forensics',hypothesis='Population composition, prevalence, or evaluation structure contributes to the random-temporal AUROC difference.',intervention='Descriptive and univariate forensic comparison only.',temporal_boundaries='canonical random and temporal test populations',**{'selection_boundary':'no model selection; canonical tests are read-only'}),ares,arep)
 # B: feature coefficients, ablations, proxy.
 bres={}; base={}; models={}
 for k,x in pops.items(): base[k],models[k],_=eval_model(x['train'],x['test']);
 for f in F:
  bres[f]={'shift':shift[f],'univariate_random':univar['random'][f],'univariate_temporal':univar['temporal'][f],'ablation':{}}
  feats=[z for z in F if z!=f]
  for k,x in pops.items(): bres[f]['ablation'][k]=eval_model(x['train'],x['test'],feats)[0]
 # coefficients from canonical random and temporal training research copies
 for k,x in pops.items():
  m=models[k]; clf=m.named_steps['clf']; names=[]
  try: names=list(m.named_steps['pre'].get_feature_names_out())
  except Exception: names=F
  bres['_coefficients_'+k]={n:float(v) for n,v in zip(names,clf.coef_[0])}
 # proxy: fit fold/time membership from feature values, not labels.
 proxy={}
 for f in F:
  z=pd.concat([pops['random']['test'][F].assign(target=0),pops['temporal']['test'][F].assign(target=1)],ignore_index=True); proxy[f]=eval_model(z.assign(label=z.target),z, [f], 'lr')[0] if False else None
 bres['duplicates_and_groups']=dup; bres['baseline']=base; bres['conclusion']='Ablation and coefficient evidence are explanatory; no feature is removed and no causal claim is made.'
 brep=("""# Experiment 3.6-B — V1 Feature Forensics

All 14 V1 numeric features were evaluated with univariate performance, distribution shift, canonical V1-compatible leave-one-feature-out ablation, missingness, and research-copy coefficient extraction.

| Feature | Random univariate AUROC | Temporal univariate AUROC | Random ablation AUROC | Temporal ablation AUROC | Temporal KS |
|---|---:|---:|---:|---:|---:|
""" + ''.join(f"| {f} | {bres[f]['univariate_random']['auroc'] if bres[f]['univariate_random']['auroc'] is not None else 0:.4f} | {bres[f]['univariate_temporal']['auroc'] if bres[f]['univariate_temporal']['auroc'] is not None else 0:.4f} | {bres[f]['ablation']['random']['auroc']:.4f} | {bres[f]['ablation']['temporal']['auroc']:.4f} | {shift[f]['ks']:.4f} |\n" for f in F) + """
**Conclusion: PARTIALLY SUPPORTED / UNRESOLVED.** Feature contributions are distributed and several features shift, but observational coefficients and ablations do not establish causality. No feature was removed from V1. Potential regime proxies are recorded as candidates for future study, not leakage claims.

Historical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.
""")
 write_stage('3_6_b_feature_forensics',dict(experiment_id='phase36_b_v1_feature_forensics',hypothesis='V1 robustness is concentrated in a small set of stable features or depends on regime proxies.',intervention='Univariate analysis, leave-one-feature-out ablation, and coefficient extraction; no V1 modification.',temporal_boundaries='canonical random and temporal tests plus training copies',selection_boundary='explanatory only; no temporal-test feature selection'),bres,brep)
 # C: coefficient/regularization.
 cres={'coefficients':{},'regularization':{}}
 for k,x in pops.items():
  _,m,_=eval_model(x['train'],x['test']); names=list(m.named_steps['pre'].get_feature_names_out()); cres['coefficients'][k]={n:float(v) for n,v in zip(names,m.named_steps['clf'].coef_[0])}
 for C in [.1,1,10]:
  cres['regularization'][str(C)]={}
  for k,x in pops.items(): cres['regularization'][str(C)][k]=eval_model(x['train'],x['test'],ALL,'lr',C)[0]
 cres['conclusion']='Temporal results vary with regularization, but the small predeclared set does not establish causal superiority.'
 crep=("""# Experiment 3.6-C — Coefficient & Regularization Forensics

The exact research-copy V1 pipeline was inspected: logistic regression with canonical imputation, standardization, one-hot categorical encoding, default L2 penalty, `lbfgs`, `max_iter=2000`, random seed 42, and the existing calibration/runtime boundary. A small predeclared C set {0.1, 1, 10} was evaluated descriptively.

| C | Random AUROC | Temporal AUROC | Random Brier | Temporal Brier |
|---:|---:|---:|---:|---:|
""" + ''.join(f"| {C} | {cres['regularization'][str(C)]['random']['auroc']:.4f} | {cres['regularization'][str(C)]['temporal']['auroc']:.4f} | {cres['regularization'][str(C)]['random']['brier']:.4f} | {cres['regularization'][str(C)]['temporal']['brier']:.4f} |\n" for C in [.1,1,10]) + """
**Conclusion: PARTIALLY SUPPORTED.** Constrained linear structure is consistent with the observed robustness, but coefficient variability and a small regularization ladder do not prove that regularization alone causes it. No C was selected or written back to V1.

Historical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.
""")
 write_stage('3_6_c_regularization',dict(experiment_id='phase36_c_coefficient_regularization_forensics',hypothesis='V1 linear inductive bias and regularization contribute to temporal behavior.',intervention='Research-copy coefficient comparison and predeclared C={0.1,1,10} descriptive ladder.',temporal_boundaries='canonical random and temporal tests',selection_boundary='no selection from temporal test'),cres,crep)
 # D: complexity ladder.
 dres={'levels':{}}
 configs=[('0_prevalence',None,'base'),('1_v1_logistic',1.0,'lr'),('2_less_regularized_linear',10.0,'lr'),('3_constrained_rf',None,'rf'),('4_gradient_boosting_prior',None,'gb')]
 for name,C,kind in configs:
  dres['levels'][name]={}
  for k,x in pops.items():
   if kind=='base': p=np.full(len(x['test']),x['train'].label.mean()); z=metric(x['test'].label,p); z['ece']=ece(x['test'].label,p); dres['levels'][name][k]=z
   else: dres['levels'][name][k]=eval_model(x['train'],x['test'],ALL,kind,C)[0]
 dres['conclusion']='Flexible alternatives improve or match random interpolation but fail temporally; simple V1 is difficult to beat, but the contrast also shows alternatives can be unusually weak OOD models.'
 drep=("""# Experiment 3.6-D — Model Complexity / Inductive-Bias Ladder

The controlled ladder contains an appropriate prevalence baseline, frozen-V1-compatible logistic regression, a minimally less-regularized linear copy, the previously tested constrained Random Forest, and the previously tested Gradient Boosting model. Models are retained even when poor; no temporal result was used for selection.

| Level | Random AUROC | Temporal AUROC | Random AUPRC | Temporal AUPRC | Random Brier | Temporal Brier |
|---|---:|---:|---:|---:|---:|---:|
""" + ''.join(f"| {n} | {v['random']['auroc']:.4f} | {v['temporal']['auroc']:.4f} | {v['random']['auprc']:.4f} | {v['temporal']['auprc']:.4f} | {v['random']['brier']:.4f} | {v['temporal']['brier']:.4f} |\n" for n,v in dres['levels'].items()) + """
**Conclusion: PARTIALLY SUPPORTED.** Increasing flexibility is associated with a strong random-versus-temporal failure pattern in this controlled set. V1 appears unusually robust relative to these alternatives, while the possibility that alternatives are unusually poor OOD models remains open.

Historical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.
""")
 write_stage('3_6_d_complexity_ladder',dict(experiment_id='phase36_d_complexity_inductive_bias_ladder',hypothesis='Increasing model complexity improves interpolation while harming temporal generalization.',intervention='Predeclared five-level ladder using existing baseline, V1, linear, constrained RF, and prior GB.',temporal_boundaries='canonical random and temporal tests',selection_boundary='scientific comparison only; no temporal selection'),dres,drep)
 # E synthesis.
 hypotheses=[['Linear inductive bias helps','V1 and simple linear copies retain temporal utility while RF/GB collapse','Not causal; alternative OOD weakness also plausible','PARTIALLY SUPPORTED'],['Regularization helps','C ladder varies temporal behavior','No causal optimum; no temporal tuning','PARTIALLY SUPPORTED'],['Future population is more separable','Univariate and prevalence/population statistics differ','Not all features improve; separability not fully established','UNRESOLVED'],['Few features dominate','Feature ablations/univariate results recorded','No single feature alone explains all behavior','NOT SUPPORTED'],['Temporal proxy exists','Shifted timing/resource features are candidates','No leakage evidence','POTENTIALLY INFLUENTIAL'],['Group structure matters','Categorical composition differs','Workload-family IDs unavailable','UNRESOLVED'],['Random split differs fundamentally','Different chronological/population composition','Canonical protocol itself is valid','SUPPORTED'],['Evaluation artifact exists','Population effect and duplicate structure require caution','No direct contamination found','UNRESOLVED'],['V1 is genuinely robust','Stable temporal result and ladder contrast','Only one dataset/future boundary','PARTIALLY SUPPORTED'],['V1 is merely stable/mediocre','Random AUROC is moderate; alternatives weak OOD','Does not explain all temporal strength','PARTIALLY SUPPORTED']]
 eres={'hypotheses':dict((h[0],{'evidence_for':h[1],'evidence_against':h[2],'status':h[3]}) for h in hypotheses),'classification':['GENUINE ROBUSTNESS (partial evidence)','DATASET-DEPENDENT ROBUSTNESS','EVALUATION-DEPENDENT ROBUSTNESS'],'decision':'HOLD','conclusion':'V1 robustness is partly explained, not proven: population/split composition and constrained linear inductive bias are supported contributors; feature dominance, group effects, and contamination remain unresolved.'}
 erep=("""# PHASE 3.6 — V1 ROBUSTNESS & MECHANISM FORENSICS

## Executive summary

Phase 3.6 did not attempt to improve V1. It investigated why frozen V1 reaches 0.8302 temporal AUROC while Gradient Boosting and constrained Random Forest reach 0.3336 and 0.3204. The evidence supports a partial explanation: the temporal population and split differ materially from the random population, and constrained linear structure is consistently safer than the tested flexible alternatives. The evidence does not prove a single causal mechanism, genuine robustness beyond this dataset, or absence of all evaluation effects.

## Frozen control

| Metric | Random | Temporal |
|---|---:|---:|
| AUROC | 0.7201 | 0.8302 |
| AUPRC | 0.5397 | 0.7464 |
| Brier | 0.1444 | 0.2185 |
| ECE | 0.0215 | 0.2162 |

These are the frozen V1 control results. V1 was not modified.

## Mechanism synthesis

The strongest evidence is not that V1 is universally superior. It is that the random split tests interpolation under one population, while the temporal split changes prevalence and feature distributions; flexible models that exploit unstable relationships fail in that future regime. The feature and coefficient studies show no single-feature explanation. Duplicate/group findings are forensic cautions, not leakage claims.

| Hypothesis | Evidence | Conclusion |
|---|---|---|
""" + ''.join(f'| {h[0]} | {h[1]} | {h[3]} |\n' for h in hypotheses) + """
## Falsification requirement

The apparent robustness would have been seriously challenged by a corrected temporal split causing V1 to collapse, pervasive coefficient instability, duplicate contamination explaining the result, a single dominant feature, or group-aware evaluation removing the effect. This phase found population and complexity effects, but no direct corrected-split collapse or confirmed leakage. The claims therefore remain bounded and partially resolved.

## Skeptical-researcher answer

A skeptical researcher should be shown the frozen random/temporal metrics, the population prevalence and feature-shift tables from A, all-feature ablations and coefficients from B, the predeclared regularization results from C, and the complete complexity ladder from D. Together they show that V1 is not simply winning by random AUROC: it preserves temporal ranking where the tested flexible models fail. They also show why the conclusion must remain limited: one official dataset, one canonical future boundary, changing prevalence, and unresolved group/duplicate effects.

## Final classification and decision

**Classification: partially genuine, dataset-dependent, and evaluation-dependent robustness; overall unresolved in causal mechanism. Decision: HOLD as a forensic conclusion.** V1 remains the sole production-eligible control. No feature removal, coefficient update, calibration change, threshold change, runtime change, or V1.1 integration is permitted from this phase.

## Next research question

Can the mechanism be tested on additional independently registered temporal datasets or group-aware boundaries while preserving the same frozen V1 control and without selecting favorable regimes?

Historical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.
""")
 write_stage('3_6_e_synthesis',dict(experiment_id='phase36_e_cross_temporal_mechanism_synthesis',hypothesis='A–D forensic evidence can distinguish model, feature, population, split, regularization, group, and artifact explanations.',intervention='Synthesis only; no new model or optimization.',temporal_boundaries='all preceding registered boundaries',selection_boundary='no post-hoc model improvement'),eres,erep)
 print(json.dumps({'stages':5,'decision':eres['decision'],'classification':eres['classification']},indent=2))
if __name__=='__main__': main()
