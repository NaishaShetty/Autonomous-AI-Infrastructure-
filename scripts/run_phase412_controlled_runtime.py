"""Run Phase 4.1.2 controlled-runtime engineering scenarios.

Outputs are engineering evidence only and are explicitly controlled-runtime,
not external or benchmark evidence.
"""
from pathlib import Path
from src.phase4.controlled_runtime import run_scenarios
if __name__ == '__main__':
    root=Path(__file__).resolve().parents[1]/'experiments/results/v1_1/phase4_controlled_runtime/4_1_2'
    root.mkdir(parents=True,exist_ok=True)
    result=run_scenarios(root)
    print({k:(v.get('status') if isinstance(v,dict) else v) for k,v in result.items()})
