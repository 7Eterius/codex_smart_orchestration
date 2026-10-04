"""Current independent boundaries, including Main-authored candidates."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PACKAGE=Path(__file__).resolve().parents[1]/'codex_workflow'
sys.path.insert(0,str(PACKAGE))
from runtime import boundary as b

def record(**changes):
    r=dict(schema=1,unit='U1',attempt='A1',contract='R1',candidate='C1',target='local',
           primary='main',writer='writer',reviewer='tester',hold='held',gates={'behavior':True,'references':False})
    r.update(changes);return r

def verdict(r=None,**changes):
    r=record() if r is None else r
    v={k:r[k] for k in (*b.IDENTITY,'reviewer')}
    v.update(artifact='original/review',gates={'behavior':{'status':'executed-pass','evidence':'behavior/log'},
                                             'references':{'status':'reused-pass','evidence':'reference/log'}})
    v.update(changes);return v

class BoundaryTests(unittest.TestCase):
    def test_matching_acceptance_and_nonmutation(self):
        r=record();v=verdict(r);before=copy.deepcopy((r,v))
        self.assertTrue(b.check(r,'accept','main',v)['allowed']);self.assertEqual((r,v),before)

    def test_writer_needs_released_hold_and_correct_identity(self):
        for actor in ('main','tester','unknown','writer'):
            self.assertFalse(b.check(record(),'write',actor)['allowed'])
            self.assertEqual(b.check(record(hold='released'),'write',actor)['allowed'],actor=='writer')

    def test_main_authored_work_is_allowed_but_not_self_review(self):
        r=record(writer='main');v=verdict(r)
        self.assertTrue(b.check(r,'accept','main',v)['allowed'])
        self.assertFalse(b.check(r,'review','main')['allowed'])
        self.assertFalse(b.check(r,'accept','main')['allowed'])
        self.assertTrue(b.check(record(writer='main',hold='released'),'write','main')['allowed'])
        for role in ('main','writer'):
            with self.assertRaises(b.BoundaryError): b.check(record(reviewer=role),'review',role)

    def test_readback_never_grants_writes(self):
        for actor in ('main','writer','tester','unknown'):
            self.assertEqual(b.check(record(),'readback',actor)['allowed'],actor!='unknown')
            self.assertFalse(b.check(record(),'write',actor)['allowed'])

    def test_review_requires_reviewer_and_hold(self):
        for actor in ('main','writer','tester'):
            self.assertEqual(b.check(record(),'review',actor)['allowed'],actor=='tester')
            self.assertFalse(b.check(record(hold='released'),'review',actor)['allowed'])

    def test_acceptance_requires_primary_hold_and_verdict(self):
        for actor in ('writer','tester','unknown'):
            self.assertFalse(b.check(record(),'accept',actor,verdict())['allowed'])
        self.assertFalse(b.check(record(hold='released'),'accept','main',verdict())['allowed'])
        self.assertEqual(b.check(record(),'accept','main')['reason'],'independent_verdict_missing')

    def test_stale_identity_and_reviewer_rejected(self):
        for field in (*b.IDENTITY,'reviewer'):
            self.assertEqual(b.check(record(),'accept','main',verdict(**{field:'changed'}))['reason'],
                             'stale_or_misattributed_verdict',field)

    def test_obligations_cannot_be_omitted_added_or_waived(self):
        for gates in ({},{'behavior':{}},{**verdict()['gates'],'extra':{}}):
            self.assertEqual(b.check(record(),'accept','main',verdict(gates=gates))['reason'],'gate_map_mismatch')
        for state in ('failed','blocked','unrun','deferred','not-applicable','stale','unverified','reused-pass'):
            v=verdict();v['gates']['behavior']['status']=state
            r=b.check(record(),'accept','main',v)
            self.assertFalse(r['allowed']);self.assertEqual(r['rejected_gates'],['behavior'])

    def test_fresh_result_also_satisfies_reusable_gate(self):
        v=verdict();v['gates']['references']['status']='executed-pass'
        self.assertTrue(b.check(record(),'accept','main',v)['allowed'])

    def test_evidence_and_artifact_must_be_real_references_syntactically(self):
        for key in ('artifact','evidence'):
            for invalid in ('',' ','\x7f','\ud800'):
                v=verdict()
                if key=='artifact':v[key]=invalid
                else:v['gates']['behavior'][key]=invalid
                with self.assertRaises(b.BoundaryError):b.check(record(),'accept','main',v)

    def test_invalid_schema_types_and_freshness_are_rejected(self):
        for field in record():
            for value in (None,[],{},3.5,''):
                with self.subTest(field=field,value=value),self.assertRaises(b.BoundaryError):
                    b.check(record(**{field:value}),'review','tester')
        for value in (1,'false',[],None):
            with self.assertRaises(b.BoundaryError):b.check(record(gates={'behavior':value}),'review','tester')

    def test_unknown_fields_states_and_irrelevant_verdict_rejected(self):
        with self.assertRaises(b.BoundaryError):b.check(record(unexpected=True),'review','tester')
        v=verdict();v['gates']['behavior']['status']='probably-pass'
        with self.assertRaises(b.BoundaryError):b.check(record(),'accept','main',v)
        with self.assertRaises(b.BoundaryError):b.check(record(),'review','tester',v)

    def test_real_cli_codes_and_readonly_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'input.json'
            for payload,code in ((dict(record=record(),action='review',actor='tester'),0),
                                 (dict(record=record(),action='write',actor='writer'),1),
                                 (dict(record=record(),action='review',actor=[]),2)):
                path.write_text(json.dumps(payload));before=path.read_bytes()
                r=subprocess.run([sys.executable,'-B',str(PACKAGE/'runtime/boundary.py'),'--input',str(path)],
                    capture_output=True,text=True,timeout=10)
                self.assertEqual(r.returncode,code,r.stderr);self.assertEqual(path.read_bytes(),before)
                self.assertIn('allowed',json.loads(r.stderr if code==2 else r.stdout))

    def test_duplicate_deep_oversize_and_symlink_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'input.json'
            for text in ('{"record":{},"record":{}}','['*2000+'0'+']'*2000,' '*(b.MAX_INPUT_BYTES+1)):
                path.write_text(text)
                r=subprocess.run([sys.executable,'-B',str(PACKAGE/'runtime/boundary.py'),'--input',str(path)],capture_output=True,text=True,timeout=10)
                self.assertEqual(r.returncode,2)
            alias=Path(tmp)/'alias';alias.symlink_to(path)
            r=subprocess.run([sys.executable,'-B',str(PACKAGE/'runtime/boundary.py'),'--input',str(alias)],capture_output=True,text=True,timeout=10)
            self.assertEqual(r.returncode,2)

if __name__=='__main__':unittest.main()
