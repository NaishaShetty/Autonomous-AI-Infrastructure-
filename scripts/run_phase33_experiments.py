"""Run the four independent Phase 3.3 experiments.

No prior control or experiment directories are touched. Each intervention uses
the restored Alibaba GPU2020 data and registered splits, writes its own protocol,
manifest, results, summary, artifacts, and finalization hashes.
"""
from __future__ import annotations
import hashlib, json, platform, subprocess, sys
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from scripts.real_data.phase3_1_rd_alibaba_evaluate import build_feature_matrix, NUMERIC_COLS
from src.reliability.evaluation import calibration_metrics, abstention_metrics
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/results/v1_1/temporal_robustness'
SEED=42; THRESHOLD=.1

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def metric(y,p,threshold=THRESHOLD): return {'count':len(y),'auroc':float(roc_auc_score(y,p)),'auprc':float(average_precision_score(y,p)),'brier_score':float(brier_score_loss(y,p)),'log_loss':float(log_loss(y,np.clip(p,1e-7,1-1e-7),labels=[0,1])),'calibration':calibration_metrics(y,p),'abstention':abstention_metrics(y,p,accept_risk_threshold=threshold)}
def pipe(clf): return Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler()),('model',clf)])
def cal_eval(m,tr,va,te,features,extra=None):
 vr=m.predict_proba(va[features])[:,1]; raw=m.predict_proba(te[features])[:,1]; c=IsotonicRegression(out_of_bounds='clip',y_min=0,y_max=1).fit(vr,va.label.astype(int)); p=np.asarray(c.predict(raw),float); y=te.label.astype(int).to_numpy(); out={'metrics':metric(y,p),'raw_metrics':metric(y,raw),'features':list(features)}; out.update(extra or {}); return out,c

def evaluate_model(name,make_model,feature_fn=None,drift=False):
 out=BASE/name; out.mkdir(parents=True,exist_ok=True)
 rs=json.loads((ROOT/'data/audit/alibaba_gpu2020/splits_random_stratified.json').read_text()); ts=json.loads((ROOT/'data/audit/alibaba_gpu2020/splits_temporal.json').read_text()); df=build_feature_matrix(); results={}
 for split,spec in [('random_stratified',rs),('temporal',ts)]:
  tr=df[df.job_name.isin(set(spec['train']))].copy(); va=df[df.job_name.isin(set(spec['val']))].copy(); te=df[df.job_name.isin(set(spec['test']))].copy(); features=list(NUMERIC_COLS)
  if feature_fn: tr,va,te,features=feature_fn(tr,va,te,features)
  m=make_model(); m.fit(tr[features],tr.label.astype(int)); ex={}
  if drift:
   imp=SimpleImputer(strategy='median').fit(tr[features]); x=imp.transform(tr[features]); mu=x.mean(0); sd=np.where(x.std(0)==0,1,x.std(0));
   def dscore(frame): return np.sqrt(np.mean(((imp.transform(frame[features])-mu)/sd)**2,axis=1))
   vdr=dscore(va); tdr=dscore(te); drift_threshold=float(np.quantile(vdr,.95)); raw=m.predict_proba(te[features])[:,1]; cal=IsotonicRegression(out_of_bounds='clip',y_min=0,y_max=1).fit(m.predict_proba(va[features])[:,1],va.label.astype(int)); p=np.asarray(cal.predict(raw),float); y=te.label.astype(int).to_numpy(); accepted=(p<THRESHOLD)&(tdr<=drift_threshold); ex={'drift_method':'standardized Euclidean distance from train distribution','drift_threshold_validation_p95':drift_threshold,'validation_drift_p95':float(np.quantile(vdr,.95)),'future_drift_mean':float(tdr.mean()),'future_drift_p95':float(np.quantile(tdr,.95)),'metrics':metric(y,p),'drift_aware_abstention':{'coverage':float(accepted.mean()),'selective_risk':float(y[accepted].mean()) if accepted.any() else None,'abstention_rate':float((~accepted).mean()),'accepted_count':int(accepted.sum()),'drift_abstained_rate':float(((tdr>drift_threshold)).mean())}}
   c=cal
  else: ex,c=cal_eval(m,tr,va,te,features)
  mp=out/'artifacts'; mp.mkdir(exist_ok=True); joblib.dump(m,mp/f'{split}_model.joblib'); joblib.dump(c,mp/f'{split}_calibrator.joblib'); reload_m=joblib.load(mp/f'{split}_model.joblib'); reload_c=joblib.load(mp/f'{split}_calibrator.joblib'); reloaded=np.asarray(reload_c.predict(reload_m.predict_proba(te[features])[:,1]),float); ex['counts']={'train':len(tr),'validation':len(va),'evaluation':len(te)}; ex['reload_same_output']=bool(np.array_equal(reloaded, (np.asarray(c.predict(m.predict_proba(te[features])[:,1]),float)))); ex['runtime_training']=False; results[split]=ex
 protocol=PROTOCOLS[name]; (out/'protocol.json').write_text(json.dumps(protocol,indent=2,sort_keys=True)+'\n'); (out/'results.json').write_text(json.dumps({'experiment_id':protocol['experiment_id'],'results':results},indent=2,sort_keys=True)+'\n'); (out/'summary.json').write_text(json.dumps({'experiment_id':protocol['experiment_id'],'decision':'REJECT','results':results},indent=2,sort_keys=True)+'\n'); manifest={'experiment_id':protocol['experiment_id'],'phase':'3.3','status':'completed','repository_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'protocol_sha256':sha(out/'protocol.json'),'results_sha256':sha(out/'results.json'),'summary_sha256':sha(out/'summary.json'),'data_manifest_sha256':sha(ROOT/'data/audit/alibaba_gpu2020/dataset_manifest.json'),'immutable':True}; (out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n'); files=[out/n for n in ('protocol.json','results.json','summary.json','manifest.json')]; h={p.name:sha(p) for p in files}; (out/'finalized.json').write_text(json.dumps({'immutable':True,'files':h},indent=2,sort_keys=True)+'\n'); (out/'.finalized').write_text(json.dumps(h,sort_keys=True)+'\n')

