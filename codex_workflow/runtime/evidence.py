"""Shared gate vocabulary and satisfaction rule; not evidence authentication.

Keep parsing separate from acceptance. A recognized negative/unknown disposition is a
valid observation that does not satisfy a gate, not a malformed protocol message.
"""
from __future__ import annotations

STATUSES = frozenset({"executed-pass", "reused-pass", "failed", "blocked", "unrun",
                      "deferred", "not-applicable", "stale", "unverified"})


def normalize_status(value: str) -> str:
    """Accept the documented case-insensitive vocabulary, never invented statuses."""
    if not isinstance(value, str) or value.lower() not in STATUSES:
        raise ValueError("Unknown gate disposition")
    return value.lower()


def satisfies_gate(status: str, fresh_required: bool) -> bool:
    """A supplied PASS satisfies freshness only; authenticity/coverage stay external."""
    if type(fresh_required) is not bool:
        raise ValueError("Gate freshness obligation must be boolean")
    status = normalize_status(status)
    return status == "executed-pass" or (status == "reused-pass" and not fresh_required)
