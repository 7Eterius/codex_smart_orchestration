"""Deterministic boundary consistency checks, not live runtime qualification."""
from __future__ import annotations
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'codex_workflow'))
from runtime import boundary as b


def record(**changes):
    value = dict(schema=1, unit='U1', attempt='A1', contract='requirements-v1',
                 candidate='sha256:fixture', target='local-build-1', primary='main',
                 writer='writer-1', reviewer='tester-1', hold='held', gates={'behavior': True, 'references': False})
    value.update(changes)
    return value


def verdict(**changes):
    r = record()
    value = {k: r[k] for k in (*b.IDENTITY, 'reviewer')}
    value.update(artifact='evidence/tester-A1.json', gates={
        'behavior': {'status': 'executed-pass', 'evidence': 'evidence/behavior.log'},
        'references': {'status': 'reused-pass', 'evidence': 'evidence/reference.log'}})
    value.update(changes)
    return value


class BoundaryTests(unittest.TestCase):
    def test_matching_independent_acceptance_basis(self):
        result = b.check(record(), 'accept', 'main', verdict())
        self.assertTrue(result['allowed'])
        self.assertIn('not authenticated', result['limitation'])

    def test_no_input_mutations(self):
        r, v = record(), verdict()
        before = copy.deepcopy((r, v))
        b.check(r, 'accept', 'main', v)
        self.assertEqual((r, v), before)

    def test_writer_cannot_resume_during_hold(self):
        self.assertFalse(b.check(record(), 'write', 'writer-1')['allowed'])
        self.assertTrue(b.check(record(hold='released'), 'write', 'writer-1')['allowed'])

    def test_wrong_actor_cannot_write(self):
        for actor in ('main', 'tester-1', 'stranger'):
            self.assertFalse(b.check(record(hold='released'), 'write', actor)['allowed'])

    def test_readback_during_hold_does_not_grant_writes(self):
        for actor in ('main', 'writer-1', 'tester-1'):
            self.assertTrue(b.check(record(), 'readback', actor)['allowed'])
        self.assertFalse(b.check(record(), 'readback', 'stranger')['allowed'])

    def test_review_requires_reviewer_and_hold(self):
        self.assertTrue(b.check(record(), 'review', 'tester-1')['allowed'])
        self.assertFalse(b.check(record(hold='released'), 'review', 'tester-1')['allowed'])
        self.assertFalse(b.check(record(), 'review', 'writer-1')['allowed'])

    def test_acceptance_requires_primary_and_hold(self):
        self.assertFalse(b.check(record(), 'accept', 'writer-1', verdict())['allowed'])
        self.assertFalse(b.check(record(), 'accept', 'tester-1', verdict())['allowed'])
        self.assertFalse(b.check(record(hold='released'), 'accept', 'main', verdict())['allowed'])

    def test_missing_verdict_is_not_acceptance(self):
        self.assertEqual(b.check(record(), 'accept', 'main')['reason'], 'independent_verdict_missing')

    def test_stale_attempt_contract_candidate_target_or_identity(self):
        for field in (*b.IDENTITY, 'reviewer'):
            with self.subTest(field=field):
                self.assertEqual(b.check(record(), 'accept', 'main', verdict(**{field: 'changed'}))['reason'],
                                 'stale_or_misattributed_verdict')

    def test_no_self_review(self):
        for changes in ({'reviewer': 'writer-1'}, {'reviewer': 'main'}, {'writer': 'main'}):
            with self.subTest(changes=changes), self.assertRaises(b.BoundaryError):
                b.check(record(**changes), 'accept', 'main', verdict())

    def test_gate_map_cannot_omit_or_add_obligations(self):
        for gates in ({}, {'behavior': {'status': 'executed-pass', 'evidence': 'log'}}, {**verdict()['gates'], 'extra': {}}):
            self.assertEqual(b.check(record(), 'accept', 'main', verdict(gates=gates))['reason'], 'gate_map_mismatch')

    def test_failed_blocked_unrun_deferred_na_and_stale_pass_block(self):
        for status in ('failed', 'blocked', 'unrun', 'deferred', 'not-applicable', 'reused-pass'):
            v = verdict()
            v['gates']['behavior']['status'] = status
            with self.subTest(status=status):
                result = b.check(record(), 'accept', 'main', v)
                self.assertFalse(result['allowed'])
                self.assertEqual(result['rejected_gates'], ['behavior'])

    def test_fresh_execution_can_satisfy_reusable_gate(self):
        v = verdict()
        v['gates']['references']['status'] = 'executed-pass'
        self.assertTrue(b.check(record(), 'accept', 'main', v)['allowed'])

    def test_evidence_reference_required(self):
        for field in ('artifact', 'gate'):
            v = verdict()
            if field == 'artifact':
                v['artifact'] = ''
            else:
                v['gates']['behavior']['evidence'] = ''
            with self.assertRaises(b.BoundaryError):
                b.check(record(), 'accept', 'main', v)

    def test_schema_types_rejected_without_typeerror(self):
        for field in record():
            for value in (None, [], {}, 3.5, ''):
                with self.subTest(field=field, value=value), self.assertRaises(b.BoundaryError):
                    b.check(record(**{field: value}), 'review', 'tester-1')

    def test_freshness_is_strict_boolean(self):
        for value in (1, 'false', [], None):
            with self.assertRaises(b.BoundaryError):
                b.check(record(gates={'behavior': value}), 'review', 'tester-1')

    def test_unknown_fields_and_dispositions_are_errors(self):
        with self.assertRaises(b.BoundaryError):
            b.check(record(unexpected=True), 'review', 'tester-1')
        v = verdict()
        v['gates']['behavior']['status'] = 'probably-pass'
        with self.assertRaises(b.BoundaryError):
            b.check(record(), 'accept', 'main', v)

    def test_irrelevant_verdict_rejected(self):
        with self.assertRaises(b.BoundaryError):
            b.check(record(), 'review', 'tester-1', verdict())

    def test_cli_results_exit_codes_and_read_only_input(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'boundary.json'
            for payload, code in ((dict(record=record(), action='review', actor='tester-1'), 0),
                                  (dict(record=record(), action='write', actor='writer-1'), 1),
                                  (dict(record=record(), action='review', actor=[]), 2)):
                path.write_text(json.dumps(payload))
                before = path.read_bytes()
                output, error = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                    self.assertEqual(b.main(['--input', str(path)]), code)
                self.assertEqual(path.read_bytes(), before)
                self.assertIn('allowed', json.loads(error.getvalue() if code == 2 else output.getvalue()))

    def test_cli_duplicate_deep_oversize_and_symlink_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'boundary.json'
            for text in ('{"record":{},"record":{}}', '[' * 2000 + '0' + ']' * 2000, ' ' * (b.MAX_INPUT_BYTES + 1)):
                path.write_text(text)
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(b.main(['--input', str(path)]), 2)
            alias = Path(temp) / 'alias.json'
            alias.symlink_to(path)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(b.main(['--input', str(alias)]), 2)


if __name__ == '__main__':
    unittest.main()
