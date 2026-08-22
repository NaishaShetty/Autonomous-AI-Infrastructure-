import json
from pathlib import Path
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'experiments/results/v1_1/v1_forensics'
a=json.loads((BASE/'3_6_a_data_evaluation/results.json').read_text()); b=json.loads((BASE/'3_6_b_feature_forensics/results.json').read_text()); d=json.loads((BASE/'3_6_d_complexity_ladder/results.json').read_text())
for p in BASE.glob('*/plots'): p.mkdir(exist_ok=True)
features=[x for x in b if not x.startswith('_') and x not in {'duplicates_and_groups','baseline','conclusion'}]
fig,ax=plt.subplots(figsize=(8,4)); ax.bar(features,[b[x]['shift']['ks'] for x in features]); ax.set_xticklabels(features,rotation=75,ha='right',fontsize=7); ax.set_ylabel('KS statistic'); ax.set_title('Random versus temporal feature distribution shift'); fig.tight_layout(); fig.savefig(BASE/'3_6_a_data_evaluation/plots/feature_shift_ks.png',dpi=140); plt.close(fig)
fig,ax=plt.subplots(figsize=(8,4)); ax.bar(features,[b[x]['ablation']['random']['auroc'] for x in features],label='Without feature — random'); ax.bar(features,[b[x]['ablation']['temporal']['auroc'] for x in features],alpha=.7,label='Without feature — temporal'); ax.set_xticklabels(features,rotation=75,ha='right',fontsize=7); ax.set_ylabel('AUROC'); ax.set_title('Leave-one-feature-out ablation'); ax.legend(); fig.tight_layout(); fig.savefig(BASE/'3_6_b_feature_forensics/plots/feature_ablation.png',dpi=140); plt.close(fig)
names=list(d['levels']); fig,ax=plt.subplots(figsize=(7,4)); ax.plot(names,[d['levels'][n]['random']['auroc'] for n in names],'o-',label='Random'); ax.plot(names,[d['levels'][n]['temporal']['auroc'] for n in names],'o-',label='Temporal'); ax.set_xticklabels(names,rotation=45,ha='right',fontsize=8); ax.set_ylabel('AUROC'); ax.set_title('Complexity ladder versus generalization'); ax.legend(); fig.tight_layout(); fig.savefig(BASE/'3_6_d_complexity_ladder/plots/complexity_generalization.png',dpi=140); plt.close(fig)
print('plots written')
