"""v1.5.1 diagnostics, policy and global-upgrade regressions. No live-model claims.

Only disposable directories are mutated. Baseline is reconstructed from the exact
published v1.5.0 Git commit, or a byte-verified CI package supplied to local tests.
"""
from __future__ import annotations
import contextlib
import copy
import io
import json
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
BASE = '2d640f78831644872c1fe521d452da08c0a08855'
sys.path.insert(0, str(PACKAGE))
from runtime import doctor, efficiency, smart_install
from runtime.agent_defaults import DEFAULTS, configure
from runtime.config_assessment import assess_configuration
from runtime.errors import ValidationError
from runtime.layout import PackageLayout
from runtime.smart_restore import prepare_restore
from runtime._toml import tomllib


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


class AssessmentTests(unittest.TestCase):
    def test_empty_config_is_not_invalid_or_proof_of_activation(self):
        result = assess_configuration({})
        self.assertTrue(result['ok'])
        self.assertTrue(result['warnings'])
        self.assertTrue(result['unverified'])
        self.assertIsNone(result['configured_parent']['plan_mode_reasoning_effort'])

    def test_explicit_root_disabled_is_error(self):
        result = assess_configuration({'agents': {'enabled': False}})
        self.assertFalse(result['ok'])
        self.assertTrue(any('explicitly disabled' in e for e in result['errors']))

    def test_legacy_flags_are_compatibility_warnings_not_false_certainty(self):
        for name in ('multi_agent', 'multi_agent_v2'):
            for value in (False, True, {'enabled': False}, {'enabled': True}, {'unknown': 3}):
                with self.subTest(name=name, value=value):
                    cfg = {'features': {name: value}, 'agents': {'enabled': True}}
                    result = assess_configuration(cfg)
                    self.assertTrue(result['ok'])
                    self.assertTrue(any(name in e for e in result['warnings']))
                    self.assertTrue(any(name in e for e in result['unverified']))

    def test_conflicting_aliases_are_error(self):
        result = assess_configuration({'agents': {'max_threads': 1, 'max_concurrent_threads_per_session': 3}})
        self.assertFalse(result['ok'])
        with self.assertRaises(ValidationError):
            configure('[agents]\nmax_threads=1\nmax_concurrent_threads_per_session=3\n')

    def test_invalid_known_shapes_are_errors(self):
        cases = [{'agents': []}, {'features': False}, {'profiles': 'bad'},
                 {'agents': {'enabled': 'false'}}, {'agents': {'max_threads': True}},
                 {'agents': {'max_threads': 0}}, {'agents': {'max_threads': 1.2}},
                 {'agents': {'default_subagent_model': []}},
                 {'agents': {'default_subagent_reasoning_effort': ''}},
                 {'plan_mode_reasoning_effort': False}]
        for cfg in cases:
            with self.subTest(cfg=cfg):
                self.assertFalse(assess_configuration(cfg)['ok'])

    def test_deliberate_cost_choices_warn_without_error(self):
        cfg = {'agents': {'max_threads': 8, 'default_subagent_model': 'owner-model'}, 'service_tier': 'fast'}
        result = assess_configuration(cfg)
        self.assertTrue(result['ok'])
        self.assertTrue(any('above 3' in e for e in result['warnings']))
        self.assertTrue(any('Fast mode' in e for e in result['warnings']))

    def test_normal_and_plan_effort_remain_separate(self):
        cfg = {'model_reasoning_effort': 'low', 'plan_mode_reasoning_effort': 'high'}
        result = assess_configuration(cfg)
        self.assertEqual(result['configured_parent']['model_reasoning_effort'], 'low')
        self.assertEqual(result['configured_parent']['plan_mode_reasoning_effort'], 'high')
        self.assertFalse(any('Plan-mode effort is unset' in e for e in result['unverified']))
        self.assertEqual(assess_configuration({'plan_mode_reasoning_effort': 'none'})['configured_parent']['plan_mode_reasoning_effort'], 'none')

    def test_unset_plan_effort_does_not_copy_normal(self):
        result = assess_configuration({'model_reasoning_effort': 'low'})
        self.assertIsNone(result['configured_parent']['plan_mode_reasoning_effort'])
        self.assertTrue(any('built-in preset' in e for e in result['unverified']))

    def test_unknown_future_effort_not_silently_rewritten(self):
        cfg = {'model_reasoning_effort': 'future-effort'}
        self.assertTrue(assess_configuration(cfg)['ok'])
        self.assertEqual(assess_configuration(cfg)['configured_parent']['model_reasoning_effort'], 'future-effort')

    def test_input_and_secrets_are_preserved_not_echoed(self):
        cfg = {'api_key': 'PRIVATE', 'developer_instructions': 'SECRET',
               'profiles': {'PRIVATE_PROFILE': {'plan_mode_reasoning_effort': 'high'}},
               'agents': dict(DEFAULTS)}
        before = copy.deepcopy(cfg)
        result = assess_configuration(cfg)
        self.assertEqual(cfg, before)
        rendered = json.dumps(result)
        for secret in ('PRIVATE', 'SECRET', 'PRIVATE_PROFILE'):
            self.assertNotIn(secret, rendered)
        self.assertTrue(any('profile' in w for w in result['warnings']))


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / 'home'
        self.home.mkdir()

    def install(self):
        plan, before = smart_install.prepare(PACKAGE, self.home)
        return plan, smart_install.apply_plan(plan, before, self.home)

    def test_installer_and_doctor_share_disabled_agent_error(self):
        self.install()
        config = self.home / 'config.toml'
        config.write_text(config.read_text().replace('[agents]', '[agents]\nenabled=false'))
        result = doctor.inspect(self.home)
        self.assertFalse(result['ok'])
        with self.assertRaises(ValidationError) as caught:
            smart_install.prepare(PACKAGE, self.home)
        self.assertTrue(any(e in str(caught.exception) for e in result['errors']))

    def test_legacy_flags_preserved_and_visible_in_both_tools(self):
        for legacy in ('multi_agent', 'multi_agent_v2'):
            with self.subTest(legacy=legacy), tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                config = home / 'config.toml'
                text = f'[features]\n{legacy}=false\n'
                config.write_text(text)
                plan, before = smart_install.prepare(PACKAGE, home)
                self.assertTrue(any(legacy in w for w in plan.warnings))
                smart_install.apply_plan(plan, before, home)
                result = doctor.inspect(home)
                self.assertTrue(result['ok'])
                self.assertTrue(any(legacy in w for w in result['warnings']))
                self.assertTrue(any(legacy in w for w in result['unverified']))
                self.assertIs(tomllib.loads(config.read_text())['features'][legacy], False)
                self.assertEqual(smart_install.prepare(PACKAGE, home)[0].mutations, [])

    def test_preferences_are_not_installation_failures(self):
        config = self.home / 'config.toml'
        config.write_text('model="owner"\nmodel_reasoning_effort="low"\nplan_mode_reasoning_effort="high"\nservice_tier="fast"\n[agents]\nmax_threads=8\n')
        self.install()
        result = doctor.inspect(self.home)
        self.assertTrue(result['ok'])
        self.assertEqual(result['issues'], [])
        self.assertGreaterEqual(len(result['warnings']), 2)
        self.assertEqual(result['configured_parent']['plan_mode_reasoning_effort'], 'high')
        self.assertEqual(result['effective_configured_cap'], 8)

    def test_doctor_and_efficiency_are_read_only_and_agree_on_efforts(self):
        self.install()
        config = self.home / 'config.toml'
        config.write_text('model_reasoning_effort="low"\nplan_mode_reasoning_effort="none"\n'+config.read_text())
        before = snapshot(self.home)
        first = doctor.inspect(self.home)
        second = efficiency.settings(self.home)
        self.assertEqual(first['configured_parent'], second['configured_parent'])
        self.assertEqual(snapshot(self.home), before)
        self.assertEqual(first['configured_parent']['plan_mode_reasoning_effort'], 'none')

    def test_doctor_missing_worker_is_error(self):
        self.install()
        (self.home/'agents/tester.toml').unlink()
        result = doctor.inspect(self.home)
        self.assertFalse(result['ok'])
        self.assertIn('Worker tester is missing.', result['errors'])

    def test_valid_owner_worker_edit_is_warning_not_claim_of_breakage(self):
        self.install()
        path = self.home/'agents/tester.toml'
        path.write_text(path.read_text()+'\n# owner note\n')
        self.assertTrue(doctor.inspect(self.home)['ok'])
        self.assertTrue(any('differs' in w for w in doctor.inspect(self.home)['warnings']))
        with self.assertRaisesRegex(ValidationError, 'Custom/unowned worker'):
            smart_install.prepare(PACKAGE, self.home)

    def test_recursive_worker_is_error(self):
        self.install()
        path = self.home/'agents/tester.toml'
        path.write_text(path.read_text().replace('enabled = false', 'enabled = true'))
        self.assertFalse(doctor.inspect(self.home)['ok'])

    def test_malformed_file_returns_error_without_success(self):
        self.install()
        (self.home/'agents/tester.toml').write_text('bad=')
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = doctor.main(['--codex-home', str(self.home)])
        self.assertEqual(code, 2)
        self.assertFalse(json.loads(out.getvalue())['ok'])

    def test_diagnostics_warn_but_do_not_read_profile_files(self):
        self.install()
        profile = self.home/'owner.config.toml'
        profile.write_text('PRIVATE INVALID TOML')
        before = snapshot(self.home)
        result = doctor.inspect(self.home)
        self.assertTrue(result['ok'])
        self.assertNotIn('PRIVATE INVALID', json.dumps(result))
        self.assertTrue(any('overrides' in u for u in result['unverified']))
        self.assertEqual(before, snapshot(self.home))

    def test_fresh_install_repeat_and_exact_rollback(self):
        (self.home/'owner.txt').write_text('keep')
        (self.home/'config.toml').write_text('model="owner"\n')
        before = snapshot(self.home)
        _, backup = self.install()
        self.assertTrue(doctor.inspect(self.home)['ok'])
        self.assertEqual(self.install()[0].mutations, [])
        plan, prior = prepare_restore(self.home, backup)
        smart_install.apply_plan(plan, prior, self.home)
        remaining = {k:v for k,v in snapshot(self.home).items() if not k.startswith('.smart-orchestration-backups/')}
        self.assertEqual(remaining, before)
        self.install()
        self.assertTrue(doctor.inspect(self.home)['ok'])

    def test_real_published_v150_upgrade_then_rollback(self):
        supplied = os.environ.get('SMART_V150_BASELINE')
        if supplied:
            baseline = Path(supplied)
        else:
            baseline = self.root/'baseline'/'codex_workflow'
            raw = subprocess.run(['git', 'archive', BASE, 'codex_workflow'], cwd=ROOT,
                                 check=True, capture_output=True).stdout
            with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
                for item in archive:
                    rel = Path(item.name)
                    if rel.is_absolute() or '..' in rel.parts or rel.parts[0] != 'codex_workflow':
                        raise ValueError('Unsafe baseline member')
                    if item.isfile():
                        path = baseline.parent/rel
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(archive.extractfile(item).read())
                    elif not item.isdir():
                        raise ValueError('Unsupported baseline entry')
        self.assertEqual((baseline/'operate/VERSION').read_text().strip(), '1.5.0')
        config = self.home/'config.toml'
        config.write_text('model="owner"\nmodel_reasoning_effort="low"\nplan_mode_reasoning_effort="high"\nservice_tier="fast"\n')
        project = self.root/'owner-project'
        project.mkdir()
        (project/'AGENTS.md').write_text('owner project constraints')
        (project/'live.bin').write_bytes(b'owner-data')
        project_before = snapshot(project)
        subprocess.run([sys.executable, '-B', str(baseline/'runtime/smart_install.py'),
                        '--package-root', str(baseline), '--codex-home', str(self.home), '--apply'],
                       check=True, capture_output=True)
        before = snapshot(self.home)
        parent_before = tomllib.loads(config.read_text())
        _, backup = self.install()
        self.assertEqual(tomllib.loads(config.read_text()), parent_before)
        self.assertEqual(doctor.inspect(self.home)['version'], CURRENT_VERSION)
        self.assertEqual(snapshot(project), project_before)
        self.assertEqual(self.install()[0].mutations, [])
        plan, prior = prepare_restore(self.home, backup)
        smart_install.apply_plan(plan, prior, self.home)
        for path, data in before.items():
            self.assertEqual((self.home/path).read_bytes(), data, path)
        self.assertEqual((self.home/'codex_workflow/operate/VERSION').read_text().strip(), '1.5.0')
        self.assertFalse((self.home/'codex_workflow/runtime/config_assessment.py').exists())
        self.assertEqual(snapshot(project), project_before)


