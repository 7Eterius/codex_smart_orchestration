"""2.4 delegation/design contracts and exact archived 2.3 migration.

Prompt tests establish shipped instructions, not live routing, visual quality or savings.
All installation writes use isolated temporary homes, never the owner's actual config.
"""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'codex_workflow'
BASELINE = 'f2c40c919a64863e8539245307f7c26226a90c3f'
sys.path.insert(0, str(PACKAGE))


def flat(path):
    return ' '.join(path.read_text().split())


def snapshot(root):
    return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mode & 0o777)
            for p in root.rglob('*') if p.is_file()
            and '.smart-orchestration-backups' not in p.relative_to(root).parts}


class DelegationContracts(unittest.TestCase):
    def test_version_and_existing_prompt_budgets(self):
        self.assertEqual((PACKAGE / 'operate/VERSION').read_text(), '2.4.0\n')
        for name, limit in [('smart_orchestration.md', 1200), ('execution.md', 1000),
                            ('verification.md', 700), ('browser.md', 650), ('design.md', 600)]:
            self.assertLess(len(flat(PACKAGE / name).split()), limit, name)
        self.assertIn('Smart Orchestration 2.4', (ROOT / 'README.md').read_text())
        self.assertIn('codex-workflow-version: 2.4.0', (PACKAGE / 'operate/user_AGENTS.md').read_text())

    def test_no_new_role_or_model_downgrade(self):
        expected = {'simple_executor': ('gpt-6-luna', 'low'),
                    'routine_executor': ('gpt-6-luna', 'high'),
                    'default_executor': ('gpt-6-luna', 'xhigh'),
                    'tester': ('gpt-6-luna', 'high'),
                    'senior_executor': ('gpt-6-sol', 'xhigh'),
                    'companion': ('gpt-6-luna', 'medium'),
                    'investigator': ('gpt-6-luna', 'xhigh'),
                    'archivist': ('gpt-6-luna', 'medium')}
        paths = list((PACKAGE / 'agents').glob('*.toml'))
        self.assertEqual({p.stem for p in paths}, set(expected))
        for path in paths:
            cfg = tomllib.loads(path.read_text())
            self.assertEqual((cfg['model'], cfg['model_reasoning_effort']), expected[path.stem])
            self.assertEqual(cfg['sandbox_mode'], 'workspace-write')
            self.assertIs(cfg['agents']['enabled'], path.stem in {'routine_executor', 'default_executor'})
            self.assertLess(len(cfg['developer_instructions'].split()), 200, path.name)

    def test_small_edits_and_main_findings_must_be_delegated(self):
        core = flat(PACKAGE / 'smart_orchestration.md')
        for clause in ('MUST be delegated', 'including small edits and fixes from main',
                       'Main is not the default writer', 'Name the execution owner',
                       'Main does not patch its findings itself'):
            self.assertIn(clause, core)
        self.assertNotIn('do one already-understood trivial operation when cheaper', core)
        self.assertIn('Do not write the implementation in a prompt for a worker to paste', core)

    def test_main_keeps_decisions_actual_review_and_reassessment(self):
        guide = flat(PACKAGE / 'design.md')
        for clause in ('Main remains the design author and quality judge',
                       'Main directly reviews an early running frame',
                       'Open and assess the actual evidence',
                       'Main groups related findings into one bounded correction assignment',
                       'Main inspects the corrected evidence',
                       'Missing evidence stays open'):
            self.assertIn(clause, guide)
        self.assertIn('Never reduce review depth to meet a delegation percentage',
                      flat(PACKAGE / 'smart_orchestration.md'))
        self.assertIn('Design-only tasks stop at the authorized concept',
                      flat(PACKAGE / 'smart_orchestration.md'))

    def test_browser_access_must_be_real_and_simple_gets_whole_journeys(self):
        browser = flat(PACKAGE / 'browser.md')
        for clause in ('Simple Luna Low is the default operator',
                       'one complete bounded assignment, not a worker per click',
                       'Verify the worker has the needed browser/Computer Use tools',
                       'only the indispensable authorized bridge step',
                       'Main reviews actual evidence, not captions',
                       'One owner controls shared GUI state'):
            self.assertIn(clause, browser)

    def test_corrections_reuse_context_without_bypassing_holds(self):
        guide = flat(PACKAGE / 'design.md')
        self.assertIn('Reuse the same suitable worker with a new correction task/delta', guide)
        self.assertIn('Release any independent candidate hold before repair', guide)
        self.assertIn('Tester keeps ownership of its independent verdict', guide)
        execution = flat(PACKAGE / 'execution.md')
        self.assertIn('Keep the writer available for concrete pending main review', execution)
        self.assertIn('After main accepts, persist evidence', execution)
        self.assertIn('Do not raise limits, loop on spawns', execution)

    def test_worker_briefs_cannot_replace_main_design_authority(self):
        for role in ('simple_executor', 'routine_executor', 'default_executor'):
            text = flat(PACKAGE / 'agents' / (role + '.toml'))
            self.assertIn('Main', text)
            self.assertIn('correction', text)
            self.assertIn('design', text)
            self.assertIn('evidence', text)
            self.assertIn('main', text)
        self.assertIn('Technical approval is not main', flat(PACKAGE / 'agents/tester.toml'))
        self.assertIn('Main settles design direction before Luna continues',
                      flat(PACKAGE / 'agents/senior_executor.toml'))

    def test_explicit_overrides_and_observed_boundaries_not_latency_escape(self):
        text = flat(PACKAGE / 'execution.md')
        self.assertIn('An explicit user no-agent/direct-execution instruction remains binding', text)
        self.assertIn('verified tool or permission boundary', text)
        self.assertIn('tiny diff, faster patch or unavailable nesting is not such a boundary', text)
        self.assertIn('If no safe path exists, report the blocked action', text)
        self.assertIn('Progress commentary continues the run', text)

    def test_validation_notes_do_not_claim_live_success(self):
        text = flat(ROOT / 'docs/v2.4.md')
        self.assertIn('not live Codex qualification or measured savings', text)
        self.assertIn('UNVERIFIED until observed', text)
        runtime = flat(PACKAGE / 'runtime_check.md')
        self.assertIn('A small settled edit is delegated', runtime)
        self.assertIn('not a new admission gate', runtime)


