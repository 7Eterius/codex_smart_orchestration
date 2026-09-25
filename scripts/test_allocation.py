"""Pure allocation/lifecycle regressions; native client behavior is not simulated proof."""
from __future__ import annotations
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'codex_workflow'))
from runtime import allocation as a


def task(**kw):
    value=dict(kind='implementation',risk='low',settled=True,tiny=False,deep=False,independent_required=False)
    value.update(kw)
    return value


def thread(ident='writer', **kw):
    value=dict(id=ident,parent='main',unit='U1',role='routine_executor',state='running',
               owned=True,retain=True,durable=False,released_resources=False,review_authorized=True)
    value.update(kw)
    return value


def obs(*threads, **kw):
    value=dict(caller='main',primary='main',cap=3,complete=True,close_supported=True,threads=list(threads))
    value.update(kw)
    return value


def request(**kw):
    value=dict(unit='U1',role='routine_executor',reserve=1,reuse_id=None,spawn_failed=False,state_changed=False)
    value.update(kw)
    return value


class ResponsibilityTests(unittest.TestCase):
    def test_routine_is_settled_implementation_default(self):
        self.assertEqual(a.classify(task())['owner'],'routine_executor')

    def test_mechanical_journey_goes_to_simple_without_lead(self):
        self.assertEqual(a.classify(task(kind='operation'))['owner'],'simple_executor')

    def test_no_file_or_click_count_threshold(self):
        for key in ('files','clicks','mode'):
            with self.assertRaises(a.AllocationError):
                a.classify(task(**{key:100}))

    def test_tiny_already_understood_action_is_delegated(self):
        self.assertEqual(a.classify(task(tiny=True))['owner'],'simple_executor')

    def test_unknown_design_or_contract_not_sent_to_simple(self):
        for kind in ('operation','implementation'):
            self.assertEqual(a.classify(task(kind=kind,settled=False))['owner'],'main')

    def test_design_judgment_stays_main(self):
        self.assertEqual(a.classify(task(kind='judgment'))['owner'],'main')

    def test_material_gui_action_is_not_low_risk(self):
        result=a.classify(task(kind='operation',risk='material'))
        self.assertEqual((result['owner'],result['reviewer']),('routine_executor','tester'))

    def test_critical_small_change_keeps_independent_gate(self):
        result=a.classify(task(tiny=True,risk='critical'))
        self.assertEqual(result['reviewer'],'tester')
        self.assertNotEqual(result['owner'],'simple_executor')

    def test_required_independence_never_removed(self):
        result=a.classify(task(tiny=True,independent_required=True))
        self.assertEqual(result['reviewer'],'tester')

    def test_deep_work_skips_ritual_failure(self):
        result=a.classify(task(deep=True))
        self.assertEqual((result['owner'],result['reviewer']),('default_executor','tester'))

    def test_validation_does_not_spawn_a_writer_or_recursive_reviewer(self):
        result=a.classify(task(kind='verification',risk='critical',independent_required=True))
        self.assertEqual(result['owner'],'tester')
        self.assertIsNone(result['reviewer'])

    def test_support_is_targeted_not_a_team(self):
        for kind,deep,role in [('discovery',False,'companion'),('discovery',True,'investigator'),('memory',False,'archivist')]:
            self.assertEqual(a.classify(task(kind=kind,deep=deep))['owner'],role)

    def test_bad_inputs_are_not_truthy_shortcuts(self):
        for payload in (task(risk='whatever'),task(deep='false'),task(tiny=True,deep=True),task(kind='normal')):
            with self.assertRaises(a.AllocationError):
                a.classify(payload)


