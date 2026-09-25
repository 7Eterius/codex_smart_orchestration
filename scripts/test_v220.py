"""2.2 package, retirement and exact 2.1 -> current -> rollback regressions."""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'codex_workflow'
sys.path.insert(0,str(PACKAGE))
from runtime import allocation, smart_install as install
from runtime.layout import PackageLayout, BUILTIN_WORKERS, DELEGATING_WORKERS
from runtime.smart_restore import prepare_restore
from runtime.errors import ValidationError
from runtime._toml import tomllib
BASELINE='460ef504779dced6eee771e483d910efea844bee'


def snapshot(root):
    return {p.relative_to(root).as_posix():(p.read_bytes(),p.stat().st_mode&0o777)
            for p in root.rglob('*') if p.is_file() and '.smart-orchestration-backups' not in p.parts}


class CurrentContracts(unittest.TestCase):
    def test_model_role_catalog_matches_allocator(self):
        self.assertEqual(BUILTIN_WORKERS,allocation.ROLES)
        self.assertEqual(DELEGATING_WORKERS,allocation.REVIEW_OWNERS)
        self.assertEqual(len(BUILTIN_WORKERS),8)
        self.assertEqual(PackageLayout.resolve(PACKAGE).version,(PACKAGE/'operate/VERSION').read_text().strip())
        self.assertFalse((PACKAGE/'agents/chunk_lead.toml').exists())
        for name in BUILTIN_WORKERS:
            role=tomllib.loads((PACKAGE/'agents'/f'{name}.toml').read_text())
            self.assertIs(role['agents']['enabled'],name in allocation.REVIEW_OWNERS)
            self.assertLess(len(role['developer_instructions'].split()),200,name)

    def test_current_documents_are_single_loop_and_bounded(self):
        core=(PACKAGE/'smart_orchestration.md').read_text()
        for text in ('One adaptive execution loop','no Normal/Coordinated mode selection','at most two Smart-owned open',
                     'not a native scheduler','not merely a PASS sentence'):
            self.assertIn(text,core)
        for name,limit in [('smart_orchestration.md',1200),('execution.md',1000),('verification.md',700),('browser.md',650)]:
            self.assertLess(len((PACKAGE/name).read_text().split()),limit,name)
        for name in ('coordinated.md','qualification.md'):
            self.assertFalse((PACKAGE/name).exists())

    def test_no_missing_local_links_in_current_or_historical_docs(self):
        for path in [ROOT/'README.md',*(ROOT/'docs').glob('*.md')]:
            for target in re.findall(r'\]\(([^)]+)\)',path.read_text()):
                if not target.startswith(('http:','https:','#')):
                    self.assertTrue((path.parent/target.split('#')[0]).exists(),(str(path),target))

    def test_disk_check_does_not_claim_runtime_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory).resolve()/'home'
            plan,prior=install.prepare(PACKAGE,home)
            install.apply_plan(plan,prior,home)
            result=install.status(home)
            self.assertTrue(result['disk_ok'])
            self.assertEqual(result['execution_policy'],'adaptive')
            self.assertEqual(result['runtime_observation'],'not_inspected')
            self.assertNotIn('coordinated_qualification',result)

    def test_retired_worker_requires_byte_proven_ownership(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory).resolve()/'home'
            plan,prior=install.prepare(PACKAGE,home)
            install.apply_plan(plan,prior,home)
            runtime=home/'codex_workflow'
            live=home/'agents/chunk_lead.toml'
            template=runtime/'templates/agents/chunk_lead.toml'
            original=b'# codex-workflow-worker: chunk_lead\n# old managed role\n'
            live.write_bytes(original)
            template.write_bytes(original)
            state_path=runtime/'install_state.json'
            state=json.loads(state_path.read_text())
            relative='templates/agents/chunk_lead.toml'
            state['owned_workers'].append('chunk_lead')
            state['owned_runtime_files'].append(relative)
            state['owned_runtime_hashes'][relative]=install.digest(original)
            state_path.write_text(json.dumps(state))
            live.write_bytes(original+b'# owner customization\n')
            before=snapshot(home)
            with self.assertRaises(ValidationError):
                install.prepare(PACKAGE,home)
            self.assertEqual(snapshot(home),before)
            live.write_bytes(original)
            plan,prior=install.prepare(PACKAGE,home)
            backup=install.apply_plan(plan,prior,home)
            self.assertFalse(live.exists())
            self.assertFalse(template.exists())
            restore,prior=prepare_restore(home,backup)
            install.apply_plan(restore,prior,home)
            self.assertEqual(live.read_bytes(),original)
            self.assertEqual(template.read_bytes(),original)


