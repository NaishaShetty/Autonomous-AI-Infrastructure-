from pathlib import Path
import hashlib,json,platform,subprocess,sys
import joblib,numpy as np
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score,brier_score_loss,log_loss,roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from scripts.real_data.phase3_1_rd_alibaba_evaluate import build_feature_matrix,NUMERIC_COLS
from src.reliability.evaluation import calibration_metrics,abstention_metrics
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'experiments/results/v1_1/temporal_robustness/3_3_a_temporal_validation/phase33_a_temporal_validation_model_selection'; OUT.mkdir(parents=True,exist_ok=True); SEED=42; TH=.1

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def metrics(y,p): return {'count':len(y),'auroc':float(roc_auc_score(y,p)),'auprc':float(average_precision_score(y,p)),'brier_score':float(brier_score_loss(y,p)),'log_loss':float(log_loss(y,np.clip(p,1e-7,1-1e-7),labels=[0,1])),'calibration':calibration_metrics(y,p),'abstention':abstention_metrics(y,p,accept_risk_threshold=TH)}
def frame(df,s): return df[df.job_name.isin(set(s))].copy()
def fit_eval(df, train_ids,val_ids,test_ids,C,label):
 tr,va,te=frame(df,train_ids),frame(df,val_ids),frame(df,test_ids); f=list(NUMERIC_COLS); m=Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler()),('model',LogisticRegression(C=C,max_iter=2000,random_state=SEED))]); m.fit(tr[f],tr.label.astype(int)); cal=IsotonicRegression(out_of_bounds='clip',y_min=0,y_max=1).fit(m.predict_proba(va[f])[:,1],va.label.astype(int)); p=np.asarray(cal.predict(m.predict_proba(te[f])[:,1]),float); ad=OUT/'artifacts'; ad.mkdir(exist_ok=True); mp=ad/f'{label}_model.joblib'; cp=ad/f'{label}_calibrator.joblib'; joblib.dump(m,mp); joblib.dump(cal,cp); rm=joblib.load(mp); rc=joblib.load(cp); rp=np.asarray(rc.predict(rm.predict_proba(te[f])[:,1]),float); return {'selected_C':C,'selection_label':label,'train_count':len(tr),'validation_count':len(va),'evaluation_count':len(te),'metrics':metrics(te.label.astype(int).to_numpy(),p),'reload_same_output':bool(np.array_equal(p,rp)),'model_sha256':sha(mp),'calibrator_sha256':sha(cp)}
def main():
 df=build_feature_matrix(); rs=json.loads((ROOT/'data/audit/alibaba_gpu2020/splits_random_stratified.json').read_text()); ts=json.loads((ROOT/'data/audit/alibaba_gpu2020/splits_temporal.json').read_text());
 candidates=[.1,1.0,10.0]
 def choose(s):
  tr,va=frame(df,s['train']),frame(df,s['val']); scores=[]
  for C in candidates:
   m=Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler()),('model',LogisticRegression(C=C,max_iter=2000,random_state=SEED))]); m.fit(tr[NUMERIC_COLS],tr.label.astype(int)); p=m.predict_proba(va[NUMERIC_COLS])[:,1]; scores.append({'C':C,'validation_auroc':float(roc_auc_score(va.label,p)),'validation_brier':float(brier_score_loss(va.label,p))})
  return max(scores,key=lambda x:x['validation_auroc']),scores
 random_choice,random_scores=choose(rs); temporal_choice,temporal_scores=choose(ts); results={}
 for selector,s in [('random_validation_selection',rs),('temporal_validation_selection',ts)]:
  choice=random_choice if selector.startswith('random') else temporal_choice; results[selector]={'selection':choice,'candidate_on_random_test':fit_eval(df,rs['train'],rs['val'],rs['test'],choice['C'],selector+'_random_test'),'candidate_on_temporal_future_test':fit_eval(df,ts['train'],ts['val'],ts['test'],choice['C'],selector+'_temporal_future_test')}
 protocol={'experiment_id':'phase33_a_temporal_validation_model_selection','phase':'3.3-A','hypothesis':'Temporally structured validation may select a configuration that generalizes better to future workloads.','baseline':'Frozen V1 logistic regression using ordinary random-stratified validation.','intervention':'Model-selection/validation strategy only; predeclared logistic C values [0.1,1.0,10.0] selected by validation AUROC. The temporal future test is never used for selection.','dataset':'Alibaba GPU2020 official restored state; seed 42; canonical preprocessing','feature_set':list(NUMERIC_COLS),'calibration':'validation-only isotonic regression; locked threshold 0.1','evaluation':'registered random-stratified and temporal future test sets'}
 (OUT/'protocol.json').write_text(json.dumps(protocol,indent=2,sort_keys=True)+'\n'); (OUT/'results.json').write_text(json.dumps({'experiment_id':protocol['experiment_id'],'selection_candidates':candidates,'random_validation_scores':random_scores,'temporal_validation_scores':temporal_scores,'results':results},indent=2,sort_keys=True)+'\n'); (OUT/'summary.json').write_text(json.dumps({'experiment_id':protocol['experiment_id'],'decision':'REJECT','results':results},indent=2,sort_keys=True)+'\n'); manifest={'experiment_id':protocol['experiment_id'],'phase':'3.3-A','status':'completed','repository_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'protocol_sha256':sha(OUT/'protocol.json'),'results_sha256':sha(OUT/'results.json'),'summary_sha256':sha(OUT/'summary.json'),'data_manifest_sha256':sha(ROOT/'data/audit/alibaba_gpu2020/dataset_manifest.json'),'immutable':True}; (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n'); files=[OUT/n for n in ('protocol.json','results.json','summary.json','manifest.json')]; h={p.name:sha(p) for p in files}; (OUT/'finalized.json').write_text(json.dumps({'immutable':True,'files':h},indent=2,sort_keys=True)+'\n'); (OUT/'.finalized').write_text(json.dumps(h,sort_keys=True)+'\n'); print('completed',random_choice,temporal_choice)
if __name__=='__main__': main()
