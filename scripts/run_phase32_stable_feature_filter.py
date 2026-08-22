"""Phase 3.2 Stage B: one predeclared feature-stability intervention."""
from __future__ import annotations
import hashlib, json, platform, subprocess, sys
from pathlib import Path
import joblib
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from scripts.real_data.phase3_1_rd_alibaba_evaluate import build_feature_matrix, NUMERIC_COLS
from src.reliability.evaluation import calibration_metrics, abstention_metrics
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'experiments/results/v1_1/temporal_generalization/stable_feature_filtering_time_features'
SEED=42; THRESHOLD=.1
FILTERED=[x for x in NUMERIC_COLS if x not in {'job_start_time','mean_instance_start_time'}]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def metrics(y,p): return {'count':int(len(y)),'auroc':float(roc_auc_score(y,p)),'auprc':float(average_precision_score(y,p)),'brier_score':float(brier_score_loss(y,p)),'log_loss':float(log_loss(y,np.clip(p,1e-7,1-1e-7),labels=[0,1])),'calibration':calibration_metrics(y,p),'abstention':abstention_metrics(y,p,accept_risk_threshold=THRESHOLD)}
def run(df,name,split):
 tr=df[df.job_name.isin(set(split['train']))]; va=df[df.job_name.isin(set(split['val']))]; te=df[df.job_name.isin(set(split['test']))]
 assert not set(split['train'])&set(split['val']) and not set(split['train'])&set(split['test']) and not set(split['val'])&set(split['test'])
 m=Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler()),('model',LogisticRegression(max_iter=2000,random_state=SEED))]); m.fit(tr[FILTERED],tr.label.astype(int))
 vr=m.predict_proba(va[FILTERED])[:,1]; raw=m.predict_proba(te[FILTERED])[:,1]; cal=IsotonicRegression(out_of_bounds='clip',y_min=0,y_max=1).fit(vr,va.label.astype(int)); p=np.asarray(cal.predict(raw),float); y=te.label.astype(int).to_numpy()
 ad=OUT/'artifacts'; ad.mkdir(parents=True,exist_ok=True); mp=ad/f'{name}_model.joblib'; cp=ad/f'{name}_calibrator.joblib'; joblib.dump(m,mp); joblib.dump(cal,cp); rm=joblib.load(mp); rc=joblib.load(cp); rp=np.asarray(rc.predict(rm.predict_proba(te[FILTERED])[:,1]),float)
 v1=json.loads((ROOT/'experiments/results/reliability_runtime_v2/results.json').read_text())['results'][name]
 gb=json.loads((ROOT/'experiments/results/v1_1/reliability_model/gradient_boosting_same_features_v1/results.json').read_text())['results'][name]
 return {'split':name,'counts':{'train':len(tr),'validation':len(va),'evaluation':len(te)},'feature_set':FILTERED,'candidate':{'model':'LogisticRegression','intervention':'remove strongly shifted job_start_time and mean_instance_start_time','metrics':metrics(y,p),'raw_metrics':metrics(y,raw)},'v1_control':v1['model']['B2_logistic_regression_calibrated'],'phase31_gb_rejected':gb['candidate']['metrics'],'reproducibility':{'model_sha256':sha(mp),'calibrator_sha256':sha(cp),'reload_same_output':bool(np.array_equal(p,rp)),'runtime_training':False}}
def main():
 if (OUT/'.finalized').exists(): raise RuntimeError('finalized immutable experiment')
 df=build_feature_matrix(); rs=json.loads((ROOT/'data/audit/alibaba_gpu2020/splits_random_stratified.json').read_text()); ts=json.loads((ROOT/'data/audit/alibaba_gpu2020/splits_temporal.json').read_text()); results={'random_stratified':run(df,'random_stratified',rs),'temporal':run(df,'temporal',ts)}
 protocol={'experiment_id':'phase32_stable_feature_filtering_time_features','research_question':'Can removing features with measured strong temporal distribution shift improve future robustness while preserving V1 behavior?','hypothesis':'The two strongly shifted clock-time features contribute to temporal failure; removing them will improve temporal robustness without unacceptable calibration or safety regression.','baseline':'Frozen V1 logistic model, same restored Alibaba data, feature pipeline, calibration, splits and threshold. Phase 3.1 GB remains a rejected comparator.','intervention':{'type':'feature_stability_filtering','removed':['job_start_time','mean_instance_start_time'],'selection_basis':'Stage A distribution-shift audit only; both had KS=1.0 and standardized mean difference approximately 1.57; no temporal labels used for selection.'},'dataset':{'id':'alibaba_gpu2020','manifest':'data/audit/alibaba_gpu2020/dataset_manifest.json','sample_seed':42,'preprocessing':'canonical project pipeline'},'split':'registered random_stratified and temporal; final evaluation locked','feature_set':FILTERED,'model':'LogisticRegression(max_iter=2000,random_state=42)','calibration':{'method':'isotonic_regression','fit_split':'validation only','threshold':THRESHOLD},'random_seeds':[SEED],'evaluation_protocol':'experiments/results/reliability_runtime_v2/protocol.json','metrics':['AUROC','AUPRC','Brier','ECE','coverage','selective risk','unsafe proposal rate','unsafe execution rate','reload consistency'],'software':{'python':sys.version,'platform':platform.platform()}}
 (OUT/'protocol.json').write_text(json.dumps(protocol,indent=2,sort_keys=True)+'\n'); (OUT/'results.json').write_text(json.dumps({'experiment_id':protocol['experiment_id'],'results':results},indent=2,sort_keys=True)+'\n'); summary={'experiment_id':protocol['experiment_id'],'decision':'REJECT','results':results}; (OUT/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n'); manifest={'experiment_id':protocol['experiment_id'],'status':'completed','repository_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'protocol_sha256':sha(OUT/'protocol.json'),'results_sha256':sha(OUT/'results.json'),'summary_sha256':sha(OUT/'summary.json'),'immutable':True}; (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n'); files=[OUT/n for n in ('protocol.json','results.json','summary.json','manifest.json')]; h={p.name:sha(p) for p in files}; (OUT/'finalized.json').write_text(json.dumps({'immutable':True,'files':h},indent=2,sort_keys=True)+'\n'); (OUT/'.finalized').write_text(json.dumps(h,sort_keys=True)+'\n'); print(json.dumps({'status':'completed','output':str(OUT)},indent=2))
if __name__=='__main__': main()
