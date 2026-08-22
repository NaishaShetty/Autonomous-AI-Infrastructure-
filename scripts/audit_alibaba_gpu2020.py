"""Verify Alibaba GPU2020 raw archive identity and immutable boundary."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/alibaba_gpu2020"
OUT = ROOT / "data/audit/alibaba_gpu2020_identity.json"
EXPECTED = {
    "pai_group_tag_table.tar.gz": "722fef30b7fb7aa50dabd79155614b5423a9d65cf45a9b26c590d57725423a14",
    "pai_instance_table.tar.gz": "1bf1e423a7ce3f8d086699801c362fd56a7182abdb234139e5ebbed97995ca06",
    "pai_job_table.tar.gz": "5aad7f7caac501136d14ed6a48e40546f825d7b0617a3a4f337e2348fe0a6cb0",
    "pai_machine_metric.tar.gz": "53ad917193d3b1dd0f3055e723148b1f36c2f81789b014ea2930a7875892eef5",
    "pai_machine_spec.tar.gz": "cc0d38a4045af1b1af8179de8b1b54b1ddd995e6160d6d061a6b1000f1276c2d",
    "pai_sensor_table.tar.gz": "9a0b82e8bdf3949281e4ba1423d9b4b34847e52799eecb138966de46da69c7a0",
    "pai_task_table.tar.gz": "cd1d6dc3215d2a8607ccf6b6dd952b5db776df86926c73259fea7c1499ac40e5",
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    actual = {name: digest(RAW / name) for name in EXPECTED}
    mismatches = {name: (EXPECTED[name], actual[name]) for name in EXPECTED if actual[name] != EXPECTED[name]}
    if mismatches:
        raise SystemExit(f"raw archive hash mismatch: {mismatches}")
    result = {"dataset_id": "alibaba_gpu2020", "raw_files": actual, "raw_files_immutable": all(not path.stat().st_mode & 0o222 for path in RAW.glob("pai_*.tar.gz")), "status": "verified"}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
