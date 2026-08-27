"""Duplicate/collision report for record_id (Phase 5.2 deliverable 12)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import Counter


def main(dataset_dir: str) -> None:
    out = Path(dataset_dir)
    ids = []
    full_digests = []
    with open(out / "dataset" / "all_records.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            ids.append(rec["identity"]["record_id"])
            full_digests.append(rec["identity"]["record_id_full_digest"])

    id_counts = Counter(ids)
    digest_counts = Counter(full_digests)
    dup_ids = {k: v for k, v in id_counts.items() if v > 1}
    dup_digests = {k: v for k, v in digest_counts.items() if v > 1}

    audit = {
        "total_records": len(ids),
        "unique_record_ids": len(id_counts),
        "unique_full_digests": len(digest_counts),
        "duplicate_short_ids": dup_ids,
        "duplicate_full_digests": dup_digests,
        "collision_free_short_id": len(dup_ids) == 0,
        "collision_free_full_digest": len(dup_digests) == 0,
        "record_id_hex_length": len(ids[0]) if ids else 0,
    }
    with open(out / "record_id_audit.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(audit, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"record_id audit: {len(ids)} records, {len(id_counts)} unique short ids, "
          f"{len(dup_ids)} duplicates")


if __name__ == "__main__":
    main(sys.argv[1])
