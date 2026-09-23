#!/usr/bin/env python3
"""Fingerprint explicitly scoped candidate inputs; never infer test coverage.

Snapshot/verify are read-only for source. Only --output creates a private evidence
file. No Git mutations, network, model calls, result caching or automatic discovery.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys

MAX_FILES = 5000
MAX_BYTES = 64 * 1024 * 1024
MAX_MANIFEST_BYTES = 4 * 1024 * 1024
LIMITATION = "Identity of listed inputs only; not a test verdict, dependency graph, runtime-state proof or signature."


class CandidateError(ValueError):
    pass


def _relative(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise CandidateError("Use nonempty repository-relative POSIX paths")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts or ".git" in path.parts:
        raise CandidateError(f"Unsafe or unbounded candidate path: {value!r}")
    return path.as_posix()


def _safe(root: Path, relative: str) -> Path:
    path = root / _relative(relative)
    cursor = path
    while cursor != root:
        if cursor.is_symlink():
            raise CandidateError(f"Symlink in candidate scope: {relative}")
        cursor = cursor.parent
    return path


def _root(value: Path) -> Path:
    value = value.expanduser()
    if value.is_symlink() or not value.is_dir():
        raise CandidateError("Candidate root must be an existing non-symlink directory")
    # Canonicalize OS aliases such as macOS /var before enforcing paths below root.
    return value.resolve(strict=True)


def _content_id(scopes: list[dict], files: dict) -> str:
    payload = json.dumps({"scopes": scopes, "files": files}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def snapshot(root: Path, paths: list[str]) -> dict:
    root = _root(root)
    if not paths or len(paths) > MAX_FILES:
        raise CandidateError("Supply a bounded nonempty set of explicit input paths")
    names = sorted({_relative(p) for p in paths})
    scopes, files, total = [], {}, 0
    for name in names:
        target = _safe(root, name)
        if not target.exists():
            raise CandidateError(f"Required candidate input is missing: {name}")
        kind = "directory" if target.is_dir() else "file"
        scopes.append({"path": name, "kind": kind})
        pending = [target]
        while pending:
            path = pending.pop()
            relative = path.relative_to(root).as_posix()
            _safe(root, relative)
            mode = path.lstat().st_mode
            if stat.S_ISDIR(mode):
                children = list(path.iterdir())
                if len(children) + len(pending) + len(files) > MAX_FILES:
                    raise CandidateError("Candidate scope exceeds entry limit; narrow the inputs")
                pending.extend(sorted(children, reverse=True))
                continue
            if not stat.S_ISREG(mode):
                raise CandidateError(f"Candidate input is not a regular file: {relative}")
            if relative in files:
                continue
            before = path.stat()
            if before.st_size + total > MAX_BYTES or len(files) >= MAX_FILES:
                raise CandidateError("Candidate scope exceeds size limit; narrow the inputs")
            # Bound reads even when a file grows after stat().
            with path.open("rb") as stream:
                content = stream.read(MAX_BYTES - total + 1)
            after = path.stat()
            if (len(content) != before.st_size or len(content) + total > MAX_BYTES
                    or (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                    != (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)):
                raise CandidateError(f"Candidate input changed during read: {relative}")
            files[relative] = {"sha256": hashlib.sha256(content).hexdigest(),
                               "bytes": len(content), "mode": stat.S_IMODE(after.st_mode)}
            total += len(content)
    files = dict(sorted(files.items()))
    return {"schema": 1, "root": str(root), "scopes": scopes, "files": files,
            "fingerprint": _content_id(scopes, files), "limitation": LIMITATION}


def _validate(manifest: dict) -> None:
    if not isinstance(manifest, dict) or type(manifest.get("schema")) is not int or manifest.get("schema") != 1:
        raise CandidateError("Unsupported candidate manifest")
    if not isinstance(manifest.get("root"), str) or not Path(manifest["root"]).is_absolute():
        raise CandidateError("Manifest root must be absolute")
    scopes, files = manifest.get("scopes"), manifest.get("files")
    if not isinstance(scopes, list) or not scopes or len(scopes) > MAX_FILES:
        raise CandidateError("Manifest scopes must be a bounded nonempty list")
    seen = set()
    for scope in scopes:
        if not isinstance(scope, dict) or scope.get("kind") not in {"file", "directory"}:
            raise CandidateError("Invalid manifest scope")
        name = _relative(scope.get("path"))
        if name != scope["path"] or name in seen:
            raise CandidateError("Duplicate/noncanonical scope")
        seen.add(name)
    if not isinstance(files, dict) or len(files) > MAX_FILES:
        raise CandidateError("Invalid manifest file inventory")
    total = 0
    for name, info in files.items():
        if _relative(name) != name or not isinstance(info, dict):
            raise CandidateError("Invalid manifest file")
        if not any(name == s["path"] or (s["kind"] == "directory" and name.startswith(s["path"] + "/"))
                   for s in scopes):
            raise CandidateError("Manifest file escapes declared scopes")
        if not isinstance(info.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", info["sha256"]):
            raise CandidateError("Invalid content hash")
        for key in ("bytes", "mode"):
            if type(info.get(key)) is not int or info[key] < 0:
                raise CandidateError("Invalid file metadata")
        if info["mode"] > 0o7777:
            raise CandidateError("Invalid file mode")
        total += info["bytes"]
    if total > MAX_BYTES or manifest.get("fingerprint") != _content_id(scopes, files):
        raise CandidateError("Manifest size/integrity check failed")


def verify(manifest: dict) -> dict:
    _validate(manifest)
    current = snapshot(Path(manifest["root"]), [s["path"] for s in manifest["scopes"]])
    old, new = manifest["files"], current["files"]
    added, removed = sorted(new.keys() - old.keys()), sorted(old.keys() - new.keys())
    changed = sorted(p for p in old.keys() & new.keys() if old[p] != new[p])
    matched = current["fingerprint"] == manifest["fingerprint"]
    return {"matched": matched, "expected": manifest["fingerprint"], "observed": current["fingerprint"],
            "added": added, "removed": removed, "changed": changed,
            "scope_changed": current["scopes"] != manifest["scopes"], "limitation": LIMITATION}


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CandidateError("Duplicate JSON keys in candidate manifest")
        result[key] = value
    return result


def read_manifest(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise CandidateError("Manifest must be a regular file")
    with path.open("rb") as stream:
        content = stream.read(MAX_MANIFEST_BYTES + 1)
    if len(content) > MAX_MANIFEST_BYTES:
        raise CandidateError("Manifest exceeds size limit")
    value = json.loads(content, object_pairs_hook=_unique_pairs)
    _validate(value)
    return value


def write_manifest(manifest: dict, output: Path) -> None:
    _validate(manifest)
    output = output.expanduser().absolute()
    root = Path(manifest["root"])
    resolved = output.resolve(strict=False)
    for scope in manifest["scopes"]:
        watched = root / scope["path"]
        if resolved == watched or (scope["kind"] == "directory" and resolved.is_relative_to(watched)):
            raise CandidateError("Evidence output must be outside the watched input scope")
    # Create only the explicitly requested new file; never overwrite owner evidence.
    if output.is_symlink():
        raise CandidateError("Evidence output must not be a symlink")
    # Canonicalize an explicitly chosen existing directory (including OS aliases).
    # O_EXCL below still rejects an existing output/symlink without overwriting it.
    output = output.parent.resolve(strict=True) / output.name
    content = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    if len(content) > MAX_MANIFEST_BYTES:
        raise CandidateError("Manifest exceeds size limit")
    fd = os.open(output, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(content)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    take = sub.add_parser("snapshot")
    take.add_argument("--root", type=Path, required=True)
    take.add_argument("--path", action="append", required=True, dest="paths")
    take.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("verify")
    check.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "snapshot":
            manifest = snapshot(args.root, args.paths)
            write_manifest(manifest, args.output)
            print(json.dumps({"manifest": str(args.output), "fingerprint": manifest["fingerprint"],
                              "files": len(manifest["files"]), "limitation": LIMITATION}))
            return 0
        result = verify(read_manifest(args.manifest))
        # Full expected inventory stays in the manifest; bound the chat-facing delta.
        result["counts"] = {k: len(result[k]) for k in ("added", "removed", "changed")}
        result["truncated"] = any(n > 20 for n in result["counts"].values())
        for key in result["counts"]:
            result[key] = result[key][:20]
        print(json.dumps(result, sort_keys=True))
        return 0 if result["matched"] else 1
    except (OSError, ValueError) as error:
        print(json.dumps({"matched": False, "error": str(error), "limitation": LIMITATION}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
