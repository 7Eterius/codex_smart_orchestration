"""Isolated lifecycle integration tests for native fork adoption.

Use a complete source checkout; never touch a real Codex home or application.
The pinned upstream package is reconstructed through read-only local Git access
when testing upstream migration. CI must fetch full history. No network calls.
"""
from __future__ import annotations
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import install_quality_economy as install
from runtime.errors import ValidationError
from runtime.layout import PackageLayout, ProjectPaths, RuntimePaths
from runtime.lifecycle import plan_bootstrap, plan_enable, plan_personalize, plan_project_install
from runtime.markers import PROJECT_LOCAL, PROJECT_PERSONALIZATION, extract, replace

BASE = "6d9b06f73bee7f899001b0bb102c70529a24313f"


def upstream_package(destination: Path) -> PackageLayout:
    paths = subprocess.run(["git", "ls-tree", "-r", "--name-only", BASE, "codex_workflow"],
                           cwd=install.ROOT, check=True, capture_output=True, text=True).stdout.splitlines()
    if not paths:
        raise RuntimeError("Pinned upstream package missing; use a full-history checkout.")
    for relative in paths:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or path.parts[0] != "codex_workflow":
            raise RuntimeError("Unexpected baseline Git path")
        data = subprocess.run(["git", "show", f"{BASE}:{relative}"], cwd=install.ROOT,
                              check=True, capture_output=True).stdout
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return PackageLayout.resolve(destination / "codex_workflow")


