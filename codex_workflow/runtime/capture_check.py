#!/usr/bin/env python3
"""Capture one authorized, noninteractive check with bounded, recoverable output.

No LLM, proxy, test cache, retry or shell rewriting. Always executes the exact
argv under the caller's permissions. Raw output/argv may contain secrets: keep
artifacts local and private; never put credentials in command-line arguments.
Exit zero means the COMMAND exited zero, not that tests ran or acceptance passed.
"""
from __future__ import annotations

import argparse
from collections import deque
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time
from typing import Any

CHUNK = 65536
DIAGNOSTIC = re.compile(r"error|fail|warning|traceback|panic|fatal|violation|exception|skipped|todo", re.I)
LIMITATION = (
    "Command evidence only. Test counts and acceptance are not inferred. Preview is a "
    "heuristic excerpt, not an exhaustive diagnostic list. Inspect raw output/native "
    "reports for failures, zero tests, skips or ambiguity. No source/dependency/environment "
    "fingerprint is asserted; this receipt never authorizes skipping a required check."
)


def summarize(path: Path, *, preview_chars: int = 5000, preview_items: int = 24) -> dict[str, Any]:
    if not 256 <= preview_chars <= 20000 or not 4 <= preview_items <= 80:
        raise ValueError("Preview budget out of range")
    head, diagnostics, tail = [], [], deque(maxlen=8)
    digest = hashlib.sha256()
    offset = flagged = fragments = 0
    line = 1
    with path.open("rb") as stream:
        while part := stream.readline(CHUNK):
            digest.update(part)
            text = part.decode("utf-8", errors="replace").rstrip("\r\n")
            diagnostic = bool(DIAGNOSTIC.search(text))
            item = {"line": line, "byte_offset": offset, "text": text[:512],
                    "text_clipped": len(text) > 512 or (len(part) == CHUNK and not part.endswith(b"\n"))}
            if len(head) < 2:
                head.append(item)
            if diagnostic:
                flagged += 1
                if len(diagnostics) < 12:
                    diagnostics.append(item)
            tail.append(item)
            fragments += 1
            offset += len(part)
            line += part.count(b"\n")
    chosen, used = {}, 0
    # Diagnostic candidates first, then start/end. No claim that regex finds all errors.
    for item in diagnostics + head + list(tail):
        key = item["byte_offset"]
        if key in chosen or len(chosen) >= preview_items:
            continue
        available = preview_chars - used
        if available <= 0:
            break
        if len(item["text"]) > available:
            item = {**item, "text": item["text"][:available], "text_clipped": True}
        chosen[key] = item
        used += len(item["text"])
    preview = [chosen[key] for key in sorted(chosen)]
    return {"raw_output_bytes": offset, "raw_sha256": digest.hexdigest(),
            "preview": preview, "preview_text_characters": used,
            "preview_incomplete": len(preview) < fragments or any(i["text_clipped"] for i in preview),
            "diagnostic_fragments_seen": flagged, "test_counts": None}


def stop(process: subprocess.Popen[bytes]) -> None:
    """Terminate this check's process group on POSIX, not other workers."""
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
    except ProcessLookupError:
        pass
    process.wait()


def run_check(command: list[str], *, cwd: Path | None = None, artifacts: Path | None = None,
              timeout: float = 600, preview_chars: int = 5000, preview_items: int = 24) -> tuple[dict[str, Any], int]:
    if not command or any(not isinstance(a, str) or "\0" in a for a in command):
        raise ValueError("Provide a nonempty argv after --")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Timeout must be finite and positive")
    if not 256 <= preview_chars <= 20000 or not 4 <= preview_items <= 80:
        raise ValueError("Preview budget out of range")
    directory = (cwd or Path.cwd()).expanduser().resolve(strict=True)
    base = (artifacts or Path(tempfile.gettempdir())).expanduser().resolve(strict=True)
    if not directory.is_dir() or not base.is_dir():
        raise ValueError("Working directory and artifact parent must be existing directories")
    output_dir = Path(tempfile.mkdtemp(prefix="smart-check-", dir=base))
    output_dir.chmod(0o700)
    raw = output_dir / "output.log"
    started = datetime.now(timezone.utc).isoformat()
    tick = time.monotonic()
    process = None
    code = None
    status = "completed"
    error = None
    try:
        fd = os.open(raw, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as log:
            try:
                process = subprocess.Popen(command, cwd=directory, stdin=subprocess.DEVNULL,
                                           stdout=log, stderr=subprocess.STDOUT, shell=False,
                                           start_new_session=(os.name == "posix"))
            except OSError as exc:
                status = "launch_error"
                error = f"{type(exc).__name__}: {exc}"
            else:
                try:
                    code = process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    status = "timed_out"
                    stop(process)
                    code = process.returncode
                except KeyboardInterrupt:
                    status = "interrupted"
                    stop(process)
                    code = process.returncode
        exit_code = (124 if status == "timed_out" else 130 if status == "interrupted" else
                     127 if status == "launch_error" else code if code is not None and code >= 0 else
                     128 - code if code is not None else 125)
        result = {"schema": 1, "started_utc": started, "elapsed_seconds": round(time.monotonic() - tick, 3),
                  "command": command, "cwd": str(directory), "execution_status": status,
                  "command_exit_code": code, "runner_exit_code": exit_code, "launch_error": error,
                  "raw_output_path": str(raw), "receipt_path": str(output_dir / "receipt.json"),
                  "capture_kind": "combined stdout and stderr", "acceptance": "not_assessed",
                  "reused": False, "limitation": LIMITATION, **summarize(raw, preview_chars=preview_chars,
                                                                            preview_items=preview_items)}
        if os.name != "posix":
            result["platform_limitation"] = "Timeout kills the immediate process only; inspect child processes on Windows."
        receipt_fd = os.open(output_dir / "receipt.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(receipt_fd, "w", encoding="utf-8") as receipt:
            json.dump(result, receipt, ensure_ascii=True, indent=2)
            receipt.write("\n")
        return result, exit_code
    except BaseException:
        if process is not None and process.poll() is None:
            stop(process)
        # Raw evidence is deliberately retained, never removed on helper failure.
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", type=Path)
    parser.add_argument("--artifacts", type=Path, help="Existing parent directory; default system temp directory")
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--preview-chars", type=int, default=5000)
    parser.add_argument("--preview-items", type=int, default=24)
    parser.add_argument("command", nargs=argparse.REMAINDER, help="-- executable arg ... (no implicit shell)")
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    try:
        result, code = run_check(command, cwd=args.cwd, artifacts=args.artifacts, timeout=args.timeout,
                                 preview_chars=args.preview_chars, preview_items=args.preview_items)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return code
    except (ValueError, OSError) as exc:
        print(json.dumps({"execution_status": "capture_error", "acceptance": "not_assessed",
                          "error": str(exc), "runner_exit_code": 125}), file=__import__('sys').stderr)
        return 125


if __name__ == "__main__":
    raise SystemExit(main())
