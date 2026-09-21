"""v1.5.3 cumulative accounting and opt-in reporting tests.

Synthetic telemetry proves parser behavior, not usage savings or a correction
factor for the owner's screenshots. No network, live account or app writes.
"""
from __future__ import annotations
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'codex_workflow'
SCRIPT = PACKAGE / 'skills/deployment-token-report/scripts/report_tokens.py'
sys.path.insert(0, str(PACKAGE))
from runtime import smart_install, smart_restore, doctor
from runtime._toml import tomllib
from runtime.errors import ValidationError
spec = importlib.util.spec_from_file_location('usage_report_v153', SCRIPT)
r = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = r
spec.loader.exec_module(r)


def at(second):
    return f'2026-09-21T10:00:{second:02d}Z'


def counts(i=100, c=80, o=10):
    return dict(input_tokens=i, cached_input_tokens=c, output_tokens=o)


def event(second, total=None, last=None):
    return dict(timestamp=at(second), type='event_msg', payload=dict(type='token_count', info={
        'total_token_usage': total, 'last_token_usage': last}))


def meta(name='root', second=0, parent=None, role=None, fork=None):
    return dict(timestamp=at(second), type='session_meta', payload=dict(
        id=name, timestamp=at(second), forked_from_id=fork,
        source={'subagent': {'thread_spawn': {'parent_thread_id': parent,
                    'agent_role': role, 'agent_path': 'shared-task-name'}}} if parent else 'cli'))


def message(second, role, text):
    return dict(timestamp=at(second), type='response_item', payload=dict(type='message', role=role,
                content=[dict(type='output_text' if role=='assistant' else 'input_text', text=text)]))


class AccountingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.warnings=[]; self.diag=[]

    def aggregate(self, records, start=1, end=59, creation=0, fork=None):
        path=self.root/'session.jsonl'
        path.write_text('\n'.join(json.dumps(item) for item in records)+'\n')
        session=r.Session('session',path,r.parse_time(at(creation),field='creation'),None,None,None,fork)
        return r.aggregate_session(session,r.parse_time(at(start),field='start'),
                    r.parse_time(at(end),field='end'),self.warnings,self.diag)

    def test_first_fresh_usage(self):
        u=self.aggregate([event(2,counts(),counts())]); self.assertEqual(r.vector(u),(100,80,10));self.assertEqual(u.rollouts,1)

    def test_rate_limit_reemission_is_not_new_usage(self):
        u=self.aggregate([event(2,counts(),counts()),event(3,counts(),counts())])
        self.assertEqual(r.vector(u),(100,80,10)); self.assertEqual(u.rollouts,1)
        self.assertEqual(self.diag[0]['usage_notifications'],2)
        self.assertEqual(self.diag[0]['unchanged_snapshots_ignored'],1)

    def test_identical_real_requests_are_both_counted(self):
        u=self.aggregate([event(2,counts(),counts()),event(3,counts(200,160,20),counts())])
        self.assertEqual(r.vector(u),(200,160,20));self.assertEqual(u.rollouts,2)

    def test_total_equality_not_last_value_defines_duplicate(self):
        u=self.aggregate([event(2,counts(),counts()),event(3,counts(),counts(999,1,5))])
        self.assertEqual(u.rollouts,1)

    def test_pre_window_counter_is_baseline_not_usage(self):
        u=self.aggregate([event(1,counts(1000,900,100),counts()),event(4,counts(1100,980,110),counts())],start=3)
        self.assertEqual(r.vector(u),(100,80,10))

    def test_duplicate_across_window_start_is_not_new_usage(self):
        u=self.aggregate([event(1,counts(),counts()),event(4,counts(),counts())],start=3)
        self.assertEqual(u.rollouts,0)

    def test_post_cutoff_event_is_excluded(self):
        u=self.aggregate([event(2,counts(),counts()),event(4,counts(200,160,20),counts())],end=3)
        self.assertEqual(u.rollouts,1)

    def test_copied_precreation_history_only_seeds_baseline(self):
        u=self.aggregate([event(1,counts(),counts()),event(4,counts(200,160,20),counts())],creation=3)
        self.assertEqual(r.vector(u),(100,80,10))

    def test_missing_cumulative_is_error_not_legacy_guess(self):
        with self.assertRaisesRegex(r.ReportError,'missing cumulative'):
            self.aggregate([event(2,None,counts())])

    def test_ambiguous_initial_total_is_error(self):
        with self.assertRaisesRegex(r.ReportError,'baseline'):
            self.aggregate([event(2,counts(1000,800,100),counts())])

    def test_fork_without_baseline_is_error(self):
        with self.assertRaisesRegex(r.ReportError,'baseline'):
            self.aggregate([event(2,counts(),counts())],fork='parent')

    def test_counter_reset_inside_window_is_error(self):
        with self.assertRaisesRegex(r.ReportError,'regression'):
            self.aggregate([event(2,counts(),counts()),event(3,counts(20,10,2),counts(20,10,2))])

    def test_missing_notification_or_synthetic_adjustment_is_error(self):
        with self.assertRaisesRegex(r.ReportError,'does not match'):
            self.aggregate([event(2,counts(),counts()),event(3,counts(300,240,30),counts())])

    def test_bad_cached_delta_is_error(self):
        with self.assertRaisesRegex(r.ReportError,'cached-input delta'):
            self.aggregate([event(2,counts(100,0,10),counts(100,0,10)),event(3,counts(101,50,11),counts(1,1,1))])

    def test_missing_last_is_not_assumed_one_request(self):
        with self.assertRaisesRegex(r.ReportError,'missing last_token_usage'):
            self.aggregate([event(2,counts(),counts()),event(3,counts(200,160,20),None)])

    def test_bad_numeric_counters_fail(self):
        for bad in (-1,True,1.2,None,'100'):
            with self.subTest(bad=bad),self.assertRaises(r.ReportError):
                self.aggregate([event(2,counts(i=bad),counts())])

    def test_output_does_not_double_count_reasoning(self):
        c={**counts(), 'reasoning_output_tokens':7}
        u=self.aggregate([event(2,c,c)]);self.assertEqual(u.output_tokens,10)

    def test_api_cached_subset_shape_is_supported(self):
        c=dict(input_tokens=100,output_tokens=10,input_tokens_details={'cached_tokens':80})
        self.assertEqual(r.vector(self.aggregate([event(2,c,c)])),(100,80,10))

    def test_zero_snapshot_is_baseline_not_generation(self):
        u=self.aggregate([event(1,counts(0,0,0),counts(0,0,0)),event(2,counts(),counts())])
        self.assertEqual(u.rollouts,1)

    def test_out_of_order_usage_fails(self):
        with self.assertRaisesRegex(r.ReportError,'out-of-order'):
            self.aggregate([event(4,counts(),counts()),event(3,counts(200,160,20),counts())])

    def test_rate_limits_without_usage_are_ignored(self):
        rec=event(1);rec['payload']['info']=None
        u=self.aggregate([rec,event(2,counts(),counts())]);self.assertEqual(u.rollouts,1)

    def test_model_context_is_observed_not_inferred_from_role(self):
        ctx=dict(timestamp=at(1), type='turn_context', payload=dict(model='observed',effort='low'))
        self.aggregate([ctx,event(2,counts(),counts())])
        self.assertEqual(self.diag[0]['recorded_turn_contexts'],[dict(model='observed',reasoning_effort='low')])
        self.assertIn('not independent',self.diag[0]['model_attribution'])

    def test_missing_model_stays_unknown(self):
        self.aggregate([event(2,counts(),counts())])
        self.assertEqual(self.diag[0]['recorded_turn_contexts'],[dict(model=None,reasoning_effort=None)])


class ReportScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.home=Path(self.tmp.name); self.sessions=self.home/'sessions';self.sessions.mkdir()
        self.write('root',[meta(),message(1,'user','Task'),message(2,'assistant','<!-- codex-workflow-deployment-start: example -->'),event(3,counts(),counts())])

    def write(self,name,records):
        (self.sessions/f'{name}.jsonl').write_text('\n'.join(map(json.dumps,records))+'\n')

    def run_report(self,*args):
        return subprocess.run([sys.executable,'-B',str(SCRIPT),'--sessions-root',str(self.sessions),
                   '--deployment-id','example','--root-session-id','root','--end-time',at(50),*args],
                   capture_output=True,text=True)

    def test_main_can_report_without_archivist_or_explicit_start(self):
        result=self.run_report('--format','json');self.assertEqual(result.returncode,0,result.stderr)
        doc=json.loads(result.stdout);self.assertEqual(doc['schema_version'],2)
        self.assertEqual(doc['rows'][0]['agent'],'main agent');self.assertEqual(doc['rows'][0]['input_tokens'],100)
        self.assertEqual(doc['window']['start'],'2026-09-21T10:00:01+00:00')
        self.assertIsNone(doc['accounting']['weekly_allowance_percent'])

    def test_legacy_last_only_returns_no_fabricated_table(self):
        self.write('root',[meta(),message(1,'user','Task'),message(2,'assistant','codex-workflow-deployment-start: example'),event(3,None,counts())])
        result=self.run_report();self.assertEqual(result.returncode,2);self.assertEqual(result.stdout,'')

    def test_six_column_compatibility_has_explicit_scope_note(self):
        result=self.run_report();self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(all(line.count('|')==7 for line in result.stdout.splitlines()))
        self.assertIn('not guaranteed unique requests',result.stderr)

    def test_root_marker_must_be_present(self):
        result=self.run_report('--deployment-id','missing');self.assertEqual(result.returncode,2)

    def test_distinct_threads_with_same_task_name_not_collapsed(self):
        for name in ('child1','child2'):
            self.write(name,[meta(name,2,'root','tester'),event(4,counts(),counts())])
        result=self.run_report('--format','json');self.assertEqual(result.returncode,0,result.stderr)
        row=next(x for x in json.loads(result.stdout)['rows'] if x['agent']=='tester')
        self.assertEqual(row['quantity'],2);self.assertEqual(row['input_tokens'],200)

    def test_new_child_without_telemetry_is_not_reported_as_free(self):
        self.write('child',[meta('child',2,'root','tester')])
        result=self.run_report('--format','json');self.assertEqual(result.returncode,0,result.stderr)
        doc=json.loads(result.stdout);self.assertEqual(doc['accounting']['coverage'],'partial')
        self.assertNotIn('tester',[x['agent'] for x in doc['rows']]);self.assertTrue(doc['warnings'])

    def test_no_main_usage_is_limitation_not_zero(self):
        self.write('root',[meta(),message(1,'user','Task'),message(2,'assistant','codex-workflow-deployment-start: example')])
        result=self.run_report();self.assertEqual(result.returncode,2);self.assertEqual(result.stdout,'')

    def test_codex_home_is_used_for_default_sessions_root(self):
        with patch.dict(os.environ,{'CODEX_HOME':str(self.home)}):
            args=r.parser().parse_args(['--deployment-id','example']);self.assertEqual(args.sessions_root,self.sessions)

    def test_cutoff_is_fixed_before_indexing(self):
        # All future-dated events are excluded by an explicit deterministic cutoff.
        index=r.build_index(self.sessions,[])
        orig=r.datetime
        class Clock:
            calls=0
            @classmethod
            def now(cls,tz): cls.calls+=1; return orig(2026,9,21,10,0,50,tzinfo=timezone.utc)
            fromisoformat=orig.fromisoformat
        with patch.object(r,'datetime',Clock), patch.object(r,'build_index',return_value=index),patch('sys.stdout',new_callable=io.StringIO):
            self.assertEqual(r.main(['--deployment-id','example','--root-session-id','root']),0)
        self.assertEqual(Clock.calls,1)


