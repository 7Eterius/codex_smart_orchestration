"""v1.6.1 launch-benchmark routing and cache-policy regressions.

Configuration tests do not reproduce model benchmarks or Codex subscription usage.
"""
from __future__ import annotations

import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'codex_workflow'
CURRENT_VERSION = (PACKAGE / 'operate/VERSION').read_text().strip()
BASE_COMMIT = '21db3b6f3eb24c691b62d95b3ddfdff80add6073'
BASE_TREE = '47016d61d8138cf8e13842b8578b391e753b13d8'
sys.path.insert(0, str(PACKAGE))

from runtime import doctor, smart_install, smart_restore
from runtime._toml import tomllib
from test_v152 import git_tree_hash, snapshot

EXPECTED = {
    'simple_executor': ('gpt-6-luna', 'low'),
    'routine_executor': ('gpt-6-luna', 'high'),
    'default_executor': ('gpt-6-luna', 'xhigh'),
    'senior_executor': ('gpt-6-sol', 'xhigh'),
    'tester': ('gpt-6-luna', 'high'),
    'companion': ('gpt-6-luna', 'medium'),
    'investigator': ('gpt-6-luna', 'xhigh'),
    'archivist': ('gpt-6-luna', 'medium'),
}


class LaunchBenchmarkContracts(unittest.TestCase):
    def test_version_and_three_effort_changes(self):
        self.assertEqual((PACKAGE/'operate/VERSION').read_text(), CURRENT_VERSION+'\n')
        for role, expected in EXPECTED.items():
            cfg=tomllib.loads((PACKAGE/'agents'/f'{role}.toml').read_text())
            self.assertEqual((cfg['model'],cfg['model_reasoning_effort']),expected)
            self.assertIs(cfg['agents']['enabled'],False)

    def test_only_named_effort_tiers_changed_from_v160_map(self):
        changed={'routine_executor':('gpt-6-luna','high'),
                 'default_executor':('gpt-6-luna','xhigh'),
                 'senior_executor':('gpt-6-sol','xhigh')}
        for role,value in changed.items():
            cfg=tomllib.loads((PACKAGE/'agents'/f'{role}.toml').read_text())
            self.assertEqual((cfg['model'],cfg['model_reasoning_effort']),value)
        for role in ('simple_executor','tester','companion','investigator','archivist'):
            self.assertEqual((tomllib.loads((PACKAGE/'agents'/f'{role}.toml').read_text())['model'],
                              tomllib.loads((PACKAGE/'agents'/f'{role}.toml').read_text())['model_reasoning_effort']),
                             EXPECTED[role])

    def test_cache_policy_no_longer_freezes_tools_or_effort_for_cache(self):
        policy=(PACKAGE/'smart_orchestration.md').read_text()
        self.assertIn('GPT-6 preserves\nearlier prompt-cache',policy)
        self.assertIn('reasoning-effort and tool-availability changes',policy)
        self.assertIn('never weaken permissions',policy)
        self.assertNotIn('tools/MCP, sandbox and approvals stable within a task',policy)
        self.assertLess(len(policy.split()),1500)

    def test_launch_evidence_is_documented_without_quota_claim(self):
        notes=(ROOT/'docs/v1.6.1.md').read_text()
        for phrase in ('AutomationBench','33.2%','DeepSWE','66.6%','OSWorld','60.5%',
                       'one tenth its cost','not a forecast'):
            self.assertIn(phrase,notes)
        self.assertIn('No parent model/effort is automatically rewritten',notes)

    def test_v160_historical_note_has_correction(self):
        self.assertIn('Correction (v1.6.1)',(ROOT/'docs/v1.6.0.md').read_text())


class UpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        destination=Path(cls.temp.name)
        supplied=os.environ.get('SMART_V160_BASELINE')
        if supplied:
            cls.baseline=Path(supplied)
        else:
            raw=subprocess.run(['git','archive',BASE_COMMIT,'codex_workflow'],cwd=ROOT,
                               check=True,capture_output=True).stdout
            with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
                for member in archive:
                    rel=Path(member.name)
                    if rel.is_absolute() or '..' in rel.parts or rel.parts[0]!='codex_workflow':
                        raise ValueError('Unsafe v1.6.0 baseline archive member')
                    if member.isfile():
                        target=destination/rel
                        target.parent.mkdir(parents=True,exist_ok=True)
                        target.write_bytes(archive.extractfile(member).read())
                    elif not member.isdir():
                        raise ValueError('Unexpected v1.6.0 baseline archive entry')
            cls.baseline=destination/'codex_workflow'
        if git_tree_hash(cls.baseline)!=BASE_TREE:
            raise ValueError('Baseline is not exact merged v1.6.0 package tree')

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.home=self.root/'home';self.home.mkdir()
        self.project=self.root/'project';self.project.mkdir()
        (self.project/'AGENTS.md').write_text('owner project rule\n')
        (self.project/'source.swift').write_text('owner source\n')
        self.before_project=snapshot(self.project)

    def test_exact_v160_upgrade_reapply_and_rollback(self):
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
        self.assertEqual(doctor.inspect(self.home)['version'],CURRENT_VERSION)
        for role,expected in EXPECTED.items():
            cfg=tomllib.loads((self.home/'agents'/f'{role}.toml').read_text())
            self.assertEqual((cfg['model'],cfg['model_reasoning_effort']),expected)
        self.assertEqual(smart_install.prepare(PACKAGE,self.home)[0].mutations,[])
        restore,old=smart_restore.prepare_restore(self.home,backup)
        smart_install.apply_plan(restore,old,self.home)
        self.assertEqual((self.home/'codex_workflow/operate/VERSION').read_text(),'1.6.0\n')
        self.assertEqual((self.home/'config.toml').read_bytes(),before_config)
        self.assertEqual(snapshot(self.project),self.before_project)

    def test_fresh_install_preserves_parent_and_project(self):
        (self.home/'config.toml').write_text(
            'model="owner-parent"\nmodel_reasoning_effort="low"\n'
            'plan_mode_reasoning_effort="xhigh"\nservice_tier="standard"\n')
        before=(self.home/'config.toml').read_text()
        plan,prior=smart_install.prepare(PACKAGE,self.home)
        smart_install.apply_plan(plan,prior,self.home)
        cfg=tomllib.loads((self.home/'config.toml').read_text())
        original=tomllib.loads(before)
        for key,value in original.items():
            self.assertEqual(cfg[key],value)
        self.assertEqual(snapshot(self.project),self.before_project)
        self.assertEqual(doctor.inspect(self.home)['version'],CURRENT_VERSION)


if __name__=='__main__':
    unittest.main()
