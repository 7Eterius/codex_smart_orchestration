"""Read-only Work/Codex credit arithmetic and routing regressions."""
from __future__ import annotations

import contextlib
from decimal import Decimal as D
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'codex_workflow'
import sys
sys.path.insert(0, str(PACKAGE))
from runtime import efficiency as e
from runtime import smart_install as install
from runtime._toml import tomllib
from runtime.layout import PackageLayout


class EfficiencyTests(unittest.TestCase):
    def test_published_work_codex_credit_rates(self):
        self.assertEqual(e.CREDIT_RATES['gpt-6-luna'], (D('2.5'), D('.25'), D('12.5')))
        self.assertEqual(e.CREDIT_RATES['gpt-6-sol'], (D('50'), D('5'), D('250')))
        self.assertEqual(e.CREDIT_RATES['gpt-6-astra'], (D('250'), D('25'), D('1250')))
        self.assertEqual(e.CREDIT_RATES['gpt-5.6-luna'], (D('5'), D('.5'), D('30')))
        self.assertEqual(e.CREDIT_RATES['gpt-5.6-sol'], (D('100'), D('10'), D('500')))
        self.assertIs(e.RATES, e.CREDIT_RATES)

    def test_relative_credit_economics_are_exact(self):
        for idx in range(3):
            self.assertEqual(e.CREDIT_RATES['gpt-6-sol'][idx] / e.CREDIT_RATES['gpt-6-luna'][idx], D(20))
            self.assertEqual(e.CREDIT_RATES['gpt-6-astra'][idx] / e.CREDIT_RATES['gpt-6-luna'][idx], D(100))

    def test_identical_workload_uses_credit_reference_not_quota(self):
        luna=e.reference('gpt-6-luna',100000,0,10000)
        sol=e.reference('gpt-6-sol',100000,0,10000)
        self.assertEqual(luna['standard_credit_reference'],'0.375')
        self.assertEqual(sol['standard_credit_reference'],'7.5')
        self.assertEqual(sol['effective_credit_reference'],'7.5')
        self.assertEqual(D(sol['effective_credit_reference'])/D(luna['effective_credit_reference']),D(20))
        self.assertIsNone(sol['included_weekly_allowance_percent'])
        self.assertIn('not a bill',sol['limitation'])

    def test_cached_input_is_subset_not_added_twice(self):
        self.assertEqual(e.reference('gpt-6-luna',1000000,1000000,0)['standard_credit_reference'],'0.25')
        self.assertEqual(e.reference('gpt-6-sol',1000000,1000000,0)['standard_credit_reference'],'5')
        self.assertEqual(e.reference('gpt-6-sol',1000000,500000,0)['standard_credit_reference'],'27.5')

    def test_fast_is_2_5x_for_current_gpt6_models(self):
        for model in ('gpt-6-luna','gpt-6-sol','gpt-6-astra'):
            with self.subTest(model=model):
                standard=e.reference(model,100000,50000,10000,'standard')
                fast=e.reference(model,100000,50000,10000,'fast')
                self.assertEqual(D(fast['effective_credit_reference']),
                                 D(standard['effective_credit_reference'])*D('2.5'))
                self.assertEqual(fast['speed_multiplier'],'2.5')

    def test_fast_unknown_for_legacy_model_fails_closed(self):
        with self.assertRaises(ValueError):
            e.reference('gpt-5.6-luna',100,0,0,'fast')

    def test_published_pro_message_estimates(self):
        self.assertEqual(e.MESSAGE_ESTIMATES['gpt-6-luna']['pro_5x'],'1,750-14,000')
        self.assertEqual(e.MESSAGE_ESTIMATES['gpt-6-luna']['pro_20x'],'7,000-56,000')
        self.assertEqual(e.MESSAGE_ESTIMATES['gpt-6-sol']['pro_5x'],'70-700')
        self.assertEqual(e.MESSAGE_ESTIMATES['gpt-6-astra']['pro_5x'],'25-225')

    def test_invalid_counts_fail_closed(self):
        for values in [(-1,0,0),(0,1,0),(1,-1,0),(0,0,-1),(True,0,0),(1.2,0,0)]:
            with self.subTest(values=values),self.assertRaises(ValueError):
                e.reference('gpt-6-sol',*values)

    def test_unknown_model_or_speed_has_no_fallback(self):
        with self.assertRaises(ValueError):
            e.reference('future-model',1,0,0)
        with self.assertRaises(ValueError):
            e.reference('gpt-6-luna',1,0,0,'turbo')

    def test_five_day_target_and_reserve(self):
        self.assertEqual(e.pace(D(100),5,D(15))['daily_percentage_point_budget'],'17.00')
        self.assertEqual(e.pace(D(60),3,D(15))['daily_percentage_point_budget'],'15.00')

    def test_exhausted_reserve_has_no_negative_spend(self):
        result=e.pace(D(10),3,D(15))
        self.assertEqual(result['daily_percentage_point_budget'],'0.00')
        self.assertEqual(result['reserve_shortfall_percentage_points'],'5')

    def test_invalid_pacing_rejected(self):
        for remaining,days,reserve in [(D('NaN'),5,D(15)),(D(101),5,D(15)),(D(-1),5,D(15)),(D(80),0,D(15)),(D(80),True,D(15)),(D(80),5,D('Infinity'))]:
            with self.subTest(values=(remaining,days,reserve)),self.assertRaises(ValueError):
                e.pace(remaining,days,reserve)

    def test_cli_rate_metadata_is_explicit(self):
        out=io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(e.main(['rates']),0)
        result=json.loads(out.getvalue())
        self.assertIn('Work/Codex credits',result['units'])
        self.assertEqual(result['fast_multiplier'],'2.5')
        self.assertIn('weekly limits',result['limitation'])
        self.assertEqual(result['as_of'],'2026-09-22')

    def test_cli_compare_speed(self):
        out=io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(e.main(['compare','--input-tokens','100000','--cached-input-tokens','0',
                                     '--output-tokens','0','--model','gpt-6-luna','--speed','fast']),0)
        doc=json.loads(out.getvalue())['comparisons'][0]
        self.assertEqual(doc['effective_credit_reference'],'0.625')

    def test_cli_does_not_need_project_or_model_calls(self):
        out=io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(e.main(['pace','--remaining-percent','100','--workdays-left','5']),0)
        self.assertEqual(json.loads(out.getvalue())['daily_percentage_point_budget'],'17.00')

    def test_cli_errors_are_not_results(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(e.main(['compare','--input-tokens','1','--cached-input-tokens','2',
                                     '--output-tokens','0']),2)

    def test_diagnostics_omit_secrets_and_show_relative_economics(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory)
            text='model="gpt-6-sol"\nservice_tier="fast"\ndeveloper_instructions="SECRET"\napi_key="HIDDEN"\n[profiles.owner]\nmodel="gpt-6-astra"\n'
            (home/'config.toml').write_text(text)
            before={p.name:p.read_bytes() for p in home.iterdir()}
            result=e.settings(home)
            self.assertNotIn('SECRET',json.dumps(result))
            self.assertNotIn('HIDDEN',json.dumps(result))
            self.assertEqual(result['configured_parent']['model'],'gpt-6-sol')
            self.assertEqual(result['relative_credit_economics']['sol_vs_luna_per_token'],'20x')
            self.assertEqual(result['relative_credit_economics']['astra_vs_luna_per_token'],'100x')
            self.assertTrue(any('2.5x' in warning for warning in result['warnings']))
            self.assertEqual(before,{p.name:p.read_bytes() for p in home.iterdir()})

    def test_symlink_configuration_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);target=home/'outside'
            target.write_text('model="keep"')
            (home/'config.toml').symlink_to(target)
            with self.assertRaises(ValueError):
                e.settings(home)

    def test_role_map_is_unchanged_from_v161(self):
        expected={
            'simple_executor':('gpt-6-luna','low'),
            'routine_executor':('gpt-6-luna','high'),
            'default_executor':('gpt-6-luna','xhigh'),
            'tester':('gpt-6-luna','high'),
            'senior_executor':('gpt-6-sol','xhigh'),
            'companion':('gpt-6-luna','medium'),
            'investigator':('gpt-6-luna','xhigh'),
            'archivist':('gpt-6-luna','medium'),
        }
        for role,settings in expected.items():
            cfg=tomllib.loads((PACKAGE/'agents'/f'{role}.toml').read_text())
            self.assertEqual((cfg['model'],cfg['model_reasoning_effort']),settings)
        self.assertEqual(PackageLayout.resolve(PACKAGE).worker_names,set(expected))

    def test_parent_acceptance_and_luna_first_guards(self):
        policy=(PACKAGE/'smart_orchestration.md').read_text()
        for phrase in ('Keep the owner\'s selected main model/effort','must not rubber-stamp',
                       'Never weaken a required gate','independent Tester','No secrets',
                       'read-only advice','Stop the old\nwriter','one Archivist',
                       'Missing tests, novel shared state','low risk AND a clear pattern AND decisive\nchecks',
                       'Hard bounded implementation uses Default Luna xhigh',
                       'not difficulty\nalone','no forced Luna failure'):
            self.assertIn(phrase,policy)
        self.assertLess(len(policy.split()),1500)

    def test_global_install_preserves_explicit_parent_and_warns_on_fast(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory)/'home';home.mkdir()
            (home/'config.toml').write_text('model="gpt-6-sol"\nmodel_reasoning_effort="medium"\nservice_tier="fast"\n')
            plan,before=install.prepare(PACKAGE,home)
            backup=install.apply_plan(plan,before,home)
            self.assertTrue(backup.is_dir())
            cfg=tomllib.loads((home/'config.toml').read_text())
            self.assertEqual(cfg['model'],'gpt-6-sol')
            self.assertEqual(cfg['model_reasoning_effort'],'medium')
            self.assertEqual(cfg['service_tier'],'fast')
            self.assertTrue(any('2.5x' in x for x in e.settings(home)['warnings']))
            self.assertEqual(tomllib.loads((home/'agents/routine_executor.toml').read_text())['model'],'gpt-6-luna')
            self.assertEqual(install.prepare(PACKAGE,home)[0].mutations,[])

    def test_renamed_fork_is_release_source(self):
        from runtime.release import RELEASE_REPOSITORY
        self.assertEqual(RELEASE_REPOSITORY,'7Eterius/codex_smart_orchestration')


if __name__=='__main__':
    unittest.main()
