# Phase 6.7 — Research Write-up Audit

## What was created

`docs/paper/Autonomous_AI_Infrastructure_Research_Report.md` — 27 sections
(abstract through citation), matching the exact outline given in the
Phase 6 brief.

## Negative/limited findings preserved (explicit check)

Every item required to be preserved was checked present, in its own
section, not folded into a generic claim:

| Finding | Section |
|---|---|
| Sentiment near-chance discrimination ceiling, 4 rank-equivalent estimators | §6 |
| Failure-memory signal did not beat confidence alone (Phase 2) | §7 |
| Memory ON/OFF repeated-incident result AND the separate 300-episode no-difference finding, reported side by side | §8 |
| 3 of 4 prediction classes NOT VALIDATED (always-fires), all 4 NOT_EVALUABLE at record level | §9 |
| Diagnosis accuracy 1.0 always paired with false-causal-attribution-rate 1.0 | §10 |
| Recovery success 0/35 on benchmark slice | §11 |
| Ranking generalization vs. operating-point generalization kept as two distinct claims | §12 |
| Phase 4.3/4.4 both "hypothesis not supported", exploratory amendment explicitly marked non-reopening | §13 |
| No model repository published, with reasoning | §17 |
| Full capability-matrix status counts (0/6/3/0/7) | §16 |

## Cross-checks against source artifacts

Every number in the report was pulled from the same two authoritative
sources used for the README (`docs/MASTER_RECORD_CONTENT.md`,
`BENCHMARK_CARD.md`/`DATASET_CARD.md`), not re-derived independently or
copied from the README without re-checking — the report's §9 (prediction)
and §11 (recovery) numbers were checked directly against
`MASTER_RECORD_CONTENT.md` §13, §17, §19 line by line during drafting.

## No new claims, no collapsed findings

The report does not use the phrase "AI reliability" or any equivalent
umbrella claim to describe uncertainty, prediction, diagnosis, recovery,
and learning collectively — each is its own numbered section with its own
status. §18 ("Threats to validity") and §23 ("Limitations vs. future
work", which explicitly points to the README section rather than
duplicating it, to avoid the two documents drifting apart over time) keep
limitations separated from the results sections rather than mixed in.

## PDF conversion

**Not attempted.** No PDF-generation toolchain (pandoc, a LaTeX
distribution, wkhtmltopdf, etc.) was confirmed already installed and
working in this environment during this phase, and the Phase 6 brief is
explicit that Markdown is the primary source and a PDF should only be
produced "if you find a working toolchain already available" — none was
found, so none was fabricated or claimed. The Markdown file is the
canonical, complete document.

## Conclusion

The research write-up satisfies the 27-section outline, preserves every
required negative/underpowered finding in its own section, and every
number in it traces to the same two audited sources used elsewhere in
Phase 6.
