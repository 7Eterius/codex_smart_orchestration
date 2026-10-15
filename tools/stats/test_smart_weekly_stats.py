"""Synthetic tests. No user logs, model calls, network or installed Codex needed."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import smart_weekly_stats as a

START=datetime(2026,10,8,tzinfo=timezone.utc)
END=START+timedelta(days=7)


def vec(inp=100,cache=20,out=30,reason=5):
    return dict(input_tokens=inp,cached_input_tokens=cache,output_tokens=out,
                reasoning_output_tokens=reason,total_tokens=inp+out)


def record(typ,payload,seconds=0):
    return dict(timestamp=a.iso(START+timedelta(seconds=seconds)),type=typ,payload=payload)


def meta(sid='main',parent=None,created=-100,role=None):
    p=dict(id=sid,timestamp=a.iso(START+timedelta(seconds=created)),cwd='/PRIVATE-OWNER/SECRET-PROJECT',
           source='cli',cli_version='0.190.0',base_instructions={'text':'Smart Orchestration 4.0: test'})
    if parent:
        p['source']={'subagent':{'thread_spawn':{'parent_thread_id':parent,'agent_role':role or 'routine_executor'}}}
    return record('session_meta',p,created)


def context(sid='t1',seconds=0,model='gpt-6-luna',effort='max'):
    return record('turn_context',dict(turn_id=sid,model=model,effort=effort,cwd='/PRIVATE-OWNER/SECRET-PROJECT'),seconds)


def token(cur,last=None,seconds=1):
    return record('event_msg',dict(type='token_count',info=dict(total_token_usage=cur,last_token_usage=last if last is not None else cur)),seconds)


def event(name,seconds=1,**fields):
    return record('event_msg',dict(type=name,**fields),seconds)


def call(cid='c1',cmd='npm test',seconds=1,tool='exec_command',**args):
    return record('response_item',dict(type='function_call',call_id=cid,name='functions.'+tool,
                  arguments=json.dumps(dict(cmd=cmd,**args))),seconds)


def output(cid='c1',text='Wall time: 1.2 seconds\nProcess exited with code 0\nFinal output:\n10 passed',seconds=3):
    return record('response_item',dict(type='function_call_output',call_id=cid,output=text),seconds)


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.home=self.root/'home';(self.home/'sessions').mkdir(parents=True)

    def write(self,rows,name='rollout.jsonl',folder='sessions'):
        directory=self.home/folder;directory.mkdir(exist_ok=True)
        p=directory/name;p.write_text(''.join(json.dumps(x)+'\n' for x in rows))
        os.utime(p,(END.timestamp(),END.timestamp()))
        return p

    def collect(self,**kw):
        c=a.Collector(self.home,START,END,ZoneInfo('Asia/Tbilisi'),progress=False,**kw)
        c.collect([self.home/'sessions',self.home/'archived_sessions'])
        return c,c.report(START,END)


class TokenTests(Fixture):
    def test_repeated_cumulative_snapshot_not_counted_twice(self):
        self.write([meta(),context(),token(vec()),token(vec(),seconds=2)])
        c,r=self.collect();self.assertEqual(r['observed_token_usage']['total_tokens'],130)
        self.assertEqual(c.diag['legacy_repeated_snapshot_ignored'],1)

    def test_cache_and_reasoning_are_subsets(self):
        self.write([meta(),context(),token(vec())]);_,r=self.collect()
        self.assertEqual(r['observed_token_usage']['total_tokens'],130)
        self.assertEqual(r['observed_token_usage']['reasoning_output_tokens'],5)

    def test_pre_window_baseline_prevents_lifetime_overcount(self):
        self.write([meta(created=-500),context(seconds=-400),token(vec(1000,200,300,50),seconds=-200),
                    token(vec(1100,220,330,55),vec(),seconds=2)])
        _,r=self.collect();self.assertEqual(r['observed_token_usage']['total_tokens'],130)

    def test_first_huge_total_only_counts_last_and_reports_gap(self):
        self.write([meta(),context(),token(vec(10000,2000,3000,500),vec())])
        c,r=self.collect();self.assertEqual(r['observed_token_usage']['total_tokens'],130)
        self.assertGreater(c.diag['legacy_opening_unattributed_history_tokens'],0)

    def test_zero_last_checkpoint_does_not_switch_counter_stream(self):
        self.write([meta(),context(),token(vec()),token(vec(900000,0,0,0),vec(0,0,0,0),seconds=2),
                    token(vec(200,40,60,10),vec(),seconds=3)])
        _,r=self.collect();self.assertEqual(r['observed_token_usage']['total_tokens'],260)

    def test_reset_uses_last_not_lifetime(self):
        self.write([meta(),context(),token(vec(1000,200,300,50),vec()),
                    token(vec(20,0,4,0),vec(20,0,4,0),seconds=2)])
        c,r=self.collect();self.assertEqual(r['observed_token_usage']['total_tokens'],154)
        self.assertEqual(c.diag['legacy_counter_resets_or_inconsistent_deltas'],1)

    def test_missing_total_is_excluded_not_blindly_added(self):
        x=token(vec());x['payload']['info'].pop('total_token_usage')
        self.write([meta(),context(),x]);c,r=self.collect()
        self.assertEqual(r['observed_token_usage']['total_tokens'],0)
        self.assertEqual(r['sessions_without_usage'],1)

    def test_date_end_is_exclusive(self):
        self.write([meta(),context(),token(vec()),token(vec(200,40,60,10),vec(),seconds=7*86400)])
        _,r=self.collect();self.assertEqual(r['observed_token_usage']['total_tokens'],130)

    def test_response_records_supersede_legacy_for_same_turn(self):
        direct=record('token_usage_record',dict(thread_id='main',turn_id='t1',response_id='r1',usage=vec()),seconds=2)
        self.write([meta(),context(),token(vec()),direct,direct])
        c,r=self.collect();self.assertEqual(r['observed_token_usage']['total_tokens'],130)
        self.assertEqual(r['usage_method_updates'],{'response_id':1})

    def test_separate_turns_can_use_different_usage_sources(self):
        direct=record('token_usage_record',dict(thread_id='main',turn_id='t2',response_id='r1',usage=vec()),seconds=5)
        self.write([meta(),context(),token(vec()),context('t2',seconds=3),direct])
        _,r=self.collect();self.assertEqual(r['observed_token_usage']['total_tokens'],260)

    def test_response_id_deduplicates_copies(self):
        rows=[meta(),context(),record('token_usage_record',dict(thread_id='main',turn_id='t1',response_id='r1',usage=vec()),seconds=3)]
        self.write(rows);self.write(rows,name='copy.jsonl',folder='archived_sessions')
        _,r=self.collect();self.assertEqual(r['observed_token_usage']['total_tokens'],130)

    def test_legacy_replicas_do_not_double_count(self):
        rows=[meta(),context(),token(vec()),token(vec(200,40,60,10),vec(),seconds=2)]
        self.write(rows);self.write(rows,name='copy.jsonl',folder='archived_sessions')
        _,r=self.collect();self.assertEqual(r['observed_token_usage']['total_tokens'],260)

    def test_invalid_negative_or_boolean_usage_excluded(self):
        for bad in (-1,True):
            v=vec();v['input_tokens']=bad
            self.assertIsNone(a.vector(v))
        self.assertIsNone(a.vector(vec(10,20)))
        self.assertIsNone(a.vector(vec(100,20,10,30)))


class LineageTests(Fixture):
    def test_inherited_parent_history_before_child_creation_excluded(self):
        self.write([meta(),context(),token(vec())])
        self.write([meta('child','main',created=5),context(seconds=0),token(vec(),seconds=1),
                    context('ct1',seconds=6),token(vec(200,40,60,10),vec(),seconds=7)],'child.jsonl')
        c,r=self.collect();self.assertEqual(r['observed_token_usage']['total_tokens'],260)
        self.assertEqual(r['worker_sessions'],1)
        self.assertEqual(r['routing']['matching_usage_updates'],1)
        self.assertGreater(c.diag['precreation_inherited_records_excluded'],0)

    def test_explicit_foreign_token_owner_not_rebooked(self):
        parent=record('token_usage_record',dict(thread_id='main',turn_id='t1',response_id='r1',usage=vec()),seconds=7)
        self.write([meta(),context(),parent])
        self.write([meta('child','main',created=5),parent],'child.jsonl')
        c,r=self.collect();self.assertEqual(r['observed_token_usage']['total_tokens'],130)
        self.assertEqual(c.diag['foreign_owner_records_excluded'],1)

    def test_plain_user_text_does_not_prove_workflow_version(self):
        m=meta();m['payload']['base_instructions']=None
        self.write([m,context(),event('user_message',message='Smart Orchestration 4.0.1'),token(vec(),seconds=2)])
        _,r=self.collect();self.assertEqual(r['workflow_cohorts'][0]['association'],'not_identified')

    def test_series_marker_does_not_prove_patch(self):
        self.write([meta(),context(),token(vec())]);_,r=self.collect()
        self.assertEqual(r['workflow_cohorts'][0]['association'],'instruction_marker_4.0_series_patch_unproven')

    def test_unknown_effort_not_marked_mismatch(self):
        self.write([meta('child','main',created=-10),context(effort=None),token(vec())])
        _,r=self.collect();self.assertEqual(r['routing']['unknown_model_or_effort_updates'],1)
        self.assertIsNone(r['routing']['match_rate_known_updates'])

    def test_wrong_recorded_tester_model_detected(self):
        self.write([meta('child','main',role='tester'),context(effort='max'),token(vec())])
        _,r=self.collect();self.assertEqual(r['routing']['mismatching_usage_updates'],1)

    def test_spawn_tool_result_links_worker_role(self):
        rows=[meta(),context(),call('s',tool='spawn_agent',agent_type='tester'),
              output('s',json.dumps({'agent_id':'child'}))]
        self.write(rows)
        self.write([meta('child',created=4),context('c',seconds=5,effort='medium'),token(vec(),seconds=6)],'child.jsonl')
        _,r=self.collect();child=next(x for x in r['sessions'] if x['role']=='tester')
        self.assertIsNotNone(child['parent_id'])


class ToolTests(Fixture):
    def test_shell_call_is_recognized_and_zero_exit_recorded(self):
        self.write([meta(),context(),call(),output()]);_,r=self.collect()
        self.assertEqual(r['tests']['recognized_test_command_starts'],1)
        self.assertEqual(r['tests']['exits'],{'exit_zero':1})

    def test_echo_test_is_not_a_test_run(self):
        self.write([meta(),context(),call(cmd='echo "npm test"'),output()]);_,r=self.collect()
        self.assertEqual(r['tests']['recognized_test_command_starts'],0)

    def test_recognizes_representative_real_commands(self):
        for cmd in ('npm run test:unit','pnpm exec vitest run','npx playwright test','python3 -B -m unittest discover',
                    'cd app && npm test','uv run pytest','cargo test','go test ./...','swift test'):
            with self.subTest(cmd=cmd):self.assertTrue(a.is_test_command(cmd))

    def test_command_end_and_function_output_are_not_duplicate_runs(self):
        self.write([meta(),context(),call(),event('exec_command_begin',call_id='c1',command=['npm','test']),
                    event('exec_command_end',seconds=3,call_id='c1',command=['npm','test'],exit_code=0,duration={'secs':2,'nanos':0}),output()])
        _,r=self.collect();self.assertEqual(r['tests']['recognized_test_command_starts'],1)
        self.assertEqual(r['tests']['recorded_tool_wall_seconds'],2)

    def test_async_test_wait_completion_linked(self):
        self.write([meta(),context(),call(),output(text='Wall time: 1.0 seconds\nProcess running with session ID 123'),
                    call('w',cmd='',seconds=4,tool='write_stdin',session_id=123),
                    output('w','Process exited with code 1\nFinal output:\nFAILED',seconds=8)])
        _,r=self.collect();self.assertEqual(r['tests']['recognized_test_command_starts'],1)
        self.assertEqual(r['tests']['exits'],{'nonzero':1})

    def test_repeats_are_only_candidates(self):
        self.write([meta(),context(),call(),output(),call('c2',seconds=5),output('c2',seconds=7)])
        _,r=self.collect();self.assertEqual(r['tests']['repeated_command_candidates'],1)
        self.assertIn('NOT established',r['tests']['examples'][0]['label'])

    def test_completed_turn_is_not_quality_acceptance(self):
        self.write([meta(),event('task_started',turn_id='t1'),event('task_complete',seconds=10,turn_id='t1')])
        _,r=self.collect();self.assertEqual(r['turns']['statuses'],{'completed':1})
        self.assertIsNone(r['quality']['accepted_tasks'])

    def test_overlap_not_sum_of_worker_time(self):
        for sid,offset in [('a',0),('b',3)]:
            self.write([meta(sid,'main',created=-5),event('task_started',seconds=offset,turn_id='x'),
                        event('task_complete',seconds=offset+10,turn_id='x')],sid+'.jsonl')
        _,r=self.collect();self.assertEqual(r['turns']['peak_closed_worker_turn_overlap_per_root'],2)
        self.assertEqual(r['turns']['observed_closed_turn_union_seconds'],13)

    def test_rate_limit_reset_windows_not_summed(self):
        x=token(vec());x['payload']['rate_limits']={'primary':{'used_percent':90,'window_minutes':300,'resets_at':START.timestamp()+100}}
        y=token(vec(),seconds=2);y['payload']['rate_limits']={'primary':{'used_percent':5,'window_minutes':300,'resets_at':START.timestamp()+400}}
        self.write([meta(),context(),x,y]);_,r=self.collect()
        self.assertEqual(len(r['rate_limit_observations']),2)


class IOTests(Fixture):
    def test_synthetic_report_has_no_raw_private_transcript(self):
        self.write([meta(),context(),event('user_message',message='ULTRA_SECRET_PROMPT'),
                    call(cmd='TOKEN=TOP_SECRET npm test'),output(text='Process exited with code 0\nULTRA_SECRET_OUTPUT'),token(vec(),seconds=10)])
        c,r=self.collect();report=dict(current=r,diagnostics=dict(c.diag),partial_scan=False,current_configuration=c.snapshot())
        text=json.dumps(report)+a.markdown(report)
        for secret in ('PRIVATE-OWNER','SECRET-PROJECT','ULTRA_SECRET','TOP_SECRET'):
            self.assertNotIn(secret,text)

    def test_current_config_does_not_supply_historical_model(self):
        (self.home/'config.toml').write_text('model="gpt-6.1-sol"\nmodel_reasoning_effort="high"\n')
        self.write([meta(),token(vec())]);c,r=self.collect()
        self.assertEqual(r['models'][0]['model'],'unknown')
        self.assertEqual(c.snapshot()['configured_main_model'],'gpt-6.1-sol')

    def test_partial_line_is_flagged(self):
        p=self.write([meta(),context()]);p.write_text(p.read_text()+'{"unfinished":')
        c,_=self.collect();self.assertTrue(c.partial)
        self.assertEqual(c.diag['invalid_or_partial_json_records'],1)

    def test_read_limit_flags_partial(self):
        self.write([meta(),context(),token(vec())]);c,_=self.collect(max_bytes=100)
        self.assertTrue(c.partial)

    def test_oversized_line_does_not_corrupt_next_record(self):
        self.write([meta(),record('response_item',{'type':'message','content':'X'*5000}),context(),token(vec())])
        c,r=self.collect(max_line=1200);self.assertTrue(c.partial)
        self.assertEqual(r['observed_token_usage']['total_tokens'],130)

    def test_symlinks_are_not_followed(self):
        target=self.root/'elsewhere.jsonl';target.write_text(json.dumps(meta())+'\n')
        (self.home/'sessions/link.jsonl').symlink_to(target)
        c,_=self.collect();self.assertEqual(c.diag['special_or_symlink_files_skipped'],1)

    def test_mtime_prefilter_can_be_disabled(self):
        p=self.write([meta(),context(),token(vec())]);os.utime(p,(0,0))
        _,r=self.collect();self.assertEqual(r['sessions_observed'],0)
        _,r=self.collect(all_files=True);self.assertEqual(r['observed_token_usage']['total_tokens'],130)

    def test_complete_cli_bundle_is_shareable_and_inputs_unchanged(self):
        p=self.write([meta(),context(),token(vec()),call(),output()]);before=p.read_bytes()
        out=self.root/'report'
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            code=a.main(['--codex-home',str(self.home),'--since','2026-10-08T00:00:00Z',
                         '--until','2026-10-15T00:00:00Z','--out',str(out),'--quiet'])
        self.assertEqual(code,0);self.assertEqual(p.read_bytes(),before)
        with zipfile.ZipFile(out/'SHARE-summary.zip') as z:
            self.assertNotIn('local-index.PRIVATE.json',z.namelist())
            self.assertEqual(len(z.namelist()),3)
        self.assertEqual((out/'report.json').stat().st_mode&0o777,0o600)
        self.assertEqual(out.stat().st_mode&0o777,0o700)

    def test_existing_output_not_overwritten(self):
        out=self.root/'report';out.mkdir();(out/'keep').write_text('owner')
        with contextlib.redirect_stderr(io.StringIO()):code=a.main(['--codex-home',str(self.home),'--out',str(out)])
        self.assertEqual(code,2);self.assertEqual((out/'keep').read_text(),'owner')

    def test_output_inside_codex_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()):code=a.main(['--codex-home',str(self.home),'--out',str(self.home/'new')])
        self.assertEqual(code,2);self.assertFalse((self.home/'new').exists())

    def test_optional_prices_no_double_counting_subsets(self):
        self.write([meta(),context(),token(vec())]);c,_=self.collect()
        prices={'models':{'gpt-6-luna':{'input':1,'cached_input':.1,'output':2}},'as_of':'2026-10-15','currency':'USD'}
        r=c.report(START,END,prices);self.assertAlmostEqual(r['api_equivalent_estimate']['amount_for_priced_tokens'],142/1e6)

    def test_no_data_is_not_reported_as_success(self):
        out=self.root/'report'
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            code=a.main(['--codex-home',str(self.home),'--out',str(out),'--quiet'])
        self.assertEqual(code,2);self.assertTrue((out/'report.json').exists())



class AdditionalRegressions(Fixture):
    def test_developer_instruction_snapshot_is_detected(self):
        m=meta();m['payload']['base_instructions']=None
        instr=record('response_item',{'type':'message','role':'developer',
                     'content':[{'type':'input_text','text':'Smart Orchestration 4.0.1: actual instruction snapshot'}]})
        self.write([m,instr,context(),token(vec())]);_,r=self.collect()
        self.assertEqual(r['workflow_cohorts'][0]['association'],'instruction_marker_4.0.1')

    def test_legacy_review_subagent_string_classified_as_worker(self):
        m=meta();m['payload']['source']={'subagent':'review'}
        self.write([m,context(),token(vec())]);_,r=self.collect()
        self.assertEqual(r['worker_sessions'],1)

    def test_malformed_event_types_do_not_crash(self):
        self.write([meta(),record('event_msg',{'type':[]}),context(),token(vec())])
        c,r=self.collect();self.assertTrue(c.partial)
        self.assertEqual(r['observed_token_usage']['total_tokens'],130)

    def test_retained_record_bound_is_visible(self):
        self.write([meta(),context(),token(vec()),call(),output()])
        c,_=self.collect(max_events=2)
        self.assertTrue(c.partial)
        self.assertEqual(c.diag['retained_event_limit_reached'],1)

    def test_inconsistent_native_total_is_not_summed(self):
        v=vec();v['total_tokens']=135
        self.assertIsNone(a.vector(v))

    def test_large_malformed_numbers_do_not_overflow(self):
        self.assertFalse(a.finite(10**1000))
        self.assertIsNone(a.stamp(10**1000))

if __name__=='__main__':unittest.main()
