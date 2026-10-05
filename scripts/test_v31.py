"""3.1 routing, test/review separation and five-thread capacity. No model calls."""
from __future__ import annotations
import copy
from pathlib import Path
import sys
import tomllib
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'codex_workflow'))
from runtime import allocation as a
from runtime.agent_defaults import configure, DEFAULTS
from runtime.config_assessment import assess_configuration
from runtime.layout import BUILTIN_WORKERS, PackageLayout, INSTALLED_RUNTIME_FILES
from test_allocation import task, scope, thread, observation, request

class ModelRoutingTests(unittest.TestCase):
    def test_all_sol_levels_are_concrete_presets(self):
        for difficulty,role,effort in (('moderate','default_executor','low'),('deep','deep_executor','medium'),('serious','senior_executor','high')):
            with self.subTest(difficulty=difficulty):
                self.assertEqual(a.classify(task(difficulty=difficulty))['owner'],role)
                cfg=tomllib.loads((ROOT/'codex_workflow/agents'/f'{role}.toml').read_text())
                self.assertEqual((cfg['model'],cfg['model_reasoning_effort']),('gpt-6.1-sol',effort))
    def test_ordinary_unknown_bug_starts_luna_max(self):
        r=a.classify(task())
        self.assertEqual(r['owner'],'routine_executor')
        cfg=tomllib.loads((ROOT/'codex_workflow/agents/routine_executor.toml').read_text())
        self.assertEqual((cfg['model'],cfg['model_reasoning_effort']),('gpt-6-luna','max'))
    def test_critical_risk_overrides_ordinary_difficulty(self):
        r=a.classify(task(risk='critical',difficulty='ordinary'))
        self.assertEqual((r['owner'],r['reviewer']),('senior_executor','senior_reviewer'))
    def test_deep_flag_cannot_be_weakened(self):
        for level in ('ordinary','moderate'):
            self.assertEqual(a.classify(task(deep=True,difficulty=level))['owner'],'deep_executor')
    def test_bounded_and_deep_causal_routes(self):
        self.assertEqual(a.classify(task(kind='discovery'))['owner'],'investigator')
        self.assertEqual(a.classify(task(kind='discovery',difficulty='moderate'))['owner'],'default_executor')
        self.assertEqual(a.classify(task(kind='discovery',deep=True))['owner'],'deep_executor')
    def test_one_stalled_correction_skips_another_luna_attempt(self):
        self.assertEqual(a.classify(task(stalled=True))['owner'],'default_executor')
        self.assertEqual(a.classify(task(stalled=True,deep=True))['owner'],'deep_executor')
    def test_testing_is_not_legacy_semantic_verification(self):
        self.assertEqual(a.classify(task(kind='testing'))['owner'],'tester')
        self.assertEqual(a.classify(task(kind='verification'))['owner'],'reviewer')
        self.assertIsNone(a.classify(task(kind='testing',risk='critical'))['reviewer'])
    def test_procedural_testing_cannot_smuggle_in_deep_strategy(self):
        for extra in ({'deep':True},{'difficulty':'moderate'}):
            with self.assertRaises(a.AllocationError):a.classify(task(kind='testing',**extra))
    def test_semantic_escalation_uses_senior_not_tester(self):
        for extra in ({'deep':True},{'risk':'critical'},{'stalled':True}):
            self.assertEqual(a.classify(task(kind='verification',**extra))['owner'],'senior_reviewer')
    def test_bad_difficulty_fails_closed(self):
        for value in ('cheap',True,None,{},''):
            with self.subTest(value=value),self.assertRaises(a.AllocationError):a.classify(task(difficulty=value))
    def test_main_direct_path_and_required_review_survive(self):
        r=a.classify(task(tiny=True,independent_required=True))
        self.assertEqual((r['owner'],r['reviewer']),('main','reviewer'))
    def test_owner_model_and_four_thread_limit_are_preserved(self):
        text='model="owner"\n[agents]\nmax_threads=4\ndefault_subagent_model="owner-child"\ndefault_subagent_reasoning_effort="low"\n'
        result,warnings,added=configure(text)
        self.assertEqual(result,text);self.assertFalse(added);self.assertTrue(warnings)
        report=assess_configuration(tomllib.loads(result))
        self.assertEqual(report['effective_configured_cap'],4)
        self.assertEqual(report['recommended_parallel_cap'],5)
    def test_fresh_defaults_and_package_inventory_agree(self):
        self.assertEqual(DEFAULTS,{'max_concurrent_threads_per_session':5,'default_subagent_model':'gpt-6-luna','default_subagent_reasoning_effort':'max'})
        self.assertEqual(a.ROLES,BUILTIN_WORKERS)
        package=PackageLayout.resolve(ROOT/'codex_workflow')
        self.assertIn('testing.md',INSTALLED_RUNTIME_FILES)
        self.assertEqual(package.version,'3.1.0')

