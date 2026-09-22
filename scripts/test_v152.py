"""v1.5.2 design ownership and installed-package regressions.

Static instruction contracts are not model evaluations. No actual app, design
quality or token saving is claimed. Integration checks use isolated fake homes.
"""
from __future__ import annotations

import hashlib
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
BASE = '80a85b62833578cef792338a2875dac6b79c7616'
BASE_TREE = '93e80770b0a0fb740179e29c9320d1eed2c3298c'
sys.path.insert(0, str(PACKAGE))
from runtime import doctor, smart_install
from runtime.errors import ValidationError
from runtime.layout import PackageLayout
from runtime.smart_restore import prepare_restore
from runtime._toml import tomllib

EXECUTORS = ('simple_executor', 'routine_executor', 'default_executor', 'senior_executor')
TIERS = {
    'simple_executor': ('gpt-6-luna', 'low'),
    'routine_executor': ('gpt-6-luna', 'high'),
    'default_executor': ('gpt-6-luna', 'max'),
    'senior_executor': ('gpt-6-sol', 'xhigh'),
    'tester': ('gpt-6-luna', 'xhigh'),
    'companion': ('gpt-6-luna', 'medium'),
    'investigator': ('gpt-6-luna', 'xhigh'),
    'archivist': ('gpt-6-luna', 'medium'),
}


def text(path):
    return (PACKAGE / path).read_text(encoding='utf-8')


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def git_tree_hash(root):
    """Verify the complete text package against its published Git tree."""
    entries = []
    for path in root.iterdir():
        if path.is_symlink():
            raise ValueError('Unexpected baseline symlink')
        if path.is_dir():
            sha = git_tree_hash(path)
            entries.append((path.name + '/', b'40000', bytes.fromhex(sha)))
        elif path.is_file():
            raw = path.read_bytes()
            sha = hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).digest()
            entries.append((path.name, b'100644', sha))
        else:
            raise ValueError('Unexpected baseline entry')
    data = b''.join(mode + b' ' + name.rstrip('/').encode() + b'\0' + sha
                    for name, mode, sha in sorted(entries, key=lambda item: item[0].encode()))
    return hashlib.sha1(f'tree {len(data)}\0'.encode() + data).hexdigest()


def load_baseline(destination):
    supplied = os.environ.get('SMART_V151_BASELINE')
    if supplied:
        package = Path(supplied)
    else:
        raw = subprocess.run(['git', 'archive', BASE, 'codex_workflow'], cwd=ROOT,
                             check=True, capture_output=True).stdout
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            for member in archive:
                relative = Path(member.name)
                if relative.is_absolute() or '..' in relative.parts or relative.parts[0] != 'codex_workflow':
                    raise ValueError('Unsafe baseline archive path')
                if member.isfile():
                    target = destination / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.extractfile(member).read())
                elif not member.isdir():
                    raise ValueError('Unexpected baseline archive type')
        package = destination / 'codex_workflow'
    if git_tree_hash(package) != BASE_TREE:
        raise ValueError('Baseline is not the exact published v1.5.1 package tree')
    return package


