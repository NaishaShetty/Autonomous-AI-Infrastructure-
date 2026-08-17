"""FROZEN validation model for Active Phase 4.3.

Validation criteria are frozen BEFORE final dataset generation (Phase 4.3
brief section 13). Recovery success is never ``action executed == success``
-- ``src.recovery.environment.transition`` always routes through this
module's outcome vocabulary (``ValidatedOutcome``, schema.py) with an
explicit validation window and deterministic-given-seed rule, never a bare
boolean.
"""
from __future__ import annotations

VALIDATION_RULE_VERSION = "phase4_3_validation_v1"

# Validation window (seconds) allowed to elapse after an action before an
# outcome is scored -- fixed per the frozen protocol, not tuned per episode.
VALIDATION_WINDOW_SECONDS = 120.0

# An ESCALATE_TO_HUMAN action's automated validation window elapses before
# a human can plausibly close the incident in a controlled scenario -- by
# construction this always yields TIMEOUT (Phase 4.3 brief section 13:
# "required post-action observations" -- for escalation, none are produced
# within the automated window). This is a modeling decision, frozen here,
# not derived from data.
ESCALATE_ALWAYS_TIMES_OUT = True

# An action classified UNSAFE (src.recovery.actions.is_unsafe) that is
# actually selected and executed always resolves to ValidatedOutcome.UNSAFE,
# regardless of whether it would otherwise have "worked" -- safety
# classification, not success probability, determines this outcome
# (Phase 4.3 brief section 12: valid != safe).
UNSAFE_ACTION_ALWAYS_UNSAFE_OUTCOME = True
