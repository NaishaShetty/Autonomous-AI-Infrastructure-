"""Active Phase 4.1 -- Failure Memory & Experience Representation.

This package is a NEW, additive layer built on the current (post real-data
expansion, post revised-Phase-3) state of the repository. It does not
modify, import for mutation, or depend on the frozen historical
``src/experience/`` (old Phase 4.1) or ``src/patterns/`` (old Phase 4.2)
packages -- those remain untouched, historical artifacts. See
``docs/PHASE4_1_ACTIVE_FAILURE_EXPERIENCE.md`` for the full design
rationale, audit of what was reused vs. rebuilt, and why a new package name
was chosen instead of editing the old one in place.
"""
from .schema import FailureExperience

__all__ = ["FailureExperience"]
