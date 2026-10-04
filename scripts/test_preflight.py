"""Current evidence helpers: executable behavior rather than old prompt wording."""
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
from runtime import challenge, boundary, candidate, evidence


def identity(): return dict(attempt='A2',contract='R1',candidate='C2',target='preview/2')
def record():
    return dict(schema=1,unit='U',phase='handoff',current=identity(),owned_paths=['src'],
        changes=[],decisions=[],questions=[],findings=[],
        deliverables=[dict(path='src/card',required=True,state='satisfied',evidence='diff',basis=identity())],
        evidence=[dict(gate='local',required=True,fresh_required=True,status='executed-pass',evidence='log',basis=identity())])
def capsule():
    return dict(schema=1,unit='U',**identity(),primary='main',writer='writer',reviewer='tester',hold='held',gates={'local':True})
def verdict(r,status='executed-pass'):
    return {**{k:r[k] for k in (*boundary.IDENTITY,'reviewer')},'artifact':'review',
            'gates':{'local':dict(status=status,evidence='original/log')}}

class PreflightTests(unittest.TestCase):
    def test_clear_is_readonly_not_acceptance(self):
        r=record(); before=copy.deepcopy(r); result=challenge.check(r)
        self.assertEqual(result['status'],'clear'); self.assertEqual(r,before)
        self.assertEqual(result['next_action'],'return-for-required-review')
        self.assertIn('not semantic correctness',result['limitation'])

    def test_every_identity_dimension_invalidates_positive_evidence(self):
        for field in identity():
            r=record();r['evidence'][0]['basis'][field]='other'
            self.assertEqual(challenge.check(r)['class'],'evidence-stale',field)

    def test_missing_positive_binding_is_unverified(self):
        for field in ('basis','evidence'):
            r=record();del r['evidence'][0][field]
            self.assertEqual(challenge.check(r)['class'],'evidence-unverified')

    def test_gate_states_match_boundary_at_acceptance(self):
        for state in evidence.STATUSES:
            for fresh in (False,True):
                for spelling in (state,state.upper()):
                    r=record();r['phase']='accept';r['evidence'][0].update(status=spelling,fresh_required=fresh)
                    b=capsule();b['gates']['local']=fresh
                    expected=evidence.satisfies_gate(spelling,fresh)
                    self.assertEqual(challenge.check(r)['status']=='clear',expected)
                    self.assertEqual(boundary.check(b,'accept','main',verdict(b,spelling))['allowed'],expected)

    def test_later_gate_pending_but_known_current_failure_blocks(self):
        r=record();r['evidence'][0].update(due='accept',status='unrun')
        result=challenge.check(r);self.assertEqual(result['status'],'clear')
        self.assertEqual(result['pending_count'],1)
        r['evidence'][0]['status']='failed'
        self.assertEqual(challenge.check(r)['class'],'gate-failed')
        r['evidence'][0]['basis']['candidate']='old'
        self.assertEqual(challenge.check(r)['class'],'evidence-stale')

    def test_addressed_is_reviewable_not_resolved(self):
        r=record();r['findings']=[dict(id='F',blocking=True,state='addressed',evidence='repair',basis=identity())]
        self.assertEqual(challenge.check(r)['pending_count'],1)
        r['phase']='accept';self.assertEqual(challenge.check(r)['class'],'blocking-finding')
        r['findings'][0]['state']='resolved';self.assertEqual(challenge.check(r)['status'],'clear')
        r['current']['candidate']='new';self.assertEqual(challenge.check(r)['status'],'challenge')

    def test_required_unchanged_needs_authorized_outcome_and_evidence(self):
        r=record();r['deliverables'][0]['state']='unchanged'
        self.assertEqual(challenge.check(r)['class'],'deliverable-unchanged')
        r['deliverables'][0]['allow_unchanged']=True
        self.assertEqual(challenge.check(r)['status'],'clear')
        del r['deliverables'][0]['evidence']
        self.assertEqual(challenge.check(r)['class'],'evidence-unverified')

    def test_whole_record_validated_even_after_known_problem(self):
        r=record();r['changes']=[dict(path='outside',origin='owner')]
        r['evidence'].append(dict(gate='bad',required='true',fresh_required=True,status='failed'))
        with self.assertRaises(challenge.ChallengeError):challenge.check(r)
        r=record();r['evidence'].append(copy.deepcopy(r['evidence'][0]))
        with self.assertRaises(challenge.ChallengeError):challenge.check(r)

    def test_schema_paths_and_empty_obligations_fail_closed(self):
        for schema in (True,1.0,0,'1'):
            r=record();r['schema']=schema
            with self.assertRaises(challenge.ChallengeError):challenge.check(r)
        for path in ('../src','src/../elsewhere','/src','src//x','src/','src/.git/config'):
            r=record();r['owned_paths']=[path]
            with self.assertRaises(challenge.ChallengeError):challenge.check(r)
        r=record();r['deliverables']=[];r['evidence']=[]
        self.assertEqual(challenge.check(r)['class'],'obligations-unverified')

    def test_main_question_stays_visible_in_bounded_batch(self):
        r=record();r['questions']=[dict(id=f'Q{i}',state='unanswered') for i in range(12)]
        r['questions'].append(dict(id='protected',state='unknown'))
        result=challenge.check(r)
        self.assertEqual(result['reference'],'protected');self.assertEqual(result['next_action'],'decision-needed')
        self.assertEqual(result['issue_count'],13);self.assertEqual(result['omitted_issues'],5)
        self.assertEqual(len(result['issues']),8)

    def test_answer_requires_evidence_not_confidence(self):
        r=record();r['questions']=[dict(id='Q',state='answered',answer='Yes')]
        self.assertEqual(challenge.check(r)['class'],'evidence-unverified')
        r['questions'][0].update(evidence='proof',basis=identity())
        self.assertEqual(challenge.check(r)['status'],'clear')

    def test_real_manifest_drift_and_unrelated_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();(root/'src').mkdir();(root/'src/a').write_text('before')
            manifest=candidate.snapshot(root,['src']);path=root/'manifest.json';candidate.write_manifest(manifest,path)
            r=record();r['current']['candidate']=manifest['fingerprint']
            for row in r['deliverables']+r['evidence']:row['basis']=dict(r['current'])
            (root/'unrelated').write_text('change')
            self.assertTrue(challenge.verify_manifest(r,path)['matched'])
            (root/'src/a').write_text('after')
            self.assertFalse(challenge.verify_manifest(r,path)['matched'])
            r['questions']=[dict(id='protected',state='unknown')]
            inp=root/'input.json';inp.write_text(json.dumps(r))
            ran=subprocess.run([sys.executable,'-B',str(PACKAGE/'runtime/challenge.py'),
                '--input',str(inp),'--manifest',str(path)],capture_output=True,text=True,timeout=10)
            self.assertEqual(ran.returncode,1,ran.stderr)
            result=json.loads(ran.stdout);self.assertEqual(result['reference'],'protected')
            self.assertFalse(result['local_identity']['matched'])

    def test_cli_errors_and_nonmutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'record.json'
            for payload in ('{"schema":1,"schema":1}','['*2000+'0'+']'*2000,
                            '{"schema":NaN}', ' '*(challenge.MAX_INPUT_BYTES+1)):
                path.write_text(payload)
                ran=subprocess.run([sys.executable,'-B',str(PACKAGE/'runtime/challenge.py'),'--input',str(path)],capture_output=True,text=True,timeout=10)
                self.assertEqual(ran.returncode,2);self.assertEqual(path.read_text(),payload)
                self.assertEqual(json.loads(ran.stderr)['status'],'error')

    def test_boundary_main_writer_still_needs_other_reviewer(self):
        b=capsule();b['writer']='main'
        self.assertTrue(boundary.check(b,'accept','main',verdict(b))['allowed'])
        self.assertFalse(boundary.check(b,'accept','main')['allowed'])
        self.assertFalse(boundary.check(b,'review','main')['allowed'])
        self.assertFalse(boundary.check(b,'write','main')['allowed'])
        b['hold']='released';self.assertTrue(boundary.check(b,'write','main')['allowed'])
        self.assertFalse(boundary.check(b,'accept','main',verdict(b))['allowed'])
        for reviewer in ('main','writer'):
            b=capsule();b['reviewer']=reviewer
            with self.assertRaises(boundary.BoundaryError):boundary.check(b,'review',reviewer)

    def test_blank_control_refs_never_authorize_acceptance(self):
        for invalid in (' ','\t','\x7f','\x85','\ud800'):
            b=capsule();v=verdict(b);v['gates']['local']['evidence']=invalid
            with self.assertRaises(boundary.BoundaryError):boundary.check(b,'accept','main',v)
        b=capsule();v=verdict(b);v['gates']['local']['evidence']='проверка/результат'
        self.assertTrue(boundary.check(b,'accept','main',v)['allowed'])

if __name__=='__main__': unittest.main()
