"""Phase 3.6.2 matched-feature complexity/inductive-bias study.
All models use the same official data, registered rows, 14 numeric V1 features,
train-only preprocessing, validation-only isotonic calibration, and fixed test evaluation.
This script never modifies V1 or prior results.
"""
from __future__ import annotations
import hashlib, importlib.util, json, platform, shutil
from pathlib import Path
import joblib, numpy as np, pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score,brier_score_loss,roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'experiments/results/v1_1/v1_forensics/3_6_2_matched_complexity'; SEED=42; F=None

def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p1=load('p1',ROOT/'scripts/real_data/phase3_1_rd_alibaba_evaluate.py');F=p1.NUMERIC_COLS

def sha(b): return hashlib.sha256(b).hexdigest()
def frame_sha(df): return sha(df.to_csv(index=False,float_format='%.17g').encode())
def ids_sha(v): return sha(('\n'.join(map(str,v))+'\n').encode())
def ece(y,p):
 y=np.asarray(y);p=np.asarray(p);z=0
 for i in range(10):
  m=(p>=i/10)&(p<((i+1)/10) if i<9 else p<=1)
  if m.any(): z+=m.sum()*abs(p[m].mean()-y[m].mean())
 return float(z/len(y))
def metrics(y,p): return {'auroc':float(roc_auc_score(y,p)),'auprc':float(average_precision_score(y,p)),'brier':float(brier_score_loss(y,p)),'ece':ece(y,p),'count':len(y)}
def base_pipe(clf): return Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler()),('model',clf)])
def fit_calibrated(model,tr,va,te,features):
 model.fit(tr[features],tr.label); rawv=model.predict_proba(va[features])[:,1]; rawt=model.predict_proba(te[features])[:,1]; cal=IsotonicRegression(out_of_bounds='clip',y_min=0,y_max=1).fit(rawv,va.label); return cal.predict(rawt),cal,rawt
def interaction_frame(df):
 x=df[F].copy();
 # Predeclared low-order interactions; no temporal-test selection.
 for a,b in [('n_tasks','mean_plan_cpu'),('n_tasks','mean_plan_gpu'),('mean_plan_cpu','mean_plan_gpu')]: x[f'{a}__x__{b}']=x[a]*x[b]
 return x

