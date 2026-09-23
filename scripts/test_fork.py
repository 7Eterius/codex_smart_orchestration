#!/usr/bin/env python3
"""Run inherited functional/safety tests and the current Smart contract suite.

One old monolithic policy-text test is replaced by Smart contracts. Two fixtures
are adapted: no-history Archivist and dynamic next-version/template heading.
No runtime failure is suppressed. Archive roles come from the current schema.
"""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import package_smart
import test_workflow_runtime as upstream
import test_smart as smart
import test_efficiency as efficiency

SUPERSEDED='test_workflow_runtime.MarkerTests.test_operational_policies_are_compact_and_knowledge_aware'
SETTINGS='test_workflow_runtime.PlatformSettingsTests.test_fixed_route_and_worker_need_no_settings_rendering'
HISTORY='test_workflow_runtime.LifecycleIntegrationTests.test_projects_update_against_their_recorded_historical_sources'

class SmartSettingsTest(unittest.TestCase):
    def test_fixed_route_and_worker_need_no_settings_rendering(self):
        heavy=(upstream.PACKAGE/'heavy_route.md').read_text()
        default=(upstream.PACKAGE/'agents/default_executor.toml').read_text()
        self.assertNotIn('codex-workflow-effective-config',heavy)
        self.assertNotIn('Fixed Workflow Settings',heavy)
        self.assertIn('model_reasoning_effort = "xhigh"',default)
        self.assertIn('fork_turns="none"',(upstream.PACKAGE/'archivist.md').read_text())
        self.assertNotIn('fork_turns="200"',(upstream.PACKAGE/'archivist.md').read_text())

class SmartHistoryTest(upstream.LifecycleIntegrationTests):
    def test_projects_update_against_their_recorded_historical_sources(self):
        self.bootstrap()
        root=self.root/'second-project'; root.mkdir()
        second=upstream.ProjectPaths(root)
        upstream.plan_project_install(self.package,second).apply()
        version=upstream.next_patch_version(upstream.PACKAGE_VERSION)
        self.assertNotEqual(version,upstream.PACKAGE_VERSION)
        incoming=self.incoming_package('multi-project-incoming',version)
        before=incoming.project_template.read_text()
        heading=f'# Smart Orchestration ({version})'
        after=before.replace('# Smart Orchestration',heading)
        self.assertNotEqual(before,after)
        incoming.project_template.write_text(after)
        incoming=upstream.PackageLayout.resolve(incoming.root)
        upstream.plan_update(incoming,self.runtime,self.project).apply()
        plan=upstream.plan_update(incoming,self.runtime,second)
        self.assertEqual(plan.details['from_version'],version)
        self.assertEqual(plan.details['project_from_version'],upstream.PACKAGE_VERSION)
        plan.apply()
        self.assertIn(heading,second.active.read_text())

def flattened(suite):
    for item in suite:
        if isinstance(item,unittest.TestSuite): yield from flattened(item)
        else: yield item

def load_tests(loader,standard_tests,pattern):
    inherited=list(flattened(loader.loadTestsFromModule(upstream)))
    for identifier in (SUPERSEDED,SETTINGS,HISTORY):
        if sum(case.id()==identifier for case in inherited)!=1:
            raise RuntimeError('Upstream test identifiers changed; review compatibility mapping')
    replacement={SETTINGS:SmartSettingsTest('test_fixed_route_and_worker_need_no_settings_rendering'),
                 HISTORY:SmartHistoryTest('test_projects_update_against_their_recorded_historical_sources')}
    suite=unittest.TestSuite(replacement.get(case.id(),case) for case in inherited if case.id()!=SUPERSEDED)
    suite.addTests(loader.loadTestsFromModule(smart))
    suite.addTests(loader.loadTestsFromModule(efficiency))
    return suite

if __name__=='__main__':
    unittest.main()
