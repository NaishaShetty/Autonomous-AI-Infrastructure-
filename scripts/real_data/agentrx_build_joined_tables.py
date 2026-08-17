"""
Phase 3 real-data replication -- AgentRx canonical trajectory-level
join. Reads ONLY data/raw/agentrx/*.jsonl (never modified). Produces
one row per annotated trajectory, joining trajectory content with its
failure/diagnosis annotation, preserving trajectory-level grouping
(never splitting a trajectory's steps into separate rows) and full
source provenance.

Magentic pair joins directly on trajectory_id (44/58 trajectories have
annotations). Tau-retail pair requires stripping the "tau_retail_"
prefix from tau_retail_dataset.jsonl's IDs to match tau_retail.jsonl's
bare numeric IDs (verified 29/29 bijection in the feasibility audit).

Domains are kept SEPARATE (not pooled) per the "do not pool datasets
just to increase N" instruction -- these are two structurally
different task domains and pooling would misrepresent effective N.

No field is fabricated: trajectories without an annotation are
recorded with diagnosis fields explicitly MISSING, not dropped and not
inferred.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw" / "agentrx"
OUT_DIR = REPO_ROOT / "data" / "processed" / "agentrx"


def load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_domain(domain_name, traj_path, annot_path, id_map_fn):
    trajectories = load_jsonl(traj_path)
    annotations = load_jsonl(annot_path)
    annot_by_id = {a["trajectory_id"]: a for a in annotations}

    joined = []
    for t in trajectories:
        raw_id = t["trajectory_id"]
        mapped_id = id_map_fn(raw_id)
        annot = annot_by_id.get(mapped_id)
        record = {
            "source_dataset": "AgentRx",
            "domain": domain_name,
            "trajectory_id": raw_id,
            "annotation_id_used_for_join": mapped_id,
            "source_trajectory_file": traj_path.name,
            "source_annotation_file": annot_path.name,
            "instruction": t.get("instruction"),
            "num_steps": len(t.get("steps", [])),
            "has_failure_annotation": annot is not None,
            "num_failures": annot["num_failures"] if annot else "MISSING",
            "failure_categories": (
                sorted(set(f["failure_category"] for f in annot["failures"]))
                if annot else "MISSING"
            ),
            "root_cause_failure_id": annot["root_cause_failure_id"] if annot else "MISSING",
            "root_cause_reason": annot["root_cause_reason"] if annot else "MISSING",
            "recovery_action": "MISSING",  # not present in source, never inferred
            "recovery_outcome": "MISSING",  # not present in source, never inferred
            "timestamp": "MISSING",  # AgentRx has no timestamps at all
        }
        joined.append(record)

    # also record annotations with NO matching trajectory (should be 0 given
    # the audit's subset-relationship finding, but check rather than assume)
    traj_ids_mapped = set(id_map_fn(t["trajectory_id"]) for t in trajectories)
    orphan_annotations = [a["trajectory_id"] for a in annotations if a["trajectory_id"] not in traj_ids_mapped]

    return joined, orphan_annotations


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    magentic_joined, magentic_orphans = build_domain(
        "magentic_one_web_file_agent",
        RAW_DIR / "magentic_dataset.jsonl",
        RAW_DIR / "magentic_one.jsonl",
        id_map_fn=lambda x: x,
    )
    tau_joined, tau_orphans = build_domain(
        "tau_bench_retail",
        RAW_DIR / "tau_retail_dataset.jsonl",
        RAW_DIR / "tau_retail.jsonl",
        id_map_fn=lambda x: x.replace("tau_retail_", ""),
    )

    with open(OUT_DIR / "magentic_joined.jsonl", "w", encoding="utf-8") as f:
        for r in magentic_joined:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(OUT_DIR / "tau_retail_joined.jsonl", "w", encoding="utf-8") as f:
        for r in tau_joined:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    summary = {
        "magentic_one_web_file_agent": {
            "total_trajectories": len(magentic_joined),
            "with_annotation": sum(1 for r in magentic_joined if r["has_failure_annotation"]),
            "without_annotation": sum(1 for r in magentic_joined if not r["has_failure_annotation"]),
            "orphan_annotations_no_matching_trajectory": magentic_orphans,
        },
        "tau_bench_retail": {
            "total_trajectories": len(tau_joined),
            "with_annotation": sum(1 for r in tau_joined if r["has_failure_annotation"]),
            "without_annotation": sum(1 for r in tau_joined if not r["has_failure_annotation"]),
            "orphan_annotations_no_matching_trajectory": tau_orphans,
        },
        "pooling_decision": "domains kept separate; NOT pooled into one N -- see script docstring",
    }
    with open(REPO_ROOT / "data" / "audit" / "agentrx" / "join_report.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