class TestAndReviewCapacityTests(unittest.TestCase):
    def test_fifth_independent_thread_fits_observed_capacity(self):
        obs=observation(*(thread(x) for x in ('a','b','c','d')),cap=5)
        self.assertEqual(a.next_action(obs,request('e'))['action'],'spawn')
        obs['threads'].append(thread('e'))
        self.assertEqual(a.next_action(obs,request('f'))['reason'],'smart_open_thread_budget')
    def test_higher_owner_cap_does_not_raise_smart_ceiling(self):
        obs=observation(*(thread(x) for x in ('a','b','c','d','e')),cap=9)
        self.assertEqual(a.next_action(obs,request('f'))['reason'],'smart_open_thread_budget')
    def test_unrelated_threads_use_actual_native_capacity(self):
        obs=observation(*(thread(x) for x in ('a','b','c','d')),thread('other',owned=False),cap=5)
        self.assertEqual(a.next_action(obs,request('e'))['reason'],'insufficient_open_thread_budget')
    def test_tester_cannot_consume_semantic_review_reservation(self):
        obs=observation(thread('a',state='waiting',review_reserved=True),cap=2)
        req=request('a',role='tester',candidate_held=True,scope=scope(writes=[]))
        self.assertEqual(a.next_action(obs,req)['reason'],'insufficient_open_thread_budget')
        req['role']='reviewer'
        self.assertEqual(a.next_action(obs,req)['action'],'spawn')
    def test_existing_tester_does_not_satisfy_semantic_capacity(self):
        obs=observation(thread('a',state='waiting'),thread('tests',unit='a',role='tester',state='completed',scope=scope(writes=[])),cap=2)
        req=request('a',reuse_id='a',reserve=1,candidate_held=False)
        self.assertEqual(a.next_action(obs,req)['reason'],'insufficient_open_thread_budget')
    def test_senior_reviewer_can_serve_shared_queue(self):
        obs=observation(thread('a',state='waiting',review_reserved=True),cap=2)
        req=request('a',role='senior_reviewer',candidate_held=True,scope=scope(writes=[]))
        self.assertEqual(a.next_action(obs,req)['action'],'spawn')
    def test_tester_and_reviewer_can_overlap_only_with_resources(self):
        obs=observation(thread('review',unit='a',role='reviewer',scope=scope(writes=[])),cap=2)
        req=request('a',role='tester',candidate_held=True,scope=scope(writes=[],resource_writes=['tests/a']))
        self.assertEqual(a.next_action(obs,req)['action'],'spawn')
        obs['threads'][0]['scope']['resource_writes']=['tests/a']
        self.assertEqual(a.next_action(obs,req)['reason'],'scope_or_resource_conflict')
    def test_testing_requires_hold_and_stopped_writer(self):
        req=request('a',role='tester',scope=scope(writes=[]))
        self.assertEqual(a.next_action(observation(),req)['reason'],'review_requires_candidate_hold')
        req['candidate_held']=True
        self.assertNotEqual(a.next_action(observation(thread('a')),req)['action'],'spawn')
        self.assertEqual(a.next_action(observation(thread('a',state='waiting')),req)['action'],'spawn')
    def test_all_verifiers_cannot_write_their_input_scope(self):
        for role in a.VERIFIERS:
            req=request(role=role,candidate_held=True,scope=scope())
            self.assertEqual(a.next_action(observation(),req)['reason'],'verifier_writes_input_scope')
    def test_verifier_can_write_isolated_artifacts(self):
        req=request(role='tester',candidate_held=True,scope=scope(reads=['src','tests'],writes=['artifacts/run1']))
        self.assertEqual(a.next_action(observation(),req)['action'],'spawn')
    def test_root_read_protects_nested_output(self):
        req=request(role='tester',candidate_held=True,scope=scope(reads=['.'],writes=['src/result']))
        self.assertEqual(a.next_action(obs=observation(),request=req)['reason'],'verifier_writes_input_scope')
    def test_no_second_nested_verifier_without_release(self):
        parent=thread('a',state='waiting',review_authorized=True)
        child=thread('test-a',parent='a',unit='a',role='tester',scope=scope(writes=[]))
        obs=observation(parent,child,caller='a')
        req=request('a',role='reviewer',candidate_held=True,scope=scope(writes=[]))
        self.assertEqual(a.next_action(obs,req)['reason'],'nested_verifier_already_open')
    def test_returned_records_do_not_mutate_input(self):
        obs=observation(thread('a',state='waiting',review_reserved=True),cap=2)
        req=request('a',role='tester',candidate_held=True,scope=scope(writes=[]))
        before=copy.deepcopy((obs,req));a.next_action(obs,req)
        self.assertEqual((obs,req),before)

if __name__=='__main__':unittest.main()
