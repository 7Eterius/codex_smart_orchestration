"""Real isolated subprocesses; no user projects, providers or native agents."""
import copy
import fcntl
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'codex_workflow'))
from runtime import verification_run as v

class Receipts(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();(self.root/'src').mkdir();(self.root/'src/a').write_text('original')
        self.evidence=self.root/'evidence';self.evidence.mkdir()
        self.plan=dict(schema=1,task='T',requirement_ref='R',root=str(self.root),inputs=['src'],environment_ref='isolated-fixture',
                       commands=[dict(id='check',argv=[sys.executable,'-c','print("result")'],timeout_seconds=5)])

    def run_plan(self,code=None):
        if code is not None:self.plan['commands'][0]['argv']=[sys.executable,'-c',code]
        out=v.run(self.plan,self.evidence,True)
        receipt=json.loads(Path(out['receipt']).read_text())
        return out,receipt,Path(out['receipt']).parent

    def test_preview_has_no_writes_or_processes(self):
        with mock.patch.object(v.subprocess,'Popen',side_effect=AssertionError('unexpected execution')):
            out=v.run(self.plan,self.evidence)
        self.assertEqual(out['action'],'preview');self.assertEqual(list(self.evidence.iterdir()),[])

    def test_true_process_exit_cannot_be_hidden_by_receipt_creation(self):
        out,receipt,_=self.run_plan('import sys; print("failed"); sys.exit(7)')
        self.assertEqual(out['action'],'needs_inspection');self.assertEqual(receipt['commands'][0]['exit_code'],7)
        self.assertFalse(receipt['semantic_acceptance'])

    def test_zero_exit_is_process_evidence_not_test_verdict(self):
        out,receipt,_=self.run_plan()
        self.assertEqual(out['action'],'expected_process_outcomes_observed')
        self.assertEqual(receipt['commands'][0]['test_verdict'],'not_inferred_from_process_exit')

    def test_composite_masked_nested_exit_is_not_clean(self):
        out,receipt,_=self.run_plan('print("exit_status=1")')
        self.assertEqual(out['action'],'needs_inspection')
        self.assertTrue(receipt['commands'][0]['conflicting_exit_evidence'])

    def test_expected_red_keeps_original_nonzero(self):
        self.plan['commands'][0]['expected_exit']=1
        out,receipt,_=self.run_plan('import sys;sys.exit(1)')
        self.assertEqual(out['action'],'expected_process_outcomes_observed')
        self.assertEqual(receipt['commands'][0]['exit_code'],1);self.assertFalse(receipt['semantic_acceptance'])

    def test_later_required_commands_are_explicitly_not_run(self):
        self.plan['commands'].append(dict(id='later',argv=[sys.executable,'-c','print("later")'],timeout_seconds=5))
        _,receipt,_=self.run_plan('raise SystemExit(3)')
        self.assertEqual(receipt['commands'][1]['status'],'not_run')

    def test_changed_candidate_invalidates_receipt(self):
        out,receipt,_=self.run_plan('from pathlib import Path; Path("src/a").write_text("changed")')
        self.assertEqual(out['action'],'stale_inputs');self.assertFalse(receipt['listed_inputs_unchanged'])

    def test_failed_and_green_runs_have_separate_original_logs(self):
        _,first,folder1=self.run_plan('raise SystemExit(1)')
        original=(folder1/'receipt.json').read_bytes()
        _,second,folder2=self.run_plan('print("ok")')
        self.assertNotEqual(folder1,folder2);self.assertEqual((folder1/'receipt.json').read_bytes(),original)
        self.assertEqual(first['commands'][0]['exit_code'],1);self.assertEqual(second['commands'][0]['exit_code'],0)

    def test_private_modes(self):
        _,_,folder=self.run_plan()
        self.assertEqual(folder.stat().st_mode&0o777,0o700)
        for p in folder.iterdir():self.assertEqual(p.stat().st_mode&0o777,0o600)

    def test_output_location_cannot_change_watched_scope(self):
        with self.assertRaises(ValueError):v.run(self.plan,self.root/'src',True)

    def test_active_cooperative_lock_does_not_launch_again(self):
        lock=self.evidence/('.smart-check-'+v.digest(self.plan)+'.lock')
        with lock.open('w') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with mock.patch.object(v.subprocess,'Popen',side_effect=AssertionError('duplicate')):
                self.assertEqual(v.run(self.plan,self.evidence,True)['action'],'already_running')

    def test_timeout_is_not_pass(self):
        self.plan['commands'][0]['timeout_seconds']=1
        out,receipt,_=self.run_plan('import time;time.sleep(30)')
        self.assertEqual(out['action'],'needs_inspection');self.assertEqual(receipt['commands'][0]['status'],'timeout')

    def test_truncated_output_is_not_complete(self):
        with mock.patch.object(v,'MAX_OUTPUT',1024):
            out,receipt,folder=self.run_plan('print("x"*5000)')
        self.assertEqual(receipt['commands'][0]['status'],'output_limit')
        self.assertFalse(receipt['commands'][0]['output_complete'])
        self.assertLessEqual((folder/'check.log').stat().st_size,1024)

    def test_missing_executable_is_visible_and_not_retried(self):
        self.plan['commands'][0]['argv']=['/not/a/real/executable']
        _,receipt,_=self.run_plan();self.assertEqual(receipt['commands'][0]['status'],'launch_error')

    def test_invalid_argv_schema_and_duplicate_ids_rejected(self):
        for change in ('schema','argv','id','timeout'):
            p=copy.deepcopy(self.plan)
            if change=='schema':p['schema']=True
            elif change=='argv':p['commands'][0]['argv']='echo yes'
            elif change=='id':p['commands']*=2
            else:p['commands'][0]['timeout_seconds']=0
            with self.assertRaises(ValueError):v.validate(p)

    def test_stop_reaps_own_group_even_after_direct_child_exits(self):
        process=mock.Mock(pid=12345)
        with mock.patch.object(v.os,'killpg') as kill:
            v._stop(process)
        self.assertEqual(kill.call_args_list,[mock.call(12345,v.signal.SIGTERM),mock.call(12345,v.signal.SIGKILL)])
        process.wait.assert_any_call(timeout=3)

    def test_receipts_are_create_only(self):
        p=self.evidence/'receipt';v.write_new(p,{'state':'failed'})
        with self.assertRaises(FileExistsError):v.write_new(p,{'state':'pass'})
        self.assertEqual(json.loads(p.read_text()),{'state':'failed'})

if __name__=='__main__':unittest.main()
