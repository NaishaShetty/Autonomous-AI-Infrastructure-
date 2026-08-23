import json
from pathlib import Path
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parents[1]/'experiments/results/v1_1/v1_forensics/3_6_2_matched_complexity';P=D/'plots';P.mkdir(exist_ok=True)
x=json.loads((D/'results.json').read_text())['ladder']; ids=list(x); labels=['Prev','V1 LR','LR C=.1','Interactions','RF','GB']; rnd=[x[i]['random']['auroc'] for i in ids];tmp=[x[i]['temporal']['auroc'] for i in ids];gap=[rnd[i]-tmp[i] for i in range(len(ids))]
def save(name,y,title,ylabel,color):
 plt.figure(figsize=(8,4.8));plt.plot(range(6),y,marker='o',color=color);plt.xticks(range(6),labels);plt.xlabel('Model expressiveness level');plt.ylabel(ylabel);plt.title(title);plt.grid(alpha=.25);plt.tight_layout();plt.savefig(P/name,dpi=160);plt.close()
save('complexity_random_auroc.png',rnd,'Complexity vs Random AUROC','Random AUROC','#2563eb');save('complexity_temporal_auroc.png',tmp,'Complexity vs Temporal AUROC','#Temporal AUROC','#dc2626');
plt.figure(figsize=(8,4.8));plt.plot(range(6),rnd,marker='o',label='Random AUROC');plt.plot(range(6),tmp,marker='o',label='Temporal AUROC');plt.xticks(range(6),labels);plt.xlabel('Model expressiveness level');plt.ylabel('AUROC');plt.title('Random vs Temporal Performance');plt.legend();plt.grid(alpha=.25);plt.tight_layout();plt.savefig(P/'random_vs_temporal_auroc.png',dpi=160);plt.close();save('generalization_gap.png',gap,'Generalization Gap: Random AUROC − Temporal AUROC','Random AUROC − Temporal AUROC','#7c3aed')
