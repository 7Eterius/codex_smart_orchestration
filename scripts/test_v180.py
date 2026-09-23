"""v1.8.0 runtime-aware GPT-6 orchestration and exact v1.7 upgrade regressions."""
from __future__ import annotations

import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'codex_workflow'
CURRENT_VERSION=(PACKAGE/'operate/VERSION').read_text().strip()
BASE_COMMIT='1beee41b2923f7e4367d444fdd80bd265a443abe'
BASE_TREE='9f0b0e5fe81dd952994e2746585be3d106301113'
sys.path.insert(0,str(PACKAGE))

from runtime import doctor,smart_install,smart_restore
from runtime._toml import tomllib
from runtime.layout import PackageLayout
from test_v152 import git_tree_hash,snapshot

EXPECTED={
    'simple_executor':('gpt-6-luna','low'),
    'routine_executor':('gpt-6-luna','high'),
    'default_executor':('gpt-6-luna','xhigh'),
    'senior_executor':('gpt-6-sol','xhigh'),
    'tester':('gpt-6-luna','high'),
    'companion':('gpt-6-luna','medium'),
    'investigator':('gpt-6-luna','xhigh'),
    'archivist':('gpt-6-luna','medium'),
}


class RuntimeAwareContracts(unittest.TestCase):
    def setUp(self):
        self.policy=(PACKAGE/'smart_orchestration.md').read_text()
        self.flat_policy=' '.join(self.policy.split())
        self.verify=(PACKAGE/'verification.md').read_text()

    def test_version_role_map_and_prompt_bound(self):
        package=PackageLayout.resolve(PACKAGE)
        self.assertEqual(package.version,CURRENT_VERSION)
        self.assertEqual(package.worker_names,set(EXPECTED))
        for role,expected in EXPECTED.items():
            cfg=tomllib.loads((PACKAGE/'agents'/f'{role}.toml').read_text())
            self.assertEqual((cfg['model'],cfg['model_reasoning_effort']),expected)
            self.assertIs(cfg['agents']['enabled'],False)
        self.assertLess(len(self.policy.split()),1200)

    def test_routine_is_primary_and_xhigh_is_deep_exception(self):
        for phrase in ('Routine is the default implementation',
                       'Hard bounded implementation uses Default Luna xhigh only',
                       'Known deep work may start Default; no ritual failure',
                       'Senior Sol xhigh is only for'):
            self.assertIn(phrase,self.flat_policy)
        routine=tomllib.loads((PACKAGE/'agents/routine_executor.toml').read_text())['developer_instructions']
        default=tomllib.loads((PACKAGE/'agents/default_executor.toml').read_text())['developer_instructions']
        self.assertIn('primary implementation lane',routine)
        self.assertIn('genuinely deep bounded',default)

    def test_parent_effort_is_runtime_aware_not_rewritten(self):
        for phrase in ('GPT-6 Sol Medium is the parent baseline',
                       'Supported runtimes may raise High/xhigh',
                       'hard architecture/product/UX/design judgment',
                       'Never emulate self-switching',
                       'rewrite owner configuration'):
            self.assertIn(phrase,self.flat_policy)

    def test_research_and_memory_are_evidence_grounded(self):
        self.assertIn('Companion, Investigator and Archivist are evidence-grounded',self.policy)
        for role in ('companion','investigator','archivist'):
            instructions=tomllib.loads((PACKAGE/'agents'/f'{role}.toml').read_text())['developer_instructions']
            self.assertIn('exact',instructions.lower(),role)
            self.assertIn('unknown',instructions.lower(),role)

    def test_tool_loading_async_and_cache_rules_are_bounded(self):
        for phrase in ('deferred tool loading/tool search',
                       'do not invent config keys',
                       'async tools are exposed',
                       'do not combine them with parallel',
                       'GPT-6 preserves earlier prompt-cache'):
            self.assertIn(phrase,self.flat_policy)

    def test_browser_and_computer_use_are_evidence_first(self):
        for phrase in ('Browser/Computer Use has two lanes','inspect DOM/console/network',
                       'one or two trivial actions may stay main','Astra is owner-selected only',
                       'screenshots prove visible state only'):
            self.assertIn(phrase,self.flat_policy)
        self.assertIn('## Browser and Computer Use',self.verify)
        tester=tomllib.loads((PACKAGE/'agents/tester.toml').read_text())['developer_instructions']
        self.assertIn('Computer Use',tester)
        self.assertIn('DOM/console/network',tester)

    def test_readme_documents_current_economics_and_sources(self):
        readme=(ROOT/'README.md').read_text()
        for phrase in ('Smart Orchestration v1.9.0','GPT-6 Sol Medium',
                       'Computer Use','20×','100×','v1.9.0 notes'):
            self.assertIn(phrase,readme)


class UpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        destination=Path(cls.temp.name)
        supplied=os.environ.get('SMART_V170_BASELINE')
        if supplied:
            cls.baseline=Path(supplied)
        else:
            raw=subprocess.run(['git','archive',BASE_COMMIT,'codex_workflow'],cwd=ROOT,
                               check=True,capture_output=True).stdout
            with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
                for member in archive:
                    rel=Path(member.name)
                    if rel.is_absolute() or '..' in rel.parts or rel.parts[0]!='codex_workflow':
                        raise ValueError('Unsafe v1.7.0 baseline archive member')
                    if member.isfile():
                        target=destination/rel
                        target.parent.mkdir(parents=True,exist_ok=True)
                        target.write_bytes(archive.extractfile(member).read())
                    elif not member.isdir():
                        raise ValueError('Unexpected v1.7.0 baseline entry')
            cls.baseline=destination/'codex_workflow'
        if git_tree_hash(cls.baseline)!=BASE_TREE:
            raise ValueError('Baseline is not exact merged v1.7.0 package tree')

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.home=self.root/'home';self.home.mkdir()
        self.project=self.root/'project';self.project.mkdir()
        (self.project/'AGENTS.md').write_text('owner rule\n')
        (self.project/'source.swift').write_text('owner source\n')
        self.before_project=snapshot(self.project)

    def test_exact_v170_upgrade_reapply_and_rollback(self):
        (self.home/'config.toml').write_text(
            'model="gpt-6-sol"\nmodel_reasoning_effort="medium"\n'
            'plan_mode_reasoning_effort="high"\nservice_tier="standard"\n')
        subprocess.run([sys.executable,'-B',str(self.baseline/'runtime/smart_install.py'),
                        '--package-root',str(self.baseline),'--codex-home',str(self.home),'--apply'],
                       check=True,capture_output=True)
        before_config=(self.home/'config.toml').read_bytes()
        before_project=snapshot(self.project)

        plan,prior=smart_install.prepare(PACKAGE,self.home)
        backup=smart_install.apply_plan(plan,prior,self.home)
        self.assertTrue(backup.is_dir())
        self.assertEqual(doctor.inspect(self.home)['version'],CURRENT_VERSION)
        self.assertEqual((self.home/'config.toml').read_bytes(),before_config)
        self.assertEqual(snapshot(self.project),before_project)
        self.assertEqual(smart_install.prepare(PACKAGE,self.home)[0].mutations,[])

        for role,expected in EXPECTED.items():
            cfg=tomllib.loads((self.home/'agents'/f'{role}.toml').read_text())
            self.assertEqual((cfg['model'],cfg['model_reasoning_effort']),expected)

        restore,old=smart_restore.prepare_restore(self.home,backup)
        smart_install.apply_plan(restore,old,self.home)
        self.assertEqual((self.home/'codex_workflow/operate/VERSION').read_text(),'1.7.0\n')
        self.assertEqual((self.home/'config.toml').read_bytes(),before_config)
        self.assertEqual(snapshot(self.project),before_project)


if __name__=='__main__':
    unittest.main()
