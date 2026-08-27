"""Generates SHA256_MANIFEST.json over every file currently in a run
directory. Run this LAST, after every other artifact has been written --
the manifest itself is excluded from its own hash listing.

Usage:
    python scripts/generate_sha256_manifest.py <run_dir>
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def main(run_dir: Path) -> None:
    manifest = {}
    for path in sorted(run_dir.rglob("*")):
        if path.is_file() and path.name != "SHA256_MANIFEST.json":
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest[str(path.relative_to(run_dir)).replace("\\", "/")] = digest
    out = {"run_dir": str(run_dir), "n_files": len(manifest), "sha256": manifest}
    (run_dir / "SHA256_MANIFEST.json").write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote SHA256_MANIFEST.json covering {len(manifest)} files")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
