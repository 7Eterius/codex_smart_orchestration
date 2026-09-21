#!/usr/bin/env python3
"""On-demand local usage accounting. No network or model calls.

Read cumulative counters in file order, use pre-window baselines, and reject
ambiguous/missing evidence instead of summing stale last_token_usage snapshots.
The Rollouts compatibility label means reconciled usage updates, not API requests.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


DEPLOYMENT_ID = re.compile(r"^[a-z0-9][a-z0-9_]{0,63}$")
MARKER_PREFIX = "codex-workflow-deployment-start:"


class ReportError(ValueError):
    """Raised when rollout evidence cannot support a trustworthy report."""


@dataclass(frozen=True)
class Session:
    session_id: str
    path: Path
    timestamp: datetime
    parent_id: str | None
    task_name: str | None
    role: str | None
    forked_from_id: str | None = None


@dataclass
class Usage:
    rollouts: int = 0
    cached_input_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    def add(self, other: "Usage") -> None:
        self.rollouts += other.rollouts
        self.cached_input_tokens += other.cached_input_tokens
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens


@dataclass
class Row:
    agent: str
    quantity: int
    usage: Usage
    first_activity: datetime


def parse_time(raw: str, *, field: str) -> datetime:
    if not isinstance(raw, str) or not raw:
        raise ReportError(f"{field} must be a non-empty RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as error:
        raise ReportError(f"invalid {field}: {raw!r}") from error
    if parsed.tzinfo is None:
        raise ReportError(f"{field} must include a timezone: {raw!r}")
    return parsed.astimezone(timezone.utc)


def iter_jsonl(path: Path, warnings: list[str]) -> Iterator[dict[str, Any]]:
    try:
        with path.open("rb") as stream:
            line_number = 0
            while True:
                line = stream.readline()
                if not line:
                    break
                line_number += 1
                try:
                    value = json.loads(line)
                except (UnicodeDecodeError, json.JSONDecodeError) as error:
                    if not line.endswith(b"\n"):
                        warnings.append(
                            f"ignored incomplete trailing record in {path.name}"
                        )
                        break
                    raise ReportError(
                        f"malformed JSONL record {path.name}:{line_number}"
                    ) from error
                if not isinstance(value, dict):
                    raise ReportError(
                        f"JSONL record is not an object: {path.name}:{line_number}"
                    )
                yield value
    except OSError as error:
        raise ReportError(f"cannot read rollout {path}: {error}") from error


def session_from_path(path: Path, warnings: list[str]) -> Session | None:
    for index, record in enumerate(iter_jsonl(path, warnings)):
        if record.get("type") != "session_meta":
            if index >= 127:
                break
            continue
        payload = record.get("payload")
        if not isinstance(payload, dict):
            raise ReportError(f"invalid session metadata in {path.name}")
        session_id = payload.get("id") or payload.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ReportError(f"session metadata has no ID in {path.name}")
        timestamp = parse_time(
            payload.get("timestamp") or record.get("timestamp"),
            field=f"session timestamp in {path.name}",
        )
        parent_id = task_name = role = None
        source = payload.get("source")
        if isinstance(source, dict):
            subagent = source.get("subagent")
            if isinstance(subagent, dict):
                spawn = subagent.get("thread_spawn")
                if isinstance(spawn, dict):
                    parent_id = _optional_string(spawn.get("parent_thread_id"))
                    task_name = _optional_string(spawn.get("agent_path"))
                    role = _optional_string(spawn.get("agent_role"))
        return Session(session_id, path, timestamp, parent_id, task_name, role,
                       _optional_string(payload.get("forked_from_id")))
    return None


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def build_index(sessions_root: Path, warnings: list[str]) -> dict[str, Session]:
    if not sessions_root.is_dir():
        raise ReportError(f"Codex sessions directory is missing: {sessions_root}")
    result: dict[str, Session] = {}
    for path in sessions_root.rglob("*.jsonl"):
        if not path.is_file():
            continue
        session = session_from_path(path, warnings)
        if session is None:
            continue
        previous = result.get(session.session_id)
        if previous is not None and previous.path != session.path:
            raise ReportError(f"duplicate rollout session ID: {session.session_id}")
        result[session.session_id] = session
    return result


def message_texts(
    record: dict[str, Any], *, roles: frozenset[str]
) -> Iterable[str]:
    if record.get("type") != "response_item":
        return ()
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return ()
    if payload.get("type") != "message" or payload.get("role") not in roles:
        return ()
    content = payload.get("content")
    if not isinstance(content, list):
        return ()
    return tuple(
        item.get("text")
        for item in content
        if isinstance(item, dict)
        and item.get("type") in {"input_text", "output_text"}
        and isinstance(item.get("text"), str)
    )


def user_texts(record: dict[str, Any]) -> Iterable[str]:
    return message_texts(record, roles=frozenset({"user"}))


def record_time(record: dict[str, Any], *, path: Path) -> datetime:
    return parse_time(record.get("timestamp"), field=f"record timestamp in {path.name}")


def find_boundary(
    root: Session, deployment_id: str, warnings: list[str]
) -> datetime:
    marker = f"{MARKER_PREFIX} {deployment_id}"
    marker_pattern = re.compile(re.escape(marker) + r"(?![a-z0-9_])")
    marker_times: list[datetime] = []
    for record in iter_jsonl(root.path, warnings):
        texts = message_texts(record, roles=frozenset({"assistant"}))
        if any(marker_pattern.search(text) for text in texts):
            marker_times.append(record_time(record, path=root.path))
    if not marker_times:
        raise ReportError(
            f"deployment marker {marker!r} was not found in the main-agent rollout"
        )
    marker_time = min(marker_times)

    candidates: list[datetime] = []
    for record in iter_jsonl(root.path, warnings):
        timestamp = record_time(record, path=root.path)
        if timestamp > marker_time:
            continue
        if tuple(user_texts(record)):
            candidates.append(timestamp)
    if not candidates:
        raise ReportError("no main-agent user turn precedes the deployment marker")
    return max(candidates)


def descendants(root_id: str, index: dict[str, Session]) -> list[Session]:
    by_parent: dict[str, list[Session]] = defaultdict(list)
    for session in index.values():
        if session.parent_id is not None:
            by_parent[session.parent_id].append(session)
    result: list[Session] = []
    queue = deque([root_id])
    seen = {root_id}
    while queue:
        parent = queue.popleft()
        for child in sorted(
            by_parent.get(parent, ()), key=lambda item: (item.timestamp, item.session_id)
        ):
            if child.session_id in seen:
                raise ReportError(f"cycle in session ancestry at {child.session_id}")
            seen.add(child.session_id)
            result.append(child)
            queue.append(child.session_id)
    return result


def _token_integer(value: Any, *, field: str, path: Path) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ReportError(f"invalid {field} in {path.name}")
    return value



def usage_values(raw: Any, path: Path, field: str) -> Usage:
    if not isinstance(raw, dict):
        raise ReportError(f"missing {field} in {path.name}; usage cannot be reconciled")
    incoming = _token_integer(raw.get("input_tokens"), field="input count", path=path)
    outgoing = _token_integer(raw.get("output_tokens"), field="output count", path=path)
    cached = raw.get("cached_input_tokens")
    if cached is None and isinstance(raw.get("input_tokens_details"), dict):
        cached = raw["input_tokens_details"].get("cached_tokens")
    cached = _token_integer(cached, field="cached-input count", path=path)
    if cached > incoming:
        raise ReportError(f"cached-input tokens exceed input tokens in {path.name}")
    # reasoning_output_tokens is a subset of output_tokens, never an extra charge.
    return Usage(0, cached, incoming, outgoing)


def vector(usage: Usage) -> tuple[int, int, int]:
    return usage.input_tokens, usage.cached_input_tokens, usage.output_tokens


def aggregate_session(
    session: Session,
    start: datetime,
    end: datetime,
    warnings: list[str],
    diagnostics: list[dict[str, Any]] | None = None,
) -> Usage:
    total = Usage()
    previous: Usage | None = None
    previous_time: datetime | None = None
    notifications = duplicates = 0
    context: tuple[str | None, str | None] = (None, None)
    observed_contexts: set[tuple[str | None, str | None]] = set()
    # Replayed parent entries retain their timestamps. They can seed a counter
    # baseline, but are never charged to a child before that child's creation.
    lower = max(start, session.timestamp)
    for record in iter_jsonl(session.path, warnings):
        payload = record.get("payload")
        if record.get("type") == "turn_context" and isinstance(payload, dict):
            timestamp = record_time(record, path=session.path)
            if session.timestamp <= timestamp <= end:
                context = (_optional_string(payload.get("model")),
                           _optional_string(payload.get("effort")) or
                           _optional_string(payload.get("model_reasoning_effort")))
            continue
        if record.get("type") != "event_msg" or not isinstance(payload, dict) or payload.get("type") != "token_count":
            continue
        timestamp = record_time(record, path=session.path)
        if timestamp > end:
            continue  # Freeze cutoff before any indexing/reporting work.
        info = payload.get("info")
        if info is None:
            continue  # Rate-limit-only event without a usage snapshot.
        if not isinstance(info, dict):
            raise ReportError(f"malformed token usage info in {session.path.name}")
        inside = lower <= timestamp <= end
        if inside:
            notifications += 1
        cumulative_raw = info.get("total_token_usage")
        if cumulative_raw is None:
            if inside:
                raise ReportError(f"missing cumulative counters in {session.path.name}; "
                                  "last_token_usage alone cannot safely distinguish repeated notifications")
            previous = previous_time = None
            continue
        current = usage_values(cumulative_raw, session.path, "total_token_usage")
        if previous_time is not None and timestamp < previous_time:
            raise ReportError(f"out-of-order usage timestamps in {session.path.name}; scope is ambiguous")
        if not inside:
            previous, previous_time = current, timestamp
            continue
        if previous is not None and vector(current) == vector(previous):
            duplicates += 1
            previous_time = timestamp
            continue
        if previous is None:
            # A first snapshot may contain inherited/earlier consumption. Only a
            # fresh cumulative==last sample or explicit zero establishes its origin.
            if vector(current) == (0, 0, 0):
                previous, previous_time = current, timestamp
                continue
            last = usage_values(info.get("last_token_usage"), session.path, "last_token_usage")
            if session.forked_from_id or vector(last) != vector(current):
                raise ReportError(f"missing pre-window/inherited baseline in {session.path.name}; "
                                  "refusing to count a historical cumulative total")
            delta = current
        else:
            values = tuple(c - p for c, p in zip(vector(current), vector(previous)))
            if any(value < 0 for value in values):
                raise ReportError(f"cumulative counter regression in {session.path.name}; "
                                  "reset/rebase requires a narrower verified window")
            delta = Usage(0, values[1], values[0], values[2])
            if delta.cached_input_tokens > delta.input_tokens:
                raise ReportError(f"inconsistent cached-input delta in {session.path.name}")
            last = usage_values(info.get("last_token_usage"), session.path, "last_token_usage")
            if vector(delta) != vector(last):
                raise ReportError(f"cumulative delta does not match last usage in {session.path.name}; "
                                  "missing events, synthetic adjustment or window boundary is ambiguous")
        previous, previous_time = current, timestamp
        if vector(delta) != (0, 0, 0):
            delta.rollouts = 1
            total.add(delta)
            observed_contexts.add(context)
    if diagnostics is not None:
        diagnostics.append({
            "session_id": session.session_id,
            "role": session.role or ("main agent" if session.parent_id is None else "unclassified"),
            "usage_notifications": notifications,
            "unchanged_snapshots_ignored": duplicates,
            "reconciled_usage_updates": total.rollouts,
            "recorded_turn_contexts": [
                {"model": model, "reasoning_effort": effort}
                for model, effort in sorted(observed_contexts, key=lambda c: (c[0] or "", c[1] or ""))
            ],
            "model_attribution": "Recorded turn context, not independent server/billing evidence; missing values are unknown.",
        })
    return total


def compile_rows(
    root: Session,
    index: dict[str, Session],
    start: datetime,
    end: datetime,
    warnings: list[str],
    diagnostics: list[dict[str, Any]] | None = None,
) -> list[Row]:
    grouped_usage: dict[str, Usage] = defaultdict(Usage)
    grouped_tasks: dict[str, set[str]] = defaultdict(set)
    first_activity: dict[str, datetime] = {}

    for child in descendants(root.session_id, index):
        usage = aggregate_session(child, start, end, warnings, diagnostics)
        spawned_in_window = start <= child.timestamp <= end
        if usage.rollouts == 0:
            if spawned_in_window:
                warnings.append(f"no reconciled usage for spawned session {child.session_id}; omitted, not assumed free")
            continue
        role = child.role or "unclassified"
        task_name = child.session_id  # Count distinct threads, not repeated role/task labels.
        grouped_usage[role].add(usage)
        grouped_tasks[role].add(task_name)
        activity = max(start, child.timestamp)
        first_activity[role] = min(first_activity.get(role, activity), activity)

    rows = [
        Row(role, len(grouped_tasks[role]), usage, first_activity[role])
        for role, usage in grouped_usage.items()
    ]
    rows.sort(key=lambda row: (row.first_activity, row.agent))
    root_usage = aggregate_session(root, start, end, warnings, diagnostics)
    if root_usage.rollouts == 0:
        raise ReportError("no reconciled main-agent usage in the requested window")
    rows.append(Row("main agent", 1, root_usage, start))
    return rows


def markdown(rows: list[Row]) -> str:
    lines = [
        "| Agent | Quantity | Rollouts | Cached input | Input | Output |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {} | {:,} | {:,} | {:,} | {:,} | {:,} |".format(
                row.agent,
                row.quantity,
                row.usage.rollouts,
                row.usage.cached_input_tokens,
                row.usage.input_tokens,
                row.usage.output_tokens,
            )
        )
    return "\n".join(lines)


def json_output(
    deployment_id: str,
    root: Session,
    start: datetime,
    end: datetime,
    rows: list[Row],
    warnings: list[str],
    diagnostics: list[dict[str, Any]] | None = None,
) -> str:
    payload = {
        "schema_version": 2,
        "deployment_id": deployment_id,
        "root_session_id": root.session_id,
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "rows": [
            {
                "agent": row.agent,
                "quantity": row.quantity,
                "rollouts": row.usage.rollouts,
                "cached_input_tokens": row.usage.cached_input_tokens,
                "input_tokens": row.usage.input_tokens,
                "output_tokens": row.usage.output_tokens,
            }
            for row in rows
        ],
        "warnings": sorted(set(warnings)),
        "accounting": {
            "method": "cumulative_delta_reconciled_with_last_usage",
            "rollouts_semantics": "reconciled usage updates, not guaranteed unique model requests",
            "cached_input_semantics": "subset of input_tokens",
            "window_semantics": "usage notification timestamps, inclusive; not account billing time",
            "coverage": "partial" if warnings else "reconciled_available_records",
            "weekly_allowance_percent": None,
            "limitation": "Local logs are not a billing API. Absent sessions/schema or unlogged usage cannot be inferred.",
        },
        "sessions": diagnostics or [],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--deployment-id", required=True)
    result.add_argument(
        "--sessions-root",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "sessions",
    )
    result.add_argument("--caller-session-id")
    result.add_argument("--root-session-id")
    result.add_argument("--start-time")
    result.add_argument("--end-time")
    result.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    invoked_at = datetime.now(timezone.utc)
    try:
        if not DEPLOYMENT_ID.fullmatch(args.deployment_id):
            raise ReportError(
                "deployment ID must be lowercase, underscore-safe, and at most 64 characters"
            )
        if args.start_time is not None and args.root_session_id is None:
            raise ReportError("--start-time requires --root-session-id")
        warnings: list[str] = []
        index = build_index(args.sessions_root.expanduser().resolve(), warnings)
        end = (
            parse_time(args.end_time, field="end time")
            if args.end_time
            else invoked_at
        )
        if args.root_session_id:
            root = index.get(args.root_session_id)
            if root is None:
                raise ReportError(f"root session was not found: {args.root_session_id}")
            if root.parent_id is not None:
                raise ReportError("--root-session-id must identify a root, not a worker")
            start = (parse_time(args.start_time, field="start time") if args.start_time
                     else find_boundary(root, args.deployment_id, warnings))
        else:
            caller_id = args.caller_session_id or os.environ.get("CODEX_THREAD_ID")
            if not caller_id:
                raise ReportError(
                    "CODEX_THREAD_ID is unavailable; pass --caller-session-id"
                )
            caller = index.get(caller_id)
            if caller is None:
                raise ReportError(f"caller session was not found: {caller_id}")
            if caller.parent_id is None or caller.role != "archivist":
                raise ReportError("the caller is not a spawned Archivist session")
            root = index.get(caller.parent_id)
            if root is None:
                raise ReportError(
                    f"parent main-agent session is missing: {caller.parent_id}"
                )
            start = find_boundary(root, args.deployment_id, warnings)
        if start > end:
            raise ReportError("deployment start is after report cutoff")
        diagnostics: list[dict[str, Any]] = []
        rows = compile_rows(root, index, start, end, warnings, diagnostics)
        if args.format == "json":
            print(json_output(args.deployment_id, root, start, end, rows, warnings, diagnostics))
        else:
            print(markdown(rows))
            print(f"Report window: {start.isoformat()} to {end.isoformat()} (notification times). "
                  "Rollouts = reconciled usage updates, not guaranteed unique requests. "
                  "Cached input is a subset of Input. Local logs are not a quota/billing ledger.", file=sys.stderr)
            ignored = sum(item["unchanged_snapshots_ignored"] for item in diagnostics)
            if ignored:
                print(f"Accounting: ignored {ignored} unchanged cumulative snapshots.", file=sys.stderr)
            for warning in sorted(set(warnings)):
                print(f"Warning: {warning}", file=sys.stderr)
        return 0
    except ReportError as error:
        print(f"deployment-token-report: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