class PolicyTests(unittest.TestCase):
    def test_scoped_policy_additions_preserve_bounds(self):
        policy = (PACKAGE/'smart_orchestration.md').read_text()
        for text in ('one bounded discovery pass', 'Resolve assumptions', 'whole-system audit',
                     'owning Executor diagnoses', 'No rigid retry quota', 'same Tester early',
                     'Early advice does not replace final verification', 'decision rationale',
                     'Do not invent undocumented reasons', 'Never weaken a required gate',
                     'fork_turns="none"', 'independent Tester', 'must not rubber-stamp'):
            self.assertIn(text, policy)
        self.assertLess(len(policy.split()), 1500)

    def test_capabilities_and_recursion_guards_unchanged(self):
        expected = {'simple_executor':('gpt-5.6-luna','medium'), 'routine_executor':('gpt-5.6-luna','high'),
                    'default_executor':('gpt-5.6-luna','max'), 'senior_executor':('gpt-5.6-sol','medium'),
                    'tester':('gpt-5.6-luna','xhigh'), 'companion':('gpt-5.6-luna','medium'),
                    'investigator':('gpt-5.6-luna','high'), 'archivist':('gpt-5.6-luna','medium')}
        package = PackageLayout.resolve(PACKAGE)
        self.assertEqual(package.version, CURRENT_VERSION)
        self.assertEqual(package.worker_names, set(expected))
        for role, pair in expected.items():
            cfg = tomllib.loads((PACKAGE/'agents'/f'{role}.toml').read_text())
            self.assertEqual((cfg['model'], cfg['model_reasoning_effort']), pair)
            self.assertIs(cfg['agents']['enabled'], False)
            self.assertLess(len(cfg['developer_instructions'].split()), 300)


if __name__ == '__main__':
    unittest.main()