class ResourceTests(unittest.TestCase):
    def test_two_slot_unit_fits_without_lead(self):
        result=a.next_action(obs(),request())
        self.assertEqual((result['action'],result['reserve']),('spawn',1))

    def test_completed_thread_still_counts(self):
        result=a.next_action(obs(thread(state='completed')),request(unit='U2'))
        self.assertEqual(result['open_count'],1)
        self.assertEqual(result['action'],'blocked')

    def test_close_is_not_release(self):
        result=a.next_action(obs(thread(state='closing')),request(unit='U2'))
        self.assertEqual(result['open_count'],1)
        self.assertEqual(result['action'],'blocked')

    def test_closed_requires_native_evidence_reference(self):
        with self.assertRaises(a.AllocationError):
            a.next_action(obs(thread(state='closed')),request(unit='U2'))

    def test_observed_closed_not_counted(self):
        result=a.next_action(obs(thread(state='closed',closure_evidence='native-close-event-17')),request(unit='U2'))
        self.assertEqual((result['action'],result['open_count']),('spawn',0))

    def test_only_durable_released_completed_owned_thread_is_closable(self):
        value=thread(state='completed',retain=False,durable=True,released_resources=True)
        result=a.next_action(obs(value),request(unit='U2'))
        self.assertEqual(result['action'],'close')
        self.assertEqual(result['ids'],['writer'])
        self.assertEqual(result['open_count'],1)
        for field in ('durable','released_resources'):
            changed={**value,field:False}
            self.assertNotEqual(a.next_action(obs(changed),request(unit='U2'))['action'],'close')

    def test_running_thread_cannot_be_closed(self):
        value=thread(retain=False,durable=True,released_resources=True)
        self.assertNotEqual(a.next_action(obs(value),request(unit='U2'))['action'],'close')

    def test_unrelated_threads_are_never_closed(self):
        value=thread(owned=False,state='completed',retain=False,durable=True,released_resources=True)
        self.assertNotEqual(a.next_action(obs(value),request())['action'],'close')

    def test_parent_cannot_close_before_child(self):
        parent=thread(state='completed',retain=False,durable=True,released_resources=True)
        child=thread('review',parent='writer',role='tester',state='completed',retain=False,durable=True,released_resources=True)
        self.assertNotEqual(a.next_action(obs(parent,child),request(unit='U2'))['action'],'close')
        nested=a.next_action(obs(parent,child,caller='writer'),request(role='tester',unit='U2',reserve=0))
        self.assertEqual(nested['ids'],['review'])

    def test_same_writer_repair_reuses_context_without_new_slot(self):
        result=a.next_action(obs(thread(state='waiting')),request(reuse_id='writer',reserve=0))
        self.assertEqual((result['action'],result['id']),('reuse','writer'))

    def test_no_reuse_of_active_wrong_unit_wrong_role_or_closed(self):
        for change in ({'state':'running'},{'unit':'U2'},{'role':'tester'},{'owned':False},
                       {'state':'closed','closure_evidence':'event'}):
            with self.subTest(change=change),self.assertRaises(a.AllocationError):
                a.next_action(obs(thread(state='waiting',**change) if 'state' not in change else thread(**change)),request(reuse_id='writer'))

    def test_no_duplicate_owner_while_current_is_open(self):
        self.assertEqual(a.next_action(obs(thread()),request())['action'],'wait')

    def test_no_second_writer_under_another_role(self):
        result=a.next_action(obs(thread()),request(role='default_executor'))
        self.assertEqual(result['reason'],'existing_writer_requires_explicit_transfer')

    def test_no_native_close_does_not_free_done_thread(self):
        value=thread(state='completed',retain=False,durable=True,released_resources=True)
        result=a.next_action(obs(value,close_supported=False),request(unit='U2'))
        self.assertEqual(result['action'],'blocked')

    def test_no_blind_retry_even_when_config_says_slot_free(self):
        result=a.next_action(obs(),request(spawn_failed=True,state_changed=False))
        self.assertEqual(result['reason'],'no_blind_spawn_retry')
        self.assertEqual(a.next_action(obs(),request(spawn_failed=True,state_changed=True))['action'],'spawn')

    def test_unknown_cap_or_partial_inventory_is_not_guessed(self):
        self.assertEqual(a.next_action(obs(cap=None),request())['reason'],'capacity_unknown')
        self.assertEqual(a.next_action(obs(complete=False),request())['action'],'inspect')

    def test_external_open_threads_reduce_available_capacity(self):
        others=[thread('other'+str(i),owned=False,unit='other'+str(i)) for i in range(2)]
        result=a.next_action(obs(*others),request())
        self.assertEqual(result['reason'],'insufficient_open_thread_budget')

    def test_higher_owner_cap_is_not_used_as_fanout_target(self):
        values=[thread('a',unit='U0'),thread('b',unit='U0',role='tester')]
        result=a.next_action(obs(*values,cap=20),request(unit='U2',reserve=0))
        self.assertEqual(result['reason'],'smart_open_thread_budget')

    def test_single_slot_forces_explicit_serial_review_plan(self):
        self.assertEqual(a.next_action(obs(cap=1),request())['action'],'blocked')
        self.assertEqual(a.next_action(obs(cap=1),request(reserve=0))['action'],'spawn')

    def test_old_second_group_failure_is_not_paper_reclaimed(self):
        # Hypothetical occupancy matching the report's failure, not a claimed cause.
        old_writer=thread('oldwriter',parent='oldlead',unit='U0',state='completed')
        old_tester=thread('oldtester',parent='oldlead',role='tester',unit='U0',state='completed')
        new_lead=thread('newlead',role='chunk_lead',unit='U2')
        result=a.next_action(obs(old_writer,old_tester,new_lead),request(unit='U2'))
        self.assertEqual(result['action'],'blocked')
        self.assertEqual(result['open_count'],3)

    def test_two_complete_pairs_reuse_only_observed_closed_slots(self):
        inventory=obs()
        for index in range(2):
            unit='U'+str(index)
            self.assertEqual(a.next_action(inventory,request(unit=unit))['action'],'spawn')
            owner=thread('writer'+str(index),unit=unit)
            inventory['threads'].append(owner)
            review_request=request(unit=unit,role='tester',reserve=0)
            owner_obs={**inventory,'caller':owner['id']}
            self.assertEqual(a.next_action(owner_obs,review_request)['action'],'spawn')
            reviewer=thread('review'+str(index),unit=unit,parent=owner['id'],role='tester',state='completed',retain=False,durable=True,released_resources=True)
            inventory['threads'].append(reviewer)
            # Closing is a separate native observation, not a planner side effect.
            owner_obs={**inventory,'caller':owner['id']}
            result=a.next_action(owner_obs,request(unit='finished',role='tester',reserve=0))
            self.assertEqual(result['ids'],[reviewer['id']])
            self.assertEqual(reviewer['state'],'completed')
            reviewer.update(state='closed',closure_evidence='native-review-close-'+str(index))
            owner.update(state='completed',retain=False,durable=True,released_resources=True)
            result=a.next_action(inventory,request(unit='next'))
            self.assertEqual(result['ids'],[owner['id']])
            owner.update(state='closed',closure_evidence='native-owner-close-'+str(index))
        self.assertEqual(a.next_action(inventory,request(unit='next'))['open_count'],0)

    def test_role_delegation_is_reviewer_only(self):
        with self.assertRaises(a.AllocationError):
            a.next_action(obs(thread(),caller='writer'),request(role='routine_executor',unit='U2'))
        with self.assertRaises(a.AllocationError):
            a.next_action(obs(thread(role='tester'),caller='writer'),request(role='tester',unit='U2'))

    def test_invalid_observation_rejected(self):
        values=[obs(cap=True),obs(cap=0),obs(complete='true'),obs(thread(),thread()),
                obs(thread('a',parent='b'),thread('b',parent='a'))]
        for value in values:
            with self.subTest(value=value),self.assertRaises(a.AllocationError):
                a.next_action(value,request())

    def test_planner_does_not_modify_input(self):
        value=obs(thread(state='completed',retain=False,durable=True,released_resources=True))
        before=copy.deepcopy(value)
        a.next_action(value,request(unit='U2'))
        self.assertEqual(value,before)

    def test_review_dispatch_fallback_preserves_named_reviewer(self):
        base=dict(owner_role='routine_executor',free_slots=1,close_supported=True)
        self.assertEqual(a.review_host(nested_observed=True,**base),'owner')
        self.assertEqual(a.review_host(nested_observed=False,**base),'main')
        self.assertEqual(a.review_host(nested_observed=True,**{**base,'owner_role':'simple_executor'}),'main')
        self.assertEqual(a.review_host(nested_observed=False,**{**base,'free_slots':0}),'release_completed_owner_then_main')
        self.assertEqual(a.review_host(nested_observed=False,**{**base,'free_slots':0,'close_supported':False}),'blocked')

    def test_cli_reports_blocked_not_success_and_rejects_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'input.json'
            path.write_text(json.dumps(dict(observation=obs(cap=1),request=request())))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(a.main(['--input',str(path)]),1)
            path.write_text('{"observation":{},"observation":{}}')
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(a.main(['--input',str(path)]),2)


if __name__=='__main__':
    unittest.main()
