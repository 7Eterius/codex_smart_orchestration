"""v2.0 architecture, installation integrity and real v1.9 upgrade regressions.

Tests establish file/runtime contracts, not live Codex nesting or token savings.
"""
from __future__ import annotations

import contextlib
import hashlib
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
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'codex_workflow'
sys.path.insert(0, str(PACKAGE))
from runtime import smart_install as install, transaction
from runtime.agent_defaults import configure
from runtime.config_assessment import assess_configuration
from runtime.errors import ValidationError, TransactionError
from runtime.layout import PackageLayout, RuntimePaths, BUILTIN_WORKERS, DELEGATING_WORKERS
from runtime.plan import resolve_owned_runtime_path
from runtime.smart_config import patch_config, SMART
from runtime.smart_restore import prepare_restore
from runtime._toml import tomllib

BASELINE = 'e0baa2d69ef9247bd4e3c0e42658358b3fbf8e3c'


def snapshot(root: Path):
    """Compare bytes and permissions while preserving the reversible backup trail."""
    return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mode & 0o777)
            for p in root.rglob('*') if p.is_file()
            and '.smart-orchestration-backups' not in p.relative_to(root).parts}


class V2ArchitectureTests(unittest.TestCase):
    def test_one_delegator_and_no_unverified_config_keys(self):
        self.assertEqual(DELEGATING_WORKERS, {'chunk_lead'})
        for path in (PACKAGE / 'agents').glob('*.toml'):
            cfg = tomllib.loads(path.read_text())
            self.assertEqual(set(cfg), {'name', 'description', 'model', 'model_reasoning_effort',
                                       'sandbox_mode', 'developer_instructions', 'agents'})
            self.assertEqual(cfg['agents'], {'enabled': path.stem == 'chunk_lead'})
        lead = ' '.join((PACKAGE / 'agents/chunk_lead.toml').read_text().split())
        for role in ('simple_executor', 'routine_executor', 'default_executor', 'tester'):
            self.assertIn(role, lead)
        self.assertIn('Never spawn another lead', lead)

    def test_progressive_disclosure_and_gate_contracts(self):
        policy = ' '.join((PACKAGE / 'smart_orchestration.md').read_text().split())
        coordinated = ' '.join((PACKAGE / 'coordinated.md').read_text().split())
        verify = ' '.join((PACKAGE / 'verification.md').read_text().split())
        self.assertIn('Normal is the default', policy)
        self.assertIn('Read `coordinated.md` only for this mode', policy)
        self.assertIn('No acknowledgement or retirement chatter', policy)
        self.assertIn('Freeze relevant candidate inputs', policy)
        self.assertIn('same writer', coordinated)
        self.assertIn('qualification.md', coordinated)
        self.assertNotIn('capture_check.py', verify)
        self.assertIn('candidate.py', verify)
        self.assertIn('identity only for listed inputs, not test coverage', verify)
        self.assertLess(len((PACKAGE / 'coordinated.md').read_text().split()), 1000)
        self.assertLess(len((PACKAGE / 'browser.md').read_text().split()), 650)

    def test_current_guides_and_links_exist(self):
        import re
        for name in ('README.md', 'docs/smart_orchestration.md', 'docs/v2.0.md'):
            path = ROOT / name
            self.assertTrue(path.is_file(), name)
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if not target.startswith(('https:', 'http:', '#')):
                    self.assertTrue((path.parent / target.split('#')[0]).exists(), (name, target))

    def test_parent_defaults_not_silently_increased(self):
        original = ('model="custom-sol"\nmodel_reasoning_effort="low"\n'
                    'plan_mode_reasoning_effort="high"\nservice_tier="standard"\n'
                    '[agents]\nmax_threads=2\ndefault_subagent_model="custom-luna"\n'
                    'default_subagent_reasoning_effort="low"\n')
        patched, warnings, added = configure(patch_config(original, Path('/example')))
        before, after = tomllib.loads(original), tomllib.loads(patched)
        after.pop('developer_instructions')
        self.assertEqual(before, after)
        self.assertEqual(added, {})
        self.assertTrue(warnings)
        self.assertNotIn('max_depth', patched)

    def test_inline_agent_configuration_preserved(self):
        original = 'agents = { enabled=true, max_threads=2 }\n'
        result, warnings, added = configure(original)
        self.assertEqual(result, original)
        self.assertEqual(added, {})
        self.assertTrue(warnings)

    def test_explicit_disablement_is_not_overridden(self):
        result = assess_configuration({'agents': {'enabled': False}})
        self.assertFalse(result['ok'])
        self.assertTrue(result['errors'])


class InstallerIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.home = self.root / 'Codex home тест'
        self.home.mkdir()
        self.package = self.root / 'source' / 'codex_workflow'
        shutil.copytree(PACKAGE, self.package, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        self.config = ('model="owner-model"\nmodel_reasoning_effort="low"\n'
                       'approval_policy="on-request"\nsandbox_mode="workspace-write"\n'
                       '[agents]\nmax_threads=2\n'
                       '[mcp_servers.mine]\ncommand="keep"\n')
        (self.home / 'config.toml').write_text(self.config)
        (self.home / 'AGENTS.md').write_text('Keep this owner instruction.\n')
        self.runtime = RuntimePaths(self.home)

    def apply(self):
        plan, before = install.prepare(self.package, self.home)
        return install.apply_plan(plan, before, self.home)

    def state(self):
        return json.loads((self.runtime.runtime / 'install_state.json').read_text())

    def write_state(self, value):
        (self.runtime.runtime / 'install_state.json').write_text(json.dumps(value))

    def test_preview_never_writes(self):
        before = snapshot(self.home)
        with contextlib.redirect_stdout(io.StringIO()):
            code = install.main(['--package-root', str(self.package), '--codex-home', str(self.home)])
        self.assertEqual(code, 0)
        self.assertEqual(snapshot(self.home), before)

    def test_check_verifies_disk_not_live_nesting(self):
        self.apply()
        before = snapshot(self.home)
        result = install.status(self.home)
        self.assertTrue(result['disk_ok'], result)
        self.assertEqual(result['coordinated_qualification'], 'unverified')
        self.assertEqual(snapshot(self.home), before)
        self.assertEqual(result['package_fingerprint'], PackageLayout.resolve(self.package).fingerprint)
        config = tomllib.loads((self.home / 'config.toml').read_text())
        self.assertEqual(config['agents']['max_threads'], 2)
        self.assertEqual(config['approval_policy'], 'on-request')
        self.assertEqual(config['mcp_servers']['mine']['command'], 'keep')
        entry = (self.home / 'AGENTS.md').read_text()
        self.assertTrue(entry.startswith('Keep this owner instruction.'))
        self.assertIn(str(self.home), entry)
        self.assertNotIn('~/.codex', entry)

    def test_check_detects_corrupt_runtime_and_runtime_overwrite_is_blocked(self):
        self.apply()
        path = self.runtime.runtime / 'coordinated.md'
        path.write_text(path.read_text() + '\nowner edit\n')
        self.assertFalse(install.status(self.home)['disk_ok'])
        before = snapshot(self.home)
        with self.assertRaisesRegex(ValidationError, 'runtime file requires review'):
            install.prepare(self.package, self.home)
        self.assertEqual(snapshot(self.home), before)

    def test_check_detects_changed_worker_and_managed_block(self):
        self.apply()
        (self.runtime.agents / 'chunk_lead.toml').write_text('owner replacement')
        (self.home / 'AGENTS.md').write_text('only owner instructions')
        result = install.status(self.home)
        self.assertFalse(result['disk_ok'])
        self.assertIn('agents/chunk_lead.toml', result['mismatches'])
        self.assertIn('global AGENTS managed block', result['mismatches'])

    def test_missing_hash_inventory_cannot_pass_check(self):
        self.apply()
        state = self.state()
        state['owned_runtime_hashes'].pop('browser.md')
        self.write_state(state)
        self.assertFalse(install.status(self.home)['disk_ok'])

    def test_disk_check_rejects_invalid_state_schema(self):
        self.apply()
        state = self.state()
        state['schema_version'] = True
        self.write_state(state)
        self.assertFalse(install.status(self.home)['disk_ok'])

    def test_same_version_source_update_is_supported(self):
        self.apply()
        path = self.package / 'browser.md'
        path.write_text(path.read_text() + '\nA reviewed follow-up source change.\n')
        self.apply()
        self.assertEqual((self.runtime.runtime / 'browser.md').read_bytes(), path.read_bytes())
        self.assertTrue(install.status(self.home)['disk_ok'])
        self.assertEqual(install.prepare(self.package, self.home)[0].mutations, [])

    def test_unknown_file_collision_is_not_adopted(self):
        path = self.runtime.runtime / 'coordinated.md'
        path.parent.mkdir()
        path.write_text('unowned')
        with self.assertRaises(ValidationError):
            install.prepare(self.package, self.home)
        self.assertEqual(path.read_text(), 'unowned')

    def test_adjacent_source_scratch_is_not_installed(self):
        (self.package / 'private-scratch.txt').write_text('not distributed')
        self.apply()
        self.assertFalse((self.runtime.runtime / 'private-scratch.txt').exists())
        self.assertTrue(install.status(self.home)['disk_ok'])

    def test_corrupt_template_cannot_authorize_worker_replacement(self):
        self.apply()
        template = self.runtime.runtime / 'templates/agents/routine_executor.toml'
        target = self.runtime.agents / 'routine_executor.toml'
        for path in (template, target):
            path.write_text(path.read_text() + '\n# owner\n')
        with self.assertRaises(ValidationError):
            install.prepare(self.package, self.home)

    def test_required_guide_and_delegation_shape_validated(self):
        guide = self.package / 'qualification.md'
        guide.unlink()
        with self.assertRaises(ValidationError):
            PackageLayout.resolve(self.package)
        shutil.copyfile(PACKAGE / 'qualification.md', guide)
        path = self.package / 'agents/simple_executor.toml'
        path.write_text(path.read_text().replace('enabled = false', 'enabled = true'))
        with self.assertRaises(ValidationError):
            PackageLayout.resolve(self.package)

    def test_wrong_worker_name_and_nonboolean_enabled_rejected(self):
        path = self.package / 'agents/chunk_lead.toml'
        original = path.read_text()
        path.write_text(original.replace('name = "chunk_lead"', 'name = "something_else"'))
        with self.assertRaises(ValidationError):
            PackageLayout.resolve(self.package)
        path.write_text(original.replace('enabled = true', 'enabled = 1'))
        with self.assertRaises(ValidationError):
            PackageLayout.resolve(self.package)

    @unittest.skipIf(os.name == 'nt', 'symlink privileges vary')
    def test_config_symlink_is_rejected_without_touching_target(self):
        original = self.home / 'config.toml'
        outside = self.root / 'outside.toml'
        outside.write_text(self.config)
        original.unlink()
        original.symlink_to(outside)
        with self.assertRaises(ValidationError):
            install.prepare(self.package, self.home)
        self.assertEqual(outside.read_text(), self.config)

    @unittest.skipIf(os.name == 'nt', 'symlink privileges vary')
    def test_parent_symlink_in_runtime_is_rejected(self):
        outside = self.root / 'outside'
        outside.mkdir()
        self.runtime.runtime.mkdir()
        (self.runtime.runtime / 'templates').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValidationError):
            install.prepare(self.package, self.home)
        self.assertEqual(list(outside.iterdir()), [])

    def test_backups_and_source_cache_are_retained(self):
        self.apply()
        source = self.runtime.runtime / '.source_backup/1.9.0/unknown.txt'
        source.parent.mkdir(parents=True)
        source.write_text('unique old data')
        backups = self.home / '.smart-orchestration-backups'
        before = snapshot(backups)
        self.apply()
        self.assertEqual(source.read_text(), 'unique old data')
        self.assertEqual(snapshot(backups), before)

    def test_state_cannot_retire_backup_or_traversal_paths(self):
        for relative in ('../config.toml', '/etc/passwd', '.source_backup/1.9.0/x', '.backups/x', '.git/config', '.'):
            with self.subTest(relative=relative), self.assertRaises(ValidationError):
                resolve_owned_runtime_path(self.runtime.runtime, relative)

    def test_state_identity_or_schema_conflict_stops(self):
        self.apply()
        original = self.state()
        for key, value in (('workflow', 'another'), ('schema_version', True), ('version', '1.0.0')):
            changed = dict(original)
            changed[key] = value
            self.write_state(changed)
            with self.subTest(key=key), self.assertRaises(ValidationError):
                install.prepare(self.package, self.home)
        self.write_state(original)

    def test_modified_retired_skill_is_not_swept_by_marker(self):
        self.apply()
        skill = self.runtime.skills / 'deployment-token-report'
        skill.mkdir(parents=True)
        (skill / 'SKILL.md').write_text('<!-- codex-workflow-skill: deployment-token-report -->\n')
        (skill / 'owner-notes.md').write_text('do not delete')
        state = self.state()
        state['owned_skills'] = ['deployment-token-report']
        self.write_state(state)
        self.apply()
        self.assertTrue((skill / 'SKILL.md').exists())
        self.assertEqual((skill / 'owner-notes.md').read_text(), 'do not delete')

    def test_retired_template_with_edits_is_not_queued_for_deletion(self):
        self.apply()
        path = self.runtime.runtime / 'templates/agents/obsolete.toml'
        path.write_text('# codex-workflow-worker: obsolete\n# local changes\n')
        state = self.state()
        state['owned_runtime_files'].append('templates/agents/obsolete.toml')
        state['owned_runtime_hashes']['templates/agents/obsolete.toml'] = '0' * 64
        self.write_state(state)
        self.apply()
        self.assertTrue(path.exists())

    def test_stale_lock_requires_review_not_deletion(self):
        lock = self.home / '.smart-orchestration-install.lock'
        lock.mkdir()
        with self.assertRaises(ValidationError):
            self.apply()
        self.assertTrue(lock.exists())
        self.assertFalse(self.runtime.runtime.exists())

    def test_transaction_failure_restores_original_bytes(self):
        before = snapshot(self.home)
        real = transaction._atomic_write
        counter = 0
        def injected(path, content, mode):
            nonlocal counter
            counter += 1
            if counter == 6:
                raise OSError('injected disk failure')
            return real(path, content, mode)
        with mock.patch.object(transaction, '_atomic_write', side_effect=injected):
            with self.assertRaises(TransactionError):
                self.apply()
        self.assertEqual(snapshot(self.home), before)
        self.assertFalse((self.home / '.smart-orchestration-install.lock').exists())

    def test_restore_refuses_postinstall_edits(self):
        backup = self.apply()
        (self.home / 'config.toml').write_text('# user changed after install\n')
        with self.assertRaises(ValidationError):
            prepare_restore(self.home, backup)

    def test_restore_refuses_altered_backup(self):
        backup = self.apply()
        (backup / 'files/config.toml').write_text('corrupt')
        with self.assertRaises(ValidationError):
            prepare_restore(self.home, backup)

    def test_check_exit_code_is_not_false_success(self):
        self.apply()
        (self.runtime.runtime / 'browser.md').unlink()
        with contextlib.redirect_stdout(io.StringIO()):
            code = install.main(['--codex-home', str(self.home), '--check'])
        self.assertEqual(code, 1)


