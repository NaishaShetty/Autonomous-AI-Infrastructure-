"""Stage A Phase 3.2 audit using only the established Alibaba data and splits."""
from __future__ import annotations
import json, hashlib, sys
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp, wasserstein_distance, spearmanr
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from scripts.real_data.phase3_1_rd_alibaba_evaluate import build_feature_matrix, NUMERIC_COLS

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'experiments/results/v1_1/temporal_generalization'
RANDOM=ROOT/'data/audit/alibaba_gpu2020/splits_random_stratified.json'
TEMPORAL=ROOT/'data/audit/alibaba_gpu2020/splits_temporal.json'
PHASE31=ROOT/'experiments/results/v1_1/reliability_model/gradient_boosting_same_features_v1'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def values(frame, col): return pd.to_numeric(frame[col], errors='coerce').dropna().to_numpy(float)
def stats(frame):
    return {'n':int(len(frame)), 'failure_rate':float(frame.label.mean()), 'time_min':float(frame.job_start_time.min()), 'time_max':float(frame.job_start_time.max()), 'features':{c:{'missing_rate':float(frame[c].isna().mean()),'mean':float(frame[c].mean()),'median':float(frame[c].median()),'std':float(frame[c].std()),'q01':float(frame[c].quantile(.01)),'q25':float(frame[c].quantile(.25)),'q75':float(frame[c].quantile(.75)),'q99':float(frame[c].quantile(.99))} for c in NUMERIC_COLS}}
def auc(y,x):
    try: return float(roc_auc_score(y,x)) if len(np.unique(y))==2 else None
    except ValueError: return None
def drift(a,b):
    out={}
    for c in NUMERIC_COLS:
        x,y=values(a,c),values(b,c)
        pooled=np.r_[x,y]; sd=float(np.std(pooled,ddof=1)) if len(pooled)>1 else 0.0
        smd=float((np.mean(y)-np.mean(x))/sd) if sd else 0.0
        q={str(q):float(np.quantile(y,q)-np.quantile(x,q)) for q in (.01,.25,.5,.75,.99)}
        ks=ks_2samp(x,y)
        wd=wasserstein_distance(x,y)
        # PSI with fixed train quantile bins; zero-count smoothing avoids infinities.
        edges=np.unique(np.quantile(x,np.linspace(0,1,11)))
        if len(edges)<3: psi=0.0
        else:
            px,_=np.histogram(x,bins=edges); py,_=np.histogram(y,bins=edges)
            px=(px+0.5)/ (px.sum()+0.5*len(px)); py=(py+0.5)/(py.sum()+0.5*len(py)); psi=float(np.sum((py-px)*np.log(py/px)))
        stability='stable' if abs(smd)<0.1 and ks.statistic<0.1 and psi<0.1 else ('moderately shifted' if abs(smd)<0.5 and ks.statistic<0.25 and psi<0.25 else 'strongly shifted')
        out[c]={'train_mean':float(np.mean(x)),'future_mean':float(np.mean(y)),'mean_shift':float(np.mean(y)-np.mean(x)),'median_shift':float(np.median(y)-np.median(x)),'std_shift':float(np.std(y,ddof=1)-np.std(x,ddof=1)),'quantile_shifts':q,'standardized_mean_difference':smd,'wasserstein_distance':float(wd),'ks_statistic':float(ks.statistic),'ks_pvalue':float(ks.pvalue),'psi':psi,'stability':stability}
    return out
def fit_v1(train, val, test):
    m=Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler()),('model',LogisticRegression(max_iter=2000,random_state=42))])
    m.fit(train[NUMERIC_COLS],train.label); return m
