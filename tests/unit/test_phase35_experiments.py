import hashlib, json
from pathlib import Path
import joblib
ROOT=Path(__file__).resolve().parents[2]; BASE=ROOT/'experiments/results/v1_1/distribution_robust_uncertainty'; EXPS=['3_5_a_temporal_folds','3_5_b_uncertainty_stability','3_5_c_selective_policy','3_5_d_synthesis']

def test_four_isolated_phase35_stages_exist(): assert [p.name for p in sorted(BASE.iterdir()) if p.is_dir()]==EXPS

def test_fold_ordering_and_nonoverlap():
 d=json.loads((BASE/'3_5_a_temporal_folds/results.json').read_text())['folds']; prev=-1
 for f in d:
  assert f['train_idx'][1] <= f['validation_idx'][0] < f['validation_idx'][1] <= f['test_idx'][0] < f['test_idx'][1]
  assert f['test_idx'][0] >= prev; prev=f['test_idx'][1]
  assert f['n_train']>0 and f['n_validation']>0 and f['n_test']>=1000

def test_phase35_protocols_are_locked_to_train_validation():
 for n in EXPS:
  p=json.loads((BASE/n/'protocol.json').read_text())
  assert p['selection_boundary'].startswith('all fold definitions')
  assert 'future-fold evaluation' in p['selection_boundary']
  assert p['experiment_id'] and p['hypothesis'] and p['intervention']

def test_uncertainty_stability_is_reported_per_fold():
 d=json.loads((BASE/'3_5_b_uncertainty_stability/results.json').read_text())
 assert set(d['temporal_folds'])=={'fold_1','fold_2','fold_3'}
 assert d['positive_folds']>=2
 for x in d['temporal_folds'].values(): assert 'error_difference' in x and 'uncertainty_error_correlation' in x

def test_selective_policy_keeps_negative_fold_results():
 d=json.loads((BASE/'3_5_c_selective_policy/results.json').read_text())
 assert len(d['risk_deltas'])==3
 assert d['improved_folds']<3
 assert d['decision']=='REJECT'

def test_all_stage_hashes_are_valid():
 for n in EXPS:
  d=BASE/n; h=json.loads((d/'.finalized').read_text())
  for rel,digest in h.items(): assert hashlib.sha256((d/rel).read_bytes()).hexdigest()==digest

def test_no_canonical_v1_paths_modified():
 assert not any((ROOT/x).exists() and (ROOT/x/'PHASE35_SYNTHESIS.md').exists() for x in ['experiments/results/v1_1/temporal_robustness'])


def test_synthesis_is_non_actionable_and_v1_remains_control():
 d=json.loads((BASE/'3_5_d_synthesis/results.json').read_text())
 assert d['classification']=='NON-ACTIONABLE' and d['decision']=='HOLD'
 assert 'V1' in (BASE/'PHASE35_SYNTHESIS.md').read_text()
