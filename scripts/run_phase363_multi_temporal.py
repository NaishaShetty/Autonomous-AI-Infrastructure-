"""Phase 3.6.3: frozen matched-feature ladder across the authoritative Phase 3.5 folds."""
from __future__ import annotations
import hashlib,importlib.util,json,platform,shutil
from pathlib import Path
import joblib,numpy as np,pandas as pd
from sklearn.ensemble import GradientBoostingClassifier,RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score,brier_score_loss,roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'experiments/results/v1_1/v1_forensics/3_6_3_multi_temporal_validation';SEED=42

def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p1=load('p1',ROOT/'scripts/real_data/phase3_1_rd_alibaba_evaluate.py');F=p1.NUMERIC_COLS
FOLDS=json.loads((ROOT/'experiments/results/v1_1/distribution_robust_uncertainty/3_5_a_temporal_folds/manifest.json').read_text())['fold_definitions']
MODELS=[('v1_logistic','V1 Logistic','low','v1'),('linear_c01','Linear C=0.1','low','c01'),('limited_interactions','Limited Interactions','moderate','interactions'),('constrained_rf','Constrained Random Forest','moderate','rf'),('gradient_boosting','Gradient Boosting','high','gb')]
def ids(v):return hashlib.sha256(('\n'.join(map(str,v))+'\n').encode()).hexdigest()
def frame(x):return hashlib.sha256(x.to_csv(index=False,float_format='%.17g').encode()).hexdigest()
def ece(y,p):
 y=np.asarray(y);p=np.asarray(p);z=0
 for i in range(10):
  m=(p>=i/10)&(p<((i+1)/10 if i<9 else 1.0000001))
  if m.any():z+=m.sum()*abs(p[m].mean()-y[m].mean())
 return float(z/len(y))
def mets(y,p):return {'auroc':float(roc_auc_score(y,p)),'auprc':float(average_precision_score(y,p)),'brier':float(brier_score_loss(y,p)),'ece':ece(y,p),'count':len(y)}
def pipe(kind):
 if kind=='v1': c=LogisticRegression(C=1.0,max_iter=2000,random_state=SEED)
 elif kind=='c01':c=LogisticRegression(C=.1,max_iter=2000,random_state=SEED)
 elif kind=='rf':c=RandomForestClassifier(n_estimators=25,max_depth=2,min_samples_leaf=50,max_features=.7,random_state=SEED,n_jobs=1)
 else:c=GradientBoostingClassifier(n_estimators=100,learning_rate=.05,max_depth=2,random_state=SEED)
 return Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler()),('model',c)])
def inter(d):
 x=d[F].copy()
 for a,b in [('n_tasks','mean_plan_cpu'),('n_tasks','mean_plan_gpu'),('mean_plan_cpu','mean_plan_gpu')]:x[f'{a}__x__{b}']=x[a]*x[b]
 return x

