#!/usr/bin/env python3
"""Install Smart Orchestration globally. Preview by default; --apply writes.

The installer touches only workflow-owned global Codex surfaces. It never scans or
rewrites projects. Installation may complete in the active Codex session; restart
Codex manually after a successful apply.
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
from runtime.layout import PackageLayout, RuntimePaths, USER_STATE
from runtime.markers import extract
from runtime.plan import (
    OperationPlan,
    json_mutation,
    read_json,
    read_string_list,
    resolve_owned_runtime_path,
)
from runtime.runtime_ops import plan_runtime_files
from runtime.smart_config import SMART, patch_config
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
    if value == {}:
        return {}
    if not isinstance(value, dict) or not all(
        isinstance(key, str)
        and key
        and isinstance(item, str)
        and re.fullmatch(r"[0-9a-f]{64}", item)
        for key, item in value.items()
    ):
        raise ValidationError("state field owned_runtime_hashes must map paths to SHA-256 hashes")
    return dict(value)


def _legacy_source_path(source_root: Path, relative: str) -> Path:
    path = Path(relative)
    parts = path.parts
    if parts == ("templates", "AGENTS.md"):
        return source_root / "AGENTS.md"
    if len(parts) >= 3 and parts[:2] == ("templates", "project_docs"):
        return source_root / "project_docs" / Path(*parts[2:])
    if len(parts) >= 3 and parts[:2] == ("templates", "skills"):
        return source_root / "skills" / Path(*parts[2:])
    return source_root / path


def _retired_runtime(
    runtime: RuntimePaths,
    state: dict,
    incoming_hashes: dict[str, str],
    installed_version: str | None,
) -> tuple[list[Mutation], list[Path], list[str]]:
    previous = set(read_string_list(state, "owned_runtime_files"))
    hashes = _hash_map(state)
    mutations: list[Mutation] = []
    cleanup_dirs: list[Path] = []
    warnings: list[str] = []
    legacy_source = (
        runtime.runtime / ".source_backup" / installed_version
        if installed_version
        else None
    )

    for relative in sorted(previous - set(incoming_hashes)):
        target = resolve_owned_runtime_path(runtime.runtime, relative)
        safe_path(target, runtime.codex_home)
        current = _read(target)
        if current is None:
            continue

        expected = hashes.get(relative)
        known = expected is not None and digest(current) == expected
        if not known and legacy_source is not None:
            source = _legacy_source_path(legacy_source, relative)
            safe_path(source, runtime.codex_home)
            if source.is_file() and current == source.read_bytes():
                known = True

        if not known:
            warnings.append(
                f"Preserved retired managed file with unverified local edits: {target}"
            )
            continue

        mutations.append(Mutation(target, None))
        parent = target.parent
        while parent != runtime.runtime:
            cleanup_dirs.append(parent)
            parent = parent.parent

    return mutations, cleanup_dirs, warnings


def _retire_source_cache(runtime: RuntimePaths) -> tuple[list[Mutation], list[Path]]:
    root = runtime.runtime / ".source_backup"
    safe_path(root, runtime.codex_home)
    if not root.exists():
        return [], []
    if root.is_symlink() or not root.is_dir():
        raise ValidationError(f"Legacy source cache is not a regular directory: {root}")
    mutations: list[Mutation] = []
    cleanup_dirs: list[Path] = [root]
    for path in sorted(root.rglob("*")):
        safe_path(path, runtime.codex_home)
        if path.is_symlink():
            raise ValidationError(f"Legacy source cache contains a symlink: {path}")
        if path.is_file():
            mutations.append(Mutation(path, None))
        elif path.is_dir():
            cleanup_dirs.append(path)
    return mutations, cleanup_dirs


def _retire_skills(runtime: RuntimePaths, state: dict) -> tuple[list[Mutation], list[Path], list[str]]:
    mutations: list[Mutation] = []
    cleanup_dirs: list[Path] = []
    warnings: list[str] = []
    for skill in sorted(set(read_string_list(state, "owned_skills"))):
        if re.fullmatch(r"[a-z0-9-]+", skill) is None:
            raise ValidationError(f"Unsafe owned skill name in state: {skill!r}")
        root = runtime.skills / skill
        safe_path(root, runtime.codex_home)
        if not root.exists():
            continue
        entry = root / "SKILL.md"
        if root.is_symlink() or not root.is_dir() or not entry.is_file():
            warnings.append(f"Preserved retired skill with unverifiable ownership: {root}")
            continue
        match = _SKILL_MARKER.search(entry.read_text(encoding="utf-8"))
        if match is None or match.group(1) != skill:
            warnings.append(f"Preserved retired skill with unverifiable ownership: {root}")
            continue
        for path in sorted(root.rglob("*")):
            safe_path(path, runtime.codex_home)
            if path.is_symlink():
                raise ValidationError(f"Retired workflow skill contains a symlink: {path}")
            if path.is_file():
                mutations.append(Mutation(path, None))
            elif path.is_dir():
                cleanup_dirs.append(path)
        cleanup_dirs.append(root)
    return mutations, cleanup_dirs, warnings


def prepare(package_root: Path, home: Path) -> tuple[OperationPlan, dict[str, bytes | None]]:
    home = home.expanduser().absolute()
    safe_path(home, home)
    package = PackageLayout.resolve(package_root)
    runtime = RuntimePaths(home)

    if package.root == runtime.runtime.resolve():
        raise ValidationError(
            "Install from an extracted source checkout/archive, not the already-installed runtime"
        )

    installed_version_path = runtime.runtime / "operate" / "VERSION"
    safe_path(installed_version_path, home)
    installed_version = (
        installed_version_path.read_text(encoding="utf-8").strip()
        if installed_version_path.is_file()
        else None
    )
    if installed_version and _version_tuple(installed_version) > _version_tuple(package.version):
        raise ValidationError("Refusing to downgrade a newer installation")

    for directory in (runtime.runtime, runtime.agents, runtime.skills):
        safe_path(directory, home)
        if directory.exists() and not directory.is_dir():
            raise ValidationError(f"Expected a directory: {directory}")

    for worker in package.worker_names:
        target = runtime.agents / f"{worker}.toml"
        safe_path(target, home)
        if not target.exists():
            continue
        before = target.read_bytes()
        incoming = (package.agent_templates / f"{worker}.toml").read_bytes()
        known_path = runtime.runtime / "templates" / "agents" / f"{worker}.toml"
        known = known_path.read_bytes() if known_path.is_file() else None
        if before != incoming and (known is None or before != known):
            raise ValidationError(
                f"Custom/unowned worker requires review before replacement: {target}"
            )

    current_config = runtime.config_toml.read_text() if runtime.config_toml.is_file() else ""
    parsed = parse_config(current_config)
    assessment = assess_configuration(parsed)
    if assessment["errors"]:
        raise ValidationError("; ".join(assessment["errors"]))

    rendered_config = patch_config(current_config, home)
    rendered_config, default_warnings, defaults_added = configure(rendered_config)

    mutations, owned_hashes, cleanup_dirs = plan_runtime_files(package, runtime)
    config_mode = (
        runtime.config_toml.stat().st_mode & 0o777
        if runtime.config_toml.is_file()
        else 0o600
    )
    mutations.append(Mutation(runtime.config_toml, rendered_config.encode(), config_mode))

    current_state = read_json(runtime.runtime / USER_STATE, default={})
    retired, retired_cleanup, retirement_warnings = _retired_runtime(
        runtime, current_state, owned_hashes, installed_version
    )
    mutations.extend(retired)
    cleanup_dirs.extend(retired_cleanup)

    cache_mutations, cache_cleanup = _retire_source_cache(runtime)
    mutations.extend(cache_mutations)
    cleanup_dirs.extend(cache_cleanup)

    skill_mutations, skill_cleanup, skill_warnings = _retire_skills(runtime, current_state)
    mutations.extend(skill_mutations)
    cleanup_dirs.extend(skill_cleanup)

    chosen: dict[Path, Mutation] = {}
    for mutation in mutations:
        safe_path(mutation.path, home)
        chosen[mutation.path] = mutation

    state = {
        "schema_version": 2,
        "version": package.version,
        "workflow": "Smart Orchestration",
        "mode": "global",
        "owned_runtime_files": sorted(owned_hashes),
        "owned_runtime_hashes": dict(sorted(owned_hashes.items())),
        "owned_workers": sorted(package.worker_names),
        "owned_skills": [],
    }
    state_mutation = json_mutation(runtime.runtime / USER_STATE, state)
    chosen[state_mutation.path] = state_mutation

    changed: list[Mutation] = []
    before_by_path: dict[str, bytes | None] = {}
    for path, mutation in chosen.items():
        safe_path(path, home)
        before = _read(path)
        if before == mutation.content:
            continue
        mode = path.stat().st_mode & 0o777 if path.exists() else mutation.mode
        changed.append(Mutation(path, mutation.content, mode))
        before_by_path[str(path)] = before

    assessment_after = assess_configuration(parse_config(rendered_config))
    warnings = list(
        dict.fromkeys(
            default_warnings
            + assessment_after["warnings"]
            + retirement_warnings
            + skill_warnings
        )
    )
    if (home / "AGENTS.override.md").is_file():
        warnings.append(
            "AGENTS.override.md is preserved; activation also uses developer_instructions."
        )
    for name, profile in parsed.get("profiles", {}).items():
        if isinstance(profile, dict) and "developer_instructions" in profile:
            warnings.append(
                f"Profile {name!r} overrides developer_instructions; verify activation when using it."
            )

    plan = OperationPlan(
        "install-smart-global",
        changed,
        warnings,
        [],
        {
            "workflow": "Smart Orchestration",
            "version": package.version,
            "scope": str(home),
            "project_mutations": 0,
            "parent_settings": "preserved",
            "child_defaults_added": defaults_added,
            "retired_runtime_files": len(retired),
            "retired_skills": len(set(read_string_list(current_state, "owned_skills"))),
        },
        cleanup_dirs=cleanup_dirs,
    )
    return plan, before_by_path


def apply_plan(
    plan: OperationPlan, before: dict[str, bytes | None], home: Path
) -> Path | None:
    home = home.expanduser().absolute()
    if not plan.mutations:
        return None

    home.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = home / ".smart-orchestration-install.lock"
    safe_path(lock, home)
    try:
        lock.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise ValidationError(
            "Another installer or stale install lock exists; inspect it before retrying"
        ) from exc

    try:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        backup = home / ".smart-orchestration-backups" / stamp
        safe_path(backup, home)
        records: list[dict] = []
        backup_mutations: list[Mutation] = []
        created_dirs: set[Path] = set()

        for mutation in plan.mutations:
            path = mutation.path
            safe_path(path, home)
            if _read(path) != before[str(path)]:
                raise ValidationError(
                    f"File changed during preparation; stop and report the conflict: {path}"
                )
            cursor = path.parent
            while cursor != home and not cursor.exists():
                created_dirs.add(cursor)
                cursor = cursor.parent
            relative = path.relative_to(home)
            previous = before[str(path)]
            if previous is not None:
                backup_mutations.append(
                    Mutation(backup / "files" / relative, previous, 0o600)
                )
            records.append(
                {
                    "path": str(relative),
                    "existed": previous is not None,
                    "before": digest(previous) if previous is not None else None,
                    "after": digest(mutation.content)
                    if mutation.content is not None
                    else None,
                    "mode": mutation.mode,
                    "before_mode": path.stat().st_mode & 0o777
                    if path.exists()
                    else None,
                }
            )

        manifest = json.dumps(
            {
                "schema": 1,
                "workflow": "Smart Orchestration",
                "files": records,
                "created_dirs": [
                    str(path.relative_to(home))
                    for path in sorted(
                        created_dirs, key=lambda item: (len(item.parts), str(item))
                    )
                ],
            },
            indent=2,
        ).encode()
        backup_mutations.append(Mutation(backup / "manifest.json", manifest, 0o600))
        backup.mkdir(parents=True, exist_ok=False, mode=0o700)
        OperationPlan(
            "backup-and-install-smart",
            backup_mutations + plan.mutations,
            [],
            [],
            cleanup_dirs=plan.cleanup_dirs,
        ).apply()
        return backup
    finally:
        lock.rmdir()


def status(home: Path) -> dict:
    home = home.expanduser().absolute()
    runtime = RuntimePaths(home)
    config_path = runtime.config_toml
    safe_path(config_path, home)
    cfg = parse_config(config_path.read_text()) if config_path.is_file() else {}
    instructions = cfg.get("developer_instructions", "")
    policy = runtime.runtime / "smart_orchestration.md"
    version = runtime.runtime / "operate" / "VERSION"
    for path in (policy, version):
        safe_path(path, home)

    block_ok = False
    if (
        isinstance(instructions, str)
        and SMART.start in instructions
        and SMART.end in instructions
    ):
        block_ok = bool(extract(instructions, SMART))

    return {
        "workflow": "Smart Orchestration",
        "configuration_assessment": assess_configuration(cfg),
        "global_bootstrap_present": block_ok,
        "policy_present": policy.is_file(),
        "version": version.read_text().strip() if version.is_file() else None,
        "note": (
            "Disk configuration only; restart Codex after changes and verify "
            "effective role/model behavior in a live task."
        ),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--codex-home",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME", "~/.codex")),
    )
    parser.add_argument("--package-root", type=Path, default=PACKAGE)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--restore-backup",
        type=Path,
        help="Exact conflict-checked restoration of one backup; preview unless --apply",
    )
    args = parser.parse_args(argv)

    try:
        if args.check:
            if args.apply or args.restore_backup:
                raise ValidationError("--check cannot be combined with --apply/restore")
            print(json.dumps(status(args.codex_home), indent=2, sort_keys=True))
            return 0

        if args.restore_backup:
            from runtime.smart_restore import prepare_restore

            plan, before = prepare_restore(args.codex_home, args.restore_backup)
        else:
            plan, before = prepare(args.package_root, args.codex_home)

        result = plan.summary()
        result["applied"] = False
        if not args.apply:
            result["planned_files"] = [str(mutation.path) for mutation in plan.mutations]
            result["status"] = (
                "Preview only. Re-run with --apply in this session; restart Codex "
                "manually after a successful apply."
            )
        else:
            backup = apply_plan(plan, before, args.codex_home)
            result = {
                "workflow": "Smart Orchestration",
                "version": plan.details["version"],
                "applied": True,
                "changed_files": len(plan.mutations),
                "backup": str(backup) if backup else None,
                "warnings": plan.warnings,
                "status": (
                    "Installed globally. Restart Codex manually after this command finishes."
                    if backup
                    else "Already installed; no writes."
                ),
            }

        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, WorkflowError) as exc:
        print(json.dumps({"applied": False, "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