class BootstrapTests(unittest.TestCase):
    def test_active_bootstrap_contains_delegation_and_review_loop(self):
        from runtime.smart_config import bootstrap
        text = ' '.join(bootstrap(Path('/tmp/Codex home')).split())
        self.assertLess(len(text.split()), 260)
        for clause in ('Delegation is the execution default, including small edits and review fixes',
                       'Main inspects actual running visuals', 'grouped findings as correction tasks',
                       'then rechecks results', 'Do not self-patch to save time',
                       'No-agent/read-only requests remain binding'):
            self.assertIn(clause, text)
        managed = flat(PACKAGE / 'operate/user_AGENTS.md')
        self.assertIn('including small edits and main', managed)
        self.assertIn('not self-patching', managed)

    def test_bootstrap_patch_preserves_owner_settings_and_is_idempotent(self):
        from runtime.smart_config import patch_config, SMART
        owner = ('developer_instructions="Protected owner guidance."\n'
                 'model="owner-main"\nmodel_reasoning_effort="high"\n'
                 'plan_mode_reasoning_effort="xhigh"\nservice_tier="standard"\n'
                 'approval_policy="on-request"\nsandbox_mode="workspace-write"\n'
                 '[agents]\nmax_threads=1\ndefault_subagent_model="gpt-5.6-luna"\n'
                 'default_subagent_reasoning_effort="medium"\n'
                 '[mcp_servers.owner]\ncommand="keep-me"\n')
        home = Path('/tmp/Codex home тест')
        patched = patch_config(owner, home)
        before, after = tomllib.loads(owner), tomllib.loads(patched)
        original = before.pop('developer_instructions')
        active = after.pop('developer_instructions')
        self.assertEqual(before, after)
        self.assertTrue(active.startswith(original))
        self.assertEqual(active.count(SMART.start), 1)
        self.assertIn(str(home / 'codex_workflow/smart_orchestration.md'), active)
        self.assertEqual(patch_config(patched, home), patched)

    def test_only_managed_bootstrap_region_is_replaced(self):
        from runtime.smart_config import patch_config, SMART
        original = 'Protected prefix.\n' + SMART.start + '\nOld Smart policy.\n' + SMART.end + '\nProtected suffix.'
        config = 'developer_instructions=' + json.dumps(original) + '\nmodel="custom"\n'
        result = tomllib.loads(patch_config(config, Path('/tmp/codex')))
        self.assertTrue(result['developer_instructions'].startswith('Protected prefix.\n'))
        self.assertTrue(result['developer_instructions'].endswith('\nProtected suffix.'))
        self.assertNotIn('Old Smart policy.', result['developer_instructions'])
        self.assertEqual(result['model'], 'custom')


