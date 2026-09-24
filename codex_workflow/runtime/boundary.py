#!/usr/bin/env python3
"""Check supplied independent-review boundaries, not native locks or evidence truth.

No writes, discovery, persistence, network, model calls or native agent operations.
Use one existing capsule at review/repair/acceptance boundaries, not every command.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

IDENTITY = ("unit", "attempt", "contract", "candidate", "target")
MAX_INPUT_BYTES = 65536
MAX_GATES = 128
LIMITATION = "Supplied boundary consistency only; not authenticated authority, a lock, a test run or permission to release."


class BoundaryError(ValueError):
    pass


def _keys(value, required, optional=()):
    if not isinstance(value, dict) or set(value) != set(required) | (set(value) & set(optional)):
        raise BoundaryError("Unexpected or missing boundary fields")


def _text(value):
    if not isinstance(value, str) or not value or len(value) > 256 or any(ord(c) < 32 for c in value):
        raise BoundaryError("Expected a bounded nonempty identifier")
    return value


def validate(record: dict) -> None:
    _keys(record, {"schema", *IDENTITY, "primary", "writer", "reviewer", "hold", "gates"})
    if type(record["schema"]) is not int or record["schema"] != 1:
        raise BoundaryError("Unsupported boundary schema")
    for key in (*IDENTITY, "primary", "writer", "reviewer"):
        _text(record[key])
    if len({record[key] for key in ("primary", "writer", "reviewer")}) != 3:
        raise BoundaryError("Independent review requires distinct primary, writer and reviewer identities")
    if _text(record["hold"]) not in {"held", "released"}:
        raise BoundaryError("Hold must be held or released")
    gates = record["gates"]
    if not isinstance(gates, dict) or not 1 <= len(gates) <= MAX_GATES:
        raise BoundaryError("Supply a bounded nonempty authoritative gate map")
    for gate, fresh in gates.items():
        _text(gate)
        if type(fresh) is not bool:
            raise BoundaryError("Gate freshness obligations must be boolean")


def check(record: dict, action: str, actor: str, verdict: dict | None = None) -> dict:
    """Check one transition against an authoritative capsule and separate verdict.

    Records describe independent-review units only. A verdict cannot silently omit
    obligations or waive failures. Reused evidence is allowed only where fresh=False.
    """
    validate(record)
    _text(actor)
    if _text(action) not in {"write", "readback", "review", "accept"}:
        raise BoundaryError("Unknown boundary action")
    if verdict is not None and action != "accept":
        raise BoundaryError("Verdict is only applicable at acceptance")
    result = {"allowed": False, "action": action, "limitation": LIMITATION}
    if action == "readback":
        allowed = actor in {record[k] for k in ("primary", "writer", "reviewer")}
        return {**result, "allowed": allowed, "reason": "readback_only" if allowed else "actor_mismatch"}
    if action == "write":
        allowed = actor == record["writer"] and record["hold"] == "released"
        return {**result, "allowed": allowed,
                "reason": "writer_may_resume" if allowed else "writer_mismatch_or_candidate_held"}
    if action == "review":
        allowed = actor == record["reviewer"] and record["hold"] == "held"
        return {**result, "allowed": allowed,
                "reason": "review_may_start" if allowed else "reviewer_mismatch_or_hold_missing"}
    if actor != record["primary"] or record["hold"] != "held":
        return {**result, "reason": "acceptance_requires_primary_and_hold"}
    if verdict is None:
        return {**result, "reason": "independent_verdict_missing"}
    _keys(verdict, {*IDENTITY, "reviewer", "artifact", "gates"})
    for key in (*IDENTITY, "reviewer", "artifact"):
        _text(verdict[key])
    if any(verdict[key] != record[key] for key in (*IDENTITY, "reviewer")):
        return {**result, "reason": "stale_or_misattributed_verdict"}
    gates = verdict["gates"]
    if not isinstance(gates, dict) or set(gates) != set(record["gates"]):
        return {**result, "reason": "gate_map_mismatch"}
    rejected = []
    for gate, fresh in record["gates"].items():
        item = gates[gate]
        _keys(item, {"status", "evidence"})
        status = _text(item["status"])
        if status not in {"executed-pass", "reused-pass", "failed", "blocked", "unrun", "deferred", "not-applicable"}:
            raise BoundaryError("Unknown gate disposition")
        _text(item["evidence"])
        if status != "executed-pass" and not (status == "reused-pass" and not fresh):
            rejected.append(gate)
    return {**result, "allowed": not rejected, "reason": "consistent_acceptance_basis" if not rejected else "required_gates_unsatisfied",
            "rejected_gates": rejected}


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise BoundaryError("Duplicate JSON key")
        result[key] = value
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.input.is_symlink() or not args.input.is_file():
            raise BoundaryError("Input must be a regular file")
        with args.input.open("rb") as stream:
            data = stream.read(MAX_INPUT_BYTES + 1)
        if len(data) > MAX_INPUT_BYTES:
            raise BoundaryError("Input exceeds size limit")
        try:
            value = json.loads(data, object_pairs_hook=_pairs)
        except RecursionError as error:
            raise BoundaryError("JSON nesting exceeds parser limit") from error
        _keys(value, {"record", "action", "actor"}, {"verdict"})
        result = check(value["record"], value["action"], value["actor"], value.get("verdict"))
        print(json.dumps(result, sort_keys=True))
        return 0 if result["allowed"] else 1
    except (OSError, ValueError) as error:
        print(json.dumps({"allowed": False, "error": str(error), "limitation": LIMITATION}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
