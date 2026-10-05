"""Smart 3 routing, concurrency and lifecycle regressions. No model calls."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'codex_workflow'))
from runtime import allocation as a


def task(**kw):
    d=dict(kind='implementation', risk='low', settled=True, tiny=False, deep=False, independent_required=False)
    d.update(kw); return d


def scope(path='src/a', **kw):
    d=dict(workspace='/repo', reads=[path], writes=[path], resource_reads=[], resource_writes=[])
    d.update(kw); return d


def thread(ident='a', **kw):
    d=dict(id=ident,parent='main',unit=ident,role='default_executor',state='running',owned=True,
           retain=True,durable=False,released_resources=False,scope=scope('src/'+ident))
    d.update(kw); return d


def observation(*ts, **kw):
    d=dict(caller='main',primary='main',cap=4,complete=True,close_supported=True,
           main_scope=None, threads=list(ts))
    d.update(kw); return d


def request(unit='b', **kw):
    d=dict(unit=unit,role='default_executor',reserve=0,reuse_id=None,spawn_failed=False,state_changed=False,
           scope=scope('src/'+unit))
    d.update(kw); return d


class RoutingTests(unittest.TestCase):
    def test_normal_feature_uses_luna_max_owner(self):
        self.assertEqual(a.classify(task())['owner'],'routine_executor')
    def test_tiny_known_change_can_finish_in_main(self):
        self.assertEqual(a.classify(task(tiny=True))['owner'],'main')
    def test_tiny_off_path_recipe_can_use_simple(self):
        self.assertEqual(a.classify(task(tiny=True,in_context=False,mechanical=True))['owner'],'simple_executor')
    def test_critical_path_with_context_avoids_duplicate_solver(self):
        self.assertEqual(a.classify(task(in_context=True,on_critical_path=True))['owner'],'main')
    def test_unknown_browser_work_is_sol(self):
        self.assertEqual(a.classify(task(kind='operation'))['owner'],'default_executor')
    def test_known_browser_journey_is_simple(self):
        self.assertEqual(a.classify(task(kind='operation',mechanical=True))['owner'],'simple_executor')
    def test_prescribed_bulk_is_luna_routine(self):
        self.assertEqual(a.classify(task(mechanical=True))['owner'],'routine_executor')
    def test_material_recipe_retains_independent_review(self):
        result=a.classify(task(mechanical=True,risk='material'))
        self.assertEqual((result['owner'],result['reviewer']),('routine_executor','reviewer'))
    def test_stalled_cheap_work_does_not_get_cheap_retry(self):
        self.assertEqual(a.classify(task(mechanical=True,stalled=True))['owner'],'default_executor')
    def test_main_fix_preserves_required_review(self):
        self.assertEqual(a.classify(task(tiny=True,independent_required=True))['reviewer'],'reviewer')
    def test_deep_starts_sol_medium_with_senior_review(self):
        r=a.classify(task(deep=True)); self.assertEqual((r['owner'],r['reviewer']),('deep_executor','senior_reviewer'))
    def test_design_authority_stays_main(self):
        self.assertEqual(a.classify(task(kind='judgment'))['owner'],'main')
        self.assertEqual(a.classify(task(settled=False))['owner'],'main')
    def test_verification_does_not_spawn_writer_or_reviewer_chain(self):
        r=a.classify(task(kind='verification',risk='critical'))
        self.assertEqual((r['owner'],r['reviewer']),('senior_reviewer',None))
    def test_exact_lookup_vs_causal_investigation(self):
        self.assertEqual(a.classify(task(kind='discovery',mechanical=True))['owner'],'companion')
        self.assertEqual(a.classify(task(kind='discovery'))['owner'],'investigator')
    def test_bad_routing_types_fail_closed(self):
        for kw in ({'mechanical':'yes'},{'tiny':1},{'stalled':[]},{'deep':True,'tiny':True},{'risk':'maybe'}):
            with self.subTest(kw=kw),self.assertRaises(a.AllocationError):a.classify(task(**kw))


class ParallelTests(unittest.TestCase):
    def test_two_disjoint_workers_can_start(self):
        self.assertEqual(a.next_action(observation(thread()),request())['action'],'spawn')
    def test_preserved_four_thread_owner_cap_blocks_fifth(self):
        obs=observation(thread('a'),thread('b'),thread('c'))
        self.assertEqual(a.next_action(obs,request('d'))['action'],'spawn')
        obs['threads'].append(thread('d'))
        self.assertNotEqual(a.next_action(obs,request('e'))['action'],'spawn')
    def test_lower_owner_cap_is_respected(self):
        self.assertNotEqual(a.next_action(observation(thread(),cap=1),request())['action'],'spawn')
    def test_main_disjoint_work_is_allowed(self):
        obs=observation(thread(),main_scope=scope('src/main'))
        self.assertEqual(a.next_action(obs,request())['action'],'spawn')
    def test_main_conflicting_write_is_blocked(self):
        self.assertEqual(a.next_action(observation(main_scope=scope('src/b')),request())['reason'],'main_scope_conflict')
    def test_unknown_main_or_peer_scope_is_not_parallel(self):
        obs=observation(thread());del obs['main_scope']
        self.assertEqual(a.next_action(obs,request())['reason'],'main_activity_unknown')
        obs=observation(thread());del obs['threads'][0]['scope']
        self.assertEqual(a.next_action(obs,request())['reason'],'peer_scope_unknown')
    def test_unscoped_unrelated_work_cannot_fan_out(self):
        r=request();r.pop('scope')
        self.assertEqual(a.next_action(observation(thread()),r)['reason'],'parallel_scopes_required')
    def test_same_file_or_parent_conflicts(self):
        for path in ('src/a','src','src/a/child'):
            with self.subTest(path=path):
                self.assertEqual(a.next_action(observation(thread()),request(scope=scope(path)))['reason'],'scope_or_resource_conflict')
    def test_read_dependency_conflicts_with_other_write(self):
        s=scope('src/b',reads=['src/a'])
        self.assertEqual(a.next_action(observation(thread()),request(scope=s))['reason'],'scope_or_resource_conflict')
    def test_shared_read_only_inputs_are_parallel(self):
        obs=observation(thread(scope=scope('src/a',reads=['shared/tokens'])))
        self.assertEqual(a.next_action(obs,request(scope=scope('src/b',reads=['shared/tokens'])))['action'],'spawn')
    def test_nested_workspace_alias_paths_overlap(self):
        s=scope('a',workspace='/repo/src')
        self.assertEqual(a.next_action(observation(thread()),request(scope=s))['reason'],'scope_or_resource_conflict')
    def test_root_reads_block_any_source_mutation(self):
        self.assertEqual(a.next_action(observation(thread()),request(scope=scope('src/b',reads=['.'])))['reason'],'scope_or_resource_conflict')
    def test_separate_workspaces_can_parallelize(self):
        self.assertEqual(a.next_action(observation(thread()),request(scope=scope('src/a',workspace='/other')))['action'],'spawn')
    def test_shared_browser_is_not_isolated_by_different_workspaces(self):
        obs=observation(thread(scope=scope(resource_writes=['browser/default'])))
        r=request(scope=scope('b',workspace='/other',resource_writes=['browser/default']))
        self.assertEqual(a.next_action(obs,r)['reason'],'scope_or_resource_conflict')
    def test_separate_browser_resources_allow_parallel(self):
        obs=observation(thread(scope=scope(resource_writes=['browser/a'])))
        self.assertEqual(a.next_action(obs,request(scope=scope('src/b',resource_writes=['browser/b'])))['action'],'spawn')
    def test_completed_dependency_not_accepted_yet_blocks(self):
        obs=observation(thread(state='completed'))
        self.assertEqual(a.next_action(obs,request(depends_on=['a']))['reason'],'dependencies_not_accepted')
    def test_accepted_dependency_unblocks_disjoint_unit(self):
        obs=observation(thread(state='closed',closure_evidence='native/close'),accepted_units={'a':'accepted/a'})
        self.assertEqual(a.next_action(obs,request(depends_on=['a']))['action'],'spawn')
    def test_two_writers_and_one_shared_review_slot_fit_cap_three(self):
        obs=observation(thread(review_reserved=True),cap=3)
        self.assertEqual(a.next_action(obs,request(reserve=1))['action'],'spawn')
    def test_shared_reservation_blocks_unrelated_slot_filling(self):
        obs=observation(thread('a',review_reserved=True),thread('b',review_reserved=True),cap=3)
        self.assertEqual(a.next_action(obs,request('c'))['reason'],'insufficient_open_thread_budget')
    def test_reviewer_consumes_shared_slot_not_an_extra_reservation(self):
        obs=observation(thread('a',state='waiting',review_reserved=True),thread('b',review_reserved=True),cap=3)
        req=request('a',role='reviewer',scope=scope('src/a',writes=[]),candidate_held=True)
        self.assertEqual(a.next_action(obs,req)['action'],'spawn')
    def test_review_needs_stopped_writer_and_real_hold(self):
        for state,held in (('running',True),('waiting',False)):
            obs=observation(thread(state=state))
            self.assertNotEqual(a.next_action(obs,request('a',role='reviewer',scope=scope(writes=[]),candidate_held=held))['action'],'spawn')
    def test_hold_never_authorizes_reviewer_to_edit_source(self):
        obs=observation(thread(state='waiting',released_resources=True))
        req=request('a',role='reviewer',scope=scope(),candidate_held=True)
        self.assertNotEqual(a.next_action(obs,req)['action'],'spawn')
    def test_review_does_not_take_unreleased_browser(self):
        obs=observation(thread(state='waiting',scope=scope(resource_writes=['browser/default'])))
        req=request('a',role='reviewer',scope=scope(writes=[],resource_writes=['browser/default']),candidate_held=True)
        self.assertNotEqual(a.next_action(obs,req)['action'],'spawn')
    def test_repair_can_reuse_stopped_reviewer_after_hold_release(self):
        obs=observation(thread('a',state='waiting'),thread('review',unit='a',role='reviewer',state='completed',scope=scope(writes=[])))
        req=request('a',reuse_id='a',candidate_held=False)
        self.assertEqual(a.next_action(obs,req)['action'],'reuse')
    def test_repair_cannot_race_active_reviewer(self):
        obs=observation(thread('a',state='waiting'),thread('review',unit='a',role='reviewer',scope=scope(writes=[])))
        self.assertNotEqual(a.next_action(obs,request('a',reuse_id='a',candidate_held=False))['action'],'reuse')
    def test_reuse_cannot_widen_scope(self):
        obs=observation(thread(state='waiting'))
        self.assertEqual(a.next_action(obs,request('a',reuse_id='a',scope=scope('src')))['reason'],'scope_change_requires_transfer')
    def test_current_unit_cannot_gain_second_writer(self):
        self.assertEqual(a.next_action(observation(thread()),request('a',role='routine_executor'))['reason'],'existing_writer_requires_explicit_transfer')
    def test_closed_agent_is_not_reused(self):
        with self.assertRaises(a.AllocationError):
            a.next_action(observation(thread(state='closed',closure_evidence='native')),request('a',reuse_id='a'))
    def test_completion_does_not_reclaim_slot(self):
        obs=observation(thread(state='completed'),cap=1)
        self.assertNotEqual(a.next_action(obs,request())['action'],'spawn')
    def test_release_requires_durable_resources_and_native_closure(self):
        obs=observation(thread(state='completed',retain=False,durable=True,released_resources=True))
        r=a.next_action(obs,request());self.assertEqual((r['action'],r['ids']),('close',['a']))
    def test_no_blind_retry(self):
        self.assertEqual(a.next_action(observation(),request(spawn_failed=True))['reason'],'no_blind_spawn_retry')
    def test_no_fake_primary(self):
        with self.assertRaises(a.AllocationError):a.next_action(observation(caller='imposter'),request())
    def test_readback_is_not_a_write(self):
        obs=observation(thread('a',state='waiting'),thread('other',unit='a'))
        r=request('a',intent='readback',reuse_id='a')
        self.assertEqual(a.next_action(obs,r)['reason'],'readback_only')
    def test_malformed_or_ambiguous_scope_rejected(self):
        for path in ('../a','src/../b','src//a','src/./a','src/.git','src/','C:\\a'):
            with self.subTest(path=path),self.assertRaises(a.AllocationError):
                a.next_action(observation(),request(scope=scope(path)))
    def test_resource_root_requires_explicit_identity(self):
        with self.assertRaises(a.AllocationError):
            a.next_action(observation(),request(scope=scope(resource_writes=['.'])))
    def test_parent_cycles_rejected(self):
        obs=observation(thread('a',parent='b'),thread('b',parent='a'))
        with self.assertRaises(a.AllocationError):a.next_action(obs,request())
    def test_incomplete_inventory_is_not_authorization(self):
        self.assertEqual(a.next_action(observation(complete=False),request())['action'],'inspect')
    def test_observations_not_modified(self):
        obs,req=observation(thread()),request();before=copy.deepcopy((obs,req))
        a.next_action(obs,req);self.assertEqual((obs,req),before)
    def test_native_closure_reference_required(self):
        with self.assertRaises(a.AllocationError):a.next_action(observation(thread(state='closed')),request())
    def test_real_cli_exit_codes_and_no_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input.json';p.write_text(json.dumps(dict(observation=observation(thread()),request=request())))
            before=p.read_bytes()
            r=subprocess.run([sys.executable,'-B',a.__file__,'--input',str(p)],capture_output=True,text=True,timeout=10)
            self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout)['action'],'spawn')
            self.assertEqual(p.read_bytes(),before)
            p.write_text('{"observation": NaN, "request": {}}')
            r=subprocess.run([sys.executable,'-B',a.__file__,'--input',str(p)],capture_output=True,text=True,timeout=10)
            self.assertEqual(r.returncode,2);self.assertIn('Non-finite',r.stderr)

if __name__=='__main__':unittest.main()
