"""Strict ownership-marker parsing for the global Smart installer."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ValidationError


@dataclass(frozen=True)
class Marker:
    start: str
    end: str


# Keep the established marker pair so existing global installations update in place.
USER_MANAGED = Marker(
    "<!-- codex-workflow-user-managed-start -->",
    "<!-- codex-workflow-user-managed-end -->",
)


def _bounds(text: str, marker: Marker) -> tuple[int, int]:
    if text.count(marker.start) != 1 or text.count(marker.end) != 1:
        raise ValidationError(
            f"expected exactly one marker pair: {marker.start} / {marker.end}"
        )
    start = text.index(marker.start) + len(marker.start)
    end = text.index(marker.end)
    if start > end:
        raise ValidationError(f"marker end precedes start: {marker.start}")
    return start, end


def extract(text: str, marker: Marker) -> str:
    start, end = _bounds(text, marker)
    body = text[start:end]
    if body.startswith("\n"):
        body = body[1:]
    if body.endswith("\n"):
        body = body[:-1]
    return body


def replace(text: str, marker: Marker, body: str) -> str:
    start, end = _bounds(text, marker)
    normalized = body.strip("\n")
    replacement = "\n" + normalized + "\n" if normalized else "\n"
    return text[:start] + replacement + text[end:]


def append_region(text: str, marker: Marker, body: str) -> str:
    if marker.start in text or marker.end in text:
        raise ValidationError(f"partial or unexpected marker already present: {marker.start}")
    prefix = text.rstrip() + "\n\n" if text.strip() else ""
    normalized = body.strip("\n")
    middle = f"\n{normalized}\n" if normalized else "\n"
    return prefix + marker.start + middle + marker.end + "\n"
