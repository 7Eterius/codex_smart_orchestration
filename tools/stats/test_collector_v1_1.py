"""Regression fixtures for typed items and interval grain. No real user logs."""
import importlib.util
import json
from datetime import timedelta
from pathlib import Path
import unittest
from test_smart_weekly_stats import Fixture, START, END, meta, event, context, call, output, record, vec
import smart_weekly_stats as a

def command_item(cid='cmd-1',seconds=8,kind='item_completed',**kw):
    item=dict(type='CommandExecution',id=cid,command=['/bin/zsh','-lc','npm test'],
              cwd='/PRIVATE-OWNER/SECRET-PROJECT',source='agent',status='completed',
              aggregated_output='PRIVATE_TEST_OUTPUT',exit_code=0,duration={'secs':5,'nanos':0})
    item.update(kw)
    return event(kind,seconds,thread_id='main',turn_id='t1',item=item)

class TypedItemTests(Fixture):
    def test_completed_command_is_recognized_from_real_protocol_shape(self):
        self.write([meta(),context(),command_item()]);c,r=self.collect()
        self.assertEqual(r['tests']['recognized_test_command_runs'],1)
        self.assertEqual(r['tests']['exits'],{'exit_zero':1})
        self.assertEqual(r['tests']['recorded_tool_wall_seconds'],5)
        self.assertEqual(r['tests']['start_evidence'],{'duration_inferred':1})
        self.assertEqual(c.calls[('main','cmd-1')]['started'],START+timedelta(seconds=3))

    def test_start_and_completion_are_one_run(self):
        self.write([meta(),context(),command_item(seconds=2,kind='item_started',status='in_progress',duration=None,exit_code=None),command_item()])
        _,r=self.collect();self.assertEqual(r['tests']['recognized_test_command_runs'],1)
        self.assertEqual(r['tests']['start_evidence'],{'start_event':1})

    def test_function_call_plus_typed_completion_deduplicates_by_call_id(self):
        self.write([meta(),context(),call('cmd-1',seconds=2),command_item()]);_,r=self.collect()
        self.assertEqual(r['tests']['recognized_test_command_runs'],1)
        self.assertEqual(r['tools'],{'exec_command':1})

    def test_distinct_items_at_same_timestamp_not_suppressed(self):
        self.write([meta(),context(),command_item('a'),command_item('b')]);_,r=self.collect()
        self.assertEqual(r['tests']['recognized_test_command_runs'],2)

    def test_repeated_typed_item_keeps_one_command(self):
        self.write([meta(),context(),command_item(),command_item()]);_,r=self.collect()
        self.assertEqual(r['tests']['recognized_test_command_runs'],1)

    def test_unsupported_item_not_fake_test(self):
        self.write([meta(),context(),command_item(type='Unsupported',command=['npm','test'])]);_,r=self.collect()
        self.assertEqual(r['tests']['recognized_test_command_runs'],0)
        self.assertEqual(r['recorded_item_types'],{'unknown':1})

    def test_code_mode_text_is_wrapper_not_proof_of_nested_execution(self):
        self.write([meta(),context(),record('response_item',dict(type='custom_tool_call',id='c',call_id='c',name='exec',input='await tools.exec_command({cmd:"npm test"})'),3)])
        _,r=self.collect();self.assertEqual(r['tools'],{'exec':1})
        self.assertEqual(r['tests']['recognized_test_command_runs'],0)

    def test_command_interaction_not_new_test(self):
        self.write([meta(),context(),command_item(source='unified_exec_interaction')]);c,r=self.collect()
        self.assertEqual(r['tests']['recognized_test_command_runs'],0)
        self.assertEqual(c.diag['command_interaction_items_observed'],1)

    def test_snake_case_command_variant(self):
        self.write([meta(),context(),command_item(type='command_execution')]);_,r=self.collect()
        self.assertEqual(r['tests']['recognized_test_command_runs'],1)

    def test_missing_duration_does_not_claim_known_start(self):
        self.write([meta(),context(),command_item(duration=None)]);_,r=self.collect()
        self.assertEqual(r['tests']['recognized_test_command_runs'],1)
        self.assertEqual(r['tests']['recognized_test_command_starts'],0)
        self.assertEqual(r['tests']['start_evidence'],{'completion_only':1})

    def test_exit_nonzero_kept(self):
        self.write([meta(),context(),command_item(status='failed',exit_code=1)]);_,r=self.collect()
        self.assertEqual(r['tests']['exits'],{'nonzero':1})

    def test_dynamic_tool_item_matches_existing_call(self):
        self.write([meta(),context(),call('z',tool='list_agents',cmd=''),event('item_completed',3,
           thread_id='main',turn_id='t1',item=dict(type='DynamicToolCall',id='z',tool='list_agents',arguments={},status='completed',success=True,duration={'secs':1,'nanos':0}))]);_,r=self.collect()
        self.assertEqual(r['tools'],{'list_agents':1})

    def test_unknown_tool_name_and_output_are_not_exported(self):
        self.write([meta(),context(),call('z',tool='PRIVATE_TOOL',cmd=''),command_item()]);_,r=self.collect()
        text=json.dumps(r)
        for secret in ('PRIVATE_TOOL','PRIVATE_TEST_OUTPUT','PRIVATE-OWNER','SECRET-PROJECT','npm test'):
            self.assertNotIn(secret,text)
        self.assertEqual(sum(r['unknown_tool_ids'].values()),1)

    def test_item_types_filtered_to_requested_period(self):
        self.write([meta(),context(),command_item(seconds=2),command_item('c2',seconds=200)])
        c,_=self.collect();r=c.report(START+timedelta(seconds=100),END)
        self.assertEqual(r['recorded_item_types'],{'commandexecution':1})

    def test_no_command_in_item_does_not_invent_test(self):
        self.write([meta(),context(),command_item(command=None)]);_,r=self.collect()
        self.assertEqual(r['tests']['recognized_test_command_runs'],0)