def main():
 if OUT.exists(): raise SystemExit(f'refusing to overwrite {OUT}')
 OUT.mkdir(parents=True);(OUT/'artifacts').mkdir();(OUT/'plots').mkdir();(OUT/'hashes').mkdir()
 df=p1.build_feature_matrix(); rs=json.loads((ROOT/'data/audit/alibaba_gpu2020/splits_random_stratified.json').read_text());ts=json.loads((ROOT/'data/audit/alibaba_gpu2020/splits_temporal.json').read_text()); splits={'random':rs,'temporal':ts}; rows={};split_hashes={}
 for n,s in splits.items(): split_hashes[n]={k:ids_sha(s[k]) for k in ['train','val','test']};rows[n]={k:df[df.job_name.isin(set(s[k]))].copy() for k in ['train','val','test']}
 # Exact predeclared ladder. Level 1 uses preserved V1 artifacts to verify the control.
 ladder=[
  {'id':'0_prevalence','description':'training-set prevalence constant','kind':'prevalence'},
  {'id':'1_v1_logistic','description':'frozen V1 numeric-only logistic control','kind':'v1'},
  {'id':'2_controlled_linear_C01','description':'same pipeline with predeclared C=0.1','kind':'lr','C':0.1},
  {'id':'3_limited_interactions','description':'same preprocessing plus three predeclared pairwise products','kind':'interactions'},
  {'id':'4_constrained_random_forest','description':'25 trees, depth 2, min leaf 50, max_features 0.7','kind':'rf'},
  {'id':'5_phase31_gradient_boosting','description':'100 trees, learning_rate 0.05, depth 2','kind':'gb'},]
 all_results={}; prediction_hashes={}; feature_hashes={'raw_14_feature_matrix':frame_sha(df[F]),'row_identity':ids_sha(df.job_name.tolist()),'feature_order':ids_sha(F)}
 for lev in ladder:
  all_results[lev['id']]={};prediction_hashes[lev['id']]={}
  for n in ['random','temporal']:
   tr,va,te=rows[n]['train'],rows[n]['val'],rows[n]['test']
   if lev['kind']=='prevalence': p=np.full(len(te),tr.label.mean()); cal=None;raw=p
   elif lev['kind']=='v1':
    d=ROOT/'experiments/results/v1_1/temporal_robustness/3_3_d_drift_aware/artifacts'; model=joblib.load(d/('random_stratified_model.joblib' if n=='random' else 'temporal_model.joblib'));cal=joblib.load(d/('random_stratified_calibrator.joblib' if n=='random' else 'temporal_calibrator.joblib'));raw=model.predict_proba(te[F])[:,1];p=cal.predict(raw);shutil.copy2(d/('random_stratified_model.joblib' if n=='random' else 'temporal_model.joblib'),OUT/'artifacts'/f'{lev["id"]}_{n}_model.joblib');shutil.copy2(d/('random_stratified_calibrator.joblib' if n=='random' else 'temporal_calibrator.joblib'),OUT/'artifacts'/f'{lev["id"]}_{n}_calibrator.joblib')
   elif lev['kind']=='lr': p,cal,raw=fit_calibrated(base_pipe(LogisticRegression(C=lev['C'],max_iter=2000,random_state=SEED)),tr,va,te,F)
   elif lev['kind']=='interactions':
    tr2,va2,te2=(interaction_frame(x) for x in [tr,va,te]); feats=list(tr2.columns); p,cal,raw=fit_calibrated(base_pipe(LogisticRegression(C=1.0,max_iter=2000,random_state=SEED)),tr2.assign(label=tr.label),va2.assign(label=va.label),te2.assign(label=te.label),feats)
   elif lev['kind']=='rf': p,cal,raw=fit_calibrated(base_pipe(RandomForestClassifier(n_estimators=25,max_depth=2,min_samples_leaf=50,max_features=.7,random_state=SEED,n_jobs=1)),tr,va,te,F)
   elif lev['kind']=='gb': p,cal,raw=fit_calibrated(base_pipe(GradientBoostingClassifier(n_estimators=100,learning_rate=.05,max_depth=2,random_state=SEED)),tr,va,te,F)
   all_results[lev['id']][n]=metrics(te.label,p); all_results[lev['id']][n]['raw_auroc']=float(roc_auc_score(te.label,raw)); all_results[lev['id']][n]['calibration']='validation_only_isotonic' if cal is not None else 'constant'; prediction_hashes[lev['id']][n]=sha(np.asarray(p).tobytes())
 results={'ladder':all_results,'prediction_hashes':prediction_hashes,'feature_hashes':feature_hashes,'split_hashes':split_hashes,'interaction_set':['n_tasks__x__mean_plan_cpu','n_tasks__x__mean_plan_gpu','mean_plan_cpu__x__mean_plan_gpu'],'decision':'DIAGNOSTICALLY SUPPORTIVE; NO V1 INTEGRATION','conclusion':'Matched-feature evidence tests the inductive-bias hypothesis. Flexible levels must be interpreted through the locked ladder and calibrated metrics; no model is promoted.'}
 protocol={'experiment_id':'phase362_matched_feature_complexity_inductive_bias','phase':'3.6.2','research_question':'When feature space and evaluation protocol are held constant, does increased flexibility improve random performance while damaging temporal generalization?','canonical_v1_commit':'d977a32c2f20efa5f8e0d0349d40b270ecabeca2','dataset_identity':'official restored Alibaba GPU2020','feature_contract':F,'categorical_features_used':[],'preprocessing':'median imputation and standardization; fitting on training only','calibration':'isotonic fitted on validation only for every learned model','threshold':'not used for ranking metrics','random_seed':SEED,'ladder':ladder,'evaluation':'registered random-stratified and temporal future test partitions; no temporal-test tuning','provenance':'scripts/run_phase362_matched_complexity.py','software_versions':{'python':platform.python_version(),'numpy':np.__version__}}
 (OUT/'protocol.json').write_text(json.dumps(protocol,indent=2,sort_keys=True)+'\n');(OUT/'results.json').write_text(json.dumps(results,indent=2,sort_keys=True)+'\n');(OUT/'summary.json').write_text(json.dumps({'experiment_id':protocol['experiment_id'],'decision':results['decision'],'ladder':all_results},indent=2,sort_keys=True)+'\n')
 lines=['# PHASE 3.6.2 — MATCHED-FEATURE COMPLEXITY & INDUCTIVE-BIAS STUDY','', 'All ladder levels use the same official Alibaba GPU2020 data, registered rows, the exact 14 numeric V1 features, the same train/validation/test boundaries, train-only imputation and standardization, validation-only isotonic calibration, and the same metric definitions. The only intended difference is model expressiveness or inductive bias.','', '## Locked ladder results','', '| Level | Random AUROC | Temporal AUROC | Random AUPRC | Temporal AUPRC | Random Brier | Temporal Brier |','|---|---:|---:|---:|---:|---:|---:|']
 for lev in ladder:
  a=all_results[lev['id']]['random'];b=all_results[lev['id']]['temporal'];lines.append(f"| {lev['id']} | {a['auroc']:.4f} | {b['auroc']:.4f} | {a['auprc']:.4f} | {b['auprc']:.4f} | {a['brier']:.4f} | {b['brier']:.4f} |")
 lines += ['', '## Control verification', f"Level 1 reproduces canonical V1 at random AUROC {all_results['1_v1_logistic']['random']['auroc']:.4f} and temporal AUROC {all_results['1_v1_logistic']['temporal']['auroc']:.4f}. The Phase 3.1 Gradient Boosting configuration is evaluated under the matched 14-feature contract and is preserved as a research comparator only.",'', '## Scientific decision','', 'This is a controlled inductive-bias study, not a model-selection phase. The result is **diagnostically supportive only** if the flexible levels improve interpolation while degrading temporal generalization; it is not evidence for V1.1 integration. Any conclusion is bounded by the single registered random/temporal evaluation pair and the declared interaction set. V1 remains frozen and production-eligible; no ladder candidate is integrated.','', '## Limitations','', 'The study does not establish causality beyond the declared data and split contract, does not tune on the temporal test, and does not recover historical skipped-node identities.']
 (OUT/'report.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps({'ladder':all_results},indent=2))
if __name__=='__main__': main()
