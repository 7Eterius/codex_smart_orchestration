"""Standalone Smart package contracts, including bounded-delegation roles."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from ._toml import tomllib
from .errors import ValidationError
from .markers import USER_MANAGED, extract

# Stable migration identifier, not the source/distribution repository.
USER_ID = "<!-- codex-workflow-user-id: viettran-edgeAI/codex_workflow -->"
USER_STATE = "install_state.json"
WORKER_MARKER = re.compile(r"^# codex-workflow-worker: ([A-Za-z0-9_-]+)$", re.MULTILINE)
VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
BUILTIN_WORKERS = frozenset({
    "simple_executor", "routine_executor", "default_executor",
    "senior_executor", "tester", "archivist", "companion", "investigator",
})
DELEGATING_WORKERS = frozenset({"routine_executor", "default_executor"})
_REQUIRED = (
    "smart_orchestration.md", "execution.md", "verification.md", "browser.md",
    "runtime_check.md", "operate/VERSION", "operate/smart_install.md",
    "operate/user_AGENTS.md", "runtime/__init__.py", "runtime/_toml.py",
    "runtime/agent_defaults.py", "runtime/config_assessment.py", "runtime/errors.py",
    "runtime/layout.py", "runtime/markers.py", "runtime/plan.py", "runtime/runtime_ops.py",
    "runtime/smart_config.py", "runtime/smart_install.py", "runtime/smart_restore.py",
    "runtime/transaction.py", "runtime/candidate.py", "runtime/allocation.py",
    "runtime/boundary.py", "boundary.md", "design.md",
)


INSTALLED_RUNTIME_FILES = frozenset(_REQUIRED) | frozenset(
    f"templates/agents/{role}.toml" for role in BUILTIN_WORKERS
)


@dataclass(frozen=True)
class PackageLayout:
    root: Path
    operate: Path
    agent_templates: Path

    @classmethod
    def resolve(cls, root: Path) -> "PackageLayout":
        root = root.expanduser()
        if root.is_symlink():
            raise ValidationError("Package root must not be a symlink")
        root = root.resolve()
        if not (root / "operate/VERSION").is_file():
            nested = root / "codex_workflow"
            if nested.is_symlink():
                raise ValidationError("Nested package root must not be a symlink")
            if (nested / "operate/VERSION").is_file():
                root = nested
            else:
                raise ValidationError(f"package root does not contain operate/VERSION: {root}")
        layout = cls(root, root / "operate", root / "agents")
        layout.validate()
        return layout

    def validate(self) -> None:
        symlinks = [p for p in self.root.rglob("*") if p.is_symlink()]
        if symlinks:
            raise ValidationError(f"package contains symlinks: {symlinks[:3]}")
        if VERSION_RE.fullmatch(self.version) is None:
            raise ValidationError(f"VERSION must be stable semantic version X.Y.Z: {self.version!r}")
        missing = [p for p in _REQUIRED if not (self.root / p).is_file()]
        if missing:
            raise ValidationError(f"package files missing: {missing}")
        text = (self.operate / "user_AGENTS.md").read_text(encoding="utf-8")
        if USER_ID not in text:
            raise ValidationError("package user_AGENTS.md ownership marker is missing")
        if f"<!-- codex-workflow-version: {self.version} -->" not in text:
            raise ValidationError("package version and user_AGENTS.md marker disagree")
        extract(text, USER_MANAGED)
        if self.worker_names != BUILTIN_WORKERS:
            raise ValidationError(
                "package worker set is incomplete or unsupported; "
                f"missing={sorted(BUILTIN_WORKERS-self.worker_names)}, "
                f"unexpected={sorted(self.worker_names-BUILTIN_WORKERS)}"
            )
        for worker in self.worker_names:
            text = (self.agent_templates / f"{worker}.toml").read_text(encoding="utf-8")
            marker = WORKER_MARKER.search(text)
            if marker is None or marker.group(1) != worker:
                raise ValidationError(f"worker ownership marker missing or wrong: {worker}")
            try:
                cfg = tomllib.loads(text)
            except tomllib.TOMLDecodeError as error:
                raise ValidationError(f"invalid worker TOML {worker}: {error}") from error
            if cfg.get("name") != worker:
                raise ValidationError(f"worker name disagrees with filename: {worker}")
            for field in ("description", "developer_instructions", "model", "model_reasoning_effort"):
                if not isinstance(cfg.get(field), str) or not cfg[field].strip():
                    raise ValidationError(f"worker {worker} lacks a nonempty {field}")
            agents = cfg.get("agents")
            expected = worker in DELEGATING_WORKERS
            if not isinstance(agents, dict) or agents.get("enabled") is not expected:
                raise ValidationError(f"worker {worker} must set agents.enabled={expected}")

    @property
    def version(self) -> str:
        lines = (self.operate / "VERSION").read_text(encoding="utf-8").splitlines()
        if len(lines) != 1 or not lines[0]:
            raise ValidationError("VERSION must contain exactly one non-empty line")
        return lines[0]

    @property
    def worker_names(self) -> set[str]:
        return {p.stem for p in self.agent_templates.glob("*.toml") if p.is_file()}

    @property
    def files(self) -> tuple[Path, ...]:
        """Only declared package inputs are installed, not adjacent scratch or caches."""
        names = set(_REQUIRED) | {f"agents/{role}.toml" for role in BUILTIN_WORKERS}
        return tuple(self.root / name for name in sorted(names))

    @property
    def fingerprint(self) -> str:
        """Content identity, not a signature or proof of an upstream Git commit."""
        entries = {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in self.files}
        return hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()


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
