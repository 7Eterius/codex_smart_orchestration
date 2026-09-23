"""Smart Orchestration package and global Codex path contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ._toml import tomllib
from .errors import ValidationError
from .markers import USER_MANAGED, extract

USER_ID = "<!-- codex-workflow-user-id: viettran-edgeAI/codex_workflow -->"
USER_STATE = "install_state.json"
WORKER_MARKER = re.compile(r"^# codex-workflow-worker: ([A-Za-z0-9_-]+)$", re.MULTILINE)
VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")

BUILTIN_WORKERS = frozenset(
    {
        "simple_executor",
        "routine_executor",
        "default_executor",
        "senior_executor",
        "tester",
        "archivist",
        "companion",
        "investigator",
    }
)

_REQUIRED = (
    "smart_orchestration.md",
    "verification.md",
    "operate/VERSION",
    "operate/smart_install.md",
    "operate/user_AGENTS.md",
    "runtime/__init__.py",
    "runtime/_toml.py",
    "runtime/agent_defaults.py",
    "runtime/config_assessment.py",
    "runtime/errors.py",
    "runtime/layout.py",
    "runtime/markers.py",
    "runtime/plan.py",
    "runtime/runtime_ops.py",
    "runtime/smart_config.py",
    "runtime/smart_install.py",
    "runtime/smart_restore.py",
    "runtime/transaction.py",
)


@dataclass(frozen=True)
class PackageLayout:
    root: Path
    operate: Path
    agent_templates: Path

    @classmethod
    def resolve(cls, root: Path) -> "PackageLayout":
        root = root.resolve()
        if not (root / "operate" / "VERSION").is_file():
            nested = root / "codex_workflow"
            if (nested / "operate" / "VERSION").is_file():
                root = nested
            else:
                raise ValidationError(f"package root does not contain operate/VERSION: {root}")
        layout = cls(root, root / "operate", root / "agents")
        layout.validate()
        return layout

    def validate(self) -> None:
        symlinks = [path for path in self.root.rglob("*") if path.is_symlink()]
        if symlinks:
            raise ValidationError(f"package contains symlinks: {symlinks[:3]}")

        version = self.version
        if VERSION_RE.fullmatch(version) is None:
            raise ValidationError(f"VERSION must be stable semantic version X.Y.Z: {version!r}")

        missing = [relative for relative in _REQUIRED if not (self.root / relative).is_file()]
        if missing:
            raise ValidationError(f"package files missing: {missing}")

        user_agents = self.operate / "user_AGENTS.md"
        text = user_agents.read_text(encoding="utf-8")
        if USER_ID not in text:
            raise ValidationError("package user_AGENTS.md ownership marker is missing")
        if f"<!-- codex-workflow-version: {version} -->" not in text:
            raise ValidationError("package version and user_AGENTS.md marker disagree")
        extract(text, USER_MANAGED)

        workers = self.worker_names
        if workers != BUILTIN_WORKERS:
            raise ValidationError(
                "package worker set is incomplete or unsupported; "
                f"missing={sorted(BUILTIN_WORKERS - workers)}, "
                f"unexpected={sorted(workers - BUILTIN_WORKERS)}"
            )
        for worker in workers:
            path = self.agent_templates / f"{worker}.toml"
            text = path.read_text(encoding="utf-8")
            match = WORKER_MARKER.search(text)
            if match is None or match.group(1) != worker:
                raise ValidationError(f"worker ownership marker missing or wrong: {worker}")
            try:
                tomllib.loads(text)
            except tomllib.TOMLDecodeError as error:
                raise ValidationError(f"invalid worker TOML {worker}: {error}") from error

    @property
    def version(self) -> str:
        lines = (self.operate / "VERSION").read_text(encoding="utf-8").splitlines()
        if len(lines) != 1 or not lines[0]:
            raise ValidationError("VERSION must contain exactly one non-empty line")
        return lines[0]

    @property
    def worker_names(self) -> set[str]:
        return {
            path.stem
            for path in self.agent_templates.glob("*.toml")
            if path.is_file()
        }


@dataclass(frozen=True)
class RuntimePaths:
    codex_home: Path

    @property
    def runtime(self) -> Path:
        return self.codex_home / "codex_workflow"

    @property
    def agents(self) -> Path:
        return self.codex_home / "agents"

    @property
    def skills(self) -> Path:
        return self.codex_home / "skills"

    @property
    def config_toml(self) -> Path:
        return self.codex_home / "config.toml"

    @property
    def user_agents(self) -> Path:
        return self.codex_home / "AGENTS.md"
