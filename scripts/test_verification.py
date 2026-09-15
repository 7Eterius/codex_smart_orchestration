"""Deterministic output capture and risk-directed verification regressions.
No live app claims: subprocess fixtures are disposable Python commands.
"""
from __future__ import annotations
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "codex_workflow"
sys.path.insert(0, str(PACKAGE))
from runtime import capture_check as c


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def run_code(self, code, **kwargs):
        return c.run_check([sys.executable, "-B", "-c", code], cwd=self.root,
                           artifacts=self.root, **kwargs)

    def test_exact_raw_bytes_and_checksum(self):
        raw = b"hello\n\xffbinary\x00\n"
        result, code = self.run_code(f"import sys; sys.stdout.buffer.write({raw!r})")
        self.assertEqual(code, 0)
        self.assertEqual(Path(result['raw_output_path']).read_bytes(), raw)
        self.assertEqual(result['raw_output_bytes'], len(raw))
        self.assertEqual(result['raw_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result['acceptance'], 'not_assessed')
        self.assertIsNone(result['test_counts'])

    def test_nonzero_exit_code_not_masked(self):
        result, code = self.run_code("print('All tests passed'); raise SystemExit(17)")
        self.assertEqual(code, 17)
        self.assertEqual(result['command_exit_code'], 17)
        self.assertEqual(result['execution_status'], 'completed')
        self.assertEqual(result['acceptance'], 'not_assessed')

    def test_zero_exit_does_not_infer_a_test_pass(self):
        result, code = self.run_code("print('0 tests collected; WARNING: tests skipped')")
        self.assertEqual(code, 0)
        self.assertIsNone(result['test_counts'])
        self.assertEqual(result['acceptance'], 'not_assessed')
        self.assertGreater(result['diagnostic_fragments_seen'], 0)

    def test_stdout_and_stderr_retained(self):
        result, _ = self.run_code("import sys; print('OUT',flush=True); print('ERR',file=sys.stderr,flush=True)")
        self.assertEqual(Path(result['raw_output_path']).read_text(), 'OUT\nERR\n')

    def test_middle_diagnostic_survives_excerpt(self):
        code = "print('noise\\n'*1000); print('ERROR useful middle cause'); print('noise\\n'*1000)"
        result, _ = self.run_code(code)
        self.assertTrue(any('useful middle' in i['text'] for i in result['preview']))
        self.assertTrue(result['preview_incomplete'])
        self.assertGreater(result['raw_output_bytes'], result['preview_text_characters'])

    def test_large_single_line_has_bounded_preview(self):
        result, _ = self.run_code("print('a'*2000000)", preview_chars=256, preview_items=4)
        self.assertEqual(result['raw_output_bytes'], 2000001)
        self.assertLessEqual(sum(len(i['text']) for i in result['preview']), 256)
        self.assertTrue(result['preview_incomplete'])
        self.assertTrue(all(i['line'] == 1 for i in result['preview']))

    def test_many_errors_do_not_overflow_excerpt(self):
        result, _ = self.run_code("print('ERROR details\\n'*1000)", preview_items=4)
        self.assertLessEqual(len(result['preview']), 4)
        self.assertGreater(result['diagnostic_fragments_seen'], 4)
        self.assertTrue(result['preview_incomplete'])

    def test_preview_byte_offsets_recover_original_lines(self):
        result, _ = self.run_code("print('αβ\\nWARNING x\\ntail')")
        data = Path(result['raw_output_path']).read_bytes()
        for item in result['preview']:
            line = data[item['byte_offset']:].split(b'\n')[0].decode()
            self.assertEqual(line, item['text'])

    def test_blank_output_has_empty_excerpt_not_failure(self):
        result, code = self.run_code("pass")
        self.assertEqual(code, 0)
        self.assertEqual(result['preview'], [])
        self.assertEqual(result['raw_output_bytes'], 0)

    def test_signal_exit_keeps_signal_and_conventional_return(self):
        if os.name != 'posix':
            self.skipTest('POSIX signal fixture')
        result, code = self.run_code("import os,signal; os.kill(os.getpid(),signal.SIGTERM)")
        self.assertEqual(result['command_exit_code'], -signal.SIGTERM)
        self.assertEqual(code, 128 + signal.SIGTERM)

    def test_timeout_keeps_partial_output(self):
        result, code = self.run_code("import time; print('started',flush=True); time.sleep(10)", timeout=1.5)
        self.assertEqual(code, 124)
        self.assertEqual(result['execution_status'], 'timed_out')
        self.assertIn('started', Path(result['raw_output_path']).read_text())

    def test_missing_command_is_launch_error(self):
        result, code = c.run_check([str(self.root/'missing')], artifacts=self.root)
        self.assertEqual(code, 127)
        self.assertEqual(result['execution_status'], 'launch_error')
        self.assertIsNone(result['command_exit_code'])
        self.assertTrue(Path(result['receipt_path']).is_file())

    def test_never_uses_an_implicit_shell(self):
        command = [sys.executable, '-B', '-c', 'import sys; print(sys.argv[1])', 'hi; touch DANGER']
        result, code = c.run_check(command, cwd=self.root, artifacts=self.root)
        self.assertEqual(code, 0)
        self.assertIn('hi; touch DANGER', Path(result['raw_output_path']).read_text())
        self.assertFalse((self.root/'DANGER').exists())

    def test_noninteractive_input_reaches_eof(self):
        result, code = self.run_code("import sys; print(repr(sys.stdin.read()))")
        self.assertEqual(code, 0)
        self.assertEqual(Path(result['raw_output_path']).read_text().strip(), "''")

    def test_checks_always_execute_without_cache(self):
        code = "from pathlib import Path; p=Path('counter'); p.write_text(str(int(p.read_text())+1) if p.exists() else '1')"
        a, _ = self.run_code(code)
        b, _ = self.run_code(code)
        self.assertEqual((self.root/'counter').read_text(), '2')
        self.assertNotEqual(a['receipt_path'], b['receipt_path'])
        self.assertFalse(a['reused'])
        self.assertTrue(Path(a['raw_output_path']).exists())

    def test_private_artifacts_and_exact_receipt(self):
        result, _ = self.run_code("print('evidence')")
        path = Path(result['receipt_path'])
        self.assertEqual(json.loads(path.read_text()), result)
        if os.name == 'posix':
            self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(Path(result['raw_output_path']).stat().st_mode & 0o777, 0o600)

    def test_receipt_does_not_dump_environment(self):
        os.environ['SMART_TEST_PRIVATE_VALUE'] = 'should_not_be_dumped'
        try:
            result, _ = self.run_code("pass")
            self.assertNotIn('should_not_be_dumped', json.dumps(result))
        finally:
            del os.environ['SMART_TEST_PRIVATE_VALUE']

    def test_invalid_timeout_rejected_before_artifact_creation(self):
        for value in (0, -1, float('nan'), float('inf')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.run_code('pass', timeout=value)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_invalid_argv_rejected(self):
        for argv in ([], ['bad\x00name'], [1]):
            with self.subTest(argv=argv), self.assertRaises(ValueError):
                c.run_check(argv, artifacts=self.root)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_bad_working_directory_refused(self):
        with self.assertRaises(OSError):
            c.run_check([sys.executable], cwd=self.root/'missing', artifacts=self.root)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_preview_limits_validated(self):
        for kwargs in ({'preview_chars':0}, {'preview_chars':20001}, {'preview_items':3}, {'preview_items':81}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.run_code('pass', **kwargs)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_cli_preserves_command_failure_exit(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = c.main(['--artifacts', str(self.root), '--', sys.executable, '-c', 'raise SystemExit(7)'])
        self.assertEqual(code, 7)
        self.assertEqual(json.loads(out.getvalue())['command_exit_code'], 7)

    def test_cli_invalid_configuration_is_not_a_pass(self):
        out = io.StringIO()
        with contextlib.redirect_stderr(out):
            code = c.main(['--timeout', '0', '--', sys.executable])
        self.assertEqual(code, 125)
        self.assertEqual(json.loads(out.getvalue())['acceptance'], 'not_assessed')


class VerificationPolicyTests(unittest.TestCase):
    def setUp(self):
        self.guide = (PACKAGE/'verification.md').read_text()
        self.policy = (PACKAGE/'smart_orchestration.md').read_text()

    def test_checkpoint_coverage_not_per_worker_ceremony(self):
        for phrase in ('Edit loop:', 'Stable candidate:', 'Merge/release:', 'no full matrix per worker',
                       'independent Tester', 'explicitly OPEN'):
            self.assertIn(phrase, self.guide)

    def test_accessibility_is_triggered_not_disabled(self):
        for phrase in ('targeted accessibility', 'newly revealed states', 'Keyboard and focus/back',
                       'contrast/target size/Dynamic Type', 'Never disable rules', 'manual accessibility checks',
                       'UI impact is demonstrably absent'):
            self.assertIn(phrase, self.guide)

    def test_evidence_status_and_freshness_are_explicit(self):
        for phrase in ('execution vs reuse', 'not-applicable vs deferred vs blocked',
                       'No baseline/unknown applicability -> check', 'No blind command-result cache',
                       'owner/untracked changes'):
            self.assertIn(phrase, self.guide)

    def test_native_parallelism_cannot_race_shared_state(self):
        self.assertIn('Parallelize independent native checks', self.guide)
        self.assertIn('Serialize shared simulator, browser, build-output, database', self.guide)

    def test_reuse_builds_never_misrepresents_release(self):
        self.assertIn('Clean only for demonstrated stale artifacts', self.guide)
        self.assertIn('Debug checks do not prove Release behavior', self.guide)
        self.assertIn('Never auto-approve visual snapshots', self.guide)

    def test_strict_repo_gates_remain_and_no_lossy_audit_proxy(self):
        self.assertIn("cannot silently amend a project's stricter test plan", self.guide)
        self.assertIn('Do not compress decisive code diffs', self.guide)
        self.assertIn('read native reports/raw output'.lower(), self.guide.lower())

    def test_single_bounded_parent_policy_points_to_guide(self):
        self.assertIn('verification.md', self.policy)
        self.assertLess(len(self.policy.split()), 1500)
        self.assertLess(len(self.guide.split()), 700)


if __name__ == '__main__':
    unittest.main()
