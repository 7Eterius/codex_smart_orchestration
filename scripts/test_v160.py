"""v1.6.0 GPT-6 worker routing, upgrade and owner-preservation regressions.

These tests validate configuration and migration behavior, not live model quality,
Codex plan accounting, or unpublished GPT-6 Luna/Sol benchmark scores.
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
BASE_COMMIT = 'c4b7ab4450ec5b78fd2eea1e98674b0597c7b17b'
BASE_TREE = '0e3cc7d550cf73843e2486e37c18a88f6e417495'
sys.path.insert(0, str(PACKAGE))

from runtime import doctor, efficiency, smart_install, smart_restore
from runtime._toml import tomllib
from runtime.agent_defaults import DEFAULTS
from runtime.layout import PackageLayout
from test_v152 import git_tree_hash, snapshot

EXPECTED = {
    'simple_executor': ('gpt-6-luna', 'low'),
    'routine_executor': ('gpt-6-luna', 'medium'),
    'default_executor': ('gpt-6-luna', 'xhigh'),
    'senior_executor': ('gpt-6-sol', 'medium'),
    'tester': ('gpt-6-luna', 'xhigh'),
    'companion': ('gpt-6-luna', 'medium'),
    'investigator': ('gpt-6-luna', 'xhigh'),
    'archivist': ('gpt-6-luna', 'medium'),
}


class ModelRoutingTests(unittest.TestCase):
    def test_version_and_exact_worker_map(self):
        package = PackageLayout.resolve(PACKAGE)
        self.assertEqual(package.version, '1.6.0')
        self.assertEqual(package.worker_names, set(EXPECTED))
        for role, expected in EXPECTED.items():
            with self.subTest(role=role):
                cfg = tomllib.loads((PACKAGE / 'agents' / f'{role}.toml').read_text())
                self.assertEqual((cfg['model'], cfg['model_reasoning_effort']), expected)
                self.assertIs(cfg['agents']['enabled'], False)

    def test_named_workers_have_no_legacy_model_ids(self):
        for role in EXPECTED:
            text = (PACKAGE / 'agents' / f'{role}.toml').read_text()
            self.assertNotIn('gpt-5.6-', text)

    def test_anonymous_fallback_is_gpt6_luna_medium(self):
        self.assertEqual(DEFAULTS['default_subagent_model'], 'gpt-6-luna')
        self.assertEqual(DEFAULTS['default_subagent_reasoning_effort'], 'medium')
        self.assertEqual(DEFAULTS['max_concurrent_threads_per_session'], 3)

    def test_policy_matches_configured_effort_ladder(self):
        policy = (PACKAGE / 'smart_orchestration.md').read_text()
        for phrase in (
            '| simple_executor | Luna Low |',
            '| routine_executor | Luna Medium |',
            '| default_executor | Luna xhigh |',
            '| senior_executor | Sol Medium |',
            '| tester | Luna xhigh |',
            '| investigator | Luna xhigh |',
        ):
            self.assertIn(phrase, policy)
        self.assertIn("Keep the owner's selected main model/effort", policy)
        self.assertLess(len(policy.split()), 1500)

    def test_api_reference_prices_are_current_migration_points(self):
        self.assertEqual(efficiency.RATES['gpt-6-luna'], (
            efficiency.Decimal('0.10'), efficiency.Decimal('0.01'), efficiency.Decimal('0.50')))
        self.assertEqual(efficiency.RATES['gpt-6-sol'], (
            efficiency.Decimal('2.00'), efficiency.Decimal('0.20'), efficiency.Decimal('10.00')))
        self.assertEqual(efficiency.RATES['gpt-6-sol'][0] / efficiency.RATES['gpt-6-luna'][0], 20)
        self.assertEqual(efficiency.RATES['gpt-6-sol'][1] / efficiency.RATES['gpt-6-luna'][1], 20)
        self.assertEqual(efficiency.RATES['gpt-6-sol'][2] / efficiency.RATES['gpt-6-luna'][2], 20)

    def test_docs_do_not_invent_gpt6_benchmark_scores(self):
        notes = (ROOT / 'docs/v1.6.0.md').read_text()
        self.assertIn('No public score table for GPT-6 Luna or GPT-6 Sol', notes)
        self.assertIn('model-selection guidance', notes)
        self.assertIn('API pricing is not the included Codex/ChatGPT plan quota', notes)


class InstallAndUpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        destination = Path(cls.temp.name)
        supplied = os.environ.get('SMART_V153_BASELINE')
        if supplied:
            cls.baseline = Path(supplied)
        else:
            raw = subprocess.run(
                ['git', 'archive', BASE_COMMIT, 'codex_workflow'],
                cwd=ROOT, check=True, capture_output=True,
            ).stdout
            with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
                for member in archive:
                    rel = Path(member.name)
                    if rel.is_absolute() or '..' in rel.parts or rel.parts[0] != 'codex_workflow':
                        raise ValueError('Unsafe baseline archive member')
                    if member.isfile():
                        target = destination / rel
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(archive.extractfile(member).read())
                    elif not member.isdir():
                        raise ValueError('Unexpected baseline archive entry')
            cls.baseline = destination / 'codex_workflow'
        if git_tree_hash(cls.baseline) != BASE_TREE:
            raise ValueError('Baseline is not exact merged v1.5.3 package tree')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / 'home'
        self.home.mkdir()
        self.project = self.root / 'project'
        self.project.mkdir()
        (self.project / 'AGENTS.md').write_text('Owner constraints\n')
        (self.project / 'source.swift').write_text('owner source\n')
        self.project_before = snapshot(self.project)

    def install_current(self):
        plan, before = smart_install.prepare(PACKAGE, self.home)
        return plan, smart_install.apply_plan(plan, before, self.home)

    def test_fresh_install_uses_gpt6_workers_but_preserves_parent(self):
        config = self.home / 'config.toml'
        config.write_text(
            'model="gpt-5.6-sol"\n'
            'model_reasoning_effort="low"\n'
            'plan_mode_reasoning_effort="high"\n'
            'service_tier="standard"\n'
        )
        parent_before = tomllib.loads(config.read_text())
        plan, backup = self.install_current()
        self.assertTrue(backup.is_dir())
        after = tomllib.loads(config.read_text())
        for key, value in parent_before.items():
            self.assertEqual(after[key], value)
        self.assertEqual(after['agents']['default_subagent_model'], 'gpt-6-luna')
        for role, expected in EXPECTED.items():
            cfg = tomllib.loads((self.home / 'agents' / f'{role}.toml').read_text())
            self.assertEqual((cfg['model'], cfg['model_reasoning_effort']), expected)
        self.assertEqual(snapshot(self.project), self.project_before)
        self.assertEqual(doctor.inspect(self.home)['version'], '1.6.0')
        self.assertEqual(plan.details['project_mutations'], 0)

    def test_v153_upgrade_updates_named_roles_preserves_explicit_old_fallback(self):
        config = self.home / 'config.toml'
        config.write_text(
            'model="gpt-6-sol"\nmodel_reasoning_effort="medium"\n'
            '[agents]\ndefault_subagent_model="gpt-5.6-luna"\n'
            'default_subagent_reasoning_effort="medium"\n'
            'max_concurrent_threads_per_session=3\n'
        )
        subprocess.run(
            [sys.executable, '-B', str(self.baseline / 'runtime/smart_install.py'),
             '--package-root', str(self.baseline), '--codex-home', str(self.home), '--apply'],
            check=True, capture_output=True,
        )
        before_config = (self.home / 'config.toml').read_bytes()
        before_project = snapshot(self.project)
        plan, backup = self.install_current()
        self.assertTrue(backup.is_dir())
        # Explicit configuration is still an owner boundary even when it names a legacy model.
        self.assertEqual((self.home / 'config.toml').read_bytes(), before_config)
        self.assertEqual(tomllib.loads((self.home / 'agents/default_executor.toml').read_text())['model'], 'gpt-6-luna')
        self.assertEqual(tomllib.loads((self.home / 'agents/senior_executor.toml').read_text())['model'], 'gpt-6-sol')
        self.assertTrue(any('differs from the economical fallback' in warning for warning in plan.warnings))
        self.assertEqual(snapshot(self.project), before_project)

        again, _ = smart_install.prepare(PACKAGE, self.home)
        self.assertEqual(again.mutations, [])

        restore_plan, prior = smart_restore.prepare_restore(self.home, backup)
        smart_install.apply_plan(restore_plan, prior, self.home)
        self.assertEqual((self.home / 'codex_workflow/operate/VERSION').read_text(), '1.5.3\n')
        self.assertEqual((self.home / 'config.toml').read_bytes(), before_config)
        self.assertEqual(snapshot(self.project), before_project)

    def test_upgrade_from_normal_v153_defaults_keeps_owner_safety(self):
        subprocess.run(
            [sys.executable, '-B', str(self.baseline / 'runtime/smart_install.py'),
             '--package-root', str(self.baseline), '--codex-home', str(self.home), '--apply'],
            check=True, capture_output=True,
        )
        legacy_config = tomllib.loads((self.home / 'config.toml').read_text())
        self.assertEqual(legacy_config['agents']['default_subagent_model'], 'gpt-5.6-luna')
        plan, _ = smart_install.prepare(PACKAGE, self.home)
        self.assertTrue(any('differs from the economical fallback' in warning for warning in plan.warnings))
        # Named real assignments still migrate; the ambiguous explicit fallback is not silently rewritten.
        smart_install.apply_plan(plan, {str(m.path): (m.path.read_bytes() if m.path.is_file() else None)
                                        for m in plan.mutations}, self.home)
        self.assertEqual(tomllib.loads((self.home / 'agents/simple_executor.toml').read_text())['model'], 'gpt-6-luna')
        self.assertEqual(tomllib.loads((self.home / 'config.toml').read_text())['agents']['default_subagent_model'], 'gpt-5.6-luna')


if __name__ == '__main__':
    unittest.main()
