"""Read-only API-price arithmetic and quality-preserving tuning regressions."""
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
    def test_published_api_rates(self):
        self.assertEqual(e.RATES['gpt-6-luna'], (D('.10'), D('.01'), D('.50')))
        self.assertEqual(e.RATES['gpt-6-sol'], (D('2'), D('.20'), D('10')))
        self.assertEqual(e.RATES['gpt-6-astra'], (D('10'), D('1'), D('50')))
        self.assertEqual(e.RATES['gpt-5.6-luna'], (D('.20'), D('.02'), D('1.20')))
        self.assertEqual(e.RATES['gpt-5.6-sol'], (D('4'), D('.40'), D('20')))

    def test_identical_short_context_workloads_reference_api_usd_not_plan_quota(self):
        expected = {
            'gpt-6-luna': '0.015',
            'gpt-6-sol': '0.30',
            'gpt-6-astra': '1.50',
            'gpt-5.6-luna': '0.032',
            'gpt-5.6-sol': '0.60',
        }
        for model, value in expected.items():
            with self.subTest(model=model):
                result=e.reference(model,100000,0,10000)
                self.assertEqual(result['api_standard_short_context_usd_reference'],value)
                self.assertIsNone(result['included_weekly_allowance_percent'])
                self.assertIn('not a bill',result['limitation'])

    def test_migration_price_relationships(self):
        for index in range(2):
            self.assertEqual(e.RATES['gpt-6-sol'][index], e.RATES['gpt-5.6-sol'][index] / 2)
            self.assertEqual(e.RATES['gpt-6-luna'][index], e.RATES['gpt-5.6-luna'][index] / 2)
        self.assertEqual(e.RATES['gpt-6-sol'][2], e.RATES['gpt-5.6-sol'][2] / 2)
        self.assertEqual(e.RATES['gpt-6-luna'][2], D('0.50'))
        self.assertEqual(e.RATES['gpt-5.6-luna'][2], D('1.20'))
        for idx in range(3):
            self.assertEqual(e.RATES['gpt-6-sol'][idx] / e.RATES['gpt-6-luna'][idx], D(20))

    def test_cached_input_not_double_counted(self):
        self.assertEqual(e.reference('gpt-6-sol',1000000,1000000,0)['api_standard_short_context_usd_reference'],'0.20')
        self.assertEqual(e.reference('gpt-6-luna',1000000,1000000,0)['api_standard_short_context_usd_reference'],'0.01')
        self.assertEqual(e.reference('gpt-6-sol',1000000,500000,0)['api_standard_short_context_usd_reference'],'1.10')

    def test_long_context_not_mispriced_as_aggregate(self):
        result=e.reference('gpt-6-luna',300000,0,0)
        self.assertIn('above 272K',result['limitation'])
        self.assertIn('cannot be repriced safely',result['limitation'])

    def test_invalid_counts_fail_closed(self):
        for values in [(-1,0,0),(0,1,0),(1,-1,0),(0,0,-1),(True,0,0),(1.2,0,0)]:
            with self.subTest(values=values),self.assertRaises(ValueError):
                e.reference('gpt-6-sol',*values)

    def test_unknown_model_has_no_assumed_rate(self):
        with self.assertRaises(ValueError):
            e.reference('future-model',1,0,0)

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

    def test_cli_does_not_need_project_or_model_calls(self):
        out=io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(e.main(['pace','--remaining-percent','100','--workdays-left','5']),0)
        self.assertEqual(json.loads(out.getvalue())['daily_percentage_point_budget'],'17.00')

    def test_cli_rate_metadata_is_explicit(self):
        out=io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(e.main(['rates']),0)
        result=json.loads(out.getvalue())
        self.assertIn('USD per 1M',result['units'])
        self.assertIn('272K',result['limitation'])
        self.assertEqual(result['as_of'],'2026-09-22')

    def test_cli_errors_are_not_results(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(e.main(['compare','--input-tokens','1','--cached-input-tokens','2','--output-tokens','0']),2)

    def test_diagnostics_omit_secrets_and_are_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory)
            text='model="gpt-6-sol"\nservice_tier="fast"\ndeveloper_instructions="SECRET"\napi_key="HIDDEN"\n[profiles.owner]\nmodel="gpt-6-astra"\n'
            (home/'config.toml').write_text(text)
            before={p.name:p.read_bytes() for p in home.iterdir()}
            result=e.settings(home)
            self.assertNotIn('SECRET',json.dumps(result))
            self.assertNotIn('HIDDEN',json.dumps(result))
            self.assertEqual(result['configured_parent']['model'],'gpt-6-sol')
            self.assertTrue(result['warnings'])
            self.assertEqual(before,{p.name:p.read_bytes() for p in home.iterdir()})
            self.assertIsNone(result['workers'][0]['model'])
            self.assertFalse(result['workers'][0]['file_present'])

    def test_symlink_configuration_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);target=home/'outside'
            target.write_text('model="keep"')
            (home/'config.toml').symlink_to(target)
            with self.assertRaises(ValueError):
                e.settings(home)

    def test_role_map_matches_official_workload_guidance(self):
        expected={
            'simple_executor':('gpt-6-luna','low'),
            'routine_executor':('gpt-6-luna','high'),
            'default_executor':('gpt-6-luna','max'),
            'tester':('gpt-6-luna','xhigh'),
            'senior_executor':('gpt-6-sol','xhigh'),
            'companion':('gpt-6-luna','medium'),
            'investigator':('gpt-6-luna','xhigh'),
            'archivist':('gpt-6-luna','medium'),
        }
        for role,settings in expected.items():
            cfg=tomllib.loads((PACKAGE/'agents'/f'{role}.toml').read_text())
            self.assertEqual((cfg['model'],cfg['model_reasoning_effort']),settings)
        self.assertEqual(PackageLayout.resolve(PACKAGE).worker_names,set(expected))

    def test_parent_and_acceptance_guards_retained(self):
        policy=(PACKAGE/'smart_orchestration.md').read_text()
        for phrase in ('Keep the owner\'s selected main model/effort','must not rubber-stamp',
                       'Never weaken a required gate','independent Tester','No secrets',
                       'read-only advice','Stop the old\nwriter','one Archivist',
                       'not a hard limit on necessary parent reasoning',
                       'do not\nskip gates to meet it','Missing tests, novel shared state',
                       'low risk AND a clear pattern AND decisive\nchecks'):
            self.assertIn(phrase,policy)
        self.assertLess(len(policy.split()),1500)

    def test_global_install_preserves_explicit_parent_and_warns_on_fast(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory)/'home';home.mkdir()
            (home/'config.toml').write_text('model="gpt-5.6-sol"\nmodel_reasoning_effort="low"\nservice_tier="fast"\n')
            plan,before=install.prepare(PACKAGE,home)
            backup=install.apply_plan(plan,before,home)
            self.assertTrue(backup.is_dir())
            cfg=tomllib.loads((home/'config.toml').read_text())
            self.assertEqual(cfg['model'],'gpt-5.6-sol')
            self.assertEqual(cfg['model_reasoning_effort'],'low')
            self.assertEqual(cfg['service_tier'],'fast')
            self.assertTrue(any('Fast mode configured' in x for x in e.settings(home)['warnings']))
            self.assertEqual(tomllib.loads((home/'agents/routine_executor.toml').read_text())['model'],'gpt-6-luna')
            plan,_=install.prepare(PACKAGE,home)
            self.assertEqual(plan.mutations,[])

    def test_renamed_fork_is_release_source(self):
        from runtime.release import RELEASE_REPOSITORY
        self.assertEqual(RELEASE_REPOSITORY,'7Eterius/codex_smart_orchestration')


if __name__=='__main__':
    unittest.main()
