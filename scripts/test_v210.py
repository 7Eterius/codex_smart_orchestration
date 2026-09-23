"""2.1 policy-text contracts and an exact 2.0 upgrade/rollback integration.

Text assertions do not prove native agent scheduling or savings. Live scenarios are
specified separately in qualification.md. The migration really runs both installers.
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
    def test_version_and_prompt_budgets(self):
        import tomllib
        self.assertEqual((PACKAGE / 'operate/VERSION').read_text(), '2.1.0\n')
        self.assertIn('codex-workflow-version: 2.1.0', flat('operate/user_AGENTS.md'))
        for filename, maximum in [('smart_orchestration.md', 1200), ('coordinated.md', 1000),
                                  ('verification.md', 700), ('browser.md', 650)]:
            self.assertLess(len(flat(filename).split()), maximum, filename)
        roles = list((PACKAGE / 'agents').glob('*.toml'))
        self.assertEqual(len(roles), 9)
        for path in roles:
            cfg = tomllib.loads(path.read_text())
            self.assertLess(len(cfg['developer_instructions'].split()), 200, path.name)
            self.assertIs(cfg['agents']['enabled'], path.stem == 'chunk_lead')

    def test_assignment_shape_does_not_force_a_full_team(self):
        text = flat('coordinated.md')
        for phrase in ('mechanical-only -> Simple', 'validation-only -> Tester',
                       'No implementer for validation-only work', 'not every'):
            self.assertIn(phrase, text)

    def test_group_has_member_gates_and_finite_scope(self):
        text = flat('coordinated.md')
        for phrase in ('exact ordered member IDs', 'per-member gates',
                       'The lead cannot choose more members', 'unresolved product decisions'):
            self.assertIn(phrase, text)
        lead = flat('agents/chunk_lead.toml')
        self.assertIn("A group preserves each member's gates", lead)
        self.assertIn('never select additional work', lead)

    def test_status_is_not_final_completion(self):
        text = flat('smart_orchestration.md')
        for phrase in ('Worker final results end that assignment',
                       'Main progress replies are commentary',
                       "lead's completion does not end the coordinator's run"):
            self.assertIn(phrase, text)
        self.assertIn('one coalesced active-lead snapshot', flat('coordinated.md'))
        self.assertIn('without descendant queries or waking retired workers', text)

    def test_resource_handoff_is_distinct_from_context_reset(self):
        text = flat('coordinated.md')
        for phrase in ('Context lifetime is not resource lifetime', 'released consumers',
                       'identity, owner, consumers and release conditions',
                       'do not reinstall dependencies or replay login'):
            self.assertIn(phrase, text)

    def test_recovery_reconciles_receipts_and_stale_attempts(self):
        text = flat('coordinated.md')
        for phrase in ('Stale/duplicate results cannot advance', 'before an authorized commit',
                       'record the observed commit/readback immediately afterward',
                       'never replay blindly or infer acceptance'):
            self.assertIn(phrase, text)
        self.assertIn('outcome-unknown: inspect before retrying', flat('browser.md'))

    def test_gate_map_does_not_weaken_independence(self):
        text = flat('verification.md')
        for phrase in ('One requirement map', 'independent completeness check',
                       'Mandatory fresh execution remains fresh',
                       'required local failure does', 'not-applicable'):
            self.assertIn(phrase, text)
        self.assertIn('not the test oracle', text)
        self.assertIn('affected dependent gates', text)
        self.assertIn('not every successful test', text)

    def test_qualification_explicitly_covers_new_mechanics(self):
        text = flat('qualification.md')
        for phrase in ('Record once, invalidate selectively', 'three assignment shapes',
                       'execution continues', 'stale/duplicate result', 'outcome receipt',
                       'cost per accepted outcome'):
            self.assertIn(phrase.lower(), text.lower())

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
            self.assertEqual((home / 'codex_workflow/operate/VERSION').read_text(), '2.1.0\n')
            self.assertEqual((home / 'config.toml').read_bytes(), before['config.toml'][0])
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
