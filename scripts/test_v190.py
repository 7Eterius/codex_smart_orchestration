"""v1.9.0 cost-aware GUI routing and exact v1.8 upgrade regressions."""
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
BASE_COMMIT='45b8fc71417d617b5a132051b14f0ca27fee7fed'
BASE_TREE='025e522c706e1be420834e3b3786878294fbfbc6'
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

class V19Contracts(unittest.TestCase):
    def setUp(self):
        self.policy=(PACKAGE/'smart_orchestration.md').read_text()
        self.flat=' '.join(self.policy.split())

    def test_version_map_and_budgets(self):
        package=PackageLayout.resolve(PACKAGE)
        self.assertEqual(CURRENT_VERSION,'1.9.0')
        self.assertEqual(package.worker_names,set(EXPECTED))
        for role,expected in EXPECTED.items():
            cfg=tomllib.loads((PACKAGE/'agents'/f'{role}.toml').read_text())
            self.assertEqual((cfg['model'],cfg['model_reasoning_effort']),expected)
            self.assertIs(cfg['agents']['enabled'],False)
            self.assertLess(len(cfg['developer_instructions'].split()),200,role)
        self.assertLess(len(self.policy.split()),1200)
        self.assertLess(len((PACKAGE/'verification.md').read_text().split()),700)

    def test_simple_is_mechanical_operator_not_design_judge(self):
        simple=tomllib.loads((PACKAGE/'agents/simple_executor.toml').read_text())['developer_instructions']
        for phrase in ('mechanical Browser/Computer Use','changing explicit development settings',
                       'DOM/console/network','A GUI is not itself a reason to escalate',
                       'Do not judge product/UX/design quality'):
            self.assertIn(phrase,simple)
        for phrase in ('Operator: Simple Luna Low','It does not judge design quality',
                       'one or two trivial actions may stay main'):
            self.assertIn(phrase,self.flat)

    def test_design_intelligence_stays_expensive(self):
        for phrase in ('GPT-6 Sol Medium is the parent baseline',
                       'High/xhigh for hard architecture/product/UX/design judgment',
                       'Judge: main/Senior Sol','Astra is owner-selected only'):
            self.assertIn(phrase,self.flat)
        senior=tomllib.loads((PACKAGE/'agents/senior_executor.toml').read_text())['developer_instructions']
        self.assertIn('product/UX/design judgment',senior)
        self.assertIn('visual direction',senior)

    def test_max_is_not_automatic_and_tester_is_high(self):
        self.assertNotIn('| default_executor | Luna Max |',self.policy)
        self.assertIn('| default_executor | Luna xhigh |',self.policy)
        self.assertIn('| tester | Luna High |',self.policy)
        self.assertIn('Mechanical Browser/Computer evidence',self.policy)
        tester=tomllib.loads((PACKAGE/'agents/tester.toml').read_text())['developer_instructions']
        self.assertIn('Do not spawn merely to perform mechanical GUI navigation',tester)
        self.assertIn('Simple Luna Low can do that',tester)

    def test_readme_documents_operator_judge_split(self):
        readme=(ROOT/'README.md').read_text()
        for phrase in ('Smart Orchestration v1.9.0','operator work','Simple Luna Low',
                       'Luna xhigh','Max is intentionally absent','v1.9.0 notes'):
            self.assertIn(phrase,readme)

class UpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        destination=Path(cls.temp.name)
        supplied=os.environ.get('SMART_V180_BASELINE')
        if supplied:
            cls.baseline=Path(supplied)
        else:
            raw=subprocess.run(['git','archive',BASE_COMMIT,'codex_workflow'],cwd=ROOT,
                               check=True,capture_output=True).stdout
            with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
                for member in archive:
                    rel=Path(member.name)
                    if rel.is_absolute() or '..' in rel.parts or rel.parts[0]!='codex_workflow':
                        raise ValueError('Unsafe v1.8.0 baseline archive member')
                    if member.isfile():
                        target=destination/rel
                        target.parent.mkdir(parents=True,exist_ok=True)
                        target.write_bytes(archive.extractfile(member).read())
                    elif not member.isdir():
                        raise ValueError('Unexpected v1.8.0 baseline entry')
            cls.baseline=destination/'codex_workflow'
        if git_tree_hash(cls.baseline)!=BASE_TREE:
            raise ValueError('Baseline is not exact reviewed v1.8.0 package tree')

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.home=self.root/'home';self.home.mkdir()
        self.project=self.root/'project';self.project.mkdir()
        (self.project/'AGENTS.md').write_text('owner rule\n')
        (self.project/'source.swift').write_text('owner source\n')
        self.before_project=snapshot(self.project)

    def test_exact_v180_upgrade_reapply_and_rollback(self):
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
        self.assertEqual((self.home/'codex_workflow/operate/VERSION').read_text(),'1.8.0\n')
        self.assertEqual((self.home/'config.toml').read_bytes(),before_config)
        self.assertEqual(snapshot(self.project),before_project)

if __name__=='__main__':
    unittest.main()
