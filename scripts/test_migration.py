"""Exact historical installations -> current Smart -> no-op -> exact rollback.

Git history is mandatory in CI. The old 309-test source suite is also run unchanged
as a historical reference, separately from tests of the current implementation.
"""
from __future__ import annotations
import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import unittest

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'codex_workflow'
sys.path.insert(0,str(PACKAGE))
from runtime import smart_install as install
from runtime.smart_restore import prepare_restore
from runtime.errors import ValidationError
from test_current import VERSION, EXPECTED

BASELINE='2a82aefc381eebab769b38749bba648ad41a8161'
BASELINES=('e0baa2d69ef9247bd4e3c0e42658358b3fbf8e3c', 'v2.3.0','v2.4.0','v2.5.0',
           'v2.6.0','v2.7.0','388e8e8498bc184b05eddd0f9a1fb9d9e6223c7c',BASELINE,
           '474326b0892e473bcde5638bccf81eb8944aac50',
           'a7e4c9ac715ad7098d2ddd78f2e24eb08adc1e2a',
           '2e28dba69fb16dd8e14aa97a33862450d36a5d77',
           'a6ad69249cf264c969c106e44b15bda1f4bf9ef3',
           '332da7c08adfce2ac4d24d8a4a9a69dae3ebe017')

def snapshot(root):
    return {p.relative_to(root).as_posix():(p.read_bytes(),p.stat().st_mode&0o777)
            for p in root.rglob('*') if p.is_file() and '.smart-orchestration-backups' not in p.relative_to(root).parts}

def archive(case, ref, destination, package_only=True):
    args=['git','archive',ref]+(['codex_workflow'] if package_only else [])
    ran=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=30)
    if ran.returncode:
        if os.environ.get('CI'):case.fail('Required Git history unavailable: '+ref+'\n'+ran.stderr.decode(errors='replace'))
        case.skipTest('Exact Git history unavailable locally; required in CI')
    with tarfile.open(fileobj=io.BytesIO(ran.stdout)) as src:
        for member in src:
            rel=Path(member.name)
            case.assertFalse(rel.is_absolute());case.assertNotIn('..',rel.parts)
            if package_only:case.assertEqual(rel.parts[0],'codex_workflow')
            if member.isfile():
                dst=destination/rel;dst.parent.mkdir(parents=True,exist_ok=True)
                dst.write_bytes(src.extractfile(member).read());dst.chmod(member.mode&0o777)
            else:case.assertTrue(member.isdir())

class HistoricalMigrationTests(unittest.TestCase):
    def test_historical_upgrades_preserve_owner_and_rollback_exactly(self):
        for ref in BASELINES:
            with self.subTest(baseline=ref),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp).resolve();old=root/'old';archive(self,ref,old)
                package=old/'codex_workflow';home=root/'home';home.mkdir()
                config=('model="owner-model"\nmodel_reasoning_effort="high"\n'
                    'plan_mode_reasoning_effort="xhigh"\nservice_tier="standard"\n'
                    'approval_policy="on-request"\n[agents]\nmax_threads=2\n'
                    'default_subagent_model="owner-child"\ndefault_subagent_reasoning_effort="low"\n'
                    '[profiles.mine]\nmodel="owner-profile"\n')
                (home/'config.toml').write_text(config);(home/'AGENTS.md').write_text('Owner instructions.\n')
                project=root/'project';project.mkdir();(project/'owner').write_text('untouched')
                cmd=[sys.executable,'-B',str(package/'runtime/smart_install.py'),'--package-root',str(package),'--codex-home',str(home)]
                ran=subprocess.run(cmd+['--apply'],capture_output=True,text=True,timeout=30)
                self.assertEqual(ran.returncode,0,ran.stdout+ran.stderr)
                before,project_before=snapshot(home),snapshot(project)
                plan,prior=install.prepare(PACKAGE,home);self.assertEqual(snapshot(home),before)
                backup=install.apply_plan(plan,prior,home)
                self.assertTrue(install.status(home)['disk_ok']);self.assertEqual(install.status(home)['version'],VERSION)
                a=tomllib.loads(before['config.toml'][0].decode());b=tomllib.loads((home/'config.toml').read_text())
                a.pop('developer_instructions',None);b.pop('developer_instructions',None);self.assertEqual(a,b)
                for role,expected in EXPECTED.items():
                    cfg=tomllib.loads((home/'agents'/f'{role}.toml').read_text())
                    self.assertEqual((cfg['model'],cfg['model_reasoning_effort']),expected)
                    self.assertEqual((home/'agents'/f'{role}.toml').read_bytes(),(PACKAGE/'agents'/f'{role}.toml').read_bytes())
                self.assertEqual(install.prepare(PACKAGE,home)[0].mutations,[])
                edited=home/'agents/default_executor.toml';content=edited.read_bytes();edited.write_bytes(content+b'\n# owner customization\n')
                self.assertFalse(install.status(home)['disk_ok'])
                with self.assertRaises(ValidationError):install.prepare(PACKAGE,home)
                edited.write_bytes(content)
                self.assertEqual(snapshot(project),project_before)
                restore,prior=prepare_restore(home,backup);install.apply_plan(restore,prior,home)
                self.assertEqual(snapshot(home),before);self.assertEqual(snapshot(project),project_before)
                ran=subprocess.run(cmd+['--check'],capture_output=True,text=True,timeout=30)
                self.assertEqual(ran.returncode,0,ran.stdout+ran.stderr)

    def test_exact_271_suite_is_historical_not_current_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();archive(self,BASELINE,root,package_only=False)
            gitdir=subprocess.run(['git','rev-parse','--absolute-git-dir'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
            # Object access for archived migrations; no global GIT_DIR that would break
            # release tests creating their own isolated repositories.
            (root/'.git').write_text('gitdir: '+gitdir+'\n')
            ran=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','scripts','-p','test_*.py','-v'],
                cwd=root,capture_output=True,text=True,timeout=180)
            self.assertEqual(ran.returncode,0,ran.stdout+ran.stderr)
            self.assertIn('Ran 309 tests',ran.stderr)
            print('\nHistorical 2.7.1 reference: 309 unchanged tests passed; current tests are separate.')

if __name__=='__main__':unittest.main()
