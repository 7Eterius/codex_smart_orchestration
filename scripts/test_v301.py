"""Patch regressions for scope downgrade, holds and usable review capacity.

These exercise actual allocator entry points, not native Codex or model performance.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'codex_workflow'
sys.path.insert(0, str(PACKAGE))
from runtime import allocation as a

BASELINE = '474326b0892e473bcde5638bccf81eb8944aac50'


def scope(path='src/a', **kw):
    d = dict(workspace='/repo', reads=[path], writes=[path], resource_reads=[], resource_writes=[])
    d.update(kw)
    return d


def thread(ident='a', **kw):
    d = dict(id=ident, parent='main', unit=ident, role='default_executor', state='running',
             owned=True, retain=True, durable=False, released_resources=False,
             scope=scope('src/' + ident))
    d.update(kw)
    return d


def observation(*threads, **kw):
    d = dict(caller='main', primary='main', cap=4, complete=True, close_supported=True,
             main_scope=None, threads=list(threads))
    d.update(kw)
    return d


def request(unit='b', **kw):
    d = dict(unit=unit, role='default_executor', reserve=0, reuse_id=None,
             spawn_failed=False, state_changed=False, scope=scope('src/' + unit))
    d.update(kw)
    return d


def reproductions():
    unscoped = request()
    unscoped.pop('scope')
    reviewer = request('a', role='tester', candidate_held=True)
    reviewer.pop('scope')
    return {
        'unscoped Main conflict': (observation(main_scope=scope('src/b')), unscoped),
        'unscoped reviewer bypass': (observation(thread()), reviewer),
        'held writer reuse': (observation(thread(state='waiting')),
                              request('a', reuse_id='a', candidate_held=True)),
        'retained unrelated reviewer': (
            observation(thread(review_reserved=True),
                        thread('old-review', unit='old', role='tester', state='completed',
                               scope=scope('src/old', writes=[])), cap=3), request()),
        'ignored reuse reservation': (observation(thread(state='waiting'), cap=1),
                                      request('a', reuse_id='a', reserve=1)),
        'unrelated review steals reservation': (
            observation(thread('a', review_reserved=True), thread('b', review_reserved=True), cap=3),
            request('other', role='tester', candidate_held=True, scope=scope('src/other', writes=[]))),
    }


class ScopeAndHoldTests(unittest.TestCase):
    def test_omitted_scope_cannot_hide_main_activity(self):
        obs, req = reproductions()['unscoped Main conflict']
        self.assertEqual(a.next_action(obs, req)['reason'], 'parallel_scopes_required')

    def test_omitted_scope_cannot_bypass_scoped_writer(self):
        obs, req = reproductions()['unscoped reviewer bypass']
        self.assertEqual(a.next_action(obs, req)['reason'], 'parallel_scopes_required')

    def test_legacy_serial_without_known_concurrent_scope_stays_usable(self):
        req = request()
        req.pop('scope')
        self.assertEqual(a.next_action(observation(), req)['action'], 'spawn')

    def test_scope_is_inherited_for_same_worker_reuse(self):
        req = request('a', reuse_id='a')
        req.pop('scope')
        self.assertEqual(a.next_action(observation(thread(state='waiting')), req)['action'], 'reuse')

    def test_held_candidate_blocks_writer_spawn_and_reuse_without_reviewer(self):
        for role in a.WRITERS:
            with self.subTest(role=role):
                self.assertEqual(a.next_action(observation(), request(role=role, candidate_held=True))['reason'],
                                 'candidate_still_held')
                obs = observation(thread(role=role, state='waiting'))
                req = request('a', role=role, reuse_id='a', candidate_held=True)
                self.assertEqual(a.next_action(obs, req)['reason'], 'candidate_still_held')

    def test_release_allows_same_writer_repair(self):
        obs = observation(thread(state='waiting'))
        self.assertEqual(a.next_action(obs, request('a', reuse_id='a', candidate_held=False))['action'], 'reuse')

    def test_readback_still_is_not_write_authority(self):
        obs = observation(thread(state='waiting'))
        req = request('a', reuse_id='a', intent='readback', candidate_held=True)
        self.assertEqual(a.next_action(obs, req)['reason'], 'readback_only')

    def test_standalone_scoped_review_needs_hold_even_without_live_writer(self):
        for flags in ({}, {'candidate_held': False}):
            with self.subTest(flags=flags):
                req = request(role='tester', scope=scope('src/b', writes=[]), **flags)
                self.assertEqual(a.next_action(observation(), req)['reason'], 'review_requires_candidate_hold')
        req['candidate_held'] = True
        self.assertEqual(a.next_action(observation(), req)['action'], 'spawn')

    def test_equivalent_scope_order_reuses_context_without_transfer(self):
        old = scope(reads=['src/a', 'shared'], writes=['src/a', 'src/a2'],
                    resource_reads=['api/x', 'api/y'])
        new = {k: list(reversed(v)) if isinstance(v, list) else v for k, v in old.items()}
        obs = observation(thread(state='waiting', scope=old))
        self.assertEqual(a.next_action(obs, request('a', reuse_id='a', scope=new))['action'], 'reuse')
        new['writes'].append('src/auth')
        self.assertEqual(a.next_action(obs, request('a', reuse_id='a', scope=new))['reason'],
                         'scope_change_requires_transfer')

    def test_disjoint_work_still_runs_in_parallel(self):
        obs = observation(thread(), main_scope=scope('src/main'))
        self.assertEqual(a.next_action(obs, request())['action'], 'spawn')

    def test_shared_browser_conflicts_still_block(self):
        obs = observation(thread(scope=scope(resource_writes=['browser/main'])))
        req = request(scope=scope('src/b', resource_writes=['browser/main']))
        self.assertEqual(a.next_action(obs, req)['reason'], 'scope_or_resource_conflict')


class ReviewCapacityTests(unittest.TestCase):
    def test_retained_unrelated_reviewer_is_not_free_review_capacity(self):
        obs, req = reproductions()['retained unrelated reviewer']
        self.assertEqual(a.next_action(obs, req)['reason'], 'insufficient_open_thread_budget')
        obs['threads'][1].update(state='closed', closure_evidence='native/closed')
        self.assertEqual(a.next_action(obs, req)['action'], 'spawn')

    def test_unrelated_review_cannot_steal_pending_review_slot(self):
        obs, req = reproductions()['unrelated review steals reservation']
        self.assertEqual(a.next_action(obs, req)['reason'], 'insufficient_open_thread_budget')

    def test_queued_reviewer_can_consume_the_shared_reserved_slot(self):
        obs = observation(thread('a', state='waiting', review_reserved=True),
                          thread('b', review_reserved=True), cap=3)
        req = request('a', role='tester', candidate_held=True, scope=scope(writes=[]))
        self.assertEqual(a.next_action(obs, req)['action'], 'spawn')

    def test_two_independent_reviews_can_pipeline_without_wait_for_all(self):
        obs = observation(thread('a', state='waiting', review_reserved=True),
                          thread('b', state='waiting', review_reserved=True),
                          thread('review-a', unit='a', role='tester', scope=scope(writes=[])))
        req = request('b', role='tester', candidate_held=True, scope=scope('src/b', writes=[]))
        self.assertEqual(a.next_action(obs, req)['action'], 'spawn')
        self.assertNotEqual(a.next_action(obs, request('unrelated'))['action'], 'spawn')

    def test_two_writers_share_one_future_slot_not_two(self):
        obs = observation(thread(review_reserved=True), cap=3)
        self.assertEqual(a.next_action(obs, request(reserve=1))['action'], 'spawn')

    def test_reuse_new_reservation_needs_real_room(self):
        obs, req = reproductions()['ignored reuse reservation']
        self.assertEqual(a.next_action(obs, req)['reason'], 'insufficient_open_thread_budget')
        obs['cap'] = 2
        result = a.next_action(obs, req)
        self.assertEqual(result['action'], 'reuse')
        self.assertIs(result['record_review_reserved'], True)

    def test_reuse_keeps_existing_reservation_in_returned_observation(self):
        obs = observation(thread(state='waiting', review_reserved=True))
        result = a.next_action(obs, request('a', reuse_id='a'))
        self.assertIs(result['record_review_reserved'], True)

    def test_existing_same_unit_reviewer_needs_no_extra_reserved_slot(self):
        obs = observation(thread(state='waiting'),
                          thread('review-a', unit='a', role='tester', state='completed',
                                 scope=scope(writes=[])), cap=2)
        req = request('a', reuse_id='a', reserve=1, candidate_held=False)
        self.assertEqual(a.next_action(obs, req)['action'], 'reuse')

    def test_closing_or_unknown_reviewer_is_not_reusable_capacity(self):
        for state in ('closing', 'unknown'):
            obs = observation(thread('old-review', unit='b', role='tester', state=state,
                                     scope=scope(reads=[], writes=[])), cap=2)
            with self.subTest(state=state):
                self.assertEqual(a.next_action(obs, request(reserve=1))['reason'],
                                 'insufficient_open_thread_budget')

    def test_reuse_unknown_cap_only_blocks_new_slot_obligation(self):
        obs = observation(thread(state='waiting'), cap=None)
        req = request('a', reuse_id='a')
        self.assertEqual(a.next_action(obs, req)['action'], 'reuse')
        req['reserve'] = 1
        self.assertEqual(a.next_action(obs, req)['reason'], 'capacity_unknown')

    def test_four_thread_ceiling_and_owner_cap_are_not_raised(self):
        obs = observation(*(thread(x) for x in ('a', 'b', 'c', 'd')), cap=8)
        self.assertEqual(a.next_action(obs, request('e'))['reason'], 'smart_open_thread_budget')
        self.assertEqual(a.SMART_OPEN_LIMIT, 4)

    def test_no_new_review_obligation_is_not_forced_to_reserve(self):
        self.assertEqual(a.next_action(observation(thread(), cap=2), request())['action'], 'spawn')


class EntryPointTests(unittest.TestCase):
    def test_records_are_not_mutated_and_results_are_deterministic(self):
        for name, (obs, req) in reproductions().items():
            before = copy.deepcopy((obs, req))
            with self.subTest(name=name):
                first = a.next_action(obs, req)
                self.assertEqual(a.next_action(obs, req), first)
                self.assertEqual((obs, req), before)

    def test_actual_cli_exits_nonzero_on_reproduced_gaps(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'input.json'
            for name, (obs, req) in reproductions().items():
                path.write_text(json.dumps({'observation': obs, 'request': req}))
                before = path.read_bytes()
                ran = subprocess.run([sys.executable, '-B', a.__file__, '--input', str(path)],
                                     capture_output=True, text=True, timeout=10)
                with self.subTest(name=name):
                    self.assertEqual(ran.returncode, 1, ran.stdout + ran.stderr)
                    self.assertNotIn(json.loads(ran.stdout)['action'], ('spawn', 'reuse'))
                    self.assertEqual(path.read_bytes(), before)

    def test_archived_300_reproduces_each_fixed_gap(self):
        ran = subprocess.run(['git', 'show', BASELINE + ':codex_workflow/runtime/allocation.py'],
                             cwd=ROOT, capture_output=True, timeout=30)
        if ran.returncode:
            if os.environ.get('CI'):
                self.fail('Exact 3.0.0 source is required in CI')
            self.skipTest('Exact Git history unavailable locally; required in CI')
        old = types.ModuleType('archived_allocation')
        exec(compile(ran.stdout, 'archived_allocation.py', 'exec'), old.__dict__)
        for name, (obs, req) in reproductions().items():
            with self.subTest(name=name):
                self.assertIn(old.next_action(obs, req)['action'], ('spawn', 'reuse'))
                self.assertNotIn(a.next_action(obs, req)['action'], ('spawn', 'reuse'))


if __name__ == '__main__':
    unittest.main()
