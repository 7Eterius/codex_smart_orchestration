#!/usr/bin/env python3
"""Deterministic pre-handoff contradiction check over bounded supplied observations.

This helper reads one small JSON record. It does not scan source, inspect chat, authenticate
evidence, run tests, call a model, mutate files, or grant acceptance/authority. CLEAR means
only that none of the supported contradictions is present in the supplied record.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

MAX_INPUT_BYTES = 65536
MAX_ITEMS = 128
LIMITATION = (
    "CLEAR means no supported contradiction in supplied observations; "
    "it is not semantic correctness, evidence authenticity, coverage, authority or acceptance."
)
EVIDENCE = frozenset({
    "executed-pass", "reused-pass", "failed", "blocked", "unrun", "deferred",
    "not-applicable", "stale", "unverified",
})
DELIVERABLE = frozenset({"satisfied", "missing", "unchanged"})
FINDING = frozenset({"open", "addressed", "resolved"})
DECISION = frozenset({"resolved", "decision-needed"})
ORIGIN = frozenset({"owner", "concurrent", "unknown"})


class ChallengeError(ValueError):
    pass


def _pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ChallengeError("Duplicate JSON key")
        out[key] = value
    return out


def _keys(value, required, optional=()):
    if not isinstance(value, dict):
        raise ChallengeError("Expected an object")
    extra = set(value) - set(required) - set(optional)
    missing = set(required) - set(value)
    if extra or missing:
        raise ChallengeError("Unexpected or missing fields")


def _text(value, *, path=False):
    if not isinstance(value, str) or not value or len(value) > 512:
        raise ChallengeError("Expected a bounded nonempty string")
    if any(ord(char) < 32 for char in value):
        raise ChallengeError("Control characters are not allowed")
    if path and (value.startswith("/") or value.startswith("../") or "/../" in value or value == ".."):
        raise ChallengeError("Paths must be project-relative and cannot traverse upward")
    return value


def _bool(value):
    if type(value) is not bool:
        raise ChallengeError("Expected a boolean")
    return value


def _list(value):
    if not isinstance(value, list) or len(value) > MAX_ITEMS:
        raise ChallengeError("Expected a bounded list")
    return value


def _under(path, scopes):
    path = path.rstrip("/")
    return any(path == scope or path.startswith(scope + "/") for scope in scopes)


def _challenge(kind, reference, message):
    return {
        "status": "challenge",
        "class": kind,
        "reference": reference,
        "message": message,
        "limitation": LIMITATION,
    }


def check(record):
    _keys(record, {"schema", "unit", "owned_paths", "changes", "deliverables",
                   "findings", "evidence", "decisions"})
    if record["schema"] != 1:
        raise ChallengeError("Unsupported schema")
    unit = _text(record["unit"])
    scopes = []
    for raw in _list(record["owned_paths"]):
        path = _text(raw, path=True).rstrip("/")
        if not path:
            raise ChallengeError("Owned path cannot be project root")
        if path not in scopes:
            scopes.append(path)
    if not scopes:
        raise ChallengeError("At least one owned path is required")

    changes = []
    for row in _list(record["changes"]):
        _keys(row, {"path", "origin"})
        path = _text(row["path"], path=True)
        origin = _text(row["origin"])
        if origin not in ORIGIN:
            raise ChallengeError("Invalid change origin")
        changes.append((path, origin))
    for path, origin in changes:
        if origin == "owner" and not _under(path, scopes):
            return _challenge("scope-breach", path, "Owner-attributed change is outside owned paths.")
    for path, origin in changes:
        if origin == "unknown":
            return _challenge("attribution-unknown", path, "Changed path has unknown origin.")
        if origin == "concurrent" and _under(path, scopes):
            return _challenge("scope-conflict", path, "Concurrent change overlaps the owner's write scope.")

    for row in _list(record["decisions"]):
        _keys(row, {"id", "state"})
        ident = _text(row["id"])
        state = _text(row["state"])
        if state not in DECISION:
            raise ChallengeError("Invalid decision state")
        if state == "decision-needed":
            return _challenge("decision-needed", ident, "Protected judgment is unresolved.")

    for row in _list(record["deliverables"]):
        _keys(row, {"path", "required", "state"})
        path = _text(row["path"], path=True)
        required = _bool(row["required"])
        state = _text(row["state"])
        if state not in DELIVERABLE:
            raise ChallengeError("Invalid deliverable state")
        if required and state in {"missing", "unchanged"}:
            return _challenge("deliverable-" + state, path, "Required deliverable is not satisfied.")

    for row in _list(record["findings"]):
        _keys(row, {"id", "blocking", "state"})
        ident = _text(row["id"])
        blocking = _bool(row["blocking"])
        state = _text(row["state"])
        if state not in FINDING:
            raise ChallengeError("Invalid finding state")
        if blocking and state != "resolved":
            return _challenge("blocking-finding", ident, "Blocking finding is not resolved.")

    for row in _list(record["evidence"]):
        _keys(row, {"gate", "required", "fresh_required", "status"})
        gate = _text(row["gate"])
        required = _bool(row["required"])
        fresh = _bool(row["fresh_required"])
        status = _text(row["status"]).lower()
        if status not in EVIDENCE:
            raise ChallengeError("Invalid evidence status")
        if not required:
            continue
        if status == "failed":
            return _challenge("gate-failed", gate, "Required gate failed.")
        if status == "stale":
            return _challenge("evidence-stale", gate, "Required evidence is stale.")
        if status == "unverified":
            return _challenge("evidence-unverified", gate, "Required evidence is unverified.")
        if status in {"blocked", "unrun", "deferred", "not-applicable"}:
            return _challenge("gate-" + status, gate, "Required gate is not satisfied.")
        if fresh and status == "reused-pass":
            return _challenge("fresh-evidence-required", gate, "Required fresh gate cannot use reused evidence.")

    return {"status": "clear", "unit": unit, "limitation": LIMITATION}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path,
                        help="Private structured task/evidence JSON; source/chat are not scanned")
    args = parser.parse_args(argv)
    try:
        if args.input.is_symlink() or not args.input.is_file():
            raise ChallengeError("Input must be a regular file")
        with args.input.open("rb") as stream:
            raw = stream.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ChallengeError("Input exceeds size limit")
        try:
            record = json.loads(raw, object_pairs_hook=_pairs)
        except RecursionError as exc:
            raise ChallengeError("JSON nesting exceeds parser limit") from exc
        result = check(record)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] == "clear" else 1
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc), "limitation": LIMITATION},
                         sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
