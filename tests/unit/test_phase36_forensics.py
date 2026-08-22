import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; BASE=ROOT/'experiments/results/v1_1/v1_forensics'; STAGES=['3_6_a_data_evaluation','3_6_b_feature_forensics','3_6_c_regularization','3_6_d_complexity_ladder','3_6_e_synthesis']
def test_all_forensic_stages_exist(): assert [p.name for p in sorted(BASE.iterdir()) if p.is_dir()]==STAGES
def test_stage_contracts_and_hashes():
 for n in STAGES:
  d=BASE/n
  for f in ['protocol.json','manifest.json','results.json','summary.json','report.md','finalized.json','.finalized']: assert (d/f).exists(),(n,f)
  h=json.loads((d/'.finalized').read_text())
  for rel,digest in h.items(): assert hashlib.sha256((d/rel).read_bytes()).hexdigest()==digest,(n,rel)
def test_forensics_are_additive_and_no_prior_results_changed():
 assert not (ROOT/'experiments/results/v1_1/temporal_robustness/3_6_e_synthesis').exists()
 assert not (ROOT/'experiments/results/v1_1/calibration_abstention/3_6_e_synthesis').exists()
def test_data_forensics_contains_population_shift_duplicate_and_group_evidence():
 d=json.loads((BASE/'3_6_a_data_evaluation/results.json').read_text())
 assert set(d['population'])=={'random','temporal'} and d['feature_shift_random_test_vs_temporal_test']
 assert d['duplicates'] and 'group_composition' in d
def test_feature_forensics_covers_all_v1_features():
 d=json.loads((BASE/'3_6_b_feature_forensics/results.json').read_text())
 features=json.loads((BASE/'3_6_b_feature_forensics/manifest.json').read_text())['feature_set']
 assert all(f in d for f in features)
 assert all('ablation' in d[f] and 'shift' in d[f] for f in features)
def test_complexity_ladder_retains_prior_failures():
 d=json.loads((BASE/'3_6_d_complexity_ladder/results.json').read_text())['levels']
 assert {'0_prevalence','1_v1_logistic','2_less_regularized_linear','3_constrained_rf','4_gradient_boosting_prior'}<=set(d)
 assert d['3_constrained_rf']['temporal']['auroc']<0.5 and d['4_gradient_boosting_prior']['temporal']['auroc']<0.5
def test_synthesis_is_forensic_not_integration():
 d=json.loads((BASE/'3_6_e_synthesis/results.json').read_text())
 assert d['decision']=='HOLD' and 'remain unresolved' in d['conclusion']
 assert 'No feature removal' in (BASE/'3_6_e_synthesis/report.md').read_text()