class IntervalTests(Fixture):
    def test_two_overlapping_turns_on_one_worker_are_one_worker(self):
        self.write([meta('worker','main'),event('task_started',2,turn_id='a'),event('task_started',3,turn_id='b'),event('task_complete',10,turn_id='a'),event('task_complete',12,turn_id='b')]);_,r=self.collect()
        self.assertEqual(r['turns']['peak_closed_worker_turn_overlap_per_root'],2)
        self.assertEqual(r['turns']['peak_distinct_workers_with_closed_turn_overlap_per_root'],1)
        self.assertEqual(r['turns']['workers_with_overlapping_own_turn_records'],1)

    def test_two_distinct_workers_are_two(self):
        for sid in ['a','b']:
            self.write([meta(sid,'main'),event('task_started',2,turn_id='t'),event('task_complete',12,turn_id='t')],sid+'.jsonl')
        _,r=self.collect();self.assertEqual(r['turns']['peak_distinct_workers_with_closed_turn_overlap_per_root'],2)

    def test_missing_end_does_not_invent_interval(self):
        self.write([meta('worker','main'),event('task_started',2,turn_id='a')]);_,r=self.collect()
        self.assertEqual(r['turns']['peak_distinct_workers_with_closed_turn_overlap_per_root'],0)

    def test_completed_interval_spanning_subwindow_is_included(self):
        self.write([meta('worker','main'),event('task_started',2,turn_id='a'),event('task_complete',300,turn_id='a')]);c,_=self.collect()
        r=c.report(START+timedelta(seconds=100),START+timedelta(seconds=200))
        self.assertEqual(r['turns']['observed_closed_turn_union_seconds'],100)

    def test_distinct_root_output_keeps_both_metrics(self):
        self.write([meta('worker','main'),event('task_started',2,turn_id='a'),event('task_started',3,turn_id='b'),event('task_complete',10,turn_id='a'),event('task_complete',12,turn_id='b')]);_,r=self.collect()
        row=r['root_groups'][0];self.assertEqual(row['peak_closed_worker_turn_overlap'],2)
        self.assertEqual(row['peak_distinct_workers_with_closed_turn_overlap'],1)

class LedgerPreservationTests(Fixture):
    def test_response_usage_unchanged_by_typed_commands(self):
        self.write([meta(),context(),record('token_usage_record',dict(thread_id='main',turn_id='t1',response_id='resp',usage=vec()),2),command_item()]);_,r=self.collect()
        self.assertEqual(r['observed_token_usage']['total_tokens'],130)
        self.assertEqual(r['sessions'][0]['usage_updates'],1)

    def test_named_model_presets_unmodified(self):
        self.assertEqual(a.EXPECTED['tester'],('gpt-6-luna','medium'))
        self.assertEqual(a.EXPECTED['routine_executor'],('gpt-6-luna','max'))

if __name__=='__main__':unittest.main()
