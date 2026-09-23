"""Executable batch-candidate checks; these do not test native agent scheduling."""
from __future__ import annotations
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'codex_workflow'))
from runtime import candidate as c


class BatchCandidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.source = self.root / 'source'
        self.source.mkdir()
        for scope in ('left', 'right'):
            (self.source / scope).mkdir()
            (self.source / scope / 'input.txt').write_text('initial')
        self.left = self.take('left')
        self.right = self.take('right')

    def take(self, name):
        output = self.root / (name + '.json')
        c.write_manifest(c.snapshot(self.source, [name]), output)
        return output

    def test_all_match_is_read_only(self):
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = c.verify_many([self.left, self.right])
        self.assertTrue(result['all_matched'])
        self.assertEqual(result['exit_code'], 0)
        self.assertEqual(result['counts'], {'matched': 2, 'drift': 0, 'error': 0})
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_only_changed_scope_drifts(self):
        (self.source / 'left/input.txt').write_text('changed')
        result = c.verify_many([self.left, self.right])
        self.assertEqual(result['exit_code'], 1)
        self.assertEqual([r['status'] for r in result['results']], ['drift', 'matched'])
        self.assertEqual(result['results'][0]['changed'], ['left/input.txt'])

    def test_error_does_not_hide_other_drift(self):
        (self.source / 'left/new.txt').write_text('new untracked input')
        self.right.write_text('not JSON')
        result = c.verify_many([self.right, self.left])
        self.assertEqual(result['exit_code'], 2)
        self.assertFalse(result['all_matched'])
        self.assertEqual(result['counts'], {'matched': 0, 'drift': 1, 'error': 1})
        self.assertEqual(result['results'][1]['added'], ['left/new.txt'])

    def test_missing_manifest_is_error_but_other_results_survive(self):
        result = c.verify_many([self.root / 'missing.json', self.left])
        self.assertEqual(result['exit_code'], 2)
        self.assertEqual([r['status'] for r in result['results']], ['error', 'matched'])

    def test_missing_required_scope_is_not_a_pass(self):
        (self.source / 'left/input.txt').unlink()
        (self.source / 'left').rmdir()
        result = c.verify_many([self.left, self.right])
        self.assertEqual(result['exit_code'], 2)
        self.assertEqual(result['results'][0]['status'], 'error')

    def test_batch_does_not_cache_previous_verification(self):
        self.assertEqual(c.verify_many([self.left])['exit_code'], 0)
        (self.source / 'left/input.txt').write_text('later change')
        self.assertEqual(c.verify_many([self.left])['exit_code'], 1)

    def test_duplicate_and_invalid_batch_fail_before_reads(self):
        for values in ([], [self.left, self.left], [self.left] * (c.MAX_BATCH + 1), ['bad'], None):
            with self.subTest(values=values), mock.patch.object(c, 'read_manifest') as read:
                with self.assertRaises(c.CandidateError):
                    c.verify_many(values)
                read.assert_not_called()

    def test_output_preview_budget_is_shared(self):
        for scope in ('left', 'right'):
            for i in range(35):
                (self.source / scope / f'new-{i:02}.txt').write_text('new')
        result = c.verify_many([self.left, self.right])
        self.assertEqual(result['exit_code'], 1)
        self.assertEqual([r['counts']['added'] for r in result['results']], [35, 35])
        self.assertTrue(all(r['truncated'] for r in result['results']))
        count = sum(len(r[k]) for r in result['results'] for k in ('added', 'removed', 'changed'))
        self.assertLessEqual(count, c.MAX_BATCH_PREVIEW_PATHS)

    def test_duplicate_json_keys_are_not_accepted(self):
        self.left.write_text('{"schema":1,"schema":1}')
        self.assertEqual(c.verify_many([self.left])['results'][0]['status'], 'error')

    def test_symlink_candidate_is_not_read(self):
        target = self.source / 'left/input.txt'
        outside = self.root / 'private'
        outside.write_text('do not read')
        target.unlink()
        target.symlink_to(outside)
        result = c.verify_many([self.left])
        self.assertEqual(result['exit_code'], 2)
        self.assertNotIn('do not read', json.dumps(result))

    def test_cli_exit_codes_and_output(self):
        args = ['verify-many', '--manifest', str(self.left), '--manifest', str(self.right)]
        for expected in (0, 1, 2):
            if expected == 1:
                (self.source / 'left/input.txt').write_text('changed')
            elif expected == 2:
                self.right.write_text('invalid')
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = c.main(args)
            self.assertEqual(status, expected)
            result = json.loads(output.getvalue())
            self.assertEqual(result['exit_code'], expected)
            self.assertEqual(len(result['results']), 2)

    def test_limits_and_not_acceptance_are_explicit(self):
        result = c.verify_many([self.left])
        self.assertIn('not a test verdict', result['limitation'])
        self.assertIn('not an atomic', result['consistency'])
        self.assertNotIn('accepted', result)


if __name__ == '__main__':
    unittest.main()