def snapshot(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


class AdoptionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.home = self.root / "codex-home"
        self.projects = [self.root / "Materia", self.root / "RussianReading"]
        for p in self.projects:
            p.mkdir()
            (p / "owner-source.txt").write_text("owner source stays unchanged\n")
            (p / "live-store.bin").write_bytes(b"private-owner-data")
        self.native = PackageLayout.resolve(install.PACKAGE)

    def test_fresh_two_project_preview_does_not_write(self):
        before = snapshot(self.root)
        plan = install.build_plan(self.home, self.projects)
        self.assertEqual(snapshot(self.root), before)
        self.assertEqual(len(plan.agent_actions), 2)
        self.assertEqual(plan.details["source"], "7Eterius/codex_workflow")
        self.assertEqual(len(install.fingerprint(plan)), 64)

    def test_fresh_install_keeps_local_rules_and_live_data(self):
        (self.projects[0] / "AGENTS.md").write_text("Owner-specific safety.\n")
        plan = install.build_plan(self.home, self.projects)
        plan.apply()
        for p in self.projects:
            self.assertIn("Heavy is the default route", (p / "AGENTS.md").read_text())
            self.assertEqual((p / "live-store.bin").read_bytes(), b"private-owner-data")
            self.assertEqual((p / "owner-source.txt").read_text(), "owner source stays unchanged\n")
        self.assertIn("Owner-specific safety", extract((self.projects[0] / "AGENTS.md").read_text(), PROJECT_LOCAL))
        self.assertIn("7Eterius/codex_workflow", (self.home / "codex_workflow/runtime/release.py").read_text())

    def test_duplicate_and_nested_targets_refused(self):
        with self.assertRaises(ValidationError):
            install.build_plan(self.home, [self.projects[0], self.projects[0]])
        nested = self.projects[0] / "nested"
        nested.mkdir()
        with self.assertRaises(ValidationError):
            install.build_plan(self.home, [self.projects[0], nested])

    def test_project_must_not_contain_codex_home(self):
        with self.assertRaises(ValidationError):
            install.build_plan(self.projects[0] / ".codex", [self.projects[0]])

    def test_staging_tree_is_not_silently_cleaned(self):
        staging = self.projects[0] / "Codex_Workflow"
        staging.mkdir()
        (staging / "owner.txt").write_text("keep")
        before = snapshot(self.root)
        with self.assertRaisesRegex(ValidationError, "staging"):
            install.build_plan(self.home, self.projects)
        self.assertEqual(snapshot(self.root), before)

    def test_one_bad_target_prevents_all_writes(self):
        before = snapshot(self.root)
        with self.assertRaises(OSError):
            install.build_plan(self.home, self.projects + [self.root / "missing"])
        self.assertEqual(snapshot(self.root), before)

    def test_approval_changes_after_owner_change(self):
        plan = install.build_plan(self.home, self.projects)
        old = install.fingerprint(plan)
        (self.projects[0] / "AGENTS.md").write_text("New owner rule\n")
        self.assertNotEqual(install.fingerprint(plan), old)

    def test_apply_requires_reviewed_approval(self):
        before = snapshot(self.root)
        with contextlib.redirect_stderr(io.StringIO()):
            status = install.main(["--codex-home", str(self.home), "--project", str(self.projects[0]), "--apply"])
        self.assertEqual(status, 1)
        self.assertEqual(snapshot(self.root), before)

    def test_cli_preview_then_apply(self):
        args = ["--codex-home", str(self.home), "--project", str(self.projects[0])]
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(install.main(args), 0)
        preview = json.loads(output.getvalue())
        self.assertFalse(preview["applied"])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(install.main(args + ["--apply", "--approve", preview["approval_sha256"]]), 0)
        self.assertIn("Heavy is the default route", (self.projects[0] / "AGENTS.md").read_text())

    def test_old_optional_profile_requires_explicit_reconciliation(self):
        plan_bootstrap(self.native, RuntimePaths(self.home), ProjectPaths(self.projects[0])).apply()
        project = ProjectPaths(self.projects[0])
        resource = project.personalization.read_text().replace("Status: default\nDecision: No additional project-scoped workflow decisions.",
            "Status: customized\nDecision: ### Quality Economy v1\nOld opt-in policy.")
        self.assertIn("### Quality Economy v1", resource)
        plan_personalize(project, resource).apply()
        before = snapshot(self.root)
        with self.assertRaisesRegex(ValidationError, "earlier opt-in"):
            install.build_plan(self.home, [self.projects[0]])
        self.assertEqual(snapshot(self.root), before)

    def test_personalization_drift_is_not_overwritten(self):
        plan_bootstrap(self.native, RuntimePaths(self.home), ProjectPaths(self.projects[0])).apply()
        entry = self.projects[0] / "AGENTS.md"
        entry.write_text(replace(entry.read_text(), PROJECT_PERSONALIZATION, "Unreconciled owner decision"))
        with self.assertRaisesRegex(ValidationError, "Personalization drift"):
            install.build_plan(self.home, [self.projects[0]])

    def test_existing_runtime_can_initialize_an_empty_new_project(self):
        plan_bootstrap(self.native, RuntimePaths(self.home), ProjectPaths(self.projects[0])).apply()
        plan = install.build_plan(self.home, [self.projects[1]])
        self.assertTrue(plan.agent_actions)
        plan.apply()
        self.assertIn("Heavy is the default route", (self.projects[1] / "AGENTS.md").read_text())

    def test_upstream_takeover_preserves_state_and_disabled_project(self):
        old = upstream_package(self.root / "baseline")
        runtime = RuntimePaths(self.home)
        plan_bootstrap(old, runtime, ProjectPaths(self.projects[0])).apply()
        plan_project_install(old, ProjectPaths(self.projects[1])).apply()
        for i, root in enumerate(self.projects):
            p = ProjectPaths(root)
            (p.docs / "project_diary.md").write_text(f"Owner history {i}\n")
            p.active.write_text(replace(p.active.read_text(), PROJECT_LOCAL, f"Owner rule {i}"))
        plan_enable(ProjectPaths(self.projects[1]), enable=False).apply()
        plan = install.build_plan(self.home, self.projects)
        self.assertEqual(len(plan.details["backups"]), 2)
        digest = install.fingerprint(plan)
        self.assertEqual(install.fingerprint(install.build_plan(self.home, self.projects)), digest)
        plan.apply()
        self.assertEqual(PackageLayout.resolve(runtime.runtime).version, self.native.version)
        for i, root in enumerate(self.projects):
            p = ProjectPaths(root)
            entry = p.active if i == 0 else p.disabled
            self.assertIn("Heavy is the default route", entry.read_text())
            self.assertEqual(extract(entry.read_text(), PROJECT_LOCAL), f"Owner rule {i}")
            self.assertEqual((p.docs / "project_diary.md").read_text(), f"Owner history {i}\n")
            self.assertEqual((root / "live-store.bin").read_bytes(), b"private-owner-data")
        self.assertFalse(ProjectPaths(self.projects[1]).active.exists())
        for backup in plan.details["backups"]:
            self.assertTrue(Path(backup).is_dir())

    def test_second_project_adoption_after_global_runtime_change(self):
        old = upstream_package(self.root / "baseline")
        runtime = RuntimePaths(self.home)
        plan_bootstrap(old, runtime, ProjectPaths(self.projects[0])).apply()
        plan_project_install(old, ProjectPaths(self.projects[1])).apply()
        install.build_plan(self.home, [self.projects[0]]).apply()
        install.build_plan(self.home, [self.projects[1]]).apply()
        self.assertIn("Heavy is the default route", (self.projects[1] / "AGENTS.md").read_text())


if __name__ == "__main__":
    unittest.main()