class ActualV19Upgrade(unittest.TestCase):
    def test_exact_main_v19_to_v2_reapply_and_rollback(self):
        # Full Git history is available in CI. Offline source-only work can run all
        # other tests; it must not pretend this historical integration was executed.
        result = subprocess.run(['git', 'archive', BASELINE, 'codex_workflow'], cwd=ROOT,
                                capture_output=True, check=False)
        if result.returncode:
            if os.environ.get('CI'):
                self.fail('CI must provide the exact v1.9 baseline: ' + result.stderr.decode(errors='replace'))
            self.skipTest('Exact v1.9 Git object unavailable in this source-only checkout; required in CI')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with tarfile.open(fileobj=io.BytesIO(result.stdout)) as archive:
                for member in archive:
                    relative = Path(member.name)
                    self.assertFalse(relative.is_absolute())
                    self.assertNotIn('..', relative.parts)
                    self.assertEqual(relative.parts[0], 'codex_workflow')
                    if member.isfile():
                        target = root / 'baseline' / relative
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(archive.extractfile(member).read())
                    else:
                        self.assertTrue(member.isdir())
            baseline = root / 'baseline/codex_workflow'
            home = root / 'home'
            home.mkdir()
            config = 'model="gpt-6-sol"\nmodel_reasoning_effort="medium"\n[agents]\nmax_threads=3\n'
            (home / 'config.toml').write_text(config)
            command = [sys.executable, '-B', str(baseline / 'runtime/smart_install.py'),
                       '--package-root', str(baseline), '--codex-home', str(home), '--apply']
            old = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(old.returncode, 0, old.stdout + old.stderr)
            before = snapshot(home)
            plan, prior = install.prepare(PACKAGE, home)
            backup = install.apply_plan(plan, prior, home)
            self.assertTrue(install.status(home)['disk_ok'])
            self.assertEqual((home / 'codex_workflow/operate/VERSION').read_text(), (PACKAGE / 'operate/VERSION').read_text())
            self.assertTrue((home / 'agents/chunk_lead.toml').exists())
            self.assertEqual(tomllib.loads((home / 'config.toml').read_text())['agents']['max_threads'], 3)
            self.assertEqual(install.prepare(PACKAGE, home)[0].mutations, [])
            restore, prior = prepare_restore(home, backup)
            install.apply_plan(restore, prior, home)
            self.assertEqual(snapshot(home), before)
            self.assertFalse((home / 'agents/chunk_lead.toml').exists())


if __name__ == '__main__':
    unittest.main()
