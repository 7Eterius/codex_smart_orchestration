"""Smart Orchestration v1.5 regression contracts."""
from __future__ import annotations
import tempfile
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "codex_workflow"
sys.path.insert(0, str(PACKAGE))

from runtime._toml import tomllib
from runtime import smart_install
from runtime import smart_restore
from runtime import doctor
from runtime.agent_defaults import configure
from runtime.errors import ValidationError
from runtime.layout import BUILTIN_WORKERS, PackageLayout


class DefaultsTests(unittest.TestCase):
    def test_missing_defaults_are_added_without_changing_parent(self):
        source = 'model="gpt-5.6-sol"\nmodel_reasoning_effort="low"\nservice_tier="standard"\n'
        rendered, warnings, added = configure(source)
        data = tomllib.loads(rendered)
        self.assertEqual(data['model'], 'gpt-5.6-sol')
        self.assertEqual(data['model_reasoning_effort'], 'low')
        self.assertEqual(data['service_tier'], 'standard')
        self.assertEqual(data['agents']['max_concurrent_threads_per_session'], 3)
        self.assertEqual(data['agents']['default_subagent_model'], 'gpt-5.6-luna')
        self.assertEqual(data['agents']['default_subagent_reasoning_effort'], 'medium')
        self.assertEqual(set(added), {'max_concurrent_threads_per_session', 'default_subagent_model', 'default_subagent_reasoning_effort'})
        self.assertEqual(warnings, [])

    def test_explicit_defaults_and_lower_legacy_cap_are_preserved(self):
        source = '[agents]\nmax_threads=2\ndefault_subagent_model="owner-model"\ndefault_subagent_reasoning_effort="high"\n'
        rendered, warnings, added = configure(source)
        self.assertEqual(rendered, source)
        self.assertEqual(added, {})
        self.assertGreaterEqual(len(warnings), 2)

    def test_duplicate_cap_aliases_are_rejected(self):
        with self.assertRaises(ValidationError):
            configure('[agents]\nmax_threads=2\nmax_concurrent_threads_per_session=3\n')


class RoleContractsTests(unittest.TestCase):
    def test_all_named_children_disable_recursive_delegation(self):
        package = PackageLayout.resolve(PACKAGE)
        self.assertEqual(package.version, '1.5.0')
        self.assertEqual(package.worker_names, BUILTIN_WORKERS)
        for role in sorted(package.worker_names):
            with self.subTest(role=role):
                data = tomllib.loads((PACKAGE / 'agents' / f'{role}.toml').read_text())
                self.assertIs(data.get('agents', {}).get('enabled'), False)


class InstallAndRestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / 'home'
        self.project = self.root / 'project'
        self.project.mkdir()
        (self.project / 'owner.txt').write_text('untouched\n')

    def install(self):
        plan, before = smart_install.prepare(PACKAGE, self.home)
        return smart_install.apply_plan(plan, before, self.home)

    def test_global_install_preserves_owner_text_and_project(self):
        self.home.mkdir()
        (self.home / 'config.toml').write_text('model="gpt-5.6-sol"\nmodel_reasoning_effort="low"\n')
        (self.home / 'AGENTS.md').write_text('Owner path literal: ~/.codex remains owner text.\n')
        backup = self.install()
        self.assertTrue(backup.is_dir())
        self.assertEqual((self.project / 'owner.txt').read_text(), 'untouched\n')
        self.assertIn('Owner path literal: ~/.codex remains owner text.', (self.home / 'AGENTS.md').read_text())
        cfg = tomllib.loads((self.home / 'config.toml').read_text())
        self.assertEqual(cfg['model'], 'gpt-5.6-sol')
        self.assertEqual(cfg['model_reasoning_effort'], 'low')
        self.assertEqual(cfg['agents']['default_subagent_model'], 'gpt-5.6-luna')

    def test_reapply_from_installed_runtime_is_idempotent(self):
        self.install()
        plan, before = smart_install.prepare(self.home / 'codex_workflow', self.home)
        self.assertEqual(plan.mutations, [])
        self.assertIsNone(smart_install.apply_plan(plan, before, self.home))

    def test_doctor_reports_healthy_installed_contract(self):
        self.install()
        result = doctor.inspect(self.home)
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['version'], '1.5.0')
        self.assertTrue(all(row['child_delegation_disabled'] for row in result['workers']))

    def test_exact_restore_reverts_install_and_refuses_conflict(self):
        self.home.mkdir()
        (self.home / 'skills').mkdir()
        (self.home / 'skills' / 'owner-note.txt').write_text('preserve me\n')
        (self.home / 'config.toml').write_text('model="before"\n')
        before_config = (self.home / 'config.toml').read_bytes()
        backup = self.install()
        plan, prior = smart_restore.prepare_restore(self.home, backup)
        restore_backup = smart_install.apply_plan(plan, prior, self.home)
        self.assertTrue(restore_backup.is_dir())
        self.assertEqual((self.home / 'config.toml').read_bytes(), before_config)
        self.assertFalse((self.home / 'skills' / 'deployment-token-report').exists())
        self.assertEqual((self.home / 'skills' / 'owner-note.txt').read_text(), 'preserve me\n')

        # Reinstall, then a newer owner edit must make the old backup unsafe to apply.
        backup2 = self.install()
        (self.home / 'config.toml').write_text((self.home / 'config.toml').read_text() + '\n# owner change\n')
        with self.assertRaises(ValidationError):
            smart_restore.prepare_restore(self.home, backup2)


if __name__ == '__main__':
    unittest.main()