class PolicyAndInstallTests(unittest.TestCase):
    def test_reporting_opt_in_does_not_remove_memory_or_design(self):
        policy=(PACKAGE/'smart_orchestration.md').read_text()
        self.assertIn('Reporting is opt-in, never a closure gate',policy)
        self.assertIn('one Archivist',policy);self.assertIn('main owns product, UX, interaction and visual authorship',policy)
        self.assertIn('independent Tester',policy);self.assertIn('Never weaken a required gate',policy)
        self.assertIn('navigation and screenshot evidence where permitted',policy)
        self.assertLess(len(policy.split()),1500)
        yaml=(PACKAGE/'skills/deployment-token-report/agents/openai.yaml').read_text()
        self.assertIn('allow_implicit_invocation: false',yaml)
        archivist=tomllib.loads((PACKAGE/'agents/archivist.toml').read_text())
        self.assertIn('only when explicitly',archivist['developer_instructions'])
        self.assertLess(len(archivist['developer_instructions'].split()),300)

    def test_fresh_install_repeat_restore_preserve_project(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);home=root/'home';home.mkdir();project=root/'project';project.mkdir()
            (project/'source').write_text('owner data')
            (home/'config.toml').write_text('model="owner"\nmodel_reasoning_effort="low"\n')
            before=(home/'config.toml').read_bytes()
            plan,prior=smart_install.prepare(PACKAGE,home);backup=smart_install.apply_plan(plan,prior,home)
            self.assertEqual(doctor.inspect(home)['version'],'1.5.3')
            self.assertIn('allow_implicit_invocation: false',(home/'skills/deployment-token-report/agents/openai.yaml').read_text())
            self.assertEqual(smart_install.prepare(PACKAGE,home)[0].mutations,[])
            plan,prior=smart_restore.prepare_restore(home,backup);smart_install.apply_plan(plan,prior,home)
            self.assertEqual((home/'config.toml').read_bytes(),before)
            self.assertEqual((project/'source').read_text(),'owner data')


class PublishedUpgradeTests(unittest.TestCase):
    def test_v152_upgrade_reapply_rollback_and_custom_skill_guard(self):
        from test_v152 import git_tree_hash, snapshot
        import tarfile
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            supplied=os.environ.get('SMART_V152_BASELINE')
            if supplied:
                baseline=Path(supplied)
            else:
                raw=subprocess.run(['git','archive','2ca52d48f29c79b24d6eb0e0393f473b60ba89fc','codex_workflow'],
                                   cwd=ROOT,check=True,capture_output=True).stdout
                destination=root/'baseline'
                with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
                    for member in archive:
                        rel=Path(member.name)
                        if rel.is_absolute() or '..' in rel.parts or rel.parts[0]!='codex_workflow':
                            raise ValueError('Unsafe baseline archive')
                        if member.isfile():
                            target=destination/rel;target.parent.mkdir(parents=True,exist_ok=True)
                            target.write_bytes(archive.extractfile(member).read())
                        elif not member.isdir():
                            raise ValueError('Unexpected baseline entry')
                baseline=destination/'codex_workflow'
            self.assertEqual(git_tree_hash(baseline),'00dfb1efb8f1af94fee77a20d7c5e86bca22b327')
            home=root/'home';home.mkdir()
            (home/'config.toml').write_text('model="owner-model"\nmodel_reasoning_effort="low"\nplan_mode_reasoning_effort="high"\nservice_tier="fast"\n')
            subprocess.run([sys.executable,'-B',str(baseline/'runtime/smart_install.py'),
                            '--package-root',str(baseline),'--codex-home',str(home),'--apply'],
                           check=True,capture_output=True)
            before=snapshot(home)
            plan,prior=smart_install.prepare(PACKAGE,home);backup=smart_install.apply_plan(plan,prior,home)
            self.assertEqual((home/'config.toml').read_bytes(),before['config.toml'])
            self.assertEqual(doctor.inspect(home)['version'],'1.5.3')
            self.assertEqual(smart_install.prepare(PACKAGE,home)[0].mutations,[])
            report=home/'skills/deployment-token-report/scripts/report_tokens.py'
            original=report.read_bytes();report.write_bytes(original+b'\n# Owner tuning\n')
            with self.assertRaisesRegex(ValidationError,'Custom/unowned skill'):
                smart_install.prepare(PACKAGE,home)
            report.write_bytes(original)
            plan,prior=smart_restore.prepare_restore(home,backup);smart_install.apply_plan(plan,prior,home)
            after={k:v for k,v in snapshot(home).items() if not k.startswith('.smart-orchestration-backups/')}
            expected={k:v for k,v in before.items() if not k.startswith('.smart-orchestration-backups/')}
            self.assertEqual(after,expected)


if __name__=='__main__':
    unittest.main()
