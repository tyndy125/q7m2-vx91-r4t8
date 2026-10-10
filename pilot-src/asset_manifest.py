"""Pure deterministic renderer asset manifest validation. No private dependencies."""
from __future__ import annotations
from typing import Mapping, Tuple


def validate_manifest(entries: Mapping[str, str]) -> Tuple[Tuple[str, str], ...]:
    """Return stable ordered immutable pairs, rejecting ambiguous entries."""
    if not isinstance(entries, Mapping):
        raise TypeError("entries must be a mapping")
    ordered = []
    for key, value in entries.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError("asset identity must be non-empty")
        if not isinstance(value, str) or not value.strip():
            raise ValueError("asset reference must be non-empty")
        ordered.append((key, value))
    return tuple(sorted(ordered))
