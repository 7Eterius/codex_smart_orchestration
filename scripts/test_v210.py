"""2.1 policy-text contracts and an exact 2.0 upgrade/rollback integration.

Text assertions do not prove native agent scheduling or savings. Live scenarios are
specified separately in runtime_check.md. The migration really runs both installers.
"""
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
BASELINE = 'e90d1a513e183cb47598b4ba601e79ab392f0873'


def flat(relative):
    return ' '.join((PACKAGE / relative).read_text().split())


class V21PolicyContracts(unittest.TestCase):
    """Retain 2.1's useful guarantees under the current single-loop contract."""
    def test_version_and_prompt_budgets(self):
        import tomllib
        version = (PACKAGE / 'operate/VERSION').read_text().strip()
        self.assertIn('codex-workflow-version: ' + version, flat('operate/user_AGENTS.md'))
        for filename, maximum in [('smart_orchestration.md', 1200), ('execution.md', 1000),
                                  ('verification.md', 700), ('browser.md', 650)]:
            self.assertLess(len(flat(filename).split()), maximum, filename)
        roles = list((PACKAGE / 'agents').glob('*.toml'))
        self.assertEqual(len(roles), 8)
        for path in roles:
            cfg = tomllib.loads(path.read_text())
            self.assertLess(len(cfg['developer_instructions'].split()), 200, path.name)
            self.assertIs(cfg['agents']['enabled'], path.stem in {'routine_executor', 'default_executor'})

    def test_assignment_shape_does_not_force_a_full_team(self):
        text = flat('smart_orchestration.md')
        self.assertIn('one owner', text)
        self.assertIn('Remove the dedicated chunk_lead layer', text)
        self.assertIn('Standalone validation has no implementer or manager', flat('verification.md'))

    def test_group_has_member_gates_and_finite_scope(self):
        text = flat('execution.md')
        self.assertIn('per-member gates and dependency order', text)
        self.assertIn('never extend it to keep an agent busy', text)

    def test_status_is_not_final_completion(self):
        text = flat('execution.md')
        self.assertIn('Progress commentary continues the run', text)
        self.assertIn('final worker handoff ends only that assignment', text)
        self.assertIn('not a cascade of tests or descendant polls', flat('smart_orchestration.md'))

    def test_resource_handoff_is_distinct_from_context_reset(self):
        text = flat('browser.md')
        self.assertIn('Context lifetime is not resource lifetime', text)
        self.assertIn('One owner controls shared GUI state', text)
        self.assertIn('released consumers', text)

    def test_recovery_reconciles_receipts_and_stale_attempts(self):
        text = flat('smart_orchestration.md')
        self.assertIn('Reject stale attempts', text)
        self.assertIn('before authorized consequential writes', text)
        self.assertIn('their observed outcomes afterward', text)
        self.assertIn('inspect before retrying', flat('browser.md'))

    def test_gate_map_does_not_weaken_independence(self):
        text = flat('verification.md')
        for phrase in ('Check coverage independently', 'required fresh checks',
                       'Required local failures block local acceptance', 'not-applicable'):
            self.assertIn(phrase, text)
        self.assertIn('not the writer', flat('smart_orchestration.md'))

    def test_runtime_checks_do_not_fabricate_readiness(self):
        text = flat('runtime_check.md')
        self.assertIn('Do not convert an old failed trial into a pass', text)
        self.assertIn('second owner/reviewer pair', text)
        self.assertIn('No fixed saving percentage', text)

    def test_current_docs_links_resolve(self):
        for name in ('README.md', 'docs/smart_orchestration.md', 'docs/v2.1.md'):
            path = ROOT / name
            self.assertTrue(path.is_file())
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if not target.startswith(('https:', 'http:', '#')):
                    self.assertTrue((path.parent / target.split('#')[0]).exists(), target)


class ActualV20Upgrade(unittest.TestCase):
    def test_exact_v20_to_v21_reapply_and_rollback(self):
        result = subprocess.run(['git', 'archive', BASELINE, 'codex_workflow'], cwd=ROOT,
                                capture_output=True, check=False)
        if result.returncode:
            if os.environ.get('CI'):
                self.fail('CI requires the exact 2.0 Git object: ' + result.stderr.decode(errors='replace'))
            self.skipTest('Exact 2.0 Git object unavailable; required in CI')
        sys.path.insert(0, str(PACKAGE))
        from runtime import smart_install as install
        from runtime.smart_restore import prepare_restore
        from test_v200 import snapshot
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
                        target.chmod(member.mode & 0o777)
                    else:
                        self.assertTrue(member.isdir())
            baseline = root / 'baseline/codex_workflow'
            home = root / 'home'
            home.mkdir()
            config = ('model="owner-model"\nmodel_reasoning_effort="medium"\n'
                      'approval_policy="on-request"\n[agents]\nmax_threads=2\n')
            (home / 'config.toml').write_text(config)
            (home / 'AGENTS.md').write_text('Protected local instructions.\n')
            project = root / 'project'
            project.mkdir()
            (project / 'owner.txt').write_text('Do not change.')
            project_before = snapshot(project)
            old = subprocess.run([sys.executable, '-B', str(baseline / 'runtime/smart_install.py'),
                                  '--package-root', str(baseline), '--codex-home', str(home), '--apply'],
                                 capture_output=True, text=True, check=False)
            self.assertEqual(old.returncode, 0, old.stdout + old.stderr)
            before = snapshot(home)
            plan, prior = install.prepare(PACKAGE, home)
            self.assertEqual(snapshot(home), before, 'preview mutated disk')
            backup = install.apply_plan(plan, prior, home)
            self.assertTrue(install.status(home)['disk_ok'])
            self.assertEqual((home / 'codex_workflow/operate/VERSION').read_text(), (PACKAGE / 'operate/VERSION').read_text())
            import tomllib
            after_cfg = tomllib.loads((home / 'config.toml').read_text())
            before_cfg = tomllib.loads(before['config.toml'][0].decode())
            after_cfg.pop('developer_instructions', None)
            before_cfg.pop('developer_instructions', None)
            self.assertEqual(after_cfg, before_cfg)
            self.assertEqual(install.prepare(PACKAGE, home)[0].mutations, [])
            restore, prior = prepare_restore(home, backup)
            install.apply_plan(restore, prior, home)
            self.assertEqual(snapshot(home), before)
            self.assertEqual(snapshot(project), project_before)
            checked = subprocess.run([sys.executable, '-B', str(baseline / 'runtime/smart_install.py'),
                                      '--codex-home', str(home), '--check'],
                                     capture_output=True, text=True, check=False)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)


if __name__ == '__main__':
    unittest.main()
