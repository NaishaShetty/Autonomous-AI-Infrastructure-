import json
from pathlib import Path
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'experiments/results/v1_1/distribution_robust_uncertainty'; P=BASE/'3_5_b_uncertainty_stability/results.json'; C=BASE/'3_5_c_selective_policy/results.json'; A=BASE/'3_5_a_temporal_folds/results.json'
b=json.loads(P.read_text())['temporal_folds']; c=json.loads(C.read_text())['temporal_folds']; a=json.loads(A.read_text())['folds']; names=list(b)
for d in [BASE/'3_5_b_uncertainty_stability/plots',BASE/'3_5_c_selective_policy/plots',BASE/'3_5_a_temporal_folds/plots']:
 d.mkdir(exist_ok=True)
fig,ax=plt.subplots(figsize=(7,4));
for x in a: ax.barh(x['fold_id'],x['test_idx'][1]-x['test_idx'][0],left=x['test_idx'][0],label=x['fold_id'])
ax.set(xlabel='Chronological row index',ylabel='Research fold',title='Pre-registered chronological fold layout'); fig.tight_layout(); fig.savefig(BASE/'3_5_a_temporal_folds/plots/fold_timeline.png',dpi=140); plt.close(fig)
fig,ax=plt.subplots(figsize=(6,4)); ax.bar(names,[b[x]['high_uncertainty_error'] for x in names],label='High uncertainty'); ax.bar(names,[b[x]['low_uncertainty_error'] for x in names],alpha=.75,label='Low uncertainty'); ax.set(ylabel='Classification error rate',title='Error stratification by temporal fold'); ax.legend(); fig.tight_layout(); fig.savefig(BASE/'3_5_b_uncertainty_stability/plots/high_low_error.png',dpi=140); plt.close(fig)
fig,ax=plt.subplots(figsize=(6,4)); ax.plot(names,[c[x]['v1']['selective_risk'] for x in names],'o-',label='V1'); ax.plot(names,[c[x]['candidate']['selective_risk'] for x in names],'o-',label='Candidate'); ax.set(ylabel='Selective risk',title='Per-fold selective-risk comparison'); ax.legend(); fig.tight_layout(); fig.savefig(BASE/'3_5_c_selective_policy/plots/selective_risk.png',dpi=140); plt.close(fig)
print('plots written')