class DesignContractTests(unittest.TestCase):
    def setUp(self):
        self.policy = text('smart_orchestration.md')
        self.design = self.policy.split('## Design ownership\n', 1)[1].split('\n## ', 1)[0]

    def test_main_authorship_not_just_review(self):
        for phrase in ('main owns product, UX, interaction and visual authorship',
                       'not merely coordination or approval'):
            self.assertIn(phrase, self.design)

    def test_settled_brief_precedes_implementation(self):
        for phrase in ('accepted references', 'purpose', 'information hierarchy', 'composition',
                       'key states', 'interactions and visual direction', 'before bounded implementation'):
            self.assertIn(phrase, self.design)

    def test_unresolved_choices_and_alternatives_return_to_main(self):
        for phrase in ('Proposals and unresolved design choices return to main',
                       'no unilateral hierarchy', 'navigation, visual-language or product-meaning changes'):
            self.assertIn(phrase, self.design)

    def test_workers_keep_ordinary_implementation_autonomy(self):
        self.assertIn('ordinary details stay within agreed tokens/patterns', self.design)
        self.assertIn('owning Executor diagnoses', self.policy)

    def test_parent_owns_early_and_final_visual_review(self):
        for phrase in ('Main inspects an early running frame', 'gives concrete critique',
                       'directly reviews final evidence', 'unavailable visuals remain unverified',
                       'Mockups are not running evidence'):
            self.assertIn(phrase, self.design)

    def test_no_new_ceremony_for_small_or_concept_only_tasks(self):
        for phrase in ('no extra designer or mandatory', 'competition', 'Settled tweaks reuse direction',
                       'Design-only requests stop at the agreed', 'without unauthorized implementation'):
            self.assertIn(phrase, self.design)

    def test_novel_design_not_classified_by_diff_size(self):
        self.assertIn('Novel design is not cheap work because its diff is small', self.design)

    def test_owner_and_independent_acceptance_preserved(self):
        self.assertIn('Preserve owner decisions', self.design)
        self.assertIn('behavior/accessibility verification independent from main design judgment', self.design)
        self.assertIn('required owner approval', self.design)
        self.assertIn('Never weaken a required gate', self.policy)
        self.assertIn('deferred gates remain OPEN', self.policy)

    def test_all_executors_observe_design_boundary(self):
        for role in EXECUTORS:
            with self.subTest(role=role):
                instructions = tomllib.loads(text(f'agents/{role}.toml'))['developer_instructions']
                for phrase in ("main's settled brief", 'routine details use agreed',
                               'Return proposals or unresolved design choices to main',
                               'Small diffs do', 'not make novel design simple', 'Preserve owner decisions'):
                    self.assertIn(phrase, instructions)

    def test_tester_does_not_replace_visual_judgment(self):
        instructions = tomllib.loads(text('agents/tester.toml'))['developer_instructions']
        self.assertIn('Report behavioral/accessibility checks separately from main design judgment', instructions)
        self.assertIn('required owner approval', instructions)
        self.assertIn('never claim visual acceptance from passing tests', instructions)
        self.assertIn('never repair it', instructions)

    def test_archivist_cannot_invent_owner_approval(self):
        instructions = tomllib.loads(text('agents/archivist.toml'))['developer_instructions']
        self.assertIn('Record accepted design rationale and evidence references', instructions)
        self.assertIn('main-reviewed and owner-approved states', instructions)
        self.assertIn('Never infer owner approval from test passes', instructions)

    def test_instruction_size_and_eight_capability_tiers(self):
        self.assertLess(len(self.policy.split()), 1500)
        self.assertEqual(PackageLayout.resolve(PACKAGE).worker_names, set(TIERS))
        for role, tier in TIERS.items():
            cfg = tomllib.loads(text(f'agents/{role}.toml'))
            self.assertEqual((cfg['model'], cfg['model_reasoning_effort']), tier)
            self.assertIs(cfg['agents']['enabled'], False)
            self.assertLess(len(cfg['developer_instructions'].split()), 300)
        self.assertEqual(text('operate/VERSION'), CURRENT_VERSION + '\n')
        self.assertIn('version: ' + CURRENT_VERSION, text('operate/user_AGENTS.md'))


class InstalledDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline_temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.baseline_temp.cleanup)
        cls.baseline = load_baseline(Path(cls.baseline_temp.name))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / 'home'
        self.home.mkdir()
        self.project = self.root / 'project'
        self.project.mkdir()
        (self.project / 'AGENTS.md').write_text('Owner design and financial constraints\n')
        (self.project / 'screen.swift').write_text('Owner source\n')
        (self.project / 'live.bin').write_bytes(b'private-owner-data')
        self.before_project = snapshot(self.project)

    def apply(self):
        plan, before = smart_install.prepare(PACKAGE, self.home)
        return plan, smart_install.apply_plan(plan, before, self.home)

    def test_runtime_and_configuration_settings_are_unchanged(self):
        # v1.6 intentionally changes the anonymous child fallback and the dated
        # efficiency price reference. Every other runtime/resource byte stays fixed.
        previous_runtime = snapshot(self.baseline / 'runtime')
        current_runtime = snapshot(PACKAGE / 'runtime')
        for changed in ('agent_defaults.py', 'efficiency.py', 'layout.py', 'smart_install.py'):
            self.assertIn(changed, previous_runtime)
            self.assertIn(changed, current_runtime)
            previous_runtime.pop(changed)
            current_runtime.pop(changed)
        self.assertEqual(current_runtime, previous_runtime)
        self.assertEqual(snapshot(PACKAGE / 'resources'), snapshot(self.baseline / 'resources'))

        # Current Smart intentionally ships no built-in skill payload.
        self.assertTrue(snapshot(self.baseline / 'skills'))
        self.assertEqual(snapshot(PACKAGE / 'skills'), {})
        self.assertEqual(text('verification.md'), (self.baseline / 'verification.md').read_text())
        for role in TIERS:
            old = tomllib.loads((self.baseline / f'agents/{role}.toml').read_text())
            new = tomllib.loads(text(f'agents/{role}.toml'))
            for key in ('developer_instructions', 'description', 'model', 'model_reasoning_effort'):
                old.pop(key)
                new.pop(key)
            self.assertEqual(old, new, role)

    def test_fresh_global_install_preserves_parent_and_project(self):
        config = self.home / 'config.toml'
        config.write_text('model="owner-parent"\nmodel_reasoning_effort="low"\n'
                          'plan_mode_reasoning_effort="high"\nservice_tier="fast"\n')
        before = tomllib.loads(config.read_text())
        plan, backup = self.apply()
        self.assertEqual(plan.details['project_mutations'], 0)
        self.assertTrue(backup.is_dir())
        cfg = tomllib.loads(config.read_text())
        for key, value in before.items():
            self.assertEqual(cfg[key], value)
        self.assertEqual(snapshot(self.project), self.before_project)
        self.assertEqual(doctor.inspect(self.home)['version'], CURRENT_VERSION)
        self.assertIn('## Design ownership', (self.home / 'codex_workflow/smart_orchestration.md').read_text())
        for role in EXECUTORS:
            self.assertIn("main's settled brief", (self.home / f'agents/{role}.toml').read_text())

    def test_repeat_install_is_zero_write(self):
        self.apply()
        before = snapshot(self.home)
        plan, backup = self.apply()
        self.assertEqual(plan.mutations, [])
        self.assertIsNone(backup)
        self.assertEqual(snapshot(self.home), before)

    def test_custom_role_edits_still_block_overwrite(self):
        self.apply()
        role = self.home / 'agents/routine_executor.toml'
        role.write_text(role.read_text() + '\n# Owner override\n')
        before = snapshot(self.home)
        with self.assertRaisesRegex(ValidationError, 'Custom/unowned worker'):
            self.apply()
        self.assertEqual(snapshot(self.home), before)

    def test_exact_v151_upgrade_and_rollback(self):
        subprocess.run([sys.executable, '-B', str(self.baseline / 'runtime/smart_install.py'),
                        '--package-root', str(self.baseline), '--codex-home', str(self.home), '--apply'],
                       check=True, capture_output=True, text=True)
        before = snapshot(self.home)
        parent_before = (self.home / 'config.toml').read_bytes()
        _, backup = self.apply()
        self.assertEqual(doctor.inspect(self.home)['version'], CURRENT_VERSION)
        self.assertEqual((self.home / 'config.toml').read_bytes(), parent_before)
        self.assertEqual(self.apply()[0].mutations, [])
        plan, prior = prepare_restore(self.home, backup)
        smart_install.apply_plan(plan, prior, self.home)
        for path, data in before.items():
            self.assertEqual((self.home / path).read_bytes(), data, path)
        for path in snapshot(self.home):
            if not path.startswith('.smart-orchestration-backups/'):
                self.assertIn(path, before, path)
        self.assertEqual((self.home / 'codex_workflow/operate/VERSION').read_text(), '1.5.1\n')
        self.assertEqual(snapshot(self.project), self.before_project)


if __name__ == '__main__':
    unittest.main()
