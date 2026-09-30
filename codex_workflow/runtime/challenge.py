#!/usr/bin/env python3
"""Read-only preflight for supplied handoff facts, not semantic review or acceptance.

Legacy schema-1 records retain acceptance-strict behavior. Optional phase/current fields
add handoff readiness and evidence binding. --manifest reuses candidate.py for a fresh,
explicitly authorized local identity check. No model, test execution, writes or discovery.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import stat
import sys

if __package__:
    from .evidence import STATUSES as EVIDENCE, satisfies_gate
else:
    from evidence import STATUSES as EVIDENCE, satisfies_gate

MAX_INPUT_BYTES = 65536
MAX_ITEMS = 128
MAX_PREVIEW = 8
IDENTITY = frozenset({"attempt", "contract", "candidate", "target"})
LIMITATION = (
    "CLEAR means no supported contradiction in supplied observations; "
    "it is not semantic correctness, evidence authenticity, coverage, authority or acceptance. "
    "Omitted obligations and falsely recorded facts are not detected."
)
DELIVERABLE = frozenset({"satisfied", "missing", "unchanged"})
FINDING = frozenset({"open", "addressed", "resolved"})
DECISION = frozenset({"resolved", "decision-needed"})
ORIGIN = frozenset({"owner", "concurrent", "unknown"})
PHASES = frozenset({"handoff", "accept"})


class ChallengeError(ValueError):
    pass


def _keys(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise ChallengeError("Unexpected or missing fields")


def _text(value, *, path=False):
    if (not isinstance(value, str) or not value.strip() or len(value) > 512
            or any(ord(c) < 32 or 127 <= ord(c) <= 159 or 0xD800 <= ord(c) <= 0xDFFF for c in value)):
        raise ChallengeError("Expected bounded nonempty text without control characters")
    if path:
        # Reject ambiguous spellings rather than normalizing a possible scope escape.
        if (value != value.strip() or "\\" in value or ":" in value
                or any(p in {"", ".", "..", ".git"} for p in value.split("/"))):
            raise ChallengeError("Use canonical project-relative POSIX paths, no traversal or .git")
    return value


def _bool(value):
    if type(value) is not bool:
        raise ChallengeError("Expected a boolean")
    return value


def _enum(value, choices):
    value = _text(value)
    if value not in choices:
        raise ChallengeError("Invalid state")
    return value


def _list(value):
    if not isinstance(value, list) or len(value) > MAX_ITEMS:
        raise ChallengeError("Expected a bounded list")
    return value


def _identity(value):
    _keys(value, IDENTITY)
    for field in IDENTITY:
        _text(value[field])


def _validate(record):
    """Validate every row before evaluating anything, even after a known contradiction."""
    _keys(record, {"schema", "unit", "owned_paths", "changes", "deliverables", "findings", "evidence", "decisions"},
          {"phase", "current", "questions"})
    if type(record["schema"]) is not int or record["schema"] != 1:
        raise ChallengeError("Unsupported schema")
    _text(record["unit"])
    _enum(record.get("phase", "accept"), PHASES)
    if "current" in record:
        _identity(record["current"])
    scopes = _list(record["owned_paths"])
    for scope in scopes:
        _text(scope, path=True)
    if not scopes or len(set(scopes)) != len(scopes):
        raise ChallengeError("Owned paths must be nonempty and unique")
    definitions = {
        "changes": ({"path", "origin"}, set(), "path"),
        "deliverables": ({"path", "required", "state"}, {"allow_unchanged", "evidence", "basis"}, "path"),
        "findings": ({"id", "blocking", "state"}, {"evidence", "basis"}, "id"),
        "evidence": ({"gate", "required", "fresh_required", "status"}, {"due", "evidence", "basis"}, "gate"),
        "decisions": ({"id", "state"}, set(), "id"),
        "questions": ({"id", "state"}, {"answer", "evidence", "basis"}, "id"),
    }
    for section, (required, optional, key) in definitions.items():
        seen = set()
        for row in _list(record.get(section, [])):
            _keys(row, required, optional)
            ident = _text(row[key], path=key == "path")
            if ident in seen:
                raise ChallengeError("Duplicate identifier in " + section)
            seen.add(ident)
            for field in ("required", "blocking", "fresh_required", "allow_unchanged"):
                if field in row:
                    _bool(row[field])
            if "evidence" in row:
                _text(row["evidence"])
            if "basis" in row:
                _identity(row["basis"])
                if "current" not in record:
                    raise ChallengeError("Evidence basis requires current identity")
            if section == "changes":
                _enum(row["origin"], ORIGIN)
            elif section == "deliverables":
                _enum(row["state"], DELIVERABLE)
            elif section == "findings":
                _enum(row["state"], FINDING)
            elif section == "decisions":
                _enum(row["state"], DECISION)
            elif section == "questions":
                _enum(row["state"], {"answered", "unanswered", "unknown"})
                if "answer" in row:
                    _text(row["answer"])
            else:
                _enum(_text(row["status"]).lower(), EVIDENCE)
                _enum(row.get("due", "handoff"), PHASES)
                if "due" in row and "phase" not in record:
                    raise ChallengeError("Gate due stage requires explicit phase")


def _under(path, scopes):
    return any(path == scope or path.startswith(scope + "/") for scope in scopes)


def check(record):
    """Return a bounded batch and its routing, without modifying the supplied record."""
    _validate(record)
    phase, current = record.get("phase", "accept"), record.get("current")
    issues, pending = [], []

    def issue(kind, reference, message, route="worker"):
        issues.append({"class": kind, "reference": reference, "message": message, "route": route})

    def binding(row, reference, *, force=False):
        if not (current is not None or force):
            return True
        if not row.get("evidence") or (current is not None and "basis" not in row):
            issue("evidence-unverified", reference, "A current evidence reference/basis is missing.")
            return False
        if current is not None and row["basis"] != current:
            issue("evidence-stale", reference, "Recorded evidence belongs to another attempt/contract/candidate/target.")
            return False
        return True

    for row in record["changes"]:
        path, origin = row["path"], row["origin"]
        inside = _under(path, record["owned_paths"])
        if origin == "owner" and not inside:
            issue("scope-breach", path, "Owner-attributed change is outside scope; stop, preserve evidence, ask Main.", "main")
        elif origin == "unknown":
            issue("attribution-unknown", path, "Do not invent authorship or revert another owner's work.", "main")
        elif origin == "concurrent" and inside:
            issue("scope-conflict", path, "Concurrent work overlaps scope; reconcile ownership before writing.", "main")
    for row in record["decisions"]:
        if row["state"] == "decision-needed":
            issue("decision-needed", row["id"], "Protected judgment is unresolved.", "main")
    for row in record.get("questions", []):
        if row["state"] == "unknown":
            issue("decision-needed", row["id"], "Named question cannot be settled from available evidence.", "main")
        elif row["state"] == "unanswered" or not row.get("answer"):
            issue("question-unanswered", row["id"], "Return the requested answer or an explicit unknown.")
        else:
            binding(row, row["id"], force=True)
    for row in record["deliverables"]:
        if not row["required"]:
            continue
        if row["state"] == "missing":
            issue("deliverable-missing", row["path"], "Required deliverable is missing.")
        elif row["state"] == "unchanged" and not row.get("allow_unchanged", False):
            issue("deliverable-unchanged", row["path"], "Required change was not delivered.")
        else:
            binding(row, row["path"], force=row["state"] == "unchanged")
    for row in record["findings"]:
        if not row["blocking"]:
            continue
        if row["state"] == "resolved":
            binding(row, row["id"])
        elif row["state"] == "addressed" and phase == "handoff":
            if binding(row, row["id"], force=True):
                pending.append({"kind": "finding", "id": row["id"], "status": "addressed-awaiting-review"})
        else:
            issue("blocking-finding", row["id"], "Blocking finding still needs repair or authorized resolution.",
                  "main" if row["state"] == "addressed" else "worker")
    for row in record["evidence"]:
        if not row["required"]:
            continue
        gate, status = row["gate"], row["status"].lower()
        if phase == "handoff" and row.get("due", "handoff") == "accept":
            # A gate that is merely not due yet stays pending. A known failure on the
            # current candidate is already actionable and must not consume reviewer work.
            if status == "failed":
                if binding(row, gate):
                    issue("gate-failed", gate, "Acceptance-stage gate already failed; repair before review.")
            else:
                pending.append({"kind": "gate", "id": gate, "status": "pending-acceptance-check",
                                "reported_status": status})
            continue
        if status == "stale":
            issue("evidence-stale", gate, "Required evidence is stale.")
        elif status == "unverified":
            issue("evidence-unverified", gate, "Required evidence is unverified.")
        elif status not in {"executed-pass", "reused-pass"}:
            issue("gate-" + status, gate, "Required gate is not satisfied.")
        elif not satisfies_gate(status, row["fresh_required"]):
            issue("fresh-evidence-required", gate, "Required fresh gate cannot reuse a verdict.")
        else:
            binding(row, gate)
    count = (sum(d["required"] for d in record["deliverables"])
             + sum(g["required"] for g in record["evidence"])
             + sum(f["blocking"] for f in record["findings"])
             + len(record["decisions"]) + len(record.get("questions", [])))
    if not count:
        issue("obligations-unverified", record["unit"], "No acceptance obligations were supplied.", "main")
    result = {"unit": record["unit"], "phase": phase,
              "pending": pending[:MAX_PREVIEW], "pending_count": len(pending),
              "omitted_pending": max(0, len(pending) - MAX_PREVIEW),
              "identity_checked": current is not None, "limitation": LIMITATION}
    return _render_issues(result, issues)


def _render_issues(result, issues, *, total=None):
    """Keep the issue that requires Main visible, including after manifest drift.

    Preserve category/input order within each route. A bounded preview must not ask
    Main for a decision while hiding every issue that actually requires that decision.
    The caller may supply the full count when augmenting an already bounded result.
    """
    ordered = sorted(issues, key=lambda item: item["route"] != "main")
    count = len(issues) if total is None else total
    result.update(status="challenge" if count else "clear", issues=ordered[:MAX_PREVIEW],
                  issue_count=count, omitted_issues=max(0, count - MAX_PREVIEW))
    if ordered:
        first = ordered[0]
        result.update({key: first[key] for key in ("class", "reference", "message")})
        result["next_action"] = "decision-needed" if first["route"] == "main" else "repair-or-refresh"
    else:
        result["next_action"] = ("return-for-required-review" if result["phase"] == "handoff"
                                 else "main-assess-original-evidence")
    return result


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ChallengeError("Duplicate JSON key")
        result[key] = value
    return result


def _nonfinite(value):
    raise ChallengeError("Non-finite JSON numbers are not accepted")


def read_record(path):
    if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
        raise ChallengeError("Input must be a regular file")
    with path.open("rb") as stream:
        raw = stream.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise ChallengeError("Input exceeds size limit")
    try:
        value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_nonfinite)
    except RecursionError as exc:
        raise ChallengeError("JSON nesting exceeds parser limit") from exc
    _validate(value)
    return value


def verify_manifest(record, path):
    """Reuse the existing identity helper; do not infer scope, provenance or coverage."""
    _validate(record)
    if "current" not in record:
        raise ChallengeError("--manifest requires current candidate identity")
    try:
        from . import candidate
    except ImportError:
        import candidate
    manifest = candidate.read_manifest(path)
    if manifest["fingerprint"] != record["current"]["candidate"]:
        raise ChallengeError("Manifest does not identify the declared current candidate")
    observed = candidate.verify(manifest)
    return {"matched": observed["matched"], "expected": observed["expected"],
            "observed": observed["observed"], "limitation": candidate.LIMITATION}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, help="Optional existing candidate.py manifest; fresh read, no writes")
    args = parser.parse_args(argv)
    try:
        record = read_record(args.input)
        result = check(record)
        if args.manifest is not None:
            identity = verify_manifest(record, args.manifest)
            result["local_identity"] = identity
            if not identity["matched"]:
                drift = {"class": "evidence-stale", "reference": record["unit"],
                         "message": "Explicit candidate inputs changed; preserve findings and refresh affected evidence.",
                         "route": "worker"}
                _render_issues(result, [drift] + result["issues"], total=result["issue_count"] + 1)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] == "clear" else 1
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc), "limitation": LIMITATION}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
