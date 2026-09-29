"""2.5 recommendations, supervision contracts, global budget and exact 2.4 migration.

Source tests do not prove native waiting behavior, visual quality or quota savings.
All writes are confined to isolated temporary test homes.
"""
from __future__ import annotations
import copy
import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'codex_workflow'
sys.path.insert(0, str(PACKAGE))
from runtime.config_assessment import assess_configuration, MAIN_BASELINE
from runtime.smart_config import bootstrap, patch_config
from runtime import smart_install as install
from runtime.smart_restore import prepare_restore
from test_allocation import obs, thread, request
from runtime.allocation import next_action
from test_v240 import snapshot
BASELINE = '04fba052b2c64064ca22c24a5212b23b9d28c486'


def flat(name):
    return ' '.join((PACKAGE / name).read_text().split())


class ModelBaselineTests(unittest.TestCase):
    def test_exact_version_and_senior(self):
        self.assertEqual((PACKAGE/'operate/VERSION').read_text(), '2.5.0\n')
        senior=tomllib.loads((PACKAGE/'agents/senior_executor.toml').read_text())
        self.assertEqual((senior['model'],senior['model_reasoning_effort']),('gpt-6.1-sol','xhigh'))
        self.assertEqual(MAIN_BASELINE,dict(model='gpt-6.1-sol',model_reasoning_effort='medium'))

    def test_matching_disk_is_not_live_selection(self):
        cfg={**MAIN_BASELINE,'agents':{'max_threads':2}}
        before=copy.deepcopy(cfg)
        result=assess_configuration(cfg)
        self.assertTrue(result['ok'])
        self.assertEqual(result['parent_baseline_status'],'matches')
        self.assertEqual(result['recommended_parent'],MAIN_BASELINE)
        self.assertTrue(result['unverified'])
        self.assertIn('not live activation',result['assessment_scope'])
        self.assertEqual(cfg,before)

    def test_different_or_missing_parent_is_not_overwritten_or_corruption(self):
        for fields in ({},{'model':'gpt-6-sol','model_reasoning_effort':'low'},
                       {'model':'owner-model','model_reasoning_effort':'high'}):
            cfg={**fields,'agents':{'max_threads':1}}
            before=copy.deepcopy(cfg)
            result=assess_configuration(cfg)
            self.assertTrue(result['ok'])
            self.assertEqual(result['parent_baseline_status'],'different_or_unset')
            self.assertEqual(cfg,before)
            self.assertTrue(any('select it explicitly' in text for text in result['warnings']))

    def test_returned_recommendation_does_not_mutate_global_default(self):
        result=assess_configuration({})
        result['recommended_parent']['model']='changed'
        self.assertEqual(assess_configuration({})['recommended_parent']['model'],'gpt-6.1-sol')

    def test_sol61_supported_efforts_and_unset_are_valid(self):
        for effort in (None,'low','medium','high','xhigh','max'):
            cfg={'model':'gpt-6.1-sol','agents':{'max_threads':2}}
            if effort is not None: cfg['model_reasoning_effort']=effort
            self.assertTrue(assess_configuration(cfg)['ok'],effort)

    def test_known_unsupported_sol61_effort_is_reported_not_rewritten(self):
        for field in ('model_reasoning_effort','plan_mode_reasoning_effort'):
            for effort in ('none','minimal'):
                cfg={'model':'gpt-6.1-sol',field:effort}
                before=copy.deepcopy(cfg)
                result=assess_configuration(cfg)
                self.assertFalse(result['ok'])
                self.assertTrue(any(field in text and 'unsupported' in text for text in result['errors']))
                self.assertEqual(cfg,before)

    def test_other_models_are_not_assigned_sol61_capabilities(self):
        self.assertTrue(assess_configuration(dict(model='owner-model',model_reasoning_effort='none'))['ok'])

    def test_profiles_and_child_fallback_remain_explicit_unknowns(self):
        cfg={**MAIN_BASELINE,'agents':{'default_subagent_model':'gpt-5.6-luna'},
             'profiles':{'owner':{'model':'private-model','developer_instructions':'private text'}}}
        before=copy.deepcopy(cfg)
        result=assess_configuration(cfg)
        self.assertEqual(cfg,before)
        self.assertEqual(result['configured_child_defaults']['default_subagent_model'],'gpt-5.6-luna')
        self.assertIn('selected profile is unverified',' '.join(result['warnings']))
        self.assertNotIn('private text',str(result))

    def test_bootstrap_does_not_replace_parent_or_plan(self):
        text='model="gpt-6-sol"\nmodel_reasoning_effort="low"\nplan_mode_reasoning_effort="high"\n[agents]\nmax_threads=1\n'
        patched=tomllib.loads(patch_config(text,Path('/example/home')))
        del patched['developer_instructions']
        self.assertEqual(patched,tomllib.loads(text))