def main():
 if OUT.exists():raise SystemExit(f'refusing to overwrite {OUT}')
 OUT.mkdir(parents=True);[(OUT/x).mkdir() for x in ['fold_definitions','models','predictions','feature_contract','split_contract','preprocessing','plots','hashes']]
 df=p1.build_feature_matrix().sort_values(['job_start_time','job_name']).reset_index(drop=True); feature_hashes={'base_feature_order':ids(F),'base_full_matrix':frame(df[F]),'row_identity':ids(df.job_name.tolist())};results={};prediction_hashes={};fold_hashes={}
 for fold in FOLDS:
  fid=fold['fold_id'];a,b=fold['train_idx'];c,d=fold['validation_idx'];e,f=fold['test_idx'];tr=df.iloc[a:b].copy();va=df.iloc[c:d].copy();te=df.iloc[e:f].copy();fold_hashes[fid]={'train_rows':ids(tr.job_name.tolist()),'validation_rows':ids(va.job_name.tolist()),'future_rows':ids(te.job_name.tolist())}
  (OUT/'fold_definitions'/f'{fid}.json').write_text(json.dumps(fold,indent=2,sort_keys=True)+'\n');(OUT/'feature_contract'/f'{fid}.json').write_text(json.dumps({'feature_names':F,'train_matrix_hash':frame(tr[F]),'validation_matrix_hash':frame(va[F]),'future_matrix_hash':frame(te[F])},indent=2,sort_keys=True)+'\n')
  results[fid]={};prediction_hashes[fid]={}
  for mid,label,expr,kind in MODELS:
   if kind=='interactions':
    xtr,xva,xte=inter(tr),inter(va),inter(te);feats=list(xtr.columns);m=pipe('v1');m.fit(xtr,tr.label);rv=m.predict_proba(xva[feats])[:,1];rt=m.predict_proba(xte[feats])[:,1]
   else:
    feats=F;m=pipe(kind);m.fit(tr[feats],tr.label);rv=m.predict_proba(va[feats])[:,1];rt=m.predict_proba(te[feats])[:,1]
   cal=IsotonicRegression(out_of_bounds='clip',y_min=0,y_max=1).fit(rv,va.label);p=cal.predict(rt);z=mets(te.label,p);z.update({'model':label,'expressiveness':expr,'future_start':fold['temporal_start'],'future_end':fold['temporal_end'],'raw_auroc':float(roc_auc_score(te.label,rt)),'raw_auprc':float(average_precision_score(te.label,rt))});results[fid][mid]=z;prediction_hashes[fid][mid]=hashlib.sha256(np.asarray(p).tobytes()).hexdigest();md=OUT/'models'/mid;md.mkdir(exist_ok=True);joblib.dump(m,md/f'{fid}_model.joblib');joblib.dump(cal,md/f'{fid}_calibrator.joblib');np.save(OUT/'predictions'/f'{fid}_{mid}.npy',p)
 # summaries and interaction deltas
 summary={}
 for mid,_,_,_ in MODELS:
  vals=[results[f][mid] for f in results]; au=[x['auroc'] for x in vals];ap=[x['auprc'] for x in vals];summary[mid]={'mean_auroc':float(np.mean(au)),'median_auroc':float(np.median(au)),'min_auroc':float(np.min(au)),'max_auroc':float(np.max(au)),'std_auroc':float(np.std(au)),'range_auroc':float(np.ptp(au)),'mean_auprc':float(np.mean(ap)),'median_auprc':float(np.median(ap)),'min_auprc':float(np.min(ap)),'max_auprc':float(np.max(ap))}
 deltas=[]
 for f in results:deltas.append({'fold':f,'auroc_delta':results[f]['limited_interactions']['auroc']-results[f]['v1_logistic']['auroc'],'auprc_delta':results[f]['limited_interactions']['auprc']-results[f]['v1_logistic']['auprc']})
 summary['interaction_vs_v1']={'fold_deltas':deltas,'wins_auroc':sum(x['auroc_delta']>0 for x in deltas),'losses_auroc':sum(x['auroc_delta']<0 for x in deltas),'mean_auroc_delta':float(np.mean([x['auroc_delta'] for x in deltas])),'median_auroc_delta':float(np.median([x['auroc_delta'] for x in deltas])),'worst_auroc_delta':float(min(x['auroc_delta'] for x in deltas)),'best_auroc_delta':float(max(x['auroc_delta'] for x in deltas))}
 summary['decision']='PARTIAL VALIDATION / REGIME-SENSITIVE';summary['conclusion']='The interaction model must be evaluated across all three folds; no future fold is selected or discarded.'
 protocol={'experiment_id':'phase363_multi_temporal_inductive_bias_validation','phase':'3.6.3','hypothesis':'The Phase 3.6.2 limited-interaction result may or may not persist across multiple chronological future regimes.','canonical_v1_commit':'d977a32c2f20efa5f8e0d0349d40b270ecabeca2','fold_source':'Phase 3.5 authoritative fold manifest','fold_definitions':FOLDS,'feature_contract':F,'interaction_set':['n_tasks__x__mean_plan_cpu','n_tasks__x__mean_plan_gpu','mean_plan_cpu__x__mean_plan_gpu'],'models':MODELS,'preprocessing':'training-fitted median imputation and standardization per fold','calibration':'validation-only isotonic calibration per fold/model','metrics':'AUROC/AUPRC primary; Brier/ECE secondary','random_seed':SEED,'data_identity':'official restored Alibaba GPU2020','software_versions':{'python':platform.python_version(),'numpy':np.__version__},'provenance':'scripts/run_phase363_multi_temporal.py'}
 allout={'fold_results':results,'model_summary':summary,'fold_hashes':fold_hashes,'feature_hashes':feature_hashes,'prediction_hashes':prediction_hashes,'decision':'PARTIAL VALIDATION / REGIME-SENSITIVE'}
 (OUT/'protocol.json').write_text(json.dumps(protocol,indent=2,sort_keys=True)+'\n');(OUT/'results.json').write_text(json.dumps(allout,indent=2,sort_keys=True)+'\n');(OUT/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