class ArchivedV21Upgrade(unittest.TestCase):
    def test_exact_v21_upgrade_is_idempotent_and_reversible(self):
        result=subprocess.run(['git','archive',BASELINE,'codex_workflow'],cwd=ROOT,capture_output=True,check=False)
        if result.returncode:
            if os.environ.get('CI'):
                self.fail('CI needs exact v2.1 Git history: '+result.stderr.decode(errors='replace'))
            self.skipTest('Exact v2.1 Git object unavailable; required by CI')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve()
            baseline=root/'baseline'
            with tarfile.open(fileobj=io.BytesIO(result.stdout)) as archive:
                for member in archive:
                    relative=Path(member.name)
                    self.assertFalse(relative.is_absolute())
                    self.assertNotIn('..',relative.parts)
                    self.assertEqual(relative.parts[0],'codex_workflow')
                    if member.isfile():
                        target=baseline/relative
                        target.parent.mkdir(parents=True,exist_ok=True)
                        target.write_bytes(archive.extractfile(member).read())
                        target.chmod(member.mode&0o777)
                    else:
                        self.assertTrue(member.isdir())
            old_package=baseline/'codex_workflow'
            home=root/'home'
            home.mkdir()
            (home/'config.toml').write_text('model="gpt-6-sol"\nmodel_reasoning_effort="medium"\n'
                                           'approval_policy="on-request"\n[agents]\nmax_threads=3\n'
                                           'default_subagent_model="gpt-5.6-luna"\n')
            (home/'AGENTS.md').write_text('Owner instructions remain.\n')
            project=root/'project'
            project.mkdir()
            (project/'owner.txt').write_text('untouched')
            ran=subprocess.run([sys.executable,'-B',str(old_package/'runtime/smart_install.py'),
                                '--package-root',str(old_package),'--codex-home',str(home),'--apply'],
                               capture_output=True,text=True,check=False)
            self.assertEqual(ran.returncode,0,ran.stdout+ran.stderr)
            before=snapshot(home)
            project_before=snapshot(project)
            plan,prior=install.prepare(PACKAGE,home)
            self.assertEqual(snapshot(home),before)
            backup=install.apply_plan(plan,prior,home)
            self.assertTrue(install.status(home)['disk_ok'])
            self.assertFalse((home/'agents/chunk_lead.toml').exists())
            self.assertFalse((home/'codex_workflow/coordinated.md').exists())
            self.assertTrue((home/'codex_workflow/execution.md').exists())
            cfg=tomllib.loads((home/'config.toml').read_text())
            self.assertEqual(cfg['agents']['max_threads'],3)
            self.assertEqual(cfg['agents']['default_subagent_model'],'gpt-5.6-luna')
            self.assertEqual(cfg['approval_policy'],'on-request')
            self.assertEqual(install.prepare(PACKAGE,home)[0].mutations,[])
            restore,prior=prepare_restore(home,backup)
            install.apply_plan(restore,prior,home)
            self.assertEqual(snapshot(home),before)
            self.assertEqual(snapshot(project),project_before)
            checked=subprocess.run([sys.executable,'-B',str(old_package/'runtime/smart_install.py'),
                                    '--codex-home',str(home),'--check'],capture_output=True,text=True,check=False)
            self.assertEqual(checked.returncode,0,checked.stdout+checked.stderr)


if __name__=='__main__':
    unittest.main()
