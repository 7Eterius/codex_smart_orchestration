"""Materialize the standalone Smart runtime and its named workers."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .errors import ValidationError
from .layout import USER_STATE, WORKER_MARKER, PackageLayout, RuntimePaths
from .markers import USER_MANAGED, append_region, extract, replace
from .plan import read_json, read_string_list, text_mutation
from .transaction import Mutation


def _hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def plan_runtime_files(
    package: PackageLayout,
    runtime: RuntimePaths,
) -> tuple[list[Mutation], dict[str, str], list[Path]]:
    mutations: list[Mutation] = []
    owned_hashes: dict[str, str] = {}
    cleanup_dirs: list[Path] = []

    excluded = {"agents", "templates", ".source_backup", ".backups", USER_STATE}
    for source in sorted(package.root.rglob("*")):
        relative = source.relative_to(package.root)
        if (
            not relative.parts
            or relative.parts[0] in excluded
            or "__pycache__" in relative.parts
            or source.suffix == ".pyc"
            or not source.is_file()
        ):
            continue
        content = source.read_bytes()
        target = runtime.runtime / relative
        mutations.append(Mutation(target, content))
        owned_hashes[relative.as_posix()] = _hash(content)

    template_root = runtime.runtime / "templates" / "agents"
    for source in sorted(package.agent_templates.glob("*.toml")):
        content = source.read_bytes()
        target = template_root / source.name
        mutations.append(Mutation(target, content))
        owned_hashes[target.relative_to(runtime.runtime).as_posix()] = _hash(content)

    incoming_workers = package.worker_names
    if template_root.is_dir():
        for target in sorted(template_root.glob("*.toml")):
            if target.stem in incoming_workers:
                continue
            validate_worker_owner(target, target.stem)
            mutations.append(Mutation(target, None))
            cleanup_dirs.append(target.parent)

    mutations.extend(plan_user_agents(package, runtime))
    worker_mutations, worker_cleanup = plan_workers(runtime, package)
    mutations.extend(worker_mutations)
    cleanup_dirs.extend(worker_cleanup)
    return mutations, owned_hashes, cleanup_dirs


def plan_user_agents(package: PackageLayout, runtime: RuntimePaths) -> list[Mutation]:
    source = (package.operate / "user_AGENTS.md").read_text(encoding="utf-8")
    managed = extract(source, USER_MANAGED)
    if runtime.user_agents.is_file():
        current = runtime.user_agents.read_text(encoding="utf-8")
        if USER_MANAGED.start in current or USER_MANAGED.end in current:
            rendered = replace(current, USER_MANAGED, managed)
        else:
            rendered = append_region(current, USER_MANAGED, managed)
    else:
        rendered = append_region("", USER_MANAGED, managed)
    return [text_mutation(runtime.user_agents, rendered)]


def plan_workers(
    runtime: RuntimePaths, package: PackageLayout
) -> tuple[list[Mutation], list[Path]]:
    mutations: list[Mutation] = []
    cleanup_dirs: list[Path] = []
    current_state = read_json(runtime.runtime / USER_STATE, default={})
    previous_owned = set(read_string_list(current_state, "owned_workers"))
    workers = package.worker_names

    for worker in sorted(workers):
        source = package.agent_templates / f"{worker}.toml"
        mutations.append(
            text_mutation(
                runtime.agents / f"{worker}.toml",
                source.read_text(encoding="utf-8"),
            )
        )

    for worker in sorted(previous_owned - workers):
        target = runtime.agents / f"{worker}.toml"
        if target.exists():
            validate_worker_owner(target, worker)
            mutations.append(Mutation(target, None))
            cleanup_dirs.append(target.parent)

    return mutations, cleanup_dirs


def validate_worker_owner(path: Path, worker: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValidationError(f"worker path is not a regular file: {path}")
    match = WORKER_MARKER.search(path.read_text(encoding="utf-8"))
    if match is None or match.group(1) != worker:
        raise ValidationError(f"refusing to replace/remove unowned worker file: {path}")
