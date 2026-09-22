"""v1.6.2 Work/Codex credit economics and Luna-first routing regressions."""
from __future__ import annotations

import io
import os
from decimal import Decimal as D
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'codex_workflow'
BASE_COMMIT='d40a6e91cf36a0d2882c2b59b205f77a6147194c'
BASE_TREE='012653dd15e21b8eb83de6023c1277407d1f8e0d'
sys.path.insert(0,str(PACKAGE))

from runtime import doctor,efficiency,smart_install,smart_restore
from runtime._toml import tomllib
from test_v152 import git_tree_hash,snapshot

EXPECTED={
    'simple_executor':('gpt-6-luna','low'),
    'routine_executor':('gpt-6-luna','high'),
    'default_executor':('gpt-6-luna','max'),
    'senior_executor':('gpt-6-sol','xhigh'),
    'tester':('gpt-6-luna','xhigh'),
    'companion':('gpt-6-luna','medium'),
    'investigator':('gpt-6-luna','xhigh'),
    'archivist':('gpt-6-luna','medium'),
}


class CreditAndReadmeContracts(unittest.TestCase):
    def test_version_and_worker_map_unchanged(self):
        self.assertEqual((PACKAGE/'operate/VERSION').read_text(),'1.6.2\n')
        for role,expected in EXPECTED.items():
            cfg=tomllib.loads((PACKAGE/'agents'/f'{role}.toml').read_text())
            self.assertEqual((cfg['model'],cfg['model_reasoning_effort']),expected)

    def test_credit_rates_ratios_and_fast_multiplier(self):
        self.assertEqual(efficiency.CREDIT_RATES['gpt-6-luna'],(D('2.5'),D('.25'),D('12.5')))
        self.assertEqual(efficiency.CREDIT_RATES['gpt-6-sol'],(D('50'),D('5'),D('250')))
        self.assertEqual(efficiency.CREDIT_RATES['gpt-6-astra'],(D('250'),D('25'),D('1250')))
        for idx in range(3):
            self.assertEqual(efficiency.CREDIT_RATES['gpt-6-sol'][idx]/efficiency.CREDIT_RATES['gpt-6-luna'][idx],D(20))
            self.assertEqual(efficiency.CREDIT_RATES['gpt-6-astra'][idx]/efficiency.CREDIT_RATES['gpt-6-luna'][idx],D(100))
        self.assertEqual(efficiency.FAST_MULTIPLIER,D('2.5'))

    def test_pro_estimates_are_ranges_not_unlimited(self):
        self.assertEqual(efficiency.MESSAGE_ESTIMATES['gpt-6-luna']['pro_5x'],'1,750-14,000')
        self.assertEqual(efficiency.MESSAGE_ESTIMATES['gpt-6-sol']['pro_5x'],'70-700')
        self.assertIn('weekly limits',efficiency.DISCLAIMER)
        self.assertNotIn('unlimited',efficiency.DISCLAIMER.lower())

    def test_policy_is_luna_first_sol_exceptional(self):
        policy=(PACKAGE/'smart_orchestration.md').read_text()
        for phrase in ('Hard bounded implementation uses Default Luna Max',
                       'Senior Sol xhigh is only for',
                       'not difficulty\nalone',
                       'Known Sol-shaped work may start Senior',
                       'no forced Luna failure',
                       'GPT-6 Fast uses 2.5x credits'):
            self.assertIn(phrase,policy)
        self.assertLess(len(policy.split()),1500)

    def test_readme_is_current_architecture_not_release_stack(self):
        readme=(ROOT/'README.md').read_text()
        for phrase in ('Smart Orchestration v1.6.2','How it works','Current model ladder',
                       'Why Luna-first','Pro limits are generous, not unlimited',
                       'Main-model ownership','Cache, context and tools',
                       'Standard speed is the cost baseline','20×','100×'):
            self.assertIn(phrase,readme)
        self.assertIn('1,750-14,000',readme)
        self.assertIn('70-700',readme)
        self.assertNotIn('## v1.6.1:',readme)
        self.assertNotIn('## v1.6.0:',readme)

    def test_credit_reference_never_claims_weekly_percent(self):
        result=efficiency.reference('gpt-6-sol',100000,50000,10000)
        self.assertIsNone(result['included_weekly_allowance_percent'])
        self.assertIn('not a bill',result['limitation'])


class UpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        destination=Path(cls.temp.name)
        supplied=os.environ.get('SMART_V161_BASELINE')
        if supplied:
            cls.baseline=Path(supplied)
        else:
            raw=subprocess.run(['git','archive',BASE_COMMIT,'codex_workflow'],cwd=ROOT,
                               check=True,capture_output=True).stdout
            with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
                for member in archive:
                    rel=Path(member.name)
                    if rel.is_absolute() or '..' in rel.parts or rel.parts[0]!='codex_workflow':
                        raise ValueError('Unsafe v1.6.1 baseline archive member')
                    if member.isfile():
                        target=destination/rel
                        target.parent.mkdir(parents=True,exist_ok=True)
                        target.write_bytes(archive.extractfile(member).read())
                    elif not member.isdir():
                        raise ValueError('Unexpected v1.6.1 baseline entry')
            cls.baseline=destination/'codex_workflow'
        if git_tree_hash(cls.baseline)!=BASE_TREE:
            raise ValueError('Baseline is not exact merged v1.6.1 package tree')

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.home=self.root/'home';self.home.mkdir()
        self.project=self.root/'project';self.project.mkdir()
        (self.project/'AGENTS.md').write_text('owner rule\n')
        (self.project/'source.swift').write_text('owner source\n')
        self.before_project=snapshot(self.project)

    def test_exact_v161_upgrade_reapply_and_rollback(self):
        (self.home/'config.toml').write_text(
            'model="gpt-6-sol"\nmodel_reasoning_effort="medium"\n'
            'plan_mode_reasoning_effort="high"\nservice_tier="standard"\n')
        subprocess.run([sys.executable,'-B',str(self.baseline/'runtime/smart_install.py'),
                        '--package-root',str(self.baseline),'--codex-home',str(self.home),'--apply'],
                       check=True,capture_output=True)
        before_config=(self.home/'config.toml').read_bytes()
        plan,prior=smart_install.prepare(PACKAGE,self.home)
        backup=smart_install.apply_plan(plan,prior,self.home)
        self.assertTrue(backup.is_dir())
        self.assertEqual((self.home/'config.toml').read_bytes(),before_config)
        self.assertEqual(snapshot(self.project),self.before_project)
        self.assertEqual(doctor.inspect(self.home)['version'],'1.6.2')
        for role,expected in EXPECTED.items():
            cfg=tomllib.loads((self.home/'agents'/f'{role}.toml').read_text())
            self.assertEqual((cfg['model'],cfg['model_reasoning_effort']),expected)
        self.assertEqual(smart_install.prepare(PACKAGE,self.home)[0].mutations,[])
        restore,old=smart_restore.prepare_restore(self.home,backup)
        smart_install.apply_plan(restore,old,self.home)
        self.assertEqual((self.home/'codex_workflow/operate/VERSION').read_text(),'1.6.1\n')
        self.assertEqual((self.home/'config.toml').read_bytes(),before_config)
        self.assertEqual(snapshot(self.project),self.before_project)

    def test_fresh_install_preserves_parent_speed_and_project(self):
        (self.home/'config.toml').write_text(
            'model="owner-parent"\nmodel_reasoning_effort="low"\n'
            'plan_mode_reasoning_effort="xhigh"\nservice_tier="fast"\n')
        original=tomllib.loads((self.home/'config.toml').read_text())
        plan,prior=smart_install.prepare(PACKAGE,self.home)
        smart_install.apply_plan(plan,prior,self.home)
        after=tomllib.loads((self.home/'config.toml').read_text())
        for key,value in original.items():
            self.assertEqual(after[key],value)
        self.assertEqual(snapshot(self.project),self.before_project)
        self.assertEqual(doctor.inspect(self.home)['version'],'1.6.2')


if __name__=='__main__':
    unittest.main()