class InstallationTests(unittest.TestCase):
    def test_design_guide_installs_and_edits_remain_protected(self):
        from runtime import smart_install as install
        from runtime.layout import INSTALLED_RUNTIME_FILES, PackageLayout
        from runtime.errors import ValidationError
        self.assertIn('design.md', INSTALLED_RUNTIME_FILES)
        self.assertIn(PACKAGE / 'design.md', PackageLayout.resolve(PACKAGE).files)
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp).resolve() / 'home'
            plan, before = install.prepare(PACKAGE, home)
            install.apply_plan(plan, before, home)
            status = install.status(home)
            self.assertTrue(status['disk_ok'], status)
            self.assertEqual(status['runtime_observation'], 'not_inspected')
            guide = home / 'codex_workflow/design.md'
            self.assertEqual(guide.read_bytes(), (PACKAGE / 'design.md').read_bytes())
            guide.write_text(guide.read_text() + '\nProtected local edit.\n')
            self.assertFalse(install.status(home)['disk_ok'])
            with self.assertRaises(ValidationError):
                install.prepare(PACKAGE, home)

    def test_exact_v23_to_v24_reapply_and_rollback(self):
        from runtime import smart_install as install
        from runtime.smart_restore import prepare_restore
        result = subprocess.run(['git', 'archive', BASELINE, 'codex_workflow'], cwd=ROOT,
                                capture_output=True, check=False)
        if result.returncode:
            if os.environ.get('CI'):
                self.fail('CI requires exact v2.3 Git history: ' + result.stderr.decode(errors='replace'))
            self.skipTest('Exact v2.3 Git object unavailable; required in CI')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
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
                        target.chmod(member.mode & 0o777)
                    else:
                        self.assertTrue(member.isdir())
            old_package = root / 'baseline/codex_workflow'
            self.assertEqual((old_package / 'operate/VERSION').read_text(), '2.3.0\n')
            home = root / 'Codex home'
            home.mkdir()
            (home / 'config.toml').write_text('model="owner-main"\nmodel_reasoning_effort="high"\n'
                'service_tier="standard"\napproval_policy="on-request"\n'
                '[agents]\nmax_threads=2\ndefault_subagent_model="gpt-5.6-luna"\n'
                'default_subagent_reasoning_effort="medium"\n[mcp_servers.owner]\ncommand="keep"\n')
            (home / 'AGENTS.md').write_text('Protected owner instructions.\n')
            project = root / 'project'
            project.mkdir()
            (project / 'AGENTS.md').write_text('Protected project instructions.')
            (project / 'source.txt').write_text('Untouched source.')
            command = [sys.executable, '-B', str(old_package / 'runtime/smart_install.py'),
                       '--package-root', str(old_package), '--codex-home', str(home)]
            ran = subprocess.run(command + ['--apply'], capture_output=True, text=True)
            self.assertEqual(ran.returncode, 0, ran.stdout + ran.stderr)
            before, project_before = snapshot(home), snapshot(project)
            plan, prior = install.prepare(PACKAGE, home)
            self.assertEqual(snapshot(home), before, 'Preview must not write')
            backup = install.apply_plan(plan, prior, home)
            self.assertIsNotNone(backup)
            self.assertTrue(install.status(home)['disk_ok'])
            self.assertEqual((home / 'codex_workflow/operate/VERSION').read_text(), '2.4.0\n')
            self.assertEqual((home / 'codex_workflow/design.md').read_bytes(), (PACKAGE / 'design.md').read_bytes())
            old_cfg = tomllib.loads(before['config.toml'][0].decode())
            new_cfg = tomllib.loads((home / 'config.toml').read_text())
            self.assertNotEqual(old_cfg['developer_instructions'], new_cfg['developer_instructions'])
            self.assertIn('Delegation is the execution default', new_cfg['developer_instructions'])
            old_cfg.pop('developer_instructions')
            new_cfg.pop('developer_instructions')
            self.assertEqual(old_cfg, new_cfg)
            for role in (PACKAGE / 'agents').glob('*.toml'):
                old_role = tomllib.loads((old_package / 'agents' / role.name).read_text())
                new_role = tomllib.loads((home / 'agents' / role.name).read_text())
                for key in ('model', 'model_reasoning_effort', 'sandbox_mode', 'agents'):
                    self.assertEqual(old_role[key], new_role[key], (role.name, key))
            self.assertEqual(snapshot(project), project_before)
            self.assertEqual(install.prepare(PACKAGE, home)[0].mutations, [])
            restore, prior = prepare_restore(home, backup)
            install.apply_plan(restore, prior, home)
            self.assertEqual(snapshot(home), before)
            self.assertEqual(snapshot(project), project_before)
            self.assertFalse((home / 'codex_workflow/design.md').exists())
            checked = subprocess.run(command + ['--check'], capture_output=True, text=True)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            self.assertTrue(json.loads(checked.stdout)['disk_ok'])


if __name__ == '__main__':
    unittest.main()