def model_diagnostics(train,val,test,split):
    v1=fit_v1(train,val,test)
    gb=joblib.load(PHASE31/'artifacts'/f'{split}_candidate.joblib')
    y=test.label.to_numpy(int); v1p=v1.predict_proba(test[NUMERIC_COLS])[:,1]; gbp=gb.predict_proba(test[NUMERIC_COLS])[:,1]
    rows=[]
    for name,p in [('V1',v1p),('GB',gbp)]:
        err=(p>=.5).astype(int)!=y
        buckets=pd.Series(pd.qcut(test.job_start_time,4,duplicates='drop'), index=test.index)
        rows.append({'model':name,'auc':auc(y,p),'mean_probability':float(p.mean()),'p01':float(np.quantile(p,.01)),'p50':float(np.quantile(p,.5)),'p99':float(np.quantile(p,.99)),'extreme_low_rate':float((p<.05).mean()),'extreme_high_rate':float((p>.95).mean()),'error_rate':float(err.mean()),'error_by_time_quartile':{str(k):float(err[buckets==k].mean()) for k in buckets.cat.categories},'error_by_risk_bucket':{str(k):float(err[pd.Series(pd.cut(p,[-.01,.1,.25,.5,.75,.9,1.01]))==k].mean()) for k in pd.Series(pd.cut(p,[-.01,.1,.25,.5,.75,.9,1.01])).cat.categories}})
    coefs=v1.named_steps['model'].coef_[0]
    imp=gb.named_steps['model'].feature_importances_
    return {'models':rows,'v1_standardized_coefficients':dict(sorted(zip(NUMERIC_COLS,coefs),key=lambda z:-abs(z[1]))),'gb_feature_importances':dict(sorted(zip(NUMERIC_COLS,imp),key=lambda z:-z[1]))}
def target_drift(train,future):
    out={}
    for c in NUMERIC_COLS:
        a=auc(train.label.to_numpy(),train[c].fillna(train[c].median()).to_numpy())
        b=auc(future.label.to_numpy(),future[c].fillna(train[c].median()).to_numpy())
        ra=float(spearmanr(train[c].fillna(train[c].median()),train.label).statistic); rb=float(spearmanr(future[c].fillna(train[c].median()),future.label).statistic)
        out[c]={'train_univariate_auc':a,'future_univariate_auc':b,'auc_delta':None if a is None or b is None else b-a,'train_spearman':ra,'future_spearman':rb,'spearman_delta':rb-ra}
    return out
def main():
    OUT.mkdir(parents=True,exist_ok=True); df=build_feature_matrix(); rs=json.loads(RANDOM.read_text()); ts=json.loads(TEMPORAL.read_text())
    def parts(s): return {k:df[df.job_name.isin(set(s[k]))].copy() for k in ('train','val','test')}
    rp,tp=parts(rs),parts(ts)
    populations={'random_train':stats(rp['train']),'random_validation':stats(rp['val']),'random_test':stats(rp['test']),'temporal_train':stats(tp['train']),'temporal_validation':stats(tp['val']),'temporal_future_test':stats(tp['test'])}
    failures={}
    base=float(rp['train'].label.mean())
    for name,frame in [('random_train',rp['train']),('random_test',rp['test']),('temporal_future_test',tp['test'])]:
        rate=float(frame.label.mean()); failures[name]={'n':len(frame),'failure_rate':rate,'absolute_change_vs_train':rate-base,'relative_change_vs_train':None if base==0 else rate/base-1}
    audit={'experiment_id':'phase32_temporal_generalization_audit','dataset':'alibaba_gpu2020','source_manifest_sha256':sha(ROOT/'data/audit/alibaba_gpu2020/dataset_manifest.json'),'feature_set':list(NUMERIC_COLS),'populations':populations,'failure_prevalence':failures,'feature_distribution_shift_train_to_future':drift(tp['train'],tp['test']),'feature_target_drift_train_to_future':target_drift(tp['train'],tp['test']),'model_behavior':{'random_test':model_diagnostics(rp['train'],rp['val'],rp['test'],'random_stratified'),'temporal_future_test':model_diagnostics(tp['train'],tp['val'],tp['test'],'temporal')},'phase31_reference':{'results_sha256':sha(PHASE31/'results.json'),'decision':'REJECT','candidate':'GradientBoostingClassifier','v1_control':'logistic regression'},'methodological_boundary':'Stage A analysis only; no dataset, split, feature, threshold, or V1 artifact changes; temporal labels used only for locked audit, not tuning.'}
    (OUT/'stage_a_audit.json').write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'completed','output':str(OUT/'stage_a_audit.json'),'features':len(NUMERIC_COLS)},indent=2))
if __name__=='__main__': main()
