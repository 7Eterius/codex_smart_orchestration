"""Scoped candidate identity tests, with no network or live model dependencies."""
from __future__ import annotations

import contextlib
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'codex_workflow'))
from runtime import candidate as c


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve() / 'project with spaces'
        self.root.mkdir()
        (self.root / 'src').mkdir()
        (self.root / 'src/a.py').write_text('a = 1\n')
        (self.root / 'lock.json').write_text('{}\n')
        self.paths = ['src', 'lock.json']
        self.output = self.root.parent / 'candidate.json'

    def take(self):
        return c.snapshot(self.root, self.paths)

    def call(self, args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = c.main(args)
        return code, out.getvalue(), err.getvalue()

    def test_stable_deterministic_and_read_only(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        first, second = self.take(), self.take()
        self.assertEqual(first, second)
        self.assertTrue(c.verify(first)['matched'])
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        self.assertIn('not a test verdict', first['limitation'])

    def test_changed_content(self):
        manifest = self.take()
        (self.root / 'src/a.py').write_text('a = 2\n')
        result = c.verify(manifest)
        self.assertFalse(result['matched'])
        self.assertEqual(result['changed'], ['src/a.py'])

    def test_untracked_added_and_removed_inputs(self):
        manifest = self.take()
        (self.root / 'src/new.py').write_text('untracked')
        (self.root / 'src/a.py').unlink()
        result = c.verify(manifest)
        self.assertEqual(result['added'], ['src/new.py'])
        self.assertEqual(result['removed'], ['src/a.py'])
        self.assertFalse(result['matched'])

    def test_unrelated_inputs_do_not_invalidate(self):
        manifest = self.take()
        (self.root / 'unrelated.txt').write_text('not in the contract')
        self.assertTrue(c.verify(manifest)['matched'])

    def test_lockfile_is_a_real_input(self):
        manifest = self.take()
        (self.root / 'lock.json').write_text('{"version": 2}')
        self.assertEqual(c.verify(manifest)['changed'], ['lock.json'])

    @unittest.skipIf(os.name == 'nt', 'POSIX modes')
    def test_executable_mode_change(self):
        manifest = self.take()
        path = self.root / 'src/a.py'
        path.chmod(path.stat().st_mode ^ 0o100)
        self.assertEqual(c.verify(manifest)['changed'], ['src/a.py'])

    def test_missing_required_scope_fails_closed(self):
        manifest = self.take()
        (self.root / 'lock.json').unlink()
        with self.assertRaises(c.CandidateError):
            c.verify(manifest)

    def test_scope_kind_change_is_not_a_match(self):
        manifest = self.take()
        (self.root / 'src/a.py').unlink()
        (self.root / 'src').rmdir()
        (self.root / 'src').write_text('now a file')
        result = c.verify(manifest)
        self.assertTrue(result['scope_changed'])
        self.assertFalse(result['matched'])

    def test_paths_are_explicit_and_bounded(self):
        for value in ('', '.', '/', '../src', 'src/../lock.json', '/src', r'C:\src', 'src/.git', '.git/config'):
            with self.subTest(value=value), self.assertRaises(c.CandidateError):
                c.snapshot(self.root, [value])
        with self.assertRaises(c.CandidateError):
            c.snapshot(self.root, [])

    def test_unicode_and_overlapping_scopes(self):
        (self.root / 'src/привет мир.py').write_text('hello')
        manifest = c.snapshot(self.root, ['src', 'src/a.py', 'src'])
        self.assertEqual(len(manifest['files']), 2)
        self.assertTrue(c.verify(manifest)['matched'])

    @unittest.skipIf(os.name == 'nt', 'symlink privileges vary')
    def test_symlinks_and_ancestry_are_refused(self):
        outside = self.root.parent / 'secret'
        outside.write_text('protected')
        (self.root / 'src/link').symlink_to(outside)
        with self.assertRaises(c.CandidateError):
            self.take()
        (self.root / 'src/link').unlink()
        alias = self.root.parent / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(c.CandidateError):
            c.snapshot(alias, ['src'])
        (self.root / 'alias').symlink_to(self.root / 'src', target_is_directory=True)
        with self.assertRaises(c.CandidateError):
            c.snapshot(self.root, ['alias/a.py'])
        self.assertEqual(outside.read_text(), 'protected')

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'POSIX fifo')
    def test_special_file_refused_without_reading(self):
        os.mkfifo(self.root / 'src/pipe')
        with self.assertRaises(c.CandidateError):
            self.take()

    def test_byte_and_entry_limits(self):
        with patch.object(c, 'MAX_BYTES', 2), self.assertRaises(c.CandidateError):
            self.take()
        with patch.object(c, 'MAX_FILES', 1), self.assertRaises(c.CandidateError):
            self.take()

    def test_invalid_manifest_integrity_and_schema(self):
        original = self.take()
        for key, value in [('schema', True), ('schema', 2), ('fingerprint', '0' * 64), ('root', 'relative')]:
            value_manifest = copy.deepcopy(original)
            value_manifest[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(c.CandidateError):
                c.verify(value_manifest)

    def test_manifest_cannot_escape_scope(self):
        manifest = self.take()
        manifest['files']['outside.txt'] = manifest['files']['src/a.py']
        manifest['fingerprint'] = c._content_id(manifest['scopes'], manifest['files'])
        with self.assertRaises(c.CandidateError):
            c.verify(manifest)

    def test_duplicate_json_keys_refused(self):
        self.output.write_text('{"schema":1,"schema":1}')
        with self.assertRaises(c.CandidateError):
            c.read_manifest(self.output)

    def test_private_manifest_and_no_overwrite(self):
        manifest = self.take()
        c.write_manifest(manifest, self.output)
        self.assertEqual(c.read_manifest(self.output), manifest)
        if os.name != 'nt':
            self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)
        before = self.output.read_bytes()
        with self.assertRaises(FileExistsError):
            c.write_manifest(manifest, self.output)
        self.assertEqual(self.output.read_bytes(), before)

    def test_output_must_not_mutate_watched_scope(self):
        manifest = self.take()
        with self.assertRaises(c.CandidateError):
            c.write_manifest(manifest, self.root / 'src/evidence.json')
        self.assertFalse((self.root / 'src/evidence.json').exists())

    def test_output_does_not_create_parent_trees(self):
        with self.assertRaises(FileNotFoundError):
            c.write_manifest(self.take(), self.root.parent / 'unknown/out.json')
        self.assertFalse((self.root.parent / 'unknown').exists())

    def test_manifest_size_limit(self):
        self.output.write_text(' ' * 100)
        with patch.object(c, 'MAX_MANIFEST_BYTES', 10), self.assertRaises(c.CandidateError):
            c.read_manifest(self.output)

    def test_cli_has_distinct_success_drift_and_error_codes(self):
        code, out, err = self.call(['snapshot', '--root', str(self.root), '--path', 'src', '--output', str(self.output)])
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)['files'], 1)
        self.assertEqual(self.call(['verify', '--manifest', str(self.output)])[0], 0)
        (self.root / 'src/a.py').write_text('changed')
        code, out, err = self.call(['verify', '--manifest', str(self.output)])
        self.assertEqual(code, 1, err)
        self.assertFalse(json.loads(out)['matched'])
        self.output.write_text('not json')
        self.assertEqual(self.call(['verify', '--manifest', str(self.output)])[0], 2)

    def test_large_drift_cli_is_bounded(self):
        c.write_manifest(self.take(), self.output)
        for i in range(30):
            (self.root / f'src/new{i}.py').write_text(str(i))
        code, out, err = self.call(['verify', '--manifest', str(self.output)])
        self.assertEqual(code, 1, err)
        result = json.loads(out)
        self.assertEqual(result['counts']['added'], 30)
        self.assertEqual(len(result['added']), 20)
        self.assertTrue(result['truncated'])


if __name__ == '__main__':
    unittest.main()
