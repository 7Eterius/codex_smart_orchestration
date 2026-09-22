"""v1.6.3 retirement of workflow token-reporting skill and hooks."""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'codex_workflow'
CURRENT_VERSION=(PACKAGE/'operate/VERSION').read_text().strip()
BASE_COMMIT='f095dd9f9450ec31d2233db7ef28a405a3e5728e'
BASE_TREE='f7db39791df6b92a23eaaafebe8d76334a9ec127'
sys.path.insert(0,str(PACKAGE))

from runtime import doctor,smart_install,smart_restore
from runtime._toml import tomllib
from runtime.layout import BUILTIN_SKILLS,PackageLayout
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


class RetirementContracts(unittest.TestCase):
    def test_package_has_no_builtin_skill_payload(self):
        package=PackageLayout.resolve(PACKAGE)
        self.assertEqual(package.version,CURRENT_VERSION)
        self.assertEqual(BUILTIN_SKILLS,frozenset())
        self.assertEqual(package.skill_names,set())
        self.assertFalse((PACKAGE/'skills').exists())

    def test_active_policy_and_memory_have_no_reporting_hooks(self):
        texts=[
            (PACKAGE/'smart_orchestration.md').read_text(),
            (PACKAGE/'archivist.md').read_text(),
            (PACKAGE/'agents/archivist.toml').read_text(),
        ]
        forbidden=('deployment-token-report','codex-workflow-deployment-start','report_tokens.py')
        for text in texts:
            for phrase in forbidden:
                self.assertNotIn(phrase,text)
        self.assertIn('Do not generate orchestration token/usage statistics',texts[0])
        self.assertIn('token/usage accounting or orchestration statistics',texts[2])

    def test_readme_documents_retirement_not_usage_reporting(self):
        readme=(ROOT/'README.md').read_text()
        self.assertIn(f'Smart Orchestration v{CURRENT_VERSION}',readme)
        self.assertIn('no deployment/token-report skill',readme)
        self.assertNotIn('deployment-token report',readme.lower())
        self.assertNotIn('optional diagnostics',readme.lower())

    def test_worker_map_unchanged(self):
        for role,expected in EXPECTED.items():
            cfg=tomllib.loads((PACKAGE/'agents'/f'{role}.toml').read_text())
            self.assertEqual((cfg['model'],cfg['model_reasoning_effort']),expected)


class UpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        destination=Path(cls.temp.name)
        supplied=os.environ.get('SMART_V162_BASELINE')
        if supplied:
            cls.baseline=Path(supplied)
        else:
            raw=subprocess.run(['git','archive',BASE_COMMIT,'codex_workflow'],cwd=ROOT,
                               check=True,capture_output=True).stdout
            with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
                for member in archive:
                    rel=Path(member.name)
                    if rel.is_absolute() or '..' in rel.parts or rel.parts[0]!='codex_workflow':
                        raise ValueError('Unsafe v1.6.2 baseline archive member')
                    if member.isfile():
                        target=destination/rel
                        target.parent.mkdir(parents=True,exist_ok=True)
                        target.write_bytes(archive.extractfile(member).read())
                    elif not member.isdir():
                        raise ValueError('Unexpected v1.6.2 baseline entry')
            cls.baseline=destination/'codex_workflow'
        if git_tree_hash(cls.baseline)!=BASE_TREE:
            raise ValueError('Baseline is not exact merged v1.6.2 package tree')

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.home=self.root/'home';self.home.mkdir()
        self.project=self.root/'project';self.project.mkdir()
        (self.project/'AGENTS.md').write_text('owner rule\n')
        (self.project/'source.swift').write_text('owner source\n')
        self.project_before=snapshot(self.project)

    def install_baseline(self):
        subprocess.run([sys.executable,'-B',str(self.baseline/'runtime/smart_install.py'),
                        '--package-root',str(self.baseline),'--codex-home',str(self.home),'--apply'],
                       check=True,capture_output=True)

    def test_exact_v162_upgrade_retires_skill_reapply_and_rollback(self):
        (self.home/'config.toml').write_text(
            'model="gpt-6-sol"\nmodel_reasoning_effort="medium"\n'
            'plan_mode_reasoning_effort="high"\nservice_tier="standard"\n')
        unrelated=self.home/'skills'/'owner-skill'
        unrelated.mkdir(parents=True)
        (unrelated/'SKILL.md').write_text('# owner skill\n')
        self.install_baseline()
        retired=self.home/'skills'/'deployment-token-report'
        retired_template=self.home/'codex_workflow'/'templates'/'skills'/'deployment-token-report'
        self.assertTrue((retired/'SKILL.md').is_file())
        self.assertTrue((retired_template/'SKILL.md').is_file())
        before_config=(self.home/'config.toml').read_bytes()

        plan,prior=smart_install.prepare(PACKAGE,self.home)
        self.assertEqual(plan.details['retired_owned_skills'],['deployment-token-report'])
        backup=smart_install.apply_plan(plan,prior,self.home)
        self.assertTrue(backup.is_dir())
        self.assertFalse(retired.exists())
        self.assertFalse(retired_template.exists())
        self.assertEqual((unrelated/'SKILL.md').read_text(),'# owner skill\n')
        self.assertEqual((self.home/'config.toml').read_bytes(),before_config)
        self.assertEqual(snapshot(self.project),self.project_before)
        state=json.loads((self.home/'codex_workflow'/'install_state.json').read_text())
        self.assertEqual(state['owned_skills'],[])
        self.assertEqual(doctor.inspect(self.home)['version'],CURRENT_VERSION)
        self.assertEqual(smart_install.prepare(PACKAGE,self.home)[0].mutations,[])

        restore,old=smart_restore.prepare_restore(self.home,backup)
        smart_install.apply_plan(restore,old,self.home)
        self.assertEqual((self.home/'codex_workflow'/'operate'/'VERSION').read_text(),'1.6.2\n')
        self.assertTrue((retired/'SKILL.md').is_file())
        self.assertTrue((retired_template/'SKILL.md').is_file())
        self.assertEqual((unrelated/'SKILL.md').read_text(),'# owner skill\n')
        self.assertEqual(snapshot(self.project),self.project_before)

    def test_upgrade_after_manual_skill_uninstall_does_not_recreate_it(self):
        self.install_baseline()
        retired=self.home/'skills'/'deployment-token-report'
        shutil.rmtree(retired)
        plan,prior=smart_install.prepare(PACKAGE,self.home)
        smart_install.apply_plan(plan,prior,self.home)
        self.assertFalse(retired.exists())
        self.assertFalse((self.home/'codex_workflow'/'templates'/'skills'/'deployment-token-report').exists())
        self.assertEqual(doctor.inspect(self.home)['version'],CURRENT_VERSION)

    def test_fresh_install_has_no_reporting_skill_and_preserves_parent(self):
        (self.home/'config.toml').write_text(
            'model="owner-parent"\nmodel_reasoning_effort="low"\n'
            'plan_mode_reasoning_effort="xhigh"\nservice_tier="fast"\n')
        original=tomllib.loads((self.home/'config.toml').read_text())
        plan,prior=smart_install.prepare(PACKAGE,self.home)
        smart_install.apply_plan(plan,prior,self.home)
        after=tomllib.loads((self.home/'config.toml').read_text())
        for key,value in original.items():
            self.assertEqual(after[key],value)
        self.assertFalse((self.home/'skills'/'deployment-token-report').exists())
        state=json.loads((self.home/'codex_workflow'/'install_state.json').read_text())
        self.assertEqual(state['owned_skills'],[])
        self.assertEqual(snapshot(self.project),self.project_before)


if __name__=='__main__':
    unittest.main()
