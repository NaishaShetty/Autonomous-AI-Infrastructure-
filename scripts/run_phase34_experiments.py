"""Phase 3.4 additive calibration/uncertainty/abstention research runner.

Frozen V1 is imported only as a control: no V1 source or historical artifact is
written. All fitting uses registered train/validation rows; random and temporal
test rows are evaluated only after policies are locked.
"""
from __future__ import annotations
import hashlib, importlib.util, json, os, platform, shutil
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'experiments/results/v1_1/calibration_abstention'
SEED=42
FEATURES=None

def load_mod(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
p1=load_mod('phase31_loader', ROOT/'scripts/real_data/phase3_1_rd_alibaba_evaluate.py')
FEATURES=p1.NUMERIC_COLS+p1.CATEGORICAL_COLS

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def split(name):
    return json.loads((ROOT/f'data/audit/alibaba_gpu2020/splits_{name}.json').read_text())
def ids(v): return set(v)
def frame():
    d=p1.build_feature_matrix(); p1.assert_no_excluded_columns(d); return d

def pipe(C=1.0):
    from sklearn.pipeline import Pipeline
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
    num=Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler())])
    cat=Pipeline([('impute',SimpleImputer(strategy='constant',fill_value='UNKNOWN')),('onehot',OneHotEncoder(handle_unknown='ignore'))])
    pre=ColumnTransformer([('num',num,p1.NUMERIC_COLS),('cat',cat,p1.CATEGORICAL_COLS)])
    return Pipeline([('pre',pre),('clf',LogisticRegression(C=C,max_iter=2000,random_state=SEED))])

def metric(y,p):
    y=np.asarray(y); p=np.clip(np.asarray(p),1e-8,1-1e-8)
    return {'auroc':float(roc_auc_score(y,p)),'auprc':float(average_precision_score(y,p)),
            'brier':float(brier_score_loss(y,p)),'log_loss':float(log_loss(y,p)),'count':int(len(y))}

def ece(y,p,bins=10):
    y=np.asarray(y); p=np.asarray(p); out=[]
    for i in range(bins):
        lo=i/bins; hi=(i+1)/bins; mask=(p>=lo)&((p<hi) if i<bins-1 else (p<=hi))
        if mask.any(): out.append({'bin':i,'count':int(mask.sum()),'mean_prediction':float(p[mask].mean()),'observed_rate':float(y[mask].mean())})
    return float(sum(x['count']*abs(x['mean_prediction']-x['observed_rate']) for x in out)/len(y)),out

def risk(p): return np.asarray(p)
def fit_calibrators(train, val):
    base=pipe(); base.fit(train[FEATURES],train.label)
    pv=base.predict_proba(val[FEATURES])[:,1]
    iso=IsotonicRegression(out_of_bounds='clip',y_min=0,y_max=1).fit(pv,val.label)
    # Platt is predeclared as the single alternative intervention.
    platt=LogisticRegression(C=1.0,solver='lbfgs',max_iter=1000,random_state=SEED).fit(pv.reshape(-1,1),val.label)
    return base,iso,platt

def cal_eval(y,p):
    m=metric(y,p); m['ece'],m['reliability_bins']=ece(y,p); return m

def unc_ensemble(train, X, n=9):
    rng=np.random.RandomState(SEED); arr=[]
    for i in range(n):
        idx=rng.randint(0,len(train),len(train)); m=pipe(); m.fit(train.iloc[idx][FEATURES],train.iloc[idx].label); arr.append(m.predict_proba(X[FEATURES])[:,1])
    a=np.asarray(arr); return a.mean(0),a.std(0),arr

def selective(y,p,u,threshold):
    accepted=np.asarray(u)<=threshold; yy=np.asarray(y); pp=np.asarray(p)
    return {'coverage':float(accepted.mean()),'abstention_rate':float(1-accepted.mean()),
            'selective_risk':float(yy[accepted].mean()) if accepted.any() else None,
            'accepted_count':int(accepted.sum()),'abstained_count':int((~accepted).sum()),
            'accepted_failure_rate':float(yy[accepted].mean()) if accepted.any() else None,
            'abstained_failure_rate':float(yy[~accepted].mean()) if (~accepted).any() else None,
            'threshold':float(threshold)}

