"""Audit regressions and malformed-input checks; no native Codex claims."""
from __future__ import annotations
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'codex_workflow'))
from runtime import allocation as a, candidate as c


def thread(ident='writer', **changes):
    value = dict(id=ident, parent='main', unit='U1', role='routine_executor', state='waiting',
                 owned=True, retain=True, durable=False, released_resources=False,
                 review_authorized=True)
    value.update(changes)
    return value


def observation(*threads, **changes):
    value = dict(caller='main', primary='main', cap=3, complete=True,
                 close_supported=True, threads=list(threads))
    value.update(changes)
    return value


def request(**changes):
    value = dict(unit='U1', role='routine_executor', reserve=0, reuse_id=None,
                 spawn_failed=False, state_changed=False)
    value.update(changes)
    return value


class AllocationHardening(unittest.TestCase):
    def test_reuse_cannot_reactivate_second_writer(self):
        for role in sorted(a.WRITERS):
            for state in ('running', 'waiting', 'completed', 'closing', 'unknown'):
                with self.subTest(role=role, state=state):
                    obs = observation(thread('old'), thread('current', role=role, state=state))
                    result = a.next_action(obs, request(reuse_id='old'))
                    self.assertEqual(result['reason'], 'existing_writer_requires_explicit_transfer')
                    self.assertNotEqual(result['action'], 'reuse')

    def test_observed_closure_allows_repair_owner_reuse(self):
        obs = observation(thread('old'), thread('current', role='default_executor', state='closed', closure_evidence='native-close'))
        self.assertEqual(a.next_action(obs, request(reuse_id='old'))['action'], 'reuse')

    def test_readback_does_not_grant_write_ownership(self):
        obs = observation(thread('old'), thread('current', role='default_executor', state='running'))
        before = copy.deepcopy(obs)
        result = a.next_action(obs, request(reuse_id='old', intent='readback'))
        self.assertEqual((result['action'], result['intent'], result['reason']), ('reuse', 'readback', 'readback_only'))
        self.assertEqual(obs, before)
        self.assertNotEqual(a.next_action(obs, request(reuse_id='old'))['action'], 'reuse')

    def test_readback_cannot_spawn_or_reserve(self):
        for changes in ({}, {'reuse_id': 'writer', 'reserve': 1}):
            with self.subTest(changes=changes), self.assertRaises(a.AllocationError):
                a.next_action(observation(thread()), request(intent='readback', **changes))

    def test_readback_still_requires_stopped_matching_owned_child(self):
        for changes in ({'state': 'running'}, {'unit': 'U2'}, {'owned': False}, {'parent': 'other'}):
            with self.subTest(changes=changes), self.assertRaises(a.AllocationError):
                a.next_action(observation(thread(**changes)), request(intent='readback', reuse_id='writer'))

    def test_unknown_caller_is_not_primary(self):
        with self.assertRaises(a.AllocationError):
            a.next_action(observation(caller='unlisted'), request())

    def test_explicit_primary_supports_real_handles(self):
        obs = observation(caller='native-primary-17', primary='native-primary-17')
        self.assertEqual(a.next_action(obs, request())['action'], 'spawn')

    def test_legacy_primary_is_literal_main_only(self):
        obs = observation()
        obs.pop('primary')
        self.assertEqual(a.next_action(obs, request())['action'], 'spawn')
        obs['caller'] = 'writer'
        with self.assertRaises(a.AllocationError):
            a.next_action(obs, request())

    def test_primary_is_not_counted_as_spawned_thread(self):
        with self.assertRaises(a.AllocationError):
            a.next_action(observation(thread('main', parent='external')), request())

    def test_inactive_caller_cannot_dispatch(self):
        for state in ('completed', 'closing', 'closed', 'unknown'):
            fields = {'closure_evidence': 'native-close'} if state == 'closed' else {}
            with self.subTest(state=state), self.assertRaises(a.AllocationError):
                a.next_action(observation(thread(state=state, **fields), caller='writer'), request(role='tester'))

    def test_unowned_caller_cannot_dispatch(self):
        with self.assertRaises(a.AllocationError):
            a.next_action(observation(thread(owned=False), caller='writer'), request(role='tester'))

    def test_nested_review_requires_same_unit(self):
        with self.assertRaises(a.AllocationError):
            a.next_action(observation(thread(), caller='writer'), request(role='tester', unit='U2'))

    def test_nested_review_requires_explicit_authority(self):
        owner = thread()
        for value in (False, None):
            current = dict(owner)
            if value is None:
                current.pop('review_authorized')
            else:
                current['review_authorized'] = value
            with self.subTest(value=value), self.assertRaises(a.AllocationError):
                a.next_action(observation(current, caller='writer'), request(role='tester'))

    def test_authority_is_strictly_boolean(self):
        with self.assertRaises(a.AllocationError):
            a.next_action(observation(thread(review_authorized='true')), request())

    def test_authorized_same_unit_review_is_allowed(self):
        result = a.next_action(observation(thread(), caller='writer'), request(role='tester'))
        self.assertEqual(result['action'], 'spawn')

    def test_cleanup_precedes_unrelated_new_unit_authorization(self):
        owner = thread(state='completed')
        child = thread('reviewer', parent='writer', role='tester', state='completed',
                       retain=False, durable=True, released_resources=True)
        obs = observation(owner, child, caller='writer')
        req = request(role='tester', unit='U2')
        self.assertEqual(a.next_action(obs, req)['ids'], ['reviewer'])
        child.update(state='closed', closure_evidence='native-close')
        with self.assertRaises(a.AllocationError):
            a.next_action(obs, req)

    def test_retired_owner_can_cleanup_but_not_dispatch(self):
        owner = thread(role='chunk_lead', state='completed')
        child = thread('reviewer', parent='writer', role='tester', state='completed',
                       retain=False, durable=True, released_resources=True)
        obs = observation(owner, child, caller='writer')
        self.assertEqual(a.next_action(obs, request(intent='cleanup'))['ids'], ['reviewer'])
        child.update(state='closed', closure_evidence='native-close')
        self.assertEqual(a.next_action(obs, request(intent='cleanup'))['reason'], 'no_supported_cleanup')
        with self.assertRaises(a.AllocationError):
            a.next_action(obs, request(role='tester'))

    def test_cleanup_does_not_close_busy_or_unrelated_children(self):
        obs = observation(thread(), thread('other', owned=False, state='completed', retain=False,
                                         durable=True, released_resources=True))
        self.assertEqual(a.next_action(obs, request(intent='cleanup'))['reason'], 'no_supported_cleanup')

    def test_invalid_cleanup_and_intents_rejected(self):
        for changes in ({'intent': 'cleanup', 'reserve': 1}, {'intent': 'cleanup', 'reuse_id': 'writer'},
                        {'intent': 'anything'}, {'intent': []}):
            with self.subTest(changes=changes), self.assertRaises(a.AllocationError):
                a.next_action(observation(thread()), request(**changes))

    def test_partial_inventory_cannot_authorize_work(self):
        result = a.next_action(observation(caller='unknown', complete=False), request())
        self.assertEqual(result['action'], 'inspect')

    def test_deep_json_is_structured_cli_error(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'observation.json'
            path.write_text('[' * 2000 + '0' + ']' * 2000)
            output = io.StringIO()
            with contextlib.redirect_stderr(output):
                self.assertEqual(a.main(['--input', str(path)]), 2)
            self.assertEqual(json.loads(output.getvalue())['action'], 'blocked')


class CandidateHardening(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        source = self.root / 'src'
        source.mkdir()
        (source / 'input.txt').write_text('initial')
        self.manifest = c.snapshot(self.root, ['src'])
        self.good = self.root / 'good.json'
        c.write_manifest(self.manifest, self.good)

    def test_bad_kind_cannot_hide_drift_or_match(self):
        source = self.root / 'src/input.txt'
        source.write_text('changed')
        fresh = self.root / 'fresh.json'
        c.write_manifest(c.snapshot(self.root, ['src']), fresh)
        for value in ([], {}, None, True, 1, 'unsupported'):
            bad = copy.deepcopy(self.manifest)
            bad['scopes'][0]['kind'] = value
            path = self.root / 'bad.json'
            path.write_text(json.dumps(bad))
            with self.subTest(value=value):
                result = c.verify_many([path, self.good, fresh])
                self.assertEqual([r['status'] for r in result['results']], ['error', 'drift', 'matched'])
                self.assertEqual(result['exit_code'], 2)

    def test_schema_type_mutations_have_only_declared_errors(self):
        replacements = [None, True, 1, 1.5, [], {}, '', ['x']]
        for field in ('schema', 'root', 'scopes', 'files', 'fingerprint'):
            for value in replacements:
                if field == 'schema' and type(value) is int and value == 1:
                    continue
                bad = copy.deepcopy(self.manifest)
                bad[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(c.CandidateError):
                    c.verify(bad)

    def test_bad_scope_and_file_metadata_are_normalized(self):
        for field in ('path', 'kind'):
            for value in (None, [], {}, True):
                bad = copy.deepcopy(self.manifest)
                bad['scopes'][0][field] = value
                with self.subTest(field=field, value=value), self.assertRaises(c.CandidateError):
                    c.verify(bad)
        for field in ('sha256', 'bytes', 'mode'):
            for value in (None, [], {}, True):
                bad = copy.deepcopy(self.manifest)
                bad['files']['src/input.txt'][field] = value
                with self.subTest(field=field, value=value), self.assertRaises(c.CandidateError):
                    c.verify(bad)

    def test_unknown_nested_metadata_is_rejected(self):
        for target in ('scope', 'file'):
            bad = copy.deepcopy(self.manifest)
            item = bad['scopes'][0] if target == 'scope' else bad['files']['src/input.txt']
            item['unexpected'] = []
            with self.assertRaises(c.CandidateError):
                c.verify(bad)

    def test_directory_alias_does_not_count_twice(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        result = c.verify_many([self.good, alias / 'good.json'])
        self.assertEqual(result['counts'], {'matched': 1, 'drift': 0, 'error': 1})
        self.assertIn('Duplicate manifest identity', result['results'][1]['error'])

    def test_hardlink_does_not_count_twice(self):
        alias = self.root / 'hardlink.json'
        os.link(self.good, alias)
        result = c.verify_many([self.good, alias])
        self.assertEqual(result['counts'], {'matched': 1, 'drift': 0, 'error': 1})

    def test_equal_content_in_distinct_files_is_not_physical_duplicate(self):
        other = self.root / 'other.json'
        other.write_bytes(self.good.read_bytes())
        result = c.verify_many([self.good, other])
        self.assertEqual(result['counts']['matched'], 2)
        self.assertIn('not a test verdict', result['limitation'])

    def test_duplicate_error_does_not_hide_later_drift(self):
        alias = self.root / 'hardlink.json'
        os.link(self.good, alias)
        (self.root / 'src/input.txt').write_text('changed')
        other = self.root / 'other.json'
        other.write_bytes(self.good.read_bytes())
        result = c.verify_many([self.good, alias, other])
        self.assertEqual([r['status'] for r in result['results']], ['drift', 'error', 'drift'])

    def test_lexical_duplicates_keep_existing_fail_fast_contract(self):
        with mock.patch.object(c, 'read_manifest') as read, self.assertRaises(c.CandidateError):
            c.verify_many([self.good, self.good])
        read.assert_not_called()

    def test_unreadable_and_missing_inputs_preserve_other_results(self):
        missing = self.root / 'missing.json'
        original = c.read_manifest
        def read(path):
            if path == self.good:
                raise PermissionError('simulated unreadable evidence')
            return original(path)
        other = self.root / 'other.json'
        other.write_bytes(self.good.read_bytes())
        with mock.patch.object(c, 'read_manifest', side_effect=read):
            result = c.verify_many([missing, self.good, other])
        self.assertEqual([r['status'] for r in result['results']], ['error', 'error', 'matched'])

    def test_deep_json_is_individual_error(self):
        bad = self.root / 'bad.json'
        bad.write_text('[' * 2000 + '0' + ']' * 2000)
        result = c.verify_many([bad, self.good])
        self.assertEqual([r['status'] for r in result['results']], ['error', 'matched'])

    def test_malformed_batch_cli_is_structured_and_nonzero(self):
        bad = copy.deepcopy(self.manifest)
        bad['scopes'][0]['kind'] = []
        path = self.root / 'bad.json'
        path.write_text(json.dumps(bad))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = c.main(['verify-many', '--manifest', str(path), '--manifest', str(self.good)])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())['counts']['matched'], 1)

    def test_unexpected_programming_errors_are_not_swallowed(self):
        with mock.patch.object(c, 'verify', side_effect=RuntimeError('programming error')):
            with self.assertRaisesRegex(RuntimeError, 'programming error'):
                c.verify_many([self.good])


if __name__ == '__main__':
    unittest.main()
