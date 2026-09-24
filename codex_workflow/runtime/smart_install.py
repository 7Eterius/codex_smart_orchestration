#!/usr/bin/env python3
"""Global Smart installation: preview by default; --apply writes with backups.

No project scans, model calls, process control or automatic permission changes.
Finish in the current session, then ask the user to restart Codex manually.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid

if sys.version_info < (3, 11):
    raise SystemExit("Use Python 3.11 or newer.")
PACKAGE = Path(__file__).resolve().parent.parent
if str(PACKAGE) not in sys.path:
    sys.path.insert(0, str(PACKAGE))

from runtime.agent_defaults import configure, parse as parse_config
from runtime.config_assessment import assess_configuration
from runtime.errors import ValidationError, WorkflowError
from runtime.layout import BUILTIN_WORKERS, INSTALLED_RUNTIME_FILES, PackageLayout, RuntimePaths, USER_STATE
from runtime.markers import USER_MANAGED, extract
from runtime.plan import OperationPlan, json_mutation, read_json, read_string_list, resolve_owned_runtime_path
from runtime.runtime_ops import plan_runtime_files
from runtime.smart_config import SMART, bootstrap, patch_config
from runtime.transaction import Mutation

_SKILL_MARKER = re.compile(r"^<!-- codex-workflow-skill: ([a-z0-9-]+) -->$", re.MULTILINE)


def safe_path(path: Path, home: Path) -> None:
    if ".." in path.parts or ".." in home.parts:
        raise ValidationError("Parent traversal is not allowed in installation paths")
    try:
        path.relative_to(home)
    except ValueError as exc:
        raise ValidationError(f"Target outside Codex home: {path}") from exc
    cursor = path
    while cursor != home.parent:
        if cursor.is_symlink():
            raise ValidationError(f"Refusing symlink in target ancestry: {cursor}")
        if cursor == home:
            break
        cursor = cursor.parent


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read(path: Path) -> bytes | None:
    if path.exists() and not path.is_file():
        raise ValidationError(f"Target is not a regular file: {path}")
    return path.read_bytes() if path.is_file() else None


def _version_tuple(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", value.strip())
    if match is None:
        raise ValidationError(f"Invalid installed VERSION: {value!r}")
    return tuple(int(match.group(index)) for index in range(1, 4))


def _hash_map(state: dict) -> dict[str, str]:
    value = state.get("owned_runtime_hashes", {})
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and key and isinstance(item, str)
        and re.fullmatch(r"[0-9a-f]{64}", item) for key, item in value.items()
    ):
        raise ValidationError("owned_runtime_hashes must map paths to SHA-256 hashes")
    return dict(value)


def _legacy_source_path(source_root: Path, relative: str) -> Path:
    path = Path(relative)
    parts = path.parts
    if parts == ("templates", "AGENTS.md"):
        return source_root / "AGENTS.md"
    if len(parts) >= 3 and parts[0] == "templates" and parts[1] in {"agents", "project_docs", "skills"}:
        return source_root / Path(*parts[1:])
    return source_root / path


def _known_bytes(runtime: RuntimePaths, state: dict, relative: str, current: bytes,
                 installed_version: str | None) -> bool:
    expected = _hash_map(state).get(relative)
    # A recorded mismatch is a local edit, even if it happens to match an older cache.
    if expected is not None:
        return digest(current) == expected
    if installed_version:
        source = _legacy_source_path(runtime.runtime / ".source_backup" / installed_version, relative)
        safe_path(source, runtime.codex_home)
        return _read(source) == current
    return False


def _retired_runtime(runtime: RuntimePaths, state: dict, incoming_hashes: dict[str, str],
                     installed_version: str | None):
    changes, cleanup, warnings = [], [], []
    previous = set(read_string_list(state, "owned_runtime_files"))
    for relative in sorted(previous - set(incoming_hashes)):
        target = resolve_owned_runtime_path(runtime.runtime, relative)
        safe_path(target, runtime.codex_home)
        current = _read(target)
        if current is None:
            continue
        if not _known_bytes(runtime, state, relative, current, installed_version):
            warnings.append(f"Preserved retired managed file with unverified local edits: {target}")
            continue
        changes.append(Mutation(target, None))
        parent = target.parent
        while parent != runtime.runtime:
            cleanup.append(parent)
            parent = parent.parent
    return changes, cleanup, warnings


def _retire_workers(runtime: RuntimePaths, state: dict, incoming: set[str], installed_version: str | None):
    """Retire only live worker bytes proven by their previous managed template."""
    changes = []
    for worker in sorted(set(read_string_list(state, "owned_workers")) - incoming):
        if re.fullmatch(r"[A-Za-z0-9_-]+", worker) is None:
            raise ValidationError("Unsafe retired worker name in state")
        target = runtime.agents / f"{worker}.toml"
        relative = f"templates/agents/{worker}.toml"
        template = runtime.runtime / relative
        safe_path(target, runtime.codex_home)
        safe_path(template, runtime.codex_home)
        current = _read(target)
        if current is None:
            continue
        baseline = _read(template)
        if (baseline is None or current != baseline
                or not _known_bytes(runtime, state, relative, baseline, installed_version)):
            raise ValidationError(f"Modified/unverified retired worker requires review: {target}")
        changes.append(Mutation(target, None))
    return changes


def _retire_skills(runtime: RuntimePaths, state: dict):
    """Retire only byte-proven files, never sweep a marker-bearing directory."""
    changes, cleanup, warnings = [], [], []
    for skill in sorted(set(read_string_list(state, "owned_skills"))):
        if re.fullmatch(r"[a-z0-9-]+", skill) is None:
            raise ValidationError(f"Unsafe owned skill name in state: {skill!r}")
        root = runtime.skills / skill
        safe_path(root, runtime.codex_home)
        if not root.exists():
            continue
        entry = root / "SKILL.md"
        safe_path(entry, runtime.codex_home)
        if not root.is_dir() or not entry.is_file():
            warnings.append(f"Preserved retired skill with unverifiable ownership: {root}")
            continue
        match = _SKILL_MARKER.search(entry.read_text(encoding="utf-8"))
        if match is None or match.group(1) != skill:
            warnings.append(f"Preserved retired skill with unverifiable ownership: {root}")
            continue
        proposed, uncertain = [], False
        for path in sorted(root.rglob("*")):
            safe_path(path, runtime.codex_home)
            if path.is_dir():
                continue
            current = _read(path)
            template = runtime.runtime / "templates/skills" / skill / path.relative_to(root)
            safe_path(template, runtime.codex_home)
            relative = template.relative_to(runtime.runtime).as_posix()
            baseline = _read(template)
            # Both template provenance and live bytes must match; a comment is not proof.
            if (baseline is not None and current == baseline
                    and _known_bytes(runtime, state, relative, baseline, state.get("version"))):
                proposed.append(Mutation(path, None))
            else:
                uncertain = True
        if uncertain:
            warnings.append(f"Preserved retired skill containing unverified/local files: {root}")
            continue
        changes.extend(proposed)
        cleanup.extend(p for p in root.rglob("*") if p.is_dir())
        cleanup.append(root)
    return changes, cleanup, warnings


def prepare(package_root: Path, home: Path) -> tuple[OperationPlan, dict[str, bytes | None]]:
    home = home.expanduser().absolute()
    safe_path(home, home)
    package = PackageLayout.resolve(package_root)
    package_fingerprint = package.fingerprint
    runtime = RuntimePaths(home)
    if package.root == runtime.runtime.resolve():
        raise ValidationError("Install from an extracted source checkout/archive, not the installed runtime")
    for directory in (runtime.runtime, runtime.agents, runtime.skills):
        safe_path(directory, home)
        if directory.exists() and not directory.is_dir():
            raise ValidationError(f"Expected a directory: {directory}")
    # Check ancestry before reads, not only immediately before writes.
    for path in (runtime.config_toml, runtime.user_agents, runtime.runtime / USER_STATE,
                 runtime.runtime / "operate/VERSION", runtime.runtime / "templates/agents"):
        safe_path(path, home)
    state = read_json(runtime.runtime / USER_STATE, default={})
    _hash_map(state)
    installed_path = runtime.runtime / "operate/VERSION"
    installed_version = installed_path.read_text().strip() if installed_path.is_file() else None
    if installed_version and _version_tuple(installed_version) > _version_tuple(package.version):
        raise ValidationError("Refusing to downgrade a newer installation")
    if state and (state.get("workflow") != "Smart Orchestration"
                  or state.get("version") != installed_version
                  or type(state.get("schema_version")) is not int
                  or state.get("schema_version") not in (1, 2)):
        raise ValidationError("Installed state identity/version is inconsistent; review before installing")

    for worker in package.worker_names:
        target = runtime.agents / f"{worker}.toml"
        known_path = runtime.runtime / "templates/agents" / f"{worker}.toml"
        safe_path(target, home)
        safe_path(known_path, home)
        before = _read(target)
        incoming = (package.agent_templates / f"{worker}.toml").read_bytes()
        if before is not None and before != incoming and before != _read(known_path):
            raise ValidationError(f"Custom/unowned worker requires review before replacement: {target}")

    current_config = (_read(runtime.config_toml) or b"").decode("utf-8")
    parsed = parse_config(current_config)
    assessment = assess_configuration(parsed)
    if assessment["errors"]:
        raise ValidationError("; ".join(assessment["errors"]))
    rendered_config, default_warnings, defaults_added = configure(patch_config(current_config, home))
    mutations, owned_hashes, cleanup_dirs = plan_runtime_files(package, runtime)
    # Protect current runtime and templates as carefully as worker TOMLs.
    for mutation in mutations:
        safe_path(mutation.path, home)
        if not mutation.path.is_relative_to(runtime.runtime):
            continue
        current = _read(mutation.path)
        if current is None or current == mutation.content:
            continue
        relative = mutation.path.relative_to(runtime.runtime).as_posix()
        if not _known_bytes(runtime, state, relative, current, installed_version):
            raise ValidationError(f"Custom/unowned runtime file requires review: {mutation.path}")

    mutations.append(Mutation(runtime.config_toml, rendered_config.encode(), 0o600))
    mutations.extend(_retire_workers(runtime, state, package.worker_names, installed_version))
    retired, retired_cleanup, retirement_warnings = _retired_runtime(runtime, state, owned_hashes, installed_version)
    mutations.extend(retired)
    cleanup_dirs.extend(retired_cleanup)
    skill_changes, skill_cleanup, skill_warnings = _retire_skills(runtime, state)
    mutations.extend(skill_changes)
    cleanup_dirs.extend(skill_cleanup)
    # Preserve historical source caches and rollback backups. They are not active context.
    chosen = {mutation.path: mutation for mutation in mutations}
    new_state = {
        "schema_version": 2, "version": package.version, "workflow": "Smart Orchestration",
        "mode": "global", "package_fingerprint": package_fingerprint,
        "owned_runtime_files": sorted(owned_hashes), "owned_runtime_hashes": dict(sorted(owned_hashes.items())),
        "owned_workers": sorted(package.worker_names), "owned_skills": [],
    }
    state_mutation = json_mutation(runtime.runtime / USER_STATE, new_state)
    chosen[state_mutation.path] = state_mutation
    changed, before_by_path = [], {}
    for path, mutation in chosen.items():
        safe_path(path, home)
        before = _read(path)
        if before == mutation.content:
            continue
        mode = path.stat().st_mode & 0o777 if path.exists() else mutation.mode
        changed.append(Mutation(path, mutation.content, mode))
        before_by_path[str(path)] = before
    if package.fingerprint != package_fingerprint:
        raise ValidationError("Source package changed during preparation; discard this plan and review")
    warnings = list(dict.fromkeys(default_warnings + assess_configuration(parse_config(rendered_config))["warnings"]
                                 + retirement_warnings + skill_warnings))
    if (home / "AGENTS.override.md").is_file():
        warnings.append("AGENTS.override.md is preserved; verify effective activation.")
    if any(isinstance(profile, dict) and "developer_instructions" in profile
           for profile in parsed.get("profiles", {}).values()):
        warnings.append("Profile developer instructions may override activation; verify the selected profile.")
    warnings.append("One adaptive policy is installed; native role execution and thread release require runtime observations, not a disk check.")
    return OperationPlan("install-smart-global", changed, warnings, [], {
        "workflow": "Smart Orchestration", "version": package.version, "scope": str(home),
        "project_mutations": 0, "parent_settings": "preserved", "child_defaults_added": defaults_added,
        "package_fingerprint": package_fingerprint, "retired_runtime_files": len(retired),
    }, cleanup_dirs=cleanup_dirs), before_by_path


def apply_plan(plan: OperationPlan, before: dict[str, bytes | None], home: Path) -> Path | None:
    home = home.expanduser().absolute()
    if not plan.mutations:
        return None
    safe_path(home, home)
    home.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = home / ".smart-orchestration-install.lock"
    safe_path(lock, home)
    try:
        lock.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise ValidationError("Another installer or stale install lock exists; inspect it before retrying") from exc
    try:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        backup = home / ".smart-orchestration-backups" / stamp
        safe_path(backup, home)
        records, backup_mutations, created_dirs = [], [], set()
        for mutation in plan.mutations:
            path = mutation.path
            safe_path(path, home)
            if _read(path) != before[str(path)]:
                raise ValidationError(f"File changed during preparation; stop and report the conflict: {path}")
            cursor = path.parent
            while cursor != home and not cursor.exists():
                created_dirs.add(cursor)
                cursor = cursor.parent
            relative, previous = path.relative_to(home), before[str(path)]
            if previous is not None:
                backup_mutations.append(Mutation(backup / "files" / relative, previous, 0o600))
            records.append({
                "path": str(relative), "existed": previous is not None,
                "before": digest(previous) if previous is not None else None,
                "after": digest(mutation.content) if mutation.content is not None else None,
                "mode": mutation.mode, "before_mode": path.stat().st_mode & 0o777 if path.exists() else None,
            })
        manifest = json.dumps({
            "schema": 1, "workflow": "Smart Orchestration", "files": records,
            "created_dirs": [str(path.relative_to(home)) for path in sorted(created_dirs, key=lambda p: (len(p.parts), str(p)))],
        }, indent=2).encode()
        backup_mutations.append(Mutation(backup / "manifest.json", manifest, 0o600))
        backup.mkdir(parents=True, exist_ok=False, mode=0o700)
        OperationPlan("backup-and-install-smart", backup_mutations + plan.mutations, [], [],
                      cleanup_dirs=plan.cleanup_dirs).apply()
        return backup
    finally:
        lock.rmdir()


def status(home: Path) -> dict:
    """Read-only disk integrity check; never claims live model or mode activation."""
    home = home.expanduser().absolute()
    runtime = RuntimePaths(home)
    for path in (home, runtime.config_toml, runtime.runtime / USER_STATE, runtime.runtime / "operate/VERSION"):
        safe_path(path, home)
    cfg = parse_config((_read(runtime.config_toml) or b"").decode())
    assessment = assess_configuration(cfg)
    state = read_json(runtime.runtime / USER_STATE, default={})
    mismatches = []
    hashes = _hash_map(state)
    if set(hashes) != INSTALLED_RUNTIME_FILES:
        mismatches.append("incomplete/unexpected runtime hash inventory")
    if set(read_string_list(state, "owned_runtime_files")) != set(hashes):
        mismatches.append("owned runtime inventory disagreement")
    for relative, expected in sorted(hashes.items()):
        path = resolve_owned_runtime_path(runtime.runtime, relative)
        safe_path(path, home)
        content = _read(path)
        if content is None or digest(content) != expected:
            mismatches.append(relative)
    for worker in sorted(BUILTIN_WORKERS):
        target = runtime.agents / f"{worker}.toml"
        template = runtime.runtime / "templates/agents" / f"{worker}.toml"
        safe_path(target, home)
        safe_path(template, home)
        expected, current = _read(template), _read(target)
        if expected is None or current != expected:
            mismatches.append(f"agents/{worker}.toml")
    instructions = cfg.get("developer_instructions", "")
    block_ok = isinstance(instructions, str) and SMART.start in instructions and SMART.end in instructions
    if block_ok:
        block_ok = extract(instructions, SMART) == bootstrap(home)
    safe_path(runtime.user_agents, home)
    user_source = runtime.runtime / "operate/user_AGENTS.md"
    safe_path(user_source, home)
    user_bytes, source_bytes = _read(runtime.user_agents), _read(user_source)
    try:
        user_ok = (user_bytes is not None and source_bytes is not None
                   and extract(user_bytes.decode(), USER_MANAGED)
                   == extract(source_bytes.decode(), USER_MANAGED).replace("~/.codex", str(home)))
    except (ValueError, WorkflowError):
        user_ok = False
    if not user_ok:
        mismatches.append("global AGENTS managed block")
    original_hashes = {(key.removeprefix("templates/") if key.startswith("templates/agents/") else key): value
                       for key, value in hashes.items()}
    observed_fingerprint = digest(json.dumps(original_hashes, sort_keys=True).encode())
    if state.get("package_fingerprint") != observed_fingerprint:
        mismatches.append("package fingerprint inventory")
    version_bytes = _read(runtime.runtime / "operate/VERSION")
    version = version_bytes.decode().strip() if version_bytes else None
    if (state.get("workflow") != "Smart Orchestration" or state.get("version") != version
            or type(state.get("schema_version")) is not int or state.get("schema_version") != 2
            or state.get("mode") != "global"):
        mismatches.append("installed state identity/version")
    if set(read_string_list(state, "owned_workers")) != BUILTIN_WORKERS:
        mismatches.append("owned worker inventory disagreement")
    ok = assessment["ok"] and block_ok and not mismatches
    return {"workflow": "Smart Orchestration", "version": version,
            "global_bootstrap_present": block_ok, "configuration_assessment": assessment,
            "disk_ok": ok, "mismatches": mismatches, "package_fingerprint": state.get("package_fingerprint"),
            "execution_policy": "adaptive", "runtime_observation": "not_inspected",
            "note": "Disk evidence only. Restart manually after changes. Observe role execution and native closure in the client; no global execution-mode gate."}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", "~/.codex")))
    parser.add_argument("--package-root", type=Path, default=PACKAGE)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--restore-backup", type=Path, help="Exact conflict-checked backup restoration; preview unless --apply")
    args = parser.parse_args(argv)
    try:
        if args.check:
            if args.apply or args.restore_backup:
                raise ValidationError("--check cannot be combined with --apply/restore")
            result = status(args.codex_home)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["disk_ok"] else 1
        if args.restore_backup:
            from runtime.smart_restore import prepare_restore
            plan, before = prepare_restore(args.codex_home, args.restore_backup)
        else:
            plan, before = prepare(args.package_root, args.codex_home)
        result = plan.summary()
        result["applied"] = False
        if not args.apply:
            result["planned_files"] = [str(m.path) for m in plan.mutations]
            result["status"] = "Preview only. Re-run with --apply in this session; restart Codex manually after success."
        else:
            backup = apply_plan(plan, before, args.codex_home)
            action = "Backup restored" if args.restore_backup else "Installed globally"
            result = {"workflow": "Smart Orchestration", "version": plan.details["version"],
                      "applied": True, "changed_files": len(plan.mutations), "backup": str(backup) if backup else None,
                      "warnings": plan.warnings, "package_fingerprint": plan.details.get("package_fingerprint"),
                      "status": f"{action}. Restart Codex manually after this command finishes." if backup else "Already installed; no writes."}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, WorkflowError) as exc:
        print(json.dumps({"applied": False, "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
