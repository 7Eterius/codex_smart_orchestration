#!/usr/bin/env python3
"""Run inherited functional tests plus native policy/adoption tests.

One monolithic upstream policy-text test is superseded by native contracts.
Two inherited tests are adapted, not omitted: the settings test expects the
new no-history closure; the history fixture derives its next version instead
of hard-coding 1.2.0. Their other assertions and safety intent remain intact.
All other inherited tests run unchanged; no failure is reclassified as a pass.
"""
from __future__ import annotations
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import test_workflow_runtime as upstream
import test_quality_economy as policies
import test_quality_economy_install as adoption

SUPERSEDED = "test_workflow_runtime.MarkerTests.test_operational_policies_are_compact_and_knowledge_aware"
SETTINGS = "test_workflow_runtime.PlatformSettingsTests.test_fixed_route_and_worker_need_no_settings_rendering"
HISTORY = "test_workflow_runtime.LifecycleIntegrationTests.test_projects_update_against_their_recorded_historical_sources"


class ForkSettingsTest(unittest.TestCase):
    def test_fixed_route_and_worker_need_no_settings_rendering(self):
        heavy = (upstream.PACKAGE / "heavy_route.md").read_text(encoding="utf-8")
        default = (upstream.PACKAGE / "agents/default_executor.toml").read_text(encoding="utf-8")
        self.assertNotIn("codex-workflow-effective-config", heavy)
        self.assertNotIn("Fixed Workflow Settings", heavy)
        self.assertIn('model_reasoning_effort = "max"', default)
        self.assertIn('fork_turns="none"', (upstream.PACKAGE / "archivist.md").read_text(encoding="utf-8"))
        self.assertNotIn('fork_turns="200"', (upstream.PACKAGE / "archivist.md").read_text(encoding="utf-8"))


class ForkHistoryTest(upstream.LifecycleIntegrationTests):
    def test_projects_update_against_their_recorded_historical_sources(self):
        self.bootstrap()
        second_root = self.root / "second-project"
        second_root.mkdir()
        second = upstream.ProjectPaths(second_root)
        upstream.plan_project_install(self.package, second).apply()
        version = upstream.next_patch_version(upstream.PACKAGE_VERSION)
        self.assertNotEqual(version, upstream.PACKAGE_VERSION)
        incoming = self.incoming_package("multi-project-incoming", version)
        before = incoming.project_template.read_text(encoding="utf-8")
        heading = f"## Working State ({version})"
        after = before.replace("## Working State", heading)
        self.assertNotEqual(before, after)
        incoming.project_template.write_text(after, encoding="utf-8")
        incoming = upstream.PackageLayout.resolve(incoming.root)
        upstream.plan_update(incoming, self.runtime, self.project).apply()
        second_plan = upstream.plan_update(incoming, self.runtime, second)
        self.assertEqual(second_plan.details["from_version"], version)
        self.assertEqual(second_plan.details["project_from_version"], upstream.PACKAGE_VERSION)
        second_plan.apply()
        self.assertIn(heading, second.active.read_text(encoding="utf-8"))


def flattened(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flattened(item)
        else:
            yield item


def load_tests(loader, standard_tests, pattern):
    inherited = list(flattened(loader.loadTestsFromModule(upstream)))
    for identifier in (SUPERSEDED, SETTINGS, HISTORY):
        if sum(case.id() == identifier for case in inherited) != 1:
            raise RuntimeError("Upstream test layout changed; review native contract mapping.")
    replacements = {
        SETTINGS: ForkSettingsTest("test_fixed_route_and_worker_need_no_settings_rendering"),
        HISTORY: ForkHistoryTest("test_projects_update_against_their_recorded_historical_sources"),
    }
    suite = unittest.TestSuite(replacements.get(case.id(), case)
                              for case in inherited if case.id() != SUPERSEDED)
    suite.addTests(loader.loadTestsFromModule(policies))
    suite.addTests(loader.loadTestsFromModule(adoption))
    return suite


if __name__ == "__main__":
    unittest.main()
