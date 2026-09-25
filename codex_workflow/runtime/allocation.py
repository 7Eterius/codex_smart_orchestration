#!/usr/bin/env python3
"""Pure allocation and lifecycle checks for Smart 2.4, not a Codex tool adapter.

Inputs are caller-supplied classifications/observations. No source scan, persistence,
network, model call, process control or automatic close/spawn is performed here.
An allowed plan is not proof that the client executed it or that evidence is fresh.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROLES = frozenset({"simple_executor", "routine_executor", "default_executor",
                   "senior_executor", "tester", "companion", "investigator", "archivist"})
REVIEW_OWNERS = frozenset({"routine_executor", "default_executor"})
WRITERS = frozenset({"simple_executor", "routine_executor", "default_executor", "senior_executor"})
SMART_OPEN_LIMIT = 2
LIMITATION = "Advisory policy from supplied observations, not native enforcement or a correctness/cost guarantee."
MAX_INPUT_BYTES = 65536
MAX_THREADS = 128


class AllocationError(ValueError):
    pass


def _keys(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise AllocationError("Unexpected or missing fields")


def _bool(value):
    if type(value) is not bool:
        raise AllocationError("Expected a boolean, not a truthy value")
    return value


def _text(value):
    if not isinstance(value, str) or not value or len(value) > 256 or any(ord(c) < 32 for c in value):
        raise AllocationError("Expected a bounded nonempty identifier")
    return value


def classify(task: dict) -> dict:
    """Choose a responsibility, never a Normal/Coordinated mode.

    Risk and judgment override the cheap lane. Unknown/ambiguous intent is resolved
    before mutation. Field count and click count intentionally do not affect routing.
    Tiny settled execution is still delegated; it is not a main-writing exception.
    """
    _keys(task, {"kind", "risk", "settled", "tiny", "deep", "independent_required"})
    kind = _text(task["kind"])
    if kind not in {"answer", "judgment", "operation", "implementation", "verification", "discovery", "memory"}:
        raise AllocationError("Unrecognized assignment kind")
    if _text(task["risk"]) not in {"low", "material", "critical"}:
        raise AllocationError("Unrecognized risk")
    for name in ("settled", "tiny", "deep", "independent_required"):
        _bool(task[name])
    if task["tiny"] and task["deep"]:
        raise AllocationError("Tiny and deep are contradictory")
    review = task["independent_required"] or task["risk"] != "low"
    if kind == "judgment" or not task["settled"]:
        role, reason = "main", "resolve_judgment_or_contract"
    elif kind == "answer":
        role, reason = "main", "answer_without_team"
    elif kind == "verification":
        role, reason = "tester", "verification_without_writer"
    elif kind == "discovery":
        role, reason = ("investigator", "deep_evidence_gap") if task["deep"] else ("companion", "targeted_discovery")
    elif kind == "memory":
        role, reason = "archivist", "authorized_checkpoint_only"
    elif task["deep"]:
        role, reason, review = "default_executor", "deep_bounded_work", True
    elif task["risk"] == "low" and (kind == "operation" or task["tiny"]):
        role, reason = "simple_executor", "explicit_low_risk_work"
    else:
        role, reason = "routine_executor", "settled_work_default"
    # Verification is already independent work; it must not spawn another reviewer.
    reviewer = "tester" if review and kind in {"implementation", "operation"} else None
    return {"owner": role, "reviewer": reviewer, "reason": reason,
            "limitation": LIMITATION}


def _inventory(obs: dict):
    _keys(obs, {"caller", "cap", "complete", "close_supported", "threads"}, {"primary"})
    primary = _text(obs.get("primary", "main"))
    caller = _text(obs["caller"])
    cap = obs["cap"]
    if cap is not None and (type(cap) is not int or not 1 <= cap <= MAX_THREADS):
        raise AllocationError("Cap must be a positive bounded integer or null")
    _bool(obs["complete"])
    _bool(obs["close_supported"])
    if not isinstance(obs["threads"], list) or len(obs["threads"]) > MAX_THREADS:
        raise AllocationError("Thread inventory too large or malformed")
    entries = {}
    for thread in obs["threads"]:
        _keys(thread, {"id", "parent", "unit", "role", "state", "owned", "retain", "durable", "released_resources"},
              {"closure_evidence", "review_authorized"})
        for key in ("id", "parent", "unit", "role"):
            _text(thread[key])
        if thread["id"] in entries or thread["id"] == thread["parent"] or thread["id"] == primary:
            raise AllocationError("Duplicate/self-parented thread or primary included as a spawned thread")
        # Existing unknown/legacy/external roles still consume slots.
        if _text(thread["state"]) not in {"running", "waiting", "completed", "closing", "closed", "unknown"}:
            raise AllocationError("Invalid lifecycle state")
        for key in ("owned", "retain", "durable", "released_resources"):
            _bool(thread[key])
        if "review_authorized" in thread:
            _bool(thread["review_authorized"])
        if "closure_evidence" in thread:
            _text(thread["closure_evidence"])
        if thread["state"] == "closed" and not thread.get("closure_evidence"):
            raise AllocationError("Closed needs an observed native result reference, not a final message")
        entries[thread["id"]] = thread
    for ident in entries:
        visited = set()
        current = ident
        while current in entries:
            if current in visited:
                raise AllocationError("Cyclic thread parents")
            visited.add(current)
            current = entries[current]["parent"]
    open_threads = {k: t for k, t in entries.items() if t["state"] != "closed"}
    closable = sorted(t["id"] for t in open_threads.values()
                      if t["parent"] == caller and t["owned"] and t["state"] == "completed"
                      and not t["retain"] and t["durable"] and t["released_resources"]
                      and not any(c["parent"] == t["id"] for c in open_threads.values()))
    return cap, entries, open_threads, closable


def next_action(obs: dict, request: dict) -> dict:
    """Check a prospective action; observations are not authenticated capabilities.

    ``primary`` defaults only to the literal legacy ID "main". Real handles should
    supply it explicitly. Reuse defaults to work; readback must be requested and
    grants no write authority. Cleanup is distinct from new-work authorization.
    """
    _keys(request, {"unit", "role", "reserve", "reuse_id", "spawn_failed", "state_changed"},
          {"intent"})
    unit = _text(request["unit"])
    role = _text(request["role"])
    if role not in ROLES:
        raise AllocationError("Requested role is not a Smart role")
    intent = _text(request.get("intent", "work"))
    if intent not in {"work", "readback", "cleanup"}:
        raise AllocationError("Intent must be work, readback or cleanup")
    if type(request["reserve"]) is not int or request["reserve"] not in (0, 1):
        raise AllocationError("Reserve must be zero or one review slot")
    for key in ("spawn_failed", "state_changed"):
        _bool(request[key])
    if request["reuse_id"] is not None:
        _text(request["reuse_id"])
    if intent == "readback" and (request["reuse_id"] is None or request["reserve"] != 0):
        raise AllocationError("Readback requires an existing handle and no reserved slot")
    if intent == "cleanup" and (request["reuse_id"] is not None or request["reserve"] != 0):
        raise AllocationError("Cleanup cannot reuse work or reserve capacity")
    cap, entries, opened, closable = _inventory(obs)
    result = {"action": "inspect", "reason": "incomplete_inventory", "open_count": len(opened),
              "cap": cap, "limitation": LIMITATION}
    if not obs["complete"]:
        return result
    primary = obs.get("primary", "main")
    caller = entries.get(obs["caller"])
    if obs["caller"] != primary:
        if caller is None or not caller["owned"]:
            raise AllocationError("Caller must be the declared primary or a known owned thread")
        if caller["state"] not in {"running", "waiting", "completed"}:
            raise AllocationError("Caller lifecycle does not permit work or cleanup")

    def cleanup():
        if closable and obs["close_supported"]:
            return {**result, "action": "close", "reason": "release_completed_children", "ids": closable,
                    "then": "reobserve; closure requested is not closure observed"}
        return None

    # A completed/retired owner may release eligible direct children, but cannot
    # dispatch new work. A next-unit request must not prevent old-child cleanup.
    if intent == "cleanup":
        return cleanup() or {**result, "action": "wait", "reason": "no_supported_cleanup"}
    reuse = entries.get(request["reuse_id"])
    if request["reuse_id"] is None:
        same = [t for t in opened.values() if t["owned"] and t["unit"] == unit and t["role"] == role]
        if not same:
            released = cleanup()
            if released is not None:
                return released
    if caller is not None:
        if (caller["state"] not in {"running", "waiting"}
                or caller["role"] not in REVIEW_OWNERS or role != "tester"
                or caller["unit"] != unit or not caller.get("review_authorized", False)):
            raise AllocationError("New review work requires an active same-unit owner with explicit review authority")
    if request["reuse_id"] is not None:
        if (reuse is None or not reuse["owned"] or reuse["parent"] != obs["caller"]
                or reuse["role"] != role or reuse["unit"] != unit
                or reuse["state"] not in {"completed", "waiting"}):
            raise AllocationError("Reuse requires a stopped same-unit owned direct child with matching role")
    # Apply the same writer exclusion to spawning AND reactivating a writer.
    # Even a stopped other writer retains ownership until explicitly released.
    if intent == "work" and role in WRITERS and any(
            t["owned"] and t["unit"] == unit and t["role"] in WRITERS
            and t["id"] != request["reuse_id"] for t in opened.values()):
        if request["reuse_id"] is None and any(
                t["owned"] and t["unit"] == unit and t["role"] == role for t in opened.values()):
            return {**result, "action": "wait", "reason": "assignment_already_open"}
        return {**result, "action": "wait", "reason": "existing_writer_requires_explicit_transfer"}
    if reuse is not None:
        return {**result, "action": "reuse", "reason": "readback_only" if intent == "readback" else "same_unit_delta",
                "id": reuse["id"], "intent": intent}
    if any(t["owned"] and t["unit"] == unit and t["role"] == role for t in opened.values()):
        return {**result, "action": "wait", "reason": "assignment_already_open"}
    if request["spawn_failed"] and not request["state_changed"]:
        return {**result, "action": "blocked", "reason": "no_blind_spawn_retry"}
    if cap is None:
        return {**result, "reason": "capacity_unknown"}
    required = 1 + request["reserve"]
    if sum(t["owned"] for t in opened.values()) + required > SMART_OPEN_LIMIT:
        return {**result, "action": "blocked", "reason": "smart_open_thread_budget", "required_free": required}
    if cap - len(opened) < required:
        return {**result, "action": "blocked", "reason": "insufficient_open_thread_budget", "required_free": required}
    return {**result, "action": "spawn", "reason": "budget_available", "role": role,
            "reserve": request["reserve"]}


def review_host(*, nested_observed: bool, owner_role: str, free_slots: int, close_supported: bool) -> str:
    """Same reviewer contract, different dispatcher when nesting isn't established."""
    _bool(nested_observed)
    _bool(close_supported)
    if _text(owner_role) not in ROLES or type(free_slots) is not int or free_slots < 0:
        raise AllocationError("Invalid review-host inputs")
    if free_slots == 0:
        return "release_completed_owner_then_main" if close_supported else "blocked"
    return "owner" if nested_observed and owner_role in REVIEW_OWNERS and close_supported else "main"


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AllocationError("Duplicate JSON key")
        result[key] = value
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Small private observation JSON; not a log archive")
    args = parser.parse_args(argv)
    try:
        if args.input.is_symlink() or not args.input.is_file():
            raise AllocationError("Input must be a regular file")
        with args.input.open("rb") as stream:
            data = stream.read(MAX_INPUT_BYTES + 1)
        if len(data) > MAX_INPUT_BYTES:
            raise AllocationError("Input exceeds size limit")
        try:
            value = json.loads(data, object_pairs_hook=_pairs)
        except RecursionError as error:
            raise AllocationError("JSON nesting exceeds parser limit") from error
        _keys(value, {"observation", "request"})
        result = next_action(value["observation"], value["request"])
        print(json.dumps(result, sort_keys=True))
        return 0 if result["action"] in {"spawn", "reuse", "close"} else 1
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"action": "blocked", "error": str(exc), "limitation": LIMITATION}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
