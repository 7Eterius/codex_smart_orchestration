"""Materialize declared Smart inputs and workers without adopting unrelated files."""
from __future__ import annotations

import hashlib
from pathlib import Path

from .errors import ValidationError
from .layout import USER_STATE, WORKER_MARKER, PackageLayout, RuntimePaths
from .markers import USER_MANAGED, append_region, extract, replace
from .plan import read_json, read_string_list, text_mutation
from .transaction import Mutation


def plan_runtime_files(package: PackageLayout, runtime: RuntimePaths):
    mutations: list[Mutation] = []
    owned_hashes: dict[str, str] = {}
    for source in package.files:
        relative = source.relative_to(package.root)
        if relative.parts[0] == "agents":
            target = runtime.runtime / "templates" / relative
        else:
            target = runtime.runtime / relative
        content = source.read_bytes()
        mutations.append(Mutation(target, content))
        owned_hashes[target.relative_to(runtime.runtime).as_posix()] = hashlib.sha256(content).hexdigest()
    mutations.extend(plan_user_agents(package, runtime))
    # Retired templates are handled once by the installer's hash-checked retirement,
    # never first scheduled for unconditional deletion and later "preserved" in prose.
    mutations.extend(plan_workers(runtime, package))
    return mutations, owned_hashes, []


def plan_user_agents(package: PackageLayout, runtime: RuntimePaths) -> list[Mutation]:
    source = (package.operate / "user_AGENTS.md").read_text(encoding="utf-8")
    managed = extract(source, USER_MANAGED).replace("~/.codex", str(runtime.codex_home))
    if runtime.user_agents.is_file():
        current = runtime.user_agents.read_text(encoding="utf-8")
        if USER_MANAGED.start in current or USER_MANAGED.end in current:
            rendered = replace(current, USER_MANAGED, managed)
        else:
            rendered = append_region(current, USER_MANAGED, managed)
    else:
        rendered = append_region("", USER_MANAGED, managed)
    return [text_mutation(runtime.user_agents, rendered)]


def plan_workers(runtime: RuntimePaths, package: PackageLayout) -> list[Mutation]:
    # Preserve other/unlisted workers. No v2 role has been retired; future retirement
    # must verify its exact previous template, not merely an ownership comment.
    return [text_mutation(runtime.agents / f"{worker}.toml",
                          (package.agent_templates / f"{worker}.toml").read_text(encoding="utf-8"))
            for worker in sorted(package.worker_names)]


def validate_worker_owner(path: Path, worker: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValidationError(f"worker path is not a regular file: {path}")
    match = WORKER_MARKER.search(path.read_text(encoding="utf-8"))
    if match is None or match.group(1) != worker:
        raise ValidationError(f"refusing to replace/remove unowned worker file: {path}")
