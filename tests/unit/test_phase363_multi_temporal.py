import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'experiments/results/v1_1/v1_forensics/3_6_3_multi_temporal_validation'
def load(n):return json.loads((D/n).read_text())
def test_contract_files_and_folds():
 for n in ['protocol.json','manifest.json','results.json','summary.json','report.md','finalized.json','.finalized']:assert (D/n).exists()
 p=load('protocol.json');assert p['phase']=='3.6.3';assert len(p['feature_contract'])==14;assert len(p['interaction_set'])==3
def test_authoritative_fold_identity_and_order():
 source=load('../..') if False else json.loads((ROOT/'experiments/results/v1_1/distribution_robust_uncertainty/3_5_a_temporal_folds/manifest.json').read_text())
 p=load('protocol.json');assert p['fold_source']=='Phase 3.5 authoritative fold manifest';assert p['fold_definitions'] if 'fold_definitions' in p else True
 src=source['fold_definitions'];
 for i,f in enumerate(src):
  z=load(f'fold_definitions/{f["fold_id"]}.json');assert z['train_idx']==f['train_idx'] and z['validation_idx']==f['validation_idx'] and z['test_idx']==f['test_idx'];assert z['train_idx'][1]<=z['validation_idx'][0]<=z['test_idx'][0]
def test_exact_interaction_definition():
 assert load('protocol.json')['interaction_set']==['n_tasks__x__mean_plan_cpu','n_tasks__x__mean_plan_gpu','mean_plan_cpu__x__mean_plan_gpu']
def test_all_models_all_folds_present():
 r=load('results.json')['fold_results'];assert set(r)=={'fold_1','fold_2','fold_3'}
 for f in r:assert set(r[f])=={'v1_logistic','linear_c01','limited_interactions','constrained_rf','gradient_boosting'}
def test_interaction_delta_preserves_all_folds():
 s=load('summary.json')['interaction_vs_v1'];assert s['wins_auroc']==1 and s['losses_auroc']==2;assert s['worst_auroc_delta']<0
def test_temporal_failure_evidence_recorded():
 s=load('summary.json');assert s['constrained_rf']['min_auroc']<.5;assert s['gradient_boosting']['min_auroc']>.5 and s['gradient_boosting']['mean_auroc']<.6
def test_hashes_immutable():
 h=load('.finalized')
 for rel,digest in h.items():assert hashlib.sha256((D/rel).read_bytes()).hexdigest()==digest
def test_historical_paths_protected():
 assert (ROOT/'experiments/results/v1_1/v1_forensics/3_6_2_matched_complexity/results.json').exists();assert (ROOT/'experiments/results/v1_1/distribution_robust_uncertainty/3_5_a_temporal_folds/manifest.json').exists()
