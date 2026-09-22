"""v1.7.0 adaptive workflow efficiency and exact-upgrade regressions."""
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
BASE_COMMIT='e0a544fc97740e546f800843a89a5b3ac30c6da1'
BASE_TREE='ffc1ed3a440ce9a4c36a66355b966ba8fe5fd128'
sys.path.insert(0,str(PACKAGE))

from runtime import doctor,smart_install,smart_restore
from runtime._toml import tomllib
from runtime.layout import PackageLayout
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


class AdaptiveWorkflowContracts(unittest.TestCase):
    def setUp(self):
        self.policy=(PACKAGE/'smart_orchestration.md').read_text()

    def test_version_and_model_map_unchanged(self):
        package=PackageLayout.resolve(PACKAGE)
        self.assertEqual(package.version,'1.7.0')
        self.assertEqual(package.worker_names,set(EXPECTED))
        for role,expected in EXPECTED.items():
            cfg=tomllib.loads((PACKAGE/'agents'/f'{role}.toml').read_text())
            self.assertEqual((cfg['model'],cfg['model_reasoning_effort']),expected)
            self.assertIs(cfg['agents']['enabled'],False)

    def test_senior_is_advisory_first(self):
        for phrase in ('Senior is **advisory-first**','read-only advice',
                       'Decision, Rationale, Constraints, Next action',
                       'Transfer production\nownership to Senior only',
                       'Stop the old\nwriter first','Main retains acceptance'):
            self.assertIn(phrase,self.policy)
        senior=tomllib.loads((PACKAGE/'agents/senior_executor.toml').read_text())['developer_instructions']
        self.assertIn('Default to read-only advice',senior)
        self.assertIn('current Luna writer can continue',senior)
        self.assertIn('explicitly says ownership is transferred',senior)

    def test_tester_is_risk_adaptive(self):
        for phrase in ('**Simple:** self-check','no independent Tester by default',
                       '**Routine:** add independent Tester',
                       '**Default:** independent Tester by default',
                       '**Senior transferred implementation:** independent Tester by default',
                       'repository-specific verification rule'):
            self.assertIn(phrase,self.policy)
        tester=tomllib.loads((PACKAGE/'agents/tester.toml').read_text())['developer_instructions']
        self.assertIn('when the parent/repository risk rules justify',tester)
        self.assertIn('never repair it',tester)

    def test_compact_worker_handoff_contract(self):
        for role in EXPECTED:
            cfg=tomllib.loads((PACKAGE/'agents'/f'{role}.toml').read_text())
            instructions=cfg['developer_instructions']
            self.assertLess(len(instructions.split()),200,role)
            if role=='senior_executor':
                self.assertIn('Decision; Rationale; Constraints; Next action',instructions)
            else:
                self.assertIn('Outcome; Changed; Checks; Risks',instructions)
        self.assertIn('normally <=180 words',self.policy)
        self.assertIn('Put long logs in artifacts',self.policy)

    def test_parallelism_is_independence_based(self):
        self.assertIn('One production writer owns each mutable boundary',self.policy)
        self.assertIn('only for genuinely independent work',self.policy)
        self.assertIn('do not duplicate the same\nquestion unless competing hypotheses are useful',self.policy)

    def test_milestone_context_lifecycle(self):
        for phrase in ('Keep one coherent feature/task in one main working context',
                       'Do not reset context\nmid-implementation',
                       'prefer a\nfresh main session seeded by that handoff',
                       'platform-native compaction if available'):
            self.assertIn(phrase,self.policy)
        handoff=(PACKAGE/'archivist.md').read_text()
        self.assertIn('accepted major milestone',handoff)
        self.assertIn('seed for a future fresh main session',handoff)

    def test_optional_luna_parent_is_documented_not_automatic(self):
        readme=(ROOT/'README.md').read_text()
        self.assertIn('Optional Luna-parent pilot',readme)
        self.assertIn('owner may deliberately select GPT-6 Luna Max',readme)
        self.assertIn('does not enable this\nautomatically',readme)

    def test_main_policy_is_materially_smaller_than_v163(self):
        self.assertLess(len(self.policy.split()),1200)
        self.assertLess(len(self.policy.split()),1450)
        for phrase in ('main model owns the plan','must not rubber-stamp',
                       'Never weaken a required gate','fork_turns="none"',
                       'main owns product, UX, interaction and visual authorship',
                       'Do not generate orchestration token/usage statistics'):
            self.assertIn(phrase,self.policy)


class UpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        destination=Path(cls.temp.name)
        supplied=os.environ.get('SMART_V163_BASELINE')
        if supplied:
            cls.baseline=Path(supplied)
        else:
            raw=subprocess.run(['git','archive',BASE_COMMIT,'codex_workflow'],cwd=ROOT,
                               check=True,capture_output=True).stdout
            with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
                for member in archive:
                    rel=Path(member.name)
                    if rel.is_absolute() or '..' in rel.parts or rel.parts[0]!='codex_workflow':
                        raise ValueError('Unsafe v1.6.3 baseline archive member')
                    if member.isfile():
                        target=destination/rel
                        target.parent.mkdir(parents=True,exist_ok=True)
                        target.write_bytes(archive.extractfile(member).read())
                    elif not member.isdir():
                        raise ValueError('Unexpected v1.6.3 baseline entry')
            cls.baseline=destination/'codex_workflow'
        if git_tree_hash(cls.baseline)!=BASE_TREE:
            raise ValueError('Baseline is not exact merged v1.6.3 package tree')

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.home=self.root/'home';self.home.mkdir()
        self.project=self.root/'project';self.project.mkdir()
        (self.project/'AGENTS.md').write_text('owner rule\n')
        (self.project/'source.swift').write_text('owner source\n')
        self.before_project=snapshot(self.project)

    def test_exact_v163_upgrade_reapply_and_rollback(self):
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
        self.assertEqual(doctor.inspect(self.home)['version'],'1.7.0')
        self.assertEqual((self.home/'config.toml').read_bytes(),before_config)
        self.assertEqual(snapshot(self.project),before_project)
        self.assertEqual(smart_install.prepare(PACKAGE,self.home)[0].mutations,[])

        for role,expected in EXPECTED.items():
            cfg=tomllib.loads((self.home/'agents'/f'{role}.toml').read_text())
            self.assertEqual((cfg['model'],cfg['model_reasoning_effort']),expected)

        restore,old=smart_restore.prepare_restore(self.home,backup)
        smart_install.apply_plan(restore,old,self.home)
        self.assertEqual((self.home/'codex_workflow/operate/VERSION').read_text(),'1.6.3\n')
        self.assertEqual((self.home/'config.toml').read_bytes(),before_config)
        self.assertEqual(snapshot(self.project),before_project)

    def test_fresh_install_preserves_parent_project_and_no_skills(self):
        (self.home/'config.toml').write_text(
            'model="owner-parent"\nmodel_reasoning_effort="low"\n'
            'plan_mode_reasoning_effort="xhigh"\nservice_tier="fast"\n')
        original=tomllib.loads((self.home/'config.toml').read_text())
        plan,prior=smart_install.prepare(PACKAGE,self.home)
        smart_install.apply_plan(plan,prior,self.home)
        after=tomllib.loads((self.home/'config.toml').read_text())
        for key,value in original.items():
            self.assertEqual(after[key],value)
        self.assertEqual(PackageLayout.resolve(PACKAGE).skill_names,set())
        self.assertEqual(snapshot(self.project),self.before_project)


if __name__=='__main__':
    unittest.main()
