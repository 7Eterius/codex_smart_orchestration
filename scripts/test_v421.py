"""4.2.1 regressions and deterministic work-count checks, not model savings."""
import copy
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'codex_workflow'))
from runtime import candidate as c, verification_run as v, work_contracts as w, review_rules as r
from test_v42_contracts import transfer, catalog, predictions

BASE='e96ad3bd5cbd368141f58d1940466b80fd27f578'

def old_module(name,tmp):
    path=Path(tmp)/(name+'.py')
    path.write_bytes(subprocess.check_output(['git','show',BASE+':codex_workflow/runtime/'+name+'.py'],cwd=ROOT))
    key='runtime._v420_'+name
    spec=importlib.util.spec_from_file_location(key,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[key]=mod;spec.loader.exec_module(mod)
    return mod

class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();(self.root/'src').mkdir();(self.root/'src/a').write_text('original')
        self.evidence=self.root/'evidence';self.evidence.mkdir()
        self.plan=dict(schema=1,task='T',requirement_ref='R',root=str(self.root),inputs=['src'],environment_ref='fixture',
                       commands=[dict(id='check',argv=[sys.executable,'-c','print("done")'],timeout_seconds=10)])

class ReceiptEfficiency(Fixture):
    def test_success_uses_two_fresh_snapshots_not_three(self):
        with mock.patch.object(c,'snapshot',wraps=c.snapshot) as reads:
            out=v.run(self.plan,self.evidence,True)
        self.assertEqual(out['action'],'expected_process_outcomes_observed')
        self.assertEqual(reads.call_count,2)

    def test_existing_active_batch_is_rejected_without_hashing(self):
        lock=self.evidence/('.smart-check-'+v.digest(self.plan)+'.lock')
        with lock.open('w') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with mock.patch.object(c,'snapshot',side_effect=AssertionError('redundant hashing')):
                self.assertEqual(v.run(self.plan,self.evidence,True)['action'],'already_running')

    def test_preview_still_reads_once_and_writes_nothing(self):
        with mock.patch.object(c,'snapshot',wraps=c.snapshot) as reads:
            self.assertEqual(v.run(self.plan,self.evidence)['action'],'preview')
        self.assertEqual(reads.call_count,1);self.assertEqual(list(self.evidence.iterdir()),[])

    def test_preview_fingerprint_rejects_changed_candidate_before_launch(self):
        pin=v.run(self.plan,self.evidence)['candidate'];(self.root/'src/a').write_text('changed')
        with mock.patch.object(v.subprocess,'Popen',side_effect=AssertionError('must not execute')):
            with self.assertRaises(ValueError):v.run(self.plan,self.evidence,True,pin)
        self.assertFalse(list(self.evidence.glob('smart-check-*')))

    def test_matching_preview_pin_executes(self):
        pin=v.run(self.plan,self.evidence)['candidate']
        self.assertEqual(v.run(self.plan,self.evidence,True,pin)['action'],'expected_process_outcomes_observed')

    def test_invalid_pin_rejected_without_output(self):
        for value in ('bad',True,12):
            with self.assertRaises(ValueError):v.run(self.plan,self.evidence,True,value)
        self.assertEqual(list(self.evidence.iterdir()),[])

    def test_completed_command_has_immutable_result_before_next_failure(self):
        self.plan['commands'].append(dict(id='second',argv=[sys.executable,'-c','print(2)'],timeout_seconds=5))
        execute=v.execute
        def fail_second(command,*args):
            if command['id']=='second':raise OSError('injected later artifact failure')
            return execute(command,*args)
        with mock.patch.object(v,'execute',side_effect=fail_second):
            with self.assertRaises(OSError):v.run(self.plan,self.evidence,True)
        results=list(self.evidence.glob('smart-check-*/check.result.json'))
        self.assertEqual(len(results),1)
        self.assertEqual(json.loads(results[0].read_text())['exit_code'],0)
        self.assertEqual(results[0].stat().st_mode&0o777,0o600)

    def test_long_selector_wait_avoids_fixed_periodic_wakeups(self):
        factory=v.selectors.DefaultSelector;timeouts=[]
        class ObservedSelector:
            def __init__(self):self.inner=factory()
            def register(self,*args):return self.inner.register(*args)
            def select(self,timeout):timeouts.append(timeout);return self.inner.select(timeout)
            def close(self):self.inner.close()
        with mock.patch.object(v.selectors,'DefaultSelector',ObservedSelector):
            out=v.run(self.plan,self.evidence,True)
        self.assertEqual(out['action'],'expected_process_outcomes_observed')
        self.assertTrue(timeouts);self.assertGreater(timeouts[0],1)

    def test_eof_before_exit_waits_for_real_outcome(self):
        self.plan['commands'][0]['argv']=[sys.executable,'-c','import os,time;os.close(1);os.close(2);time.sleep(.1);raise SystemExit(7)']
        out=v.run(self.plan,self.evidence,True)
        receipt=json.loads(Path(out['receipt']).read_text())
        self.assertEqual(receipt['commands'][0]['exit_code'],7)
        self.assertEqual(out['action'],'needs_inspection')

    def test_sigterm_and_sighup_cancel_only_the_owned_command(self):
        for sig in (signal.SIGTERM,signal.SIGHUP):
            with self.subTest(signal=sig):
                marker=self.root/('pid-'+str(sig));plan=copy.deepcopy(self.plan)
                plan['commands'][0]['argv']=[sys.executable,'-c',f'import os,time;from pathlib import Path;Path({str(marker)!r}).write_text(str(os.getpid()));time.sleep(30)']
                path=self.root/('plan-'+str(sig)+'.json');path.write_text(json.dumps(plan))
                process=subprocess.Popen([sys.executable,'-B',v.__file__,'--plan',str(path),'--evidence-parent',str(self.evidence),'--apply'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                try:
                    deadline=time.monotonic()+5
                    while not marker.exists() and process.poll() is None and time.monotonic()<deadline:time.sleep(.02)
                    self.assertTrue(marker.exists(),'fixture command did not start')
                    child=int(marker.read_text());process.send_signal(sig)
                    stdout,stderr=process.communicate(timeout=6)
                    self.assertEqual(process.returncode,1,stderr)
                    out=json.loads(stdout);receipt=json.loads(Path(out['receipt']).read_text())
                    self.assertEqual(receipt['commands'][0]['status'],'interrupted')
                    self.assertFalse(receipt['semantic_acceptance'])
                    with self.assertRaises(ProcessLookupError):os.kill(child,0)
                finally:
                    if process.poll() is None:process.kill();process.communicate(timeout=3)
                    if marker.exists():
                        try:os.killpg(int(marker.read_text()),signal.SIGKILL)
                        except ProcessLookupError:pass

    def test_cli_restores_callers_signal_handlers(self):
        handlers={s:signal.getsignal(s) for s in (signal.SIGTERM,signal.SIGHUP)}
        path=self.root/'plan.json';path.write_text(json.dumps(self.plan))
        self.assertEqual(v.main(['--plan',str(path),'--evidence-parent',str(self.evidence)]),0)
        self.assertEqual(handlers,{s:signal.getsignal(s) for s in handlers})

class StartupCleanup(Fixture):
    def test_selector_creation_failure_stops_started_child(self):
        with mock.patch.object(v.selectors,'DefaultSelector',side_effect=OSError('injected selector failure')):
            with mock.patch.object(v,'_stop',wraps=v._stop) as stop:
                with self.assertRaises(OSError):v.run(self.plan,self.evidence,True)
                stop.assert_called_once()
                self.assertIsNotNone(stop.call_args.args[0].returncode)

    def test_selector_registration_failure_stops_child_and_closes_selector(self):
        selector=mock.Mock();selector.register.side_effect=OSError('injected registration failure')
        with mock.patch.object(v.selectors,'DefaultSelector',return_value=selector):
            with mock.patch.object(v,'_stop',wraps=v._stop) as stop:
                with self.assertRaises(OSError):v.run(self.plan,self.evidence,True)
                stop.assert_called_once()
                self.assertIsNotNone(stop.call_args.args[0].returncode)
        selector.close.assert_called_once()

class CandidateReads(Fixture):
    def test_overlapping_directories_are_enumerated_once(self):
        sub=self.root/'src/sub';sub.mkdir();(sub/'b').write_text('data')
        original=Path.iterdir;visits=[]
        def listing(path):visits.append(path);return original(path)
        with mock.patch.object(Path,'iterdir',listing):
            manifest=c.snapshot(self.root,['src','src/sub'])
        self.assertEqual(visits.count(sub),1);self.assertEqual(len(manifest['files']),2)
        self.assertTrue(c.verify(manifest)['matched'])

    def test_descriptor_rejects_symlink_and_named_pipe(self):
        link=self.root/'link';link.symlink_to(self.root/'src/a')
        fifo=self.root/'fifo';os.mkfifo(fifo)
        for path in (link,fifo):
            with self.subTest(path=path),self.assertRaises((OSError,ValueError)):c._read_regular(path,1024)

    def test_descriptor_rejects_oversize_before_read(self):
        with self.assertRaises(ValueError):c._read_regular(self.root/'src/a',2)

    def test_descriptor_detects_named_file_replacement(self):
        original=os.fstat;other=self.root/'other';other.write_text('original');other_info=other.stat();calls=0
        def swapped(fd):
            nonlocal calls
            calls+=1
            return original(fd) if calls==1 else other_info
        with mock.patch.object(c.os,'fstat',side_effect=swapped):
            with self.assertRaises(ValueError):c._read_regular(self.root/'src/a',1024)

    def test_deep_empty_directory_inventory_is_bounded(self):
        (self.root/'src/one/two/three/four').mkdir(parents=True)
        with mock.patch.object(c,'MAX_FILES',3):
            with self.assertRaises(ValueError):c.snapshot(self.root,['src'])

    def test_unchanged_candidate_fingerprint_matches_original_version(self):
        old=old_module('candidate',self.temp.name)
        self.assertEqual(c.snapshot(self.root,['src'])['fingerprint'],old.snapshot(self.root,['src'])['fingerprint'])

class HandoffsAndRules(Fixture):
    def test_transfer_preserves_actual_owner_risk_and_authority(self):
        data=transfer();out=w.transition(data)
        for key in ('from_owner','to_owner','from_role','to_role','risk','authority_ref'):
            self.assertEqual(out[key],data[key])
        self.assertFalse(out['authorizes_writes'])

    def test_new_reviewer_also_requires_candidate_hold(self):
        data=transfer(to_role='reviewer',purpose='semantic_review')
        self.assertEqual(w.transition(data)['action'],'hold_candidate_before_review')
        self.assertEqual(w.transition(data|{'candidate_held':True})['action'],'transfer_ready_for_allocator')

    def test_holdout_only_predictions_are_complete_for_requested_split(self):
        cat=catalog();pred=predictions(cat);pred['split']='holdout';pred['results']=pred['results'][2:]
        out=r.score(cat,pred)
        self.assertTrue(out['complete']);self.assertEqual(out['expected'],3)
        self.assertEqual(out['run_ref'],pred['run_ref']);self.assertEqual(out['split'],'holdout')
        self.assertFalse(out['accepted']);self.assertFalse(out['model_executed'])

    def test_scoring_all_still_exposes_omitted_cases(self):
        cat=catalog();pred=predictions(cat);pred['results']=pred['results'][2:]
        self.assertEqual(r.score(cat,pred)['missing'],2)

    def test_other_split_prediction_is_not_silently_discarded(self):
        cat=catalog();pred=predictions(cat);pred['split']='holdout'
        with self.assertRaises(ValueError):r.score(cat,pred)

    def test_empty_requested_split_cannot_score_as_success(self):
        cat=catalog()
        for case in cat['rules'][0]['cases']:case['split']='development'
        pred=predictions(cat);pred.update(split='holdout',results=[])
        with self.assertRaises(ValueError):r.score(cat,pred)

    def test_compact_fixture_keeps_complete_rule_once_and_no_answer_key(self):
        cat=catalog();rule=cat['rules'][0]
        rule['mistake']='m'*500;rule['fix']='f'*500
        out=r.fixture_inputs(cat,'holdout',True);expanded=r.fixture_inputs(cat,'holdout')
        self.assertEqual(out['schema'],2);self.assertEqual(len(out['rules']),1)
        for key in ('scopes','references','exceptions','severity','check'):self.assertEqual(out['rules'][0][key],rule[key])
        self.assertNotIn('cases',out['rules'][0]);self.assertTrue(all('expected' not in row for row in out['cases']))
        self.assertLess(len(json.dumps(out)),len(json.dumps(expanded)))

    def test_legacy_fixture_now_contains_reference_and_scope(self):
        row=r.fixture_inputs(catalog(),'development')['cases'][0]
        self.assertEqual(row['references'],['src/runner.py']);self.assertEqual(row['scopes'],['src'])
        self.assertNotIn('expected',row)

    def test_valid_catalog_larger_than_handoff_limit_works_in_cli(self):
        cat=catalog()
        cat['rules'][0]['cases']*=2
        for i,case in enumerate(cat['rules'][0]['cases']):
            cat['rules'][0]['cases'][i]=case|{'id':str(i),'state':'x'*8192}
        path=self.root/'catalog.json';path.write_text(json.dumps(cat));self.assertGreater(path.stat().st_size,65536)
        with self.assertRaises(ValueError):w.read_json(path)
        self.assertEqual(r.main(['--catalog',str(path),'select','--changed','src/a','--impact-known']),0)

    def test_json_read_override_remains_strictly_bounded(self):
        path=self.root/'data.json';path.write_text('{}')
        for bound in (0,True,4*1024*1024+1):
            with self.assertRaises(ValueError):w.read_json(path,max_bytes=bound)

class OriginalCounterexamples(Fixture):
    def test_original_runner_performed_three_snapshot_passes(self):
        old=old_module('verification_run',self.temp.name)
        with mock.patch.object(c,'snapshot',wraps=c.snapshot) as reads:out=old.run(self.plan,self.evidence,True)
        self.assertEqual(reads.call_count,3);self.assertEqual(out['action'],'expected_process_outcomes_observed')

    def test_original_new_reviewer_was_ready_without_hold_and_omitted_identity(self):
        old=old_module('work_contracts',self.temp.name)
        out=old.transition(transfer(to_role='reviewer',purpose='semantic_review'))
        self.assertEqual(out['action'],'transfer_ready_for_allocator');self.assertNotIn('to_owner',out)

    def test_original_split_only_results_were_always_incomplete(self):
        old=old_module('review_rules',self.temp.name);cat=catalog();pred=predictions(cat);pred['results']=pred['results'][2:]
        self.assertFalse(old.score(cat,pred)['complete'])
        pred['split']='holdout'
        with self.assertRaises(ValueError):old.score(cat,pred)

    def test_original_overlapping_scope_walk_revisited_directory(self):
        old=old_module('candidate',self.temp.name);sub=self.root/'src/sub';sub.mkdir();(sub/'b').write_text('b')
        original=Path.iterdir;visits=[]
        def listing(path):visits.append(path);return original(path)
        with mock.patch.object(Path,'iterdir',listing):old.snapshot(self.root,['src','src/sub'])
        self.assertEqual(visits.count(sub),2)

class PromptBudget(unittest.TestCase):
    def test_global_instruction_pointer_is_smaller_without_loading_extra_guides(self):
        current=(ROOT/'codex_workflow/operate/user_AGENTS.md').read_text()
        old=subprocess.check_output(['git','show',BASE+':codex_workflow/operate/user_AGENTS.md'],cwd=ROOT).decode()
        self.assertLess(len(current.split()),len(old.split()));self.assertLessEqual(len(current.split()),100)
        self.assertIn('smart_orchestration.md',current)

    def test_no_model_effort_or_role_configuration_change(self):
        for path in (ROOT/'codex_workflow/agents').glob('*.toml'):
            old=subprocess.check_output(['git','show',BASE+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT)
            self.assertEqual(path.read_bytes(),old,path.name)

if __name__=='__main__':unittest.main()