class SupervisionContracts(unittest.TestCase):
    def test_wake_conditions_are_in_activation_and_execution(self):
        for text in (bootstrap(Path('/example/home')),flat('execution.md'),flat('smart_orchestration.md')):
            for word in ('review-ready','decision-needed','blocked'):
                self.assertIn(word,text)
        self.assertIn('timeout alone triggers no progress SEND',bootstrap(Path('/example/home')))

    def test_timeout_is_not_a_reason_for_status_tasks(self):
        text=flat('execution.md')
        for clause in ('must not trigger a SEND', 'list-agents call', 'test rerun',
                       'long, interruptible waits', 'Never hide an actual interruption'):
            self.assertIn(clause,text)
        self.assertIn('No receipt acknowledgements',text)

    def test_real_review_and_interruptions_are_not_silenced(self):
        text=flat('smart_orchestration.md')
        self.assertIn('real user interruption',text)
        self.assertIn('Never reduce review depth to meet a delegation percentage',text)
        self.assertIn('Main does not patch its findings itself',text)
        self.assertIn('Main directly reviews an early running frame',flat('design.md'))

    def test_budget_is_global_across_units_not_per_parent(self):
        a=thread('one',unit='U1',parent='main')
        b=thread('two',unit='U2',parent='one',role='tester')
        result=next_action(obs(a,b,cap=20),request(unit='U3',role='simple_executor',reserve=0))
        self.assertEqual(result['reason'],'smart_open_thread_budget')
        self.assertIn('never allocate two per parent/unit',flat('smart_orchestration.md'))

    def test_completed_prior_unit_still_consumes_capacity(self):
        a=thread('one',unit='U1',state='completed',retain=True)
        b=thread('two',unit='U2',state='waiting',role='tester')
        result=next_action(obs(a,b,cap=20),request(unit='U3',role='simple_executor',reserve=0))
        self.assertEqual(result['reason'],'smart_open_thread_budget')
        self.assertEqual(result['open_count'],2)

    def test_milestone_transition_preserves_corrections_and_resources(self):
        text=flat('execution.md')
        self.assertIn('Keep the writer available for concrete pending main review',text)
        self.assertIn('Use a fresh worker for a new contract after safe release',text)
        self.assertIn('No automatic parent restart',text)
        self.assertIn('After compaction consult the handoff and changed inputs',text)
        self.assertIn('Thread closure does not delete source',text)

    def test_docs_do_not_claim_a_native_scheduler_or_savings(self):
        text=(ROOT/'docs/v2.5.md').read_text()
        self.assertIn('not native enforcement',text)
        self.assertIn('no measured savings claim',text)
        self.assertFalse((PACKAGE/'coordinated.md').exists())
        self.assertFalse((PACKAGE/'agents/chunk_lead.toml').exists())


class ActualV24Upgrade(unittest.TestCase):
    def test_archived_24_upgrade_reapply_check_and_exact_rollback(self):
        got=subprocess.run(['git','archive',BASELINE,'codex_workflow'],cwd=ROOT,capture_output=True)
        if got.returncode:
            if os.environ.get('CI'):
                self.fail('Exact 2.4 history required: '+got.stderr.decode(errors='replace'))
            self.skipTest('Exact 2.4 object unavailable locally; required in CI')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve(); old=root/'baseline'; home=root/'home'; home.mkdir()
            with tarfile.open(fileobj=io.BytesIO(got.stdout)) as archive:
                for member in archive:
                    relative=Path(member.name)
                    self.assertFalse(relative.is_absolute());self.assertNotIn('..',relative.parts)
                    self.assertEqual(relative.parts[0],'codex_workflow')
                    if member.isfile():
                        path=old/relative;path.parent.mkdir(parents=True,exist_ok=True)
                        path.write_bytes(archive.extractfile(member).read());path.chmod(member.mode & 0o777)
                    else:self.assertTrue(member.isdir())
            package=old/'codex_workflow'
            self.assertEqual((package/'operate/VERSION').read_text(),'2.4.0\n')
            config=('model="gpt-6-sol"\nmodel_reasoning_effort="low"\n'
                    'plan_mode_reasoning_effort="high"\nservice_tier="standard"\n'
                    'approval_policy="on-request"\n[agents]\nmax_threads=2\n'
                    'default_subagent_model="gpt-5.6-luna"\n'
                    '[profiles.owner]\nmodel="owner-choice"\n')
            (home/'config.toml').write_text(config)
            (home/'AGENTS.md').write_text('Protected owner instructions.\n')
            project=root/'project';project.mkdir();(project/'important.txt').write_text('Keep unchanged.')
            command=[sys.executable,'-B',str(package/'runtime/smart_install.py'),
                     '--package-root',str(package),'--codex-home',str(home)]
            installed=subprocess.run(command+['--apply'],capture_output=True,text=True)
            self.assertEqual(installed.returncode,0,installed.stdout+installed.stderr)
            before,project_before=snapshot(home),snapshot(project)
            plan,prior=install.prepare(PACKAGE,home)
            self.assertEqual(snapshot(home),before)
            backup=install.apply_plan(plan,prior,home)
            self.assertIsNotNone(backup)
            status=install.status(home)
            self.assertTrue(status['disk_ok'],status)
            self.assertEqual(status['version'],'2.5.0')
            self.assertEqual(status['runtime_observation'],'not_inspected')
            original_cfg=tomllib.loads(before['config.toml'][0].decode())
            updated_cfg=tomllib.loads((home/'config.toml').read_text())
            original_cfg.pop('developer_instructions');updated_cfg.pop('developer_instructions')
            self.assertEqual(original_cfg,updated_cfg)
            for role in (package/'agents').glob('*.toml'):
                original=tomllib.loads(role.read_text())
                updated=tomllib.loads((home/'agents'/role.name).read_text())
                if role.stem=='senior_executor':
                    self.assertEqual(original['model'],'gpt-6-sol')
                    original['model']='gpt-6.1-sol'
                self.assertEqual(updated,original,role.name)
            self.assertEqual(install.prepare(PACKAGE,home)[0].mutations,[])
            self.assertEqual(snapshot(project),project_before)
            restore,prior=prepare_restore(home,backup);install.apply_plan(restore,prior,home)
            self.assertEqual(snapshot(home),before)
            self.assertEqual(snapshot(project),project_before)
            checked=subprocess.run(command+['--check'],capture_output=True,text=True)
            self.assertEqual(checked.returncode,0,checked.stdout+checked.stderr)


if __name__=='__main__':unittest.main()
