"""Phase 5.4 benchmark implementation of the frozen Phase 5.3 contract.

Read-only with respect to Phase 4, Phase 5.1, Phase 5.2 (canonical dataset),
and Phase 5.3 (specification). This package consumes those artifacts; it
does not modify them.
"""

from .constants import (
    BENCHMARK_VERSION,
    DATASET_VERSION,
    IMPLEMENTATION_VERSION,
    SCHEMA_VERSION,
)

__all__ = [
    "BENCHMARK_VERSION",
    "DATASET_VERSION",
    "IMPLEMENTATION_VERSION",
    "SCHEMA_VERSION",
]