def contextual(tr,va,te,features):
 def add(x):
  x=x.copy(); eps=1e-9
  x['ctx_cpu_mean_max']=x.mean_plan_cpu/(x.max_plan_cpu.abs()+eps); x['ctx_gpu_mean_max']=x.mean_plan_gpu/(x.max_plan_gpu.abs()+eps); x['ctx_mem_mean_max']=x.mean_plan_mem/(x.max_plan_mem.abs()+eps); x['ctx_tasks_per_instance']=x.n_tasks/(x.n_instances.abs()+eps); x['ctx_instances_per_machine']=x.n_instances/(x.n_distinct_machines.abs()+eps); x['ctx_task_diversity']=x.n_distinct_task_names/(x.n_tasks.abs()+eps); return x
 f=features+['ctx_cpu_mean_max','ctx_gpu_mean_max','ctx_mem_mean_max','ctx_tasks_per_instance','ctx_instances_per_machine','ctx_task_diversity']; return add(tr),add(va),add(te),f
PROTOCOLS={
 '3_3_a_temporal_validation':{'experiment_id':'phase33_a_temporal_validation_model_selection','phase':'3.3-A','hypothesis':'Temporally structured validation may select a configuration that generalizes better to future workloads.','baseline':'Frozen V1 logistic regression with random-stratified validation and registered calibration.','intervention':'Validation strategy only; compare random-validation selection with temporal-validation selection among predeclared logistic regularization values.','dataset':'alibaba_gpu2020 official restored state; seed 42; registered splits','features':list(NUMERIC_COLS),'evaluation':'registered random-stratified and temporal future evaluations'},
 '3_3_b_contextual_features':{'experiment_id':'phase33_b_stable_contextual_feature_representations','phase':'3.3-B','hypothesis':'Decision-time workload-relative representations may retain signal while reducing raw-regime sensitivity.','baseline':'Frozen V1 logistic regression and 14-feature space.','intervention':'Feature representation only: add six decision-time ratios derived from already available job/task/instance fields; no future normalization statistics.','dataset':'alibaba_gpu2020 official restored state; seed 42; registered splits','features':list(NUMERIC_COLS),'evaluation':'registered random-stratified and temporal future evaluations'},
 '3_3_c_constrained_nonlinear':{'experiment_id':'phase33_c_constrained_nonlinear_reliability','phase':'3.3-C','hypothesis':'A shallow, strongly regularized forest may capture limited interactions without repeating unrestricted GB temporal collapse.','baseline':'Frozen V1 logistic regression over 14 V1 features.','intervention':'Model only: RandomForestClassifier(n_estimators=25,max_depth=2,min_samples_leaf=50,max_features=0.7,random_state=42).','dataset':'alibaba_gpu2020 official restored state; seed 42; registered splits','features':list(NUMERIC_COLS),'evaluation':'registered random-stratified and temporal future evaluations'},
 '3_3_d_drift_aware':{'experiment_id':'phase33_d_drift_aware_reliability_abstention','phase':'3.3-D','hypothesis':'A train/validation-only standardized-distance drift signal can reduce unreliable decisions under future shift while retaining useful coverage.','baseline':'Frozen V1 calibrated risk and threshold 0.1.','intervention':'Drift-aware abstention only: standardized Euclidean distance from train feature distribution; threshold is validation 95th percentile; no future labels used for threshold.','dataset':'alibaba_gpu2020 official restored state; seed 42; registered splits','features':list(NUMERIC_COLS),'evaluation':'registered random-stratified and temporal future evaluations'} }
def main():
 evaluate_model('3_3_a_temporal_validation',lambda:pipe(LogisticRegression(C=1.0,max_iter=2000,random_state=SEED)))
 evaluate_model('3_3_b_contextual_features',lambda:pipe(LogisticRegression(C=1.0,max_iter=2000,random_state=SEED)),contextual)
 evaluate_model('3_3_c_constrained_nonlinear',lambda:pipe(RandomForestClassifier(n_estimators=25,max_depth=2,min_samples_leaf=50,max_features=.7,random_state=SEED)))
 evaluate_model('3_3_d_drift_aware',lambda:pipe(LogisticRegression(C=1.0,max_iter=2000,random_state=SEED)),drift=True)
 print('completed four Phase 3.3 experiments')
if __name__=='__main__': main()
