"""Preserved current Smart contracts, updated for v2's role and safety boundaries."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "codex_workflow"
sys.path.insert(0, str(PACKAGE))
from runtime import smart_install
from runtime._toml import tomllib
from runtime.errors import ValidationError
from runtime.layout import BUILTIN_WORKERS, PackageLayout, RuntimePaths
from runtime.smart_restore import prepare_restore

VERSION = "2.2.0"
EXPECTED = {
    "simple_executor": ("gpt-6-luna", "low"),
    "routine_executor": ("gpt-6-luna", "high"),
    "default_executor": ("gpt-6-luna", "xhigh"),
    "senior_executor": ("gpt-6-sol", "xhigh"),
    "tester": ("gpt-6-luna", "high"),
    "companion": ("gpt-6-luna", "medium"),
    "investigator": ("gpt-6-luna", "xhigh"),
    "archivist": ("gpt-6-luna", "medium"),
}


class PackageContracts(unittest.TestCase):
    def test_current_package_and_model_map(self):
        package = PackageLayout.resolve(PACKAGE)
        self.assertEqual(package.version, VERSION)
        self.assertEqual(package.worker_names, BUILTIN_WORKERS)
        self.assertEqual(set(EXPECTED), BUILTIN_WORKERS)
        for role, expected in EXPECTED.items():
            cfg = tomllib.loads((PACKAGE / "agents" / f"{role}.toml").read_text())
            self.assertEqual((cfg["model"], cfg["model_reasoning_effort"]), expected)
            self.assertIs(cfg["agents"]["enabled"], role in {"routine_executor", "default_executor"})
            self.assertLess(len(cfg["developer_instructions"].split()), 200, role)

    def test_policy_is_compact_and_keeps_operator_judge_split(self):
        policy = (PACKAGE / "smart_orchestration.md").read_text()
        flat = " ".join(policy.split())
        self.assertLess(len(policy.split()), 1200)
        self.assertLess(len((PACKAGE / "verification.md").read_text().split()), 700)
        for phrase in ("One adaptive execution loop", "routine_executor / Luna High",
                       "tester / Luna High", "No writer can self-certify a required independent gate",
                       "never close unrelated or active work"):
            self.assertIn(phrase, flat)

    def test_legacy_active_tree_is_gone(self):
        retired = ("AGENTS.md", "heavy_route.md", "medium_route.md", "archivist.md", "project_docs", "resources",
                   "runtime/workflow.py", "runtime/lifecycle.py", "runtime/project_ops.py", "runtime/release.py",
                   "runtime/efficiency.py", "runtime/capture_check.py", "runtime/platform_settings.py",
                   "operate/bootstrap.md", "operate/install.md", "operate/update.md", "operate/remove.md")
        for relative in retired:
            self.assertFalse((PACKAGE / relative).exists(), relative)

    def test_readme_uses_main_preview_apply_flow(self):
        readme = (ROOT / "README.md").read_text()
        flat = " ".join(readme.split())
        self.assertIn("current HEAD commit SHA of main", flat)
        self.assertIn("without --apply first and inspect the preview", flat)
        self.assertIn("run the same command with --apply", flat)
        installation = readme.split("## Installation or update", 1)[1]
        prompt = installation.split("```text", 2)[1]
        self.assertIn("Do not use GitHub Releases", prompt)
        self.assertNotIn("latest non-draft Smart Orchestration release", prompt)
        self.assertNotIn("workflow.py validate", readme)
        self.assertIn("restart Codex manually", readme)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name).resolve() / "home"
        self.home.mkdir()
        self.original_config = ('model="gpt-6-sol"\nmodel_reasoning_effort="medium"\n'
                                'service_tier="standard"\n[agents]\nenabled=true\n')
        (self.home / "config.toml").write_text(self.original_config)

    def install(self):
        plan, before = smart_install.prepare(PACKAGE, self.home)
        backup = smart_install.apply_plan(plan, before, self.home)
        return plan, backup

    def test_fresh_install_preserves_parent_and_projects(self):
        project = Path(self.tmp.name) / "project"
        project.mkdir()
        (project / "important.txt").write_text("owner data")
        before_project = (project / "important.txt").read_bytes()
        plan, backup = self.install()
        self.assertIsNotNone(backup)
        self.assertEqual(plan.details["project_mutations"], 0)
        self.assertEqual((project / "important.txt").read_bytes(), before_project)
        cfg = tomllib.loads((self.home / "config.toml").read_text())
        self.assertEqual(cfg["model"], "gpt-6-sol")
        self.assertEqual(cfg["model_reasoning_effort"], "medium")
        self.assertEqual(cfg["service_tier"], "standard")
        self.assertIs(cfg["agents"]["enabled"], True)
        self.assertEqual(cfg["agents"]["default_subagent_model"], "gpt-6-luna")
        self.assertEqual(cfg["agents"]["default_subagent_reasoning_effort"], "medium")
        self.assertIn("Smart Orchestration", cfg["developer_instructions"])
        runtime = RuntimePaths(self.home)
        self.assertEqual((runtime.runtime / "operate/VERSION").read_text(), VERSION + "\n")
        self.assertTrue((runtime.runtime / "smart_orchestration.md").is_file())
        self.assertFalse((runtime.runtime / "heavy_route.md").exists())
        for role in EXPECTED:
            self.assertTrue((runtime.agents / f"{role}.toml").is_file())

    def test_reapply_is_idempotent(self):
        self.install()
        plan, _ = smart_install.prepare(PACKAGE, self.home)
        self.assertEqual(plan.mutations, [])

    def test_exact_rollback_restores_preinstall_state(self):
        _, backup = self.install()
        self.assertIsNotNone(backup)
        restore, before = prepare_restore(self.home, backup)
        smart_install.apply_plan(restore, before, self.home)
        self.assertEqual((self.home / "config.toml").read_text(), self.original_config)
        self.assertFalse((self.home / "codex_workflow").exists())
        self.assertFalse((self.home / "AGENTS.md").exists())
        self.assertFalse((self.home / "agents").exists())

    def test_custom_worker_blocks_replacement(self):
        self.install()
        worker = self.home / "agents/default_executor.toml"
        worker.write_text(worker.read_text() + "\n# owner customization\n")
        with self.assertRaises(ValidationError):
            smart_install.prepare(PACKAGE, self.home)

    def test_prepare_apply_conflict_stops_without_writes(self):
        plan, before = smart_install.prepare(PACKAGE, self.home)
        (self.home / "config.toml").write_text(self.original_config + "\n# changed concurrently\n")
        with self.assertRaises(ValidationError):
            smart_install.apply_plan(plan, before, self.home)
        self.assertFalse((self.home / "codex_workflow").exists())

    def test_retires_recorded_legacy_runtime_and_skill(self):
        self.install()
        runtime = RuntimePaths(self.home)
        legacy = runtime.runtime / "heavy_route.md"
        legacy.write_text("legacy route\n")
        state_path = runtime.runtime / "install_state.json"
        state = json.loads(state_path.read_text())
        state["owned_runtime_files"].append("heavy_route.md")
        state["owned_runtime_hashes"]["heavy_route.md"] = smart_install.digest(legacy.read_bytes())
        skill = runtime.skills / "deployment-token-report"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("<!-- codex-workflow-skill: deployment-token-report -->\n# retired\n")
        (skill / "data.txt").write_text("old")
        # v2 requires actual baseline bytes and provenance, not merely a marker.
        for path in skill.iterdir():
            target = runtime.runtime / "templates/skills/deployment-token-report" / path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
            relative = target.relative_to(runtime.runtime).as_posix()
            state["owned_runtime_files"].append(relative)
            state["owned_runtime_hashes"][relative] = smart_install.digest(target.read_bytes())
        state["owned_skills"] = ["deployment-token-report"]
        state_path.write_text(json.dumps(state, indent=2) + "\n")
        plan, before = smart_install.prepare(PACKAGE, self.home)
        smart_install.apply_plan(plan, before, self.home)
        self.assertFalse(legacy.exists())
        self.assertFalse(skill.exists())

    def test_migrates_legacy_state_without_hashes_using_source_cache(self):
        self.install()
        runtime = RuntimePaths(self.home)
        legacy = runtime.runtime / "heavy_route.md"
        legacy.write_text("legacy route\n")
        generated = runtime.runtime / "templates/AGENTS.md"
        generated.parent.mkdir(parents=True, exist_ok=True)
        generated.write_text("legacy project template\n")
        source = runtime.runtime / ".source_backup" / VERSION
        source.mkdir(parents=True)
        (source / "heavy_route.md").write_text("legacy route\n")
        (source / "AGENTS.md").write_text("legacy project template\n")
        state_path = runtime.runtime / "install_state.json"
        state = json.loads(state_path.read_text())
        state["schema_version"] = 1
        state.pop("owned_runtime_hashes", None)
        state["owned_runtime_files"].extend(["heavy_route.md", "templates/AGENTS.md"])
        state_path.write_text(json.dumps(state, indent=2) + "\n")
        plan, before = smart_install.prepare(PACKAGE, self.home)
        smart_install.apply_plan(plan, before, self.home)
        self.assertFalse(legacy.exists())
        self.assertFalse(generated.exists())
        # Safety correction: backups are preserved, not swept on routine updates.
        self.assertTrue(source.exists())
        self.assertEqual((source / "heavy_route.md").read_text(), "legacy route\n")

    def test_locally_modified_retired_file_is_preserved(self):
        self.install()
        runtime = RuntimePaths(self.home)
        legacy = runtime.runtime / "heavy_route.md"
        legacy.write_text("owner changed\n")
        state_path = runtime.runtime / "install_state.json"
        state = json.loads(state_path.read_text())
        state["owned_runtime_files"].append("heavy_route.md")
        state["owned_runtime_hashes"]["heavy_route.md"] = "0" * 64
        state_path.write_text(json.dumps(state, indent=2) + "\n")
        plan, before = smart_install.prepare(PACKAGE, self.home)
        self.assertTrue(any("Preserved retired managed file" in item for item in plan.warnings))
        smart_install.apply_plan(plan, before, self.home)
        self.assertEqual(legacy.read_text(), "owner changed\n")

    def test_install_path_never_requires_self_quit(self):
        readme = (ROOT / "README.md").read_text()
        guide = (PACKAGE / "operate/smart_install.md").read_text()
        runtime = (PACKAGE / "runtime/smart_install.py").read_text()
        for forbidden in ("Quit Codex before applying", "quit Codex and retry", "Preview only. Quit Codex", "wait for Codex to terminate"):
            self.assertNotIn(forbidden, readme)
            self.assertNotIn(forbidden, guide)
            self.assertNotIn(forbidden, runtime)
        self.assertIn("must not quit, relaunch, or wait for Codex to exit", guide)
        self.assertIn("restart codex manually", runtime.lower())


if __name__ == "__main__":
    unittest.main()
