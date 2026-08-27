"""Runs dataset generation twice into two separate temp output directories
and diffs record IDs, record contents, split assignments, canonical
serialized files, and SHA-256 hashes. Writes regeneration_audit.json into
the FIRST (kept) output directory.

Usage:
    python scripts/phase5_dataset/regeneration_check.py <keep_output_dir> <scratch_dir>
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha256_tree(root: Path) -> dict:
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[str(p.relative_to(root)).replace("\\", "/")] = sha256_file(p)
    return out


def main(keep_dir: str, scratch_dir: str) -> None:
    keep = Path(keep_dir)
    scratch = Path(scratch_dir)
    run_a = scratch / "run_a"
    run_b = scratch / "run_b"
    for d in (run_a, run_b):
        if d.exists():
            import shutil
            shutil.rmtree(d)
        d.mkdir(parents=True)

    gen_script = str(REPO_ROOT / "scripts" / "phase5_dataset" / "generate.py")
    for d in (run_a, run_b):
        subprocess.run([sys.executable, gen_script, str(d)], check=True, cwd=str(REPO_ROOT))

    hashes_a = sha256_tree(run_a)
    hashes_b = sha256_tree(run_b)

    all_files = sorted(set(hashes_a) | set(hashes_b))
    diffs = []
    for fname in all_files:
        ha = hashes_a.get(fname)
        hb = hashes_b.get(fname)
        if ha != hb:
            diffs.append({"file": fname, "sha256_run_a": ha, "sha256_run_b": hb})

    # Deeper diff: record_id sets, record contents, split assignments
    def load_jsonl(p):
        rows = []
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                rows.append(json.loads(line))
        return rows

    recs_a = load_jsonl(run_a / "dataset" / "all_records.jsonl")
    recs_b = load_jsonl(run_b / "dataset" / "all_records.jsonl")

    ids_a = [r["identity"]["record_id"] for r in recs_a]
    ids_b = [r["identity"]["record_id"] for r in recs_b]
    splits_a = {r["identity"]["record_id"]: r["split_assignment"] for r in recs_a}
    splits_b = {r["identity"]["record_id"]: r["split_assignment"] for r in recs_b}

    record_ids_identical = ids_a == ids_b
    record_contents_identical = recs_a == recs_b
    split_assignments_identical = splits_a == splits_b
    file_hashes_identical = len(diffs) == 0

    result = {
        "run_a": str(run_a),
        "run_b": str(run_b),
        "n_records_a": len(recs_a),
        "n_records_b": len(recs_b),
        "record_ids_identical": record_ids_identical,
        "record_contents_identical": record_contents_identical,
        "split_assignments_identical": split_assignments_identical,
        "file_sha256_identical": file_hashes_identical,
        "n_files_compared": len(all_files),
        "n_files_differing": len(diffs),
        "differing_files_sample": diffs[:20],
        "overall_byte_identical": (
            record_ids_identical and record_contents_identical
            and split_assignments_identical and file_hashes_identical
        ),
    }

    with open(keep / "regeneration_audit.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")

    print(json.dumps({k: v for k, v in result.items() if k != "differing_files_sample"}, indent=2))

    import shutil
    shutil.rmtree(scratch)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
