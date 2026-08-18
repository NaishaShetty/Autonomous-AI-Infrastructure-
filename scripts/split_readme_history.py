"""One-shot mechanical splitter: extracts each concatenated historical
document out of README.md into its own file under docs/, verbatim.

Not part of the ongoing test suite -- a migration script, run once. Kept
in scripts/ for the record (shows exactly how the split was performed,
mechanically, with no rewording).
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
DOCS = ROOT / "docs"

ANCHOR_RE = re.compile(r'^<a id="([^"]+)"></a>$')
ORIGINAL_FILE_RE = re.compile(r'^\*\*Original file:\*\* `([^`]+)`\s*$')

# The one section with no "Original file:" banner (it's a results
# document, not a concatenated original doc) -- named per the README's
# own top-of-file note ("what used to be the separate
# docs/PHASE4_2_ACTIVE_FAILURE_PATTERNS.md").
FALLBACK_NAMES = {
    "active-phase-42--failure-pattern-learning-real-data-foundation": "PHASE4_2_ACTIVE_FAILURE_PATTERNS.md",
}


def main() -> None:
    text = README.read_text(encoding="utf-8")
    lines = text.split("\n")

    anchor_line_idxs = [i for i, l in enumerate(lines) if ANCHOR_RE.match(l)]
    assert len(anchor_line_idxs) == 33, f"expected 33 anchors (1 wrapper + 32 docs), found {len(anchor_line_idxs)}"

    # First anchor is the "project-history" wrapper -- not a document to
    # split out on its own; the 30 real documents start at the 2nd anchor.
    doc_anchor_idxs = anchor_line_idxs[1:]

    # The section body for each doc runs from its anchor line to just
    # before the "\n\n---\n\n" that precedes the NEXT anchor (or EOF for
    # the last section).
    boundaries = []
    for k, start in enumerate(doc_anchor_idxs):
        if k + 1 < len(doc_anchor_idxs):
            next_start = doc_anchor_idxs[k + 1]
            # walk back over the blank/---/blank/blank separator
            # immediately before the next anchor (verified empirically:
            # TWO blank lines precede "---", one follows it)
            end = next_start
            assert lines[end - 1] == "", f"expected blank line before anchor at {next_start}"
            assert lines[end - 2] == "---", f"expected '---' before anchor at {next_start}, got {lines[end-2]!r}"
            assert lines[end - 3] == "", f"expected blank line before '---' at {next_start}"
            assert lines[end - 4] == "", f"expected second blank line before '---' at {next_start}"
            end = end - 4  # exclusive end index (line AFTER last content line)
        else:
            end = len(lines)
            # trim trailing blank lines at EOF
            while end > start and lines[end - 1] == "":
                end -= 1
        boundaries.append((start, end))

    manifest = []
    written_files = set()
    for start, end in boundaries:
        anchor_id = ANCHOR_RE.match(lines[start]).group(1)
        section_lines = lines[start:end]

        original_file = None
        for l in section_lines[:6]:
            m = ORIGINAL_FILE_RE.match(l)
            if m:
                original_file = m.group(1)
                break

        if original_file:
            filename = Path(original_file).name  # drop any docs/ prefix, flatten to docs/
        else:
            filename = FALLBACK_NAMES[anchor_id]

        assert filename not in written_files, f"duplicate target filename {filename}"
        written_files.add(filename)

        content = "\n".join(section_lines) + "\n"
        out_path = DOCS / filename
        out_path.write_text(content, encoding="utf-8")
        manifest.append({
            "anchor": anchor_id, "filename": filename,
            "start_line_1indexed": start + 1, "end_line_1indexed": end,
            "n_lines": end - start,
        })
        print(f"wrote docs/{filename}  (lines {start+1}-{end}, {end-start} lines)")

    # --- reconstruction check ---
    # Reconstruct the span from the first doc anchor to EOF by re-joining
    # each written file's content with the exact "\n\n---\n\n" separator
    # used between sections in the original, and diff against the
    # original README slice.
    original_span = "\n".join(lines[doc_anchor_idxs[0]:]).rstrip("\n") + "\n"
    parts = []
    for filename in [m["filename"] for m in manifest]:
        parts.append((DOCS / filename).read_text(encoding="utf-8").rstrip("\n"))
    reconstructed = ("\n\n\n---\n\n".join(parts)).rstrip("\n") + "\n"

    recon_path = ROOT / "scripts" / "_reconstructed_history_span.md"
    recon_path.write_text(reconstructed, encoding="utf-8")
    orig_path = ROOT / "scripts" / "_original_history_span.md"
    orig_path.write_text(original_span, encoding="utf-8")

    print(f"\nwrote {len(manifest)} files")
    print(f"original span: {len(original_span)} bytes -> scripts/_original_history_span.md")
    print(f"reconstructed: {len(reconstructed)} bytes -> scripts/_reconstructed_history_span.md")
    print("identical:" , original_span == reconstructed)


if __name__ == "__main__":
    main()
