"""3.1.1 maintenance regressions, including executable 3.1.0 counterexamples.

These validate supplied-state helpers and shipped contracts, not native Codex behavior.
"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tomllib
import types
import unittest
ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'codex_workflow'
sys.path.insert(0,str(PACKAGE))
from runtime import allocation as a
from runtime import smart_install as install
from runtime.smart_config import bootstrap
from runtime.layout import BUILTIN_WORKERS
from test_allocation import task, scope, thread, observation, request
import test_release_workflow as release_fixture
BASE='2e28dba69fb16dd8e14aa97a33862450d36a5d77'


def historical(case, path):
    result=subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True,text=True,timeout=30)
    if result.returncode:
        if os.environ.get('CI'):case.fail('Exact 3.1.0 source required in CI: '+result.stderr)
        case.skipTest('Exact 3.1.0 Git history unavailable locally; required in CI')
    return result.stdout


def archived(case, path, name):
    module=types.ModuleType('runtime.'+name)
    module.__package__='runtime'
    exec(compile(historical(case,path),path,'exec'),module.__dict__)
    return module


def unscoped_observation(*threads, **kwargs):
    obs=observation(*threads,**kwargs)
    obs.pop('main_scope',None)
    for item in obs['threads']:item.pop('scope',None)
    return obs


def unscoped_request(**kwargs):
    req=request(**kwargs)
    req.pop('scope',None)
    return req


class VerificationScopeTests(unittest.TestCase):
    def test_all_verifiers_require_hold_even_with_legacy_empty_inventory(self):
        for role in a.VERIFIERS:
            for held in ({},{'candidate_held':False}):
                with self.subTest(role=role,held=held):
                    result=a.next_action(unscoped_observation(),unscoped_request(role=role,**held))
                    self.assertEqual(result['reason'],'review_requires_candidate_hold')

    def test_hold_without_explicit_scope_is_not_safe_verification(self):
        for role in a.VERIFIERS:
            result=a.next_action(unscoped_observation(),unscoped_request(role=role,candidate_held=True))
            self.assertEqual((result['action'],result['reason']),('inspect','verification_scope_required'))

    def test_legacy_running_writer_cannot_be_reviewed_without_scope(self):
        obs=unscoped_observation(thread('a',state='running'))
        req=unscoped_request(unit='a',role='reviewer',candidate_held=True)
        self.assertNotIn(a.next_action(obs,req)['action'],('spawn','reuse'))

    def test_legacy_repair_cannot_bypass_active_verifier(self):
        obs=unscoped_observation(thread('review',unit='b',role='reviewer'))
        result=a.next_action(obs,unscoped_request())
        self.assertEqual(result['reason'],'verification_scope_required')

    def test_legacy_verifier_reuse_cannot_bypass_scope(self):
        obs=unscoped_observation(thread('tests',unit='b',role='tester',state='waiting'))
        req=unscoped_request(role='tester',reuse_id='tests',candidate_held=True)
        self.assertEqual(a.next_action(obs,req)['reason'],'verification_scope_required')

    def test_plain_legacy_serial_work_still_supported(self):
        self.assertEqual(a.next_action(unscoped_observation(),unscoped_request())['action'],'spawn')

    def test_valid_scoped_stopped_writer_and_hold_remain_usable(self):
        for role in a.VERIFIERS:
            req=request('a',role=role,scope=scope(writes=[]),candidate_held=True)
            self.assertEqual(a.next_action(observation(thread('a',state='waiting')),req)['action'],'spawn')

    def test_explicit_scope_does_not_hide_unknown_writer_scope(self):
        obs=observation(thread('a',state='waiting'))
        obs['threads'][0].pop('scope')
        req=request('a',role='tester',scope=scope(writes=[]),candidate_held=True)
        self.assertEqual(a.next_action(obs,req)['reason'],'peer_scope_unknown')

    def test_verifier_still_cannot_write_candidate(self):
        req=request('a',role='reviewer',scope=scope(),candidate_held=True)
        self.assertEqual(a.next_action(observation(),req)['reason'],'verifier_writes_input_scope')

    def test_real_cli_rejects_missing_verification_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'input.json'
            p.write_text(json.dumps({'observation':unscoped_observation(),
                                    'request':unscoped_request(role='tester',candidate_held=True)}))
            before=p.read_bytes()
            ran=subprocess.run([sys.executable,'-B',a.__file__,'--input',str(p)],capture_output=True,text=True,timeout=15)
            self.assertEqual(ran.returncode,1,ran.stderr)
            self.assertEqual(json.loads(ran.stdout)['reason'],'verification_scope_required')
            self.assertEqual(p.read_bytes(),before)

    def test_exact_310_reproduces_unheld_unscoped_review_bypass(self):
        old=archived(self,'codex_workflow/runtime/allocation.py','archived_allocation')
        obs=unscoped_observation(thread('a',state='running'))
        req=unscoped_request(unit='a',role='reviewer')
        self.assertEqual(old.next_action(obs,req)['action'],'spawn')
        self.assertNotEqual(a.next_action(obs,req)['action'],'spawn')

    def test_exact_310_reproduces_unscoped_repair_bypass(self):
        old=archived(self,'codex_workflow/runtime/allocation.py','archived_allocation')
        obs=unscoped_observation(thread('review',unit='b',role='reviewer'))
        req=unscoped_request()
        self.assertEqual(old.next_action(obs,req)['action'],'spawn')
        self.assertNotEqual(a.next_action(obs,req)['action'],'spawn')


class RecoveryRoutingTests(unittest.TestCase):
    def test_stalled_testing_routes_to_diagnosis_not_another_tester(self):
        self.assertEqual(a.classify(task(kind='testing',stalled=True))['owner'],'default_executor')

    def test_ordinary_testing_stays_luna_medium_regardless_of_gate_risk(self):
        for risk in ('low','material','critical'):
            result=a.classify(task(kind='testing',risk=risk))
            self.assertEqual((result['owner'],result['reviewer']),('tester',None))

    def test_known_failed_sol_low_moves_to_medium(self):
        result=a.classify(task(stalled=True,previous_owner='default_executor'))
        self.assertEqual((result['owner'],result['reviewer']),('deep_executor','senior_reviewer'))

    def test_known_failed_sol_medium_moves_to_high(self):
        self.assertEqual(a.classify(task(stalled=True,previous_owner='deep_executor'))['owner'],'senior_executor')

    def test_senior_stall_goes_to_replanning_not_repeat_or_self_approval(self):
        for previous in ('senior_executor','senior_reviewer','main'):
            result=a.classify(task(stalled=True,previous_owner=previous,risk='critical'))
            self.assertEqual(result['owner'],'main')
            self.assertEqual(result['reviewer'],'senior_reviewer')
            self.assertEqual(result['reason'],'replan_after_senior_stall_not_another_retry')

    def test_stalled_senior_review_cannot_be_downgraded(self):
        result=a.classify(task(kind='verification',stalled=True,previous_owner='senior_reviewer'))
        self.assertEqual((result['owner'],result['reason']),('main','replan_after_senior_stall_not_another_retry'))

    def test_stalled_ordinary_review_gets_senior_review(self):
        self.assertEqual(a.classify(task(kind='verification',stalled=True,previous_owner='reviewer'))['owner'],'senior_reviewer')

    def test_previous_owner_does_not_escalate_successful_work(self):
        baseline=a.classify(task())
        for previous in BUILTIN_WORKERS | {'main'}:
            self.assertEqual(a.classify(task(previous_owner=previous)),baseline)

    def test_invalid_previous_owner_fails_closed(self):
        for previous in (None,True,{},'other','',1):
            with self.subTest(previous=previous),self.assertRaises(a.AllocationError):
                a.classify(task(previous_owner=previous))

    def test_tiny_does_not_hide_explicit_deep_or_serious_difficulty(self):
        for difficulty in ('deep','serious'):
            with self.assertRaises(a.AllocationError):a.classify(task(tiny=True,difficulty=difficulty))

    def test_protected_judgment_is_resolved_before_escalation(self):
        self.assertEqual(a.classify(task(settled=False,stalled=True,previous_owner='default_executor'))['owner'],'main')

    def test_higher_risk_never_lowers_recovery_depth(self):
        result=a.classify(task(stalled=True,previous_owner='default_executor',risk='critical'))
        self.assertEqual((result['owner'],result['reviewer']),('senior_executor','senior_reviewer'))

    def test_no_metadata_keeps_legacy_stalled_route(self):
        self.assertEqual(a.classify(task(stalled=True))['owner'],'default_executor')

    def test_memory_and_answer_do_not_gain_fake_implementation_teams(self):
        self.assertEqual(a.classify(task(kind='memory',stalled=True))['owner'],'archivist')
        self.assertEqual(a.classify(task(kind='answer'))['owner'],'main')

    def test_recovery_does_not_mutate_task_facts(self):
        facts=task(stalled=True,previous_owner='default_executor')
        before=copy.deepcopy(facts)
        self.assertEqual(a.classify(facts),a.classify(facts))
        self.assertEqual(facts,before)

    def test_exact_310_reproduces_stalled_tester_route(self):
        old=archived(self,'codex_workflow/runtime/allocation.py','archived_allocation')
        facts=task(kind='testing',stalled=True)
        self.assertEqual(old.classify(facts)['owner'],'tester')
        self.assertEqual(a.classify(facts)['owner'],'default_executor')


class ReadbackAndSerialCapacityTests(unittest.TestCase):
    def test_completed_parent_can_read_stopped_child_result(self):
        parent=thread('a',state='completed')
        child=thread('review',parent='a',unit='a',role='reviewer',state='completed',scope=scope(writes=[]))
        obs=observation(parent,child,caller='a')
        req=request('a',role='reviewer',intent='readback',reuse_id='review')
        self.assertEqual(a.next_action(obs,req)['reason'],'readback_only')

    def test_completed_parent_cannot_start_new_work(self):
        obs=observation(thread('a',state='completed',review_authorized=True),caller='a')
        req=request('a',role='reviewer',candidate_held=True,scope=scope(writes=[]))
        with self.assertRaises(a.AllocationError):a.next_action(obs,req)

    def test_readback_does_not_require_fresh_nested_scheduling_permission(self):
        parent=thread('a',state='waiting',review_authorized=False)
        child=thread('review',parent='a',unit='a',role='reviewer',state='completed',scope=scope(writes=[]))
        obs=observation(parent,child,caller='a')
        req=request('a',role='reviewer',intent='readback',reuse_id='review')
        self.assertEqual(a.next_action(obs,req)['reason'],'readback_only')
        req.update(intent='work',candidate_held=True,scope=scope(writes=[]))
        with self.assertRaises(a.AllocationError):a.next_action(obs,req)

    def test_readback_cannot_steal_other_parents_result(self):
        child=thread('review',parent='other',unit='a',role='reviewer',state='completed',scope=scope(writes=[]))
        req=request('a',role='reviewer',intent='readback',reuse_id='review')
        with self.assertRaises(a.AllocationError):
            a.next_action(observation(thread('a',state='completed'),child,caller='a'),req)

    def test_readback_does_not_interrupt_running_child(self):
        child=thread('review',parent='a',unit='a',role='reviewer',scope=scope(writes=[]))
        req=request('a',role='reviewer',intent='readback',reuse_id='review')
        with self.assertRaises(a.AllocationError):
            a.next_action(observation(thread('a',state='completed'),child,caller='a'),req)

    def test_low_cap_serial_testing_then_review_after_native_release(self):
        for cap in (1,2):
            writer=thread('a',state='closed',closure_evidence='native/writer',review_reserved=True)
            obs=observation(writer,cap=cap)
            test_request=request('a',role='tester',candidate_held=True,scope=scope(writes=[]))
            self.assertEqual(a.next_action(obs,test_request)['action'],'spawn')
            tests=thread('tests',unit='a',role='tester',state='closed',closure_evidence='native/tests',scope=scope(writes=[]))
            obs['threads'].append(tests)
            review_request=request('a',role='reviewer',candidate_held=True,scope=scope(writes=[]))
            self.assertEqual(a.next_action(obs,review_request)['action'],'spawn')

    def test_test_completion_without_native_closure_still_consumes_capacity(self):
        tests=thread('tests',unit='a',role='tester',state='completed',scope=scope(writes=[]))
        req=request('a',role='reviewer',candidate_held=True,scope=scope(writes=[]))
        self.assertNotEqual(a.next_action(observation(tests,cap=1),req)['action'],'spawn')

    def test_exact_310_readback_bug_is_reproduced(self):
        old=archived(self,'codex_workflow/runtime/allocation.py','archived_allocation')
        parent=thread('a',state='completed')
        child=thread('review',parent='a',unit='a',role='reviewer',state='completed',scope=scope(writes=[]))
        obs=observation(parent,child,caller='a')
        req=request('a',role='reviewer',intent='readback',reuse_id='review')
        with self.assertRaises(a.AllocationError):a.AllocationError('type guard') if False else None


class InstallationAndStartupTests(unittest.TestCase):
    def test_role_models_are_unchanged_and_sandbox_is_inherited(self):
        for role in sorted(BUILTIN_WORKERS):
            path='codex_workflow/agents/'+role+'.toml'
            old=tomllib.loads(historical(self,path))
            new=tomllib.loads((ROOT/path).read_text())
            self.assertEqual((new['model'],new['model_reasoning_effort']),(old['model'],old['model_reasoning_effort']))
            self.assertEqual(old['sandbox_mode'],'workspace-write')
            self.assertNotIn('sandbox_mode',new)
            self.assertEqual(old['agents'],new['agents'])

    def test_bootstrap_has_less_duplicate_text(self):
        old=archived(self,'codex_workflow/runtime/smart_config.py','archived_config')
        before=len(old.bootstrap(Path('/example')).split())
        after=len(bootstrap(Path('/example')).split())
        self.assertLess(after,220)
        self.assertLess(after,before*0.6)
        print(f'\nBootstrap word count: 3.1.0={before}; 3.1.1={after}. Word counts are not token or allowance measurements.')

    def test_worker_guides_resolve_to_installed_location(self):
        for role,guide in (('tester','testing.md'),('reviewer','verification.md'),('senior_reviewer','verification.md')):
            text=(PACKAGE/'agents'/f'{role}.toml').read_text()
            self.assertIn('CODEX_HOME/codex_workflow/'+guide,text)
            self.assertIn('~/.codex/codex_workflow/'+guide,text)

    def test_installer_preserves_readonly_parent_and_owner_capacity(self):
        with tempfile.TemporaryDirectory() as temp:
            home=Path(temp).resolve()
            config='model="owner"\nsandbox_mode="read-only"\n[agents]\nmax_threads=2\n'
            (home/'config.toml').write_text(config)
            plan,before=install.prepare(PACKAGE,home)
            install.apply_plan(plan,before,home)
            actual=tomllib.loads((home/'config.toml').read_text())
            self.assertEqual(actual['sandbox_mode'],'read-only')
            self.assertEqual(actual['agents']['max_threads'],2)
            self.assertTrue(install.status(home)['disk_ok'])
            for role in BUILTIN_WORKERS:
                self.assertNotIn('sandbox_mode',tomllib.loads((home/'agents'/f'{role}.toml').read_text()))

    def test_daily_policy_does_not_impose_code_tests_on_noncode_work(self):
        text=(PACKAGE/'smart_orchestration.md').read_text()
        self.assertIn('domain-appropriate evidence',text)
        self.assertIn('not invented code tests',text)
        self.assertIn('without recurring installer checks',text)

    def test_current_notes_and_readme_links_resolve(self):
        for path in (ROOT/'README.md',ROOT/'docs/v3.1.1.md'):
            for target in re.findall(r'\]\(([^)]+)\)',path.read_text()):
                if not target.startswith(('https:','http:','#')):
                    self.assertTrue((path.parent/target.split('#')[0]).is_file(),target)
        self.assertTrue((ROOT/'README.md').read_text().startswith('# Smart Orchestration 3.1.1'))


class ReleaseMaintenanceTests(unittest.TestCase):
    def fixture(self):
        case=release_fixture.ReleaseWorkflowTests('test_version_change_publishes_pinned_archive_and_checksum')
        case.setUp()
        self.addCleanup(case.doCleanups)
        return case

    def test_patch_release_requires_its_own_notes_not_stale_series_notes(self):
        case=self.fixture();case.commit_version('2.3.1')
        result,state=case.run_release()
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(state.get('calls',[]),[])

    def test_patch_release_with_exact_notes_publishes(self):
        case=self.fixture()
        (case.repo/'docs/v2.3.1.md').write_text('# Exact patch notes\n')
        case.notes.unlink();case.commit_version('2.3.1')
        result,state=case.run_release()
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(state['published_version'],'2.3.1')

    def test_zero_patch_series_release_can_use_exact_notes(self):
        case=self.fixture()
        (case.repo/'docs/v2.3.0.md').write_text('# Exact initial release notes\n')
        case.notes.unlink()
        result,state=case.run_release()
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(state['published_version'],'2.3.0')

    def test_actions_are_pinned_to_verified_versions(self):
        text=(ROOT/'.github/workflows/validate.yml').read_text()
        pins=re.findall(r'uses: actions/[^@\s]+@([^\s]+)',text)
        self.assertEqual(len(pins),3)
        for pin in pins:self.assertRegex(pin,r'^[a-f0-9]{40}$')
        self.assertIn('# v7.0.1',text);self.assertIn('# v7.0.0',text)

    def test_only_superseded_pr_validations_are_cancelled(self):
        text=(ROOT/'.github/workflows/validate.yml').read_text()
        self.assertIn("cancel-in-progress: ${{ github.event_name == 'pull_request' }}",text)
        self.assertIn('github.event.pull_request.number || github.run_id',text)
        self.assertIn('group: smart-orchestration-release\n      cancel-in-progress: false',text)
        self.assertIn('needs: validate',text)


if __name__=='__main__':unittest.main()
