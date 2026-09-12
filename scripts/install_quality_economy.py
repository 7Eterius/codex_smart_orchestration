#!/usr/bin/env python3
"""Preview and adopt the native Quality Economy fork for explicit projects.

No network, model calls or Git operations. Uses the inherited transactional
lifecycle. Stop Codex agents before applying. Python 3.11 or newer is required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

if sys.version_info < (3, 11):
    raise SystemExit("Quality Economy requires Python 3.11 or newer")

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "codex_workflow"
sys.path.insert(0, str(PACKAGE))

from runtime.errors import ValidationError, WorkflowError
from runtime.layout import PROJECT_ID, PackageLayout, ProjectPaths, RuntimePaths
from runtime.markers import PROJECT_PERSONALIZATION, extract
from runtime.personalization import materialize_personalization
from runtime.lifecycle import plan_bootstrap, plan_project_install, plan_update
from runtime.plan import OperationPlan
from runtime.release import RELEASE_REPOSITORY, parse_semver


def build_plan(home: Path, projects: list[Path]) -> OperationPlan:
    """Preflight all explicit destinations before any live write."""
    incoming = PackageLayout.resolve(PACKAGE)
    if RELEASE_REPOSITORY != "7Eterius/codex_workflow":
        raise ValidationError("Run this helper from the Quality Economy fork.")
    home = home.expanduser().resolve()
    roots = [p.expanduser().resolve(strict=True) for p in projects]
    if not roots or len(set(roots)) != len(roots):
        raise ValidationError("Provide unique, existing project directories.")
    for root in roots:
        if not root.is_dir():
            raise ValidationError(f"Project is not a directory: {root}")
        if root.is_relative_to(home) or home.is_relative_to(root):
            raise ValidationError("Project and Codex home must not contain one another.")
        if root.is_relative_to(ROOT) or ROOT.is_relative_to(root):
            raise ValidationError("Keep the source checkout outside target projects.")
        if any(other != root and root.is_relative_to(other) for other in roots):
            raise ValidationError("Nested project targets require separate reviewed installs.")
        project_paths = ProjectPaths(root)
        if project_paths.source_dir.exists():
            raise ValidationError("Move the old Codex_Workflow staging directory outside the project first; no cleanup was performed.")
        resource = project_paths.personalization
        for entry in (project_paths.active, project_paths.disabled):
            if entry.is_file() and resource.is_file():
                current = entry.read_text(encoding="utf-8")
                if PROJECT_ID in current and PROJECT_PERSONALIZATION.start in current:
                    if extract(current, PROJECT_PERSONALIZATION) != materialize_personalization(resource.read_text(encoding="utf-8")):
                        raise ValidationError(f"Personalization drift in {root}; reconcile it before adoption.")
        if resource.is_file() and "### Quality Economy v1" in resource.read_text(encoding="utf-8"):
            raise ValidationError(
                f"Remove the earlier opt-in Quality Economy v1 block via personalization "
                f"before adopting native defaults: {root}. Preserve other owner preferences."
            )
    runtime = RuntimePaths(home)
    installed = None
    if runtime.runtime.exists():
        installed = PackageLayout.resolve(runtime.runtime, allow_legacy=True)
        if parse_semver(installed.version) > parse_semver(incoming.version):
            raise ValidationError("Refusing to downgrade a newer installed runtime.")
    plans = []
    for i, root in enumerate(roots):
        project = ProjectPaths(root)
        if installed is None:
            plan = plan_bootstrap(incoming, runtime, project) if i == 0 else plan_project_install(incoming, project)
        else:
            # plan_update validates the project's own historical source version.
            # It can adopt another old project after the global runtime has already
            # changed, unlike the public CLI's equal-version update guard.
            plan = plan_update(incoming, runtime, project)
            if not project.active.exists() and not project.disabled.exists():
                plans.append(plan_project_install(incoming, project))
        plans.append(plan)
    merged = {}
    for plan in plans:
        for mutation in plan.mutations:
            path = mutation.path.resolve(strict=False)
            previous = merged.get(path)
            if previous is not None and (previous.content, previous.mode) != (mutation.content, mutation.mode):
                raise ValidationError(f"Conflicting planned writes: {path}")
            merged[path] = mutation
    return OperationPlan(
        "adopt-quality-economy",
        list(merged.values()),
        [warning for plan in plans for warning in plan.warnings],
        [action for plan in plans for action in plan.agent_actions],
        {
            "source": RELEASE_REPOSITORY,
            "version": incoming.version,
            "projects": [str(p) for p in roots],
            "backups": [plan.details["backup"] for plan in plans if "backup" in plan.details],
            "personalization": "Preserved. Explicit routing overrides still apply.",
            "scope": "Workflow-managed files only; no application source, live-store or Git operations.",
        },
        [path for plan in plans for path in plan.cleanup_dirs],
    )


def fingerprint(plan: OperationPlan) -> str:
    """Bind approval to current targets and proposed bytes, excluding new backups.

This detects changes between preview and apply, but is not a concurrent-writer
lock. Active agents must be stopped. The inherited transaction handles rollback.
"""
    rows = []
    backup_roots = [Path(p) for p in plan.details.get("backups", [])]
    for mutation in plan.mutations:
        path = mutation.path
        if any(path.is_relative_to(root) for root in backup_roots):
            continue
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValidationError(f"Unsafe target: {path}")
        before = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        before_mode = path.stat().st_mode & 0o777 if path.exists() else None
        after = hashlib.sha256(mutation.content).hexdigest() if mutation.content is not None else None
        rows.append((str(path), before, before_mode, after, mutation.mode))
    return hashlib.sha256(json.dumps(sorted(rows), separators=(",", ":")).encode()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, action="append", required=True)
    parser.add_argument("--codex-home", type=Path,
                        default=Path(os.environ.get("CODEX_HOME", "~/.codex")))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--approve", help="SHA-256 from a reviewed preview, required for --apply")
    args = parser.parse_args(argv)
    try:
        plan = build_plan(args.codex_home, args.project)
        approval = fingerprint(plan)
        result = plan.summary()
        result.update({"applied": False, "approval_sha256": approval})
        # Full paths, without file contents or secrets; the inherited summary is bounded.
        result["planned_files"] = [str(m.path) for m in plan.mutations]
        if args.apply:
            if args.approve != approval:
                raise ValidationError("Approval missing or state changed; review a fresh preview.")
            if fingerprint(plan) != approval:
                raise ValidationError("Files changed during preparation; stop agents and preview again.")
            plan.apply()
            result["applied"] = True
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, WorkflowError) as error:
        print(json.dumps({"applied": False, "error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