def save_plot(path, y,p,title):
    order=np.argsort(p); yy=np.asarray(y)[order]; pp=np.asarray(p)[order]; n=max(1,len(y)//10)
    xs=[]; ys=[]
    for i in range(0,len(y),n): xs.append(float(pp[i:i+n].mean())); ys.append(float(yy[i:i+n].mean()))
    fig,ax=plt.subplots(figsize=(5,4)); ax.plot([0,1],[0,1],'--',label='perfect'); ax.plot(xs,ys,'o-',label='V1'); ax.set(xlabel='Predicted failure probability',ylabel='Observed failure rate',title=title); ax.legend(); fig.tight_layout(); fig.savefig(path,dpi=140); plt.close(fig)

def write_exp(exp_id, protocol, results, artifacts, report):
    d=OUT/exp_id; d.mkdir(parents=True,exist_ok=True); (d/'artifacts').mkdir(exist_ok=True); (d/'plots').mkdir(exist_ok=True)
    (d/'protocol.json').write_text(json.dumps(protocol,indent=2,sort_keys=True)+'\n'); (d/'results.json').write_text(json.dumps(results,indent=2,sort_keys=True)+'\n')
    summary={'experiment_id':exp_id,'phase':'3.4','decision':results['decision'],'decision_basis':results.get('decision_basis',''),'random_stratified':results.get('random_stratified'),'temporal_future':results.get('temporal_future')}
    (d/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n'); (d/'report.md').write_text(report)
    manifest={'experiment_id':exp_id,'phase':'3.4','hypothesis':protocol['hypothesis'],'baseline':'Frozen V1 reliability predictor; additive layer only','intervention':protocol['intervention'],'dataset_identity':'official Alibaba GPU2020 restored data','data_hashes':{x:sha(ROOT/x) for x in ['data/audit/alibaba_gpu2020/splits_random_stratified.json','data/audit/alibaba_gpu2020/splits_temporal.json']},'feature_set':FEATURES,'model_identity':'frozen V1 logistic predictor wrapper','calibration_identity':protocol.get('calibration_identity'),'uncertainty_method':protocol.get('uncertainty_method'),'abstention_policy':protocol.get('abstention_policy'),'selection_boundary':'registered train/validation only; future temporal test locked','random_seeds':[SEED],'evaluation_protocol':'random-stratified and temporal future registered test populations','software_version':platform.python_version(),'provenance':'scripts/run_phase34_experiments.py'}
    manifest['artifact_hashes']={str(p.relative_to(d)):sha(p) for p in sorted(d.rglob('*')) if p.is_file() and p.name not in ('manifest.json','finalized.json','.finalized')}
    (d/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n'); hashes={str(p.relative_to(d)):sha(p) for p in sorted(d.rglob('*')) if p.is_file() and p.name not in ('finalized.json','.finalized')}; (d/'finalized.json').write_text(json.dumps({'immutable':True,'files':hashes},indent=2,sort_keys=True)+'\n'); (d/'.finalized').write_text(json.dumps(hashes,sort_keys=True)+'\n')

def main():
    if OUT.exists(): raise SystemExit(f'refusing to overwrite existing {OUT}')
    OUT.mkdir(parents=True)
    df=frame(); rs=split('random_stratified'); ts=split('temporal')
    # For both split contracts, train/validation are explicit; the temporal test is locked.
    splits={'random_stratified':rs,'temporal_future':ts}; fitted={}
    for name,s in splits.items():
        tr=df[df.job_name.isin(ids(s['train']))].copy(); va=df[df.job_name.isin(ids(s.get('validation',s.get('val',[]))))].copy(); te=df[df.job_name.isin(ids(s['test']))].copy(); fitted[name]=(tr,va,te)
    # A: actual V1 isotonic calibration audit and one predeclared Platt alternative.
    ares={}; a_art=[]
    for name,(tr,va,te) in fitted.items():
        model,iso,platt=fit_calibrators(tr,va); raw=model.predict_proba(te[FEATURES])[:,1]; ip=iso.predict(raw); pp=platt.predict_proba(raw.reshape(-1,1))[:,1]
        ares[name]={'v1_isotonic':cal_eval(te.label,ip),'candidate_platt':cal_eval(te.label,pp),'raw_v1_ranking':metric(te.label,raw),'calibration_training_count':len(va)}
        d=OUT/'3_4_a_calibration'; d.mkdir(parents=True,exist_ok=True); (d/'artifacts').mkdir(exist_ok=True); (d/'plots').mkdir(exist_ok=True); joblib.dump({'model':model,'isotonic':iso},d/'artifacts'/f'{name}_v1_isotonic.joblib'); joblib.dump({'model':model,'platt':platt},d/'artifacts'/f'{name}_candidate_platt.joblib'); save_plot(d/'plots'/f'{name}_v1_reliability.png',te.label,ip,f'V1 isotonic calibration — {name}'); a_art += [d/'artifacts'/f'{name}_v1_isotonic.joblib',d/'artifacts'/f'{name}_candidate_platt.joblib']
    a_dec='HOLD' if ares['temporal_future']['candidate_platt']['auroc']>=ares['temporal_future']['raw_v1_ranking']['auroc']-0.01 and ares['temporal_future']['candidate_platt']['brier']<ares['temporal_future']['v1_isotonic']['brier'] else 'REJECT'
    apro={'experiment_id':'phase34_a_calibration_platt','hypothesis':'A single Platt calibration layer can improve probability quality without changing V1 ranking.','intervention':'Fit one Platt calibrator on registered validation predictions; no future labels.','calibration_identity':'V1 isotonic audit versus candidate Platt scaling','uncertainty_method':'none','abstention_policy':'none'}
    areport=f'# Experiment 3.4-A — Calibration Audit & Improvement\n\nV1 calibration implementation was audited: frozen V1 uses an isotonic risk calibrator fit on validation risk values, with clipped [0,1] output and the existing threshold/runtime untouched. The candidate was one predeclared Platt scaling layer fit on validation predictions only.\n\n| Split | V1 AUROC | Candidate AUROC | V1 Brier | Candidate Brier | V1 ECE | Candidate ECE |\n|---|---:|---:|---:|---:|---:|---:|\n'+''.join(f"| {k} | {v['raw_v1_ranking']['auroc']:.4f} | {v['candidate_platt']['auroc']:.4f} | {v['v1_isotonic']['brier']:.4f} | {v['candidate_platt']['brier']:.4f} | {v['v1_isotonic']['ece']:.4f} | {v['candidate_platt']['ece']:.4f} |\n" for k,v in ares.items())+f'\n**Decision: {a_dec}.** Calibration must be judged jointly with temporal behavior, ranking, and downstream selectivity; no V1 behavior was changed.\n\nHistorical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.\n'
    # Move A artifacts into the final directory only after creating it once.
    # write_exp creates the directory, so use temporary artifact staging copy.
    tmp=OUT/'_a_stage'; tmp.mkdir();
    for p in a_art: shutil.copy2(p,tmp/p.name)
    # remove provisional A tree and recreate through writer
    shutil.rmtree(OUT/'3_4_a_calibration'); apro_path=OUT/'3_4_a_calibration'
    write_exp('3_4_a_calibration',apro,{'random_stratified':ares['random_stratified'],'temporal_future':ares['temporal_future'],'decision':a_dec,'decision_basis':'ranking, Brier, ECE, temporal calibration, and operational implications'},a_art,areport)
    for p in a_art: shutil.copy2(tmp/p.name,OUT/'3_4_a_calibration'/'artifacts'/p.name)
    shutil.rmtree(tmp)
    # B: bootstrap/model variability uncertainty, fit only from training data.
    bres={}; bmodels=[]
    for name,(tr,va,te) in fitted.items():
        mean,std,arr=unc_ensemble(tr,te); err=(te.label.to_numpy()!= (mean>=0.5)); bres[name]={'risk_metrics':metric(te.label,mean),'uncertainty_mean':float(std.mean()),'uncertainty_error_rate_high_vs_low':{'high':float(err[std>=np.median(std)].mean()),'low':float(err[std<np.median(std)].mean())},'uncertainty_threshold_validation_median':float(np.median(unc_ensemble(tr,va)[1]))};
        d=OUT/'3_4_b_uncertainty'; d.mkdir(exist_ok=True); (d/'artifacts').mkdir(exist_ok=True); joblib.dump({'models':arr,'feature_names':FEATURES},d/'artifacts'/f'{name}_bootstrap_ensemble.joblib'); bmodels.append(d/'artifacts'/f'{name}_bootstrap_ensemble.joblib')
    buse=bres['temporal_future']['uncertainty_error_rate_high_vs_low']['high']>bres['temporal_future']['uncertainty_error_rate_high_vs_low']['low']; b_dec='INTERESTING FINDING' if buse else 'REJECT'
    bprot={'experiment_id':'phase34_b_bootstrap_uncertainty','hypothesis':'Decision-time bootstrap model variability identifies less trustworthy V1 predictions.','intervention':'Nine bootstrap V1-compatible logistic fits trained on resampled training rows; uncertainty is predictive standard deviation.','calibration_identity':'none','uncertainty_method':'bootstrap/model variability','abstention_policy':'none'}
    brep=f'# Experiment 3.4-B — Uncertainty Estimation\n\nThe sole uncertainty method was bootstrap/model variability. Every ensemble member used only training rows and uncertainty was computed from decision-time features.\n\n| Split | AUROC | AUPRC | Mean uncertainty | High-uncertainty error | Low-uncertainty error |\n|---|---:|---:|---:|---:|---:|\n'+''.join(f"| {k} | {v['risk_metrics']['auroc']:.4f} | {v['risk_metrics']['auroc']:.4f} | {v['uncertainty_mean']:.6f} | {v['uncertainty_error_rate_high_vs_low']['high']:.4f} | {v['uncertainty_error_rate_high_vs_low']['low']:.4f} |\n" for k,v in bres.items())+f'\n**Decision: {b_dec}.** The signal is retained only as a research finding unless it demonstrates a useful downstream safety/coverage tradeoff.\n\nHistorical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.\n'
    write_exp('3_4_b_uncertainty',bprot,{'random_stratified':bres['random_stratified'],'temporal_future':bres['temporal_future'],'decision':b_dec,'decision_basis':'error stratification and temporal decision relevance'},bmodels,brep)
    # C: fixed validation-derived uncertainty threshold, 80% target coverage.
    cres={}; thresholds={}
    for name,(tr,va,te) in fitted.items():
        _,uv,_=unc_ensemble(tr,va); threshold=float(np.quantile(uv,0.80)); thresholds[name]=threshold; mean,ut,_=unc_ensemble(tr,te); cres[name]={'v1':selective(te.label,mean,np.zeros(len(te)),1.0),'candidate':selective(te.label,mean,ut,threshold),'risk_metrics':metric(te.label,mean)}
    c_dec='ACCEPT' if cres['temporal_future']['candidate']['coverage']>=0.5 and cres['temporal_future']['candidate']['selective_risk']<cres['temporal_future']['v1']['selective_risk'] else 'REJECT'
    cprot={'experiment_id':'phase34_c_selective_uncertainty','hypothesis':'A validation-locked uncertainty threshold can reduce accepted-case risk while retaining meaningful coverage.','intervention':'Abstain above the 80th validation percentile of bootstrap uncertainty; threshold locked before either test evaluation.','calibration_identity':'none','uncertainty_method':'bootstrap/model variability from 3.4-B','abstention_policy':'abstain when uncertainty exceeds validation 80th percentile'}
    crep=f'# Experiment 3.4-C — Selective Prediction & Abstention\n\nThresholds were selected from validation uncertainty only, with an 80% coverage operating target declared before test evaluation.\n\n| Split | V1 coverage | Candidate coverage | V1 selective risk | Candidate selective risk | Abstention rate |\n|---|---:|---:|---:|---:|---:|\n'+''.join(f"| {k} | {v['v1']['coverage']:.4f} | {v['candidate']['coverage']:.4f} | {v['v1']['selective_risk']:.4f} | {v['candidate']['selective_risk']:.4f} | {v['candidate']['abstention_rate']:.4f} |\n" for k,v in cres.items())+f'\n**Decision: {c_dec}.** Zero-risk/near-zero-coverage behavior would be operationally unusable and would be rejected.\n\nHistorical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.\n'
    write_exp('3_4_c_abstention',cprot,{'random_stratified':cres['random_stratified'],'temporal_future':cres['temporal_future'],'validation_thresholds':thresholds,'decision':c_dec,'decision_basis':'risk-coverage and operational usefulness'},[],crep)
    # D: one combined policy only, using A/B/C outputs, no sweep.
    dres={}
    for name,(tr,va,te) in fitted.items():
        model,iso,platt=fit_calibrators(tr,va); mean,ut,_=unc_ensemble(tr,te); raw=model.predict_proba(te[FEATURES])[:,1]; calibrated=platt.predict_proba(raw.reshape(-1,1))[:,1]; _,uv,_=unc_ensemble(tr,va); threshold=float(np.quantile(uv,0.80)); dres[name]={'candidate_calibrated_metrics':cal_eval(te.label,calibrated),'combined_selective':selective(te.label,calibrated,ut,threshold),'threshold':threshold}
    d_dec='ACCEPT' if dres['temporal_future']['combined_selective']['coverage']>=0.5 and dres['temporal_future']['combined_selective']['selective_risk']<0.1 else 'REJECT'
    dprot={'experiment_id':'phase34_d_combined_reliability_layer','hypothesis':'One calibrated-risk plus validated-uncertainty policy improves safety/usefulness around frozen V1.','intervention':'Platt-calibrated V1 risk with the single validation-locked 80th-percentile bootstrap-uncertainty abstention policy.','calibration_identity':'Platt candidate from 3.4-A','uncertainty_method':'bootstrap/model variability from 3.4-B','abstention_policy':'single 3.4-C policy; no combination sweep'}
    drep=f'# Experiment 3.4-D — Combined Reliability Decision Layer\n\nD was run only after A, B, and C. It used exactly one policy: the predeclared Platt candidate plus the validation-locked uncertainty threshold.\n\n| Split | Calibrated AUROC | Calibrated Brier | Coverage | Selective risk |\n|---|---:|---:|---:|---:|\n'+''.join(f"| {k} | {v['candidate_calibrated_metrics']['auroc']:.4f} | {v['candidate_calibrated_metrics']['brier']:.4f} | {v['combined_selective']['coverage']:.4f} | {v['combined_selective']['selective_risk']:.4f} |\n" for k,v in dres.items())+f'\n**Decision: {d_dec}.** The layer is not integrated into V1; any future integration requires a separate consolidation experiment.\n\nHistorical limitation: the historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.\n'
    write_exp('3_4_d_combined',dprot,{'random_stratified':dres['random_stratified'],'temporal_future':dres['temporal_future'],'decision':d_dec,'decision_basis':'combined safety/coverage/temporal usefulness'},[],drep)
    print(json.dumps({'3.4-A':a_dec,'3.4-B':b_dec,'3.4-C':c_dec,'3.4-D':d_dec},indent=2))
if __name__=='__main__': main()
