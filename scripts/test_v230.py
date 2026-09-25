"""2.3 packaging, documentation and exact archived 2.2 upgrade/rollback."""
from __future__ import annotations
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'codex_workflow'
sys.path.insert(0, str(PACKAGE))
from runtime import smart_install as install
from runtime.config_assessment import assess_configuration
from runtime.layout import INSTALLED_RUNTIME_FILES, PackageLayout
from runtime.smart_restore import prepare_restore
from runtime._toml import tomllib

BASELINE = '53454e4f87227c88c4132d8021b3d6f14fe06c63'


def snapshot(root):
    return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mode & 0o777)
            for p in root.rglob('*') if p.is_file() and '.smart-orchestration-backups' not in p.parts}


class ReleaseContracts(unittest.TestCase):
    def test_version_and_new_runtime_inputs(self):
        self.assertEqual(PackageLayout.resolve(PACKAGE).version, (PACKAGE / 'operate/VERSION').read_text().strip())
        for name in ('runtime/boundary.py', 'boundary.md'):
            self.assertIn(name, INSTALLED_RUNTIME_FILES)
        version = (PACKAGE / 'operate/VERSION').read_text().strip().rsplit('.', 1)[0]
        self.assertIn('Smart Orchestration ' + version, (ROOT / 'README.md').read_text())

    def test_concurrency_warning_matches_policy_without_mutation(self):
        config = {'agents': {'max_threads': 8}}
        result = assess_configuration(config)
        self.assertEqual(config, {'agents': {'max_threads': 8}})
        self.assertIn('at most two owned open threads', ' '.join(result['warnings']))
        self.assertNotIn('fan-out remains 1-3', ' '.join(result['warnings']))

    def test_guides_are_small_and_references_resolve(self):
        self.assertLess(len((PACKAGE / 'boundary.md').read_text().split()), 650)
        for path in [ROOT / 'README.md', *(ROOT / 'docs').glob('*.md'), *(PACKAGE).glob('*.md')]:
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if not target.startswith(('https:', 'http:', '#')):
                    self.assertTrue((path.parent / target.split('#')[0]).exists(), (path, target))

    def test_source_verification_is_not_native_qualification(self):
        notes = (ROOT / 'docs/v2.3.md').read_text()
        self.assertIn('not live Codex qualification', notes)
        self.assertIn('UNVERIFIED', notes)
        self.assertIn('No native', notes)
        policy = (PACKAGE / 'smart_orchestration.md').read_text()
        self.assertIn('not routine', policy)
        self.assertIn('Repeating a failed approach needs new evidence', policy)
        self.assertIn('boundary.md', (PACKAGE / 'execution.md').read_text())

    def test_boundary_installs_and_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp).resolve() / 'home'
            plan, before = install.prepare(PACKAGE, home)
            install.apply_plan(plan, before, home)
            self.assertTrue(install.status(home)['disk_ok'])
            helper = home / 'codex_workflow/runtime/boundary.py'
            self.assertEqual(helper.read_bytes(), (PACKAGE / 'runtime/boundary.py').read_bytes())
            helper.write_text(helper.read_text() + '\n# local edit\n')
            self.assertFalse(install.status(home)['disk_ok'])
            from runtime.errors import ValidationError
            with self.assertRaises(ValidationError):
                install.prepare(PACKAGE, home)


class ArchivedV22Upgrade(unittest.TestCase):
    def test_exact_v22_to_v23_idempotence_and_rollback(self):
        result = subprocess.run(['git', 'archive', BASELINE, 'codex_workflow'], cwd=ROOT,
                                capture_output=True, check=False)
        if result.returncode:
            if os.environ.get('CI'):
                self.fail('CI requires exact v2.2 Git history: ' + result.stderr.decode(errors='replace'))
            self.skipTest('Exact v2.2 Git object unavailable; required in CI')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            old = root / 'baseline'
            with tarfile.open(fileobj=io.BytesIO(result.stdout)) as archive:
                for member in archive:
                    relative = Path(member.name)
                    self.assertFalse(relative.is_absolute())
                    self.assertNotIn('..', relative.parts)
                    self.assertEqual(relative.parts[0], 'codex_workflow')
                    if member.isfile():
                        target = old / relative
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(archive.extractfile(member).read())
                        target.chmod(member.mode & 0o777)
                    else:
                        self.assertTrue(member.isdir())
            old_package = old / 'codex_workflow'
            home = root / 'home'
            home.mkdir()
            (home / 'config.toml').write_text('model="owner-model"\nmodel_reasoning_effort="low"\n'
                'approval_policy="on-request"\n[agents]\nmax_threads=1\n'
                'default_subagent_model="owner-fallback"\ndefault_subagent_reasoning_effort="low"\n')
            (home / 'AGENTS.md').write_text('Protected owner instructions.\n')
            project = root / 'project'
            project.mkdir()
            (project / 'owner.txt').write_text('Untouched project.')
            command = [sys.executable, '-B', str(old_package / 'runtime/smart_install.py'),
                       '--package-root', str(old_package), '--codex-home', str(home)]
            ran = subprocess.run(command + ['--apply'], capture_output=True, text=True)
            self.assertEqual(ran.returncode, 0, ran.stdout + ran.stderr)
            before, project_before = snapshot(home), snapshot(project)
            plan, prior = install.prepare(PACKAGE, home)
            self.assertEqual(snapshot(home), before, 'preview must not mutate')
            backup = install.apply_plan(plan, prior, home)
            self.assertTrue(install.status(home)['disk_ok'])
            self.assertEqual((home / 'codex_workflow/operate/VERSION').read_text(), (PACKAGE / 'operate/VERSION').read_text())
            self.assertTrue((home / 'codex_workflow/boundary.md').is_file())
            self.assertTrue((home / 'codex_workflow/runtime/boundary.py').is_file())
            old_config = tomllib.loads(before['config.toml'][0].decode())
            new_config = tomllib.loads((home / 'config.toml').read_text())
            old_config.pop('developer_instructions', None)
            new_config.pop('developer_instructions', None)
            self.assertEqual(old_config, new_config)
            self.assertEqual(install.prepare(PACKAGE, home)[0].mutations, [])
            restore, prior = prepare_restore(home, backup)
            install.apply_plan(restore, prior, home)
            self.assertEqual(snapshot(home), before)
            self.assertEqual(snapshot(project), project_before)
            checked = subprocess.run(command + ['--check'], capture_output=True, text=True)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
