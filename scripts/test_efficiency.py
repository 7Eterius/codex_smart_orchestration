"""Read-only arithmetic and quality-preserving tuning regressions."""
from __future__ import annotations

import contextlib
from decimal import Decimal as D
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'codex_workflow'
sys.path.insert(0, str(PACKAGE))
from runtime import efficiency as e
from runtime import smart_install as install
from runtime._toml import tomllib
from runtime.layout import PackageLayout


class EfficiencyTests(unittest.TestCase):
    def test_published_base_rates(self):
        self.assertEqual(e.RATES['gpt-5.6-sol'], (D(100), D(10), D(500)))
        self.assertEqual(e.RATES['gpt-6-astra'], (D(250), D(25), D(1250)))
        self.assertEqual(e.RATES['gpt-5.6-luna'], (D(5), D('.5'), D(30)))

    def test_identical_workloads_not_identical_quota(self):
        for model, expected in [('gpt-5.6-luna','0.8'), ('gpt-5.6-sol','15'), ('gpt-6-astra','37.5')]:
            result = e.reference(model, 100000, 0, 10000)
            self.assertEqual(result['standard_base_credit_reference'], expected)
            self.assertIsNone(result['included_weekly_allowance_percent'])
            self.assertIn('not a bill', result['limitation'])

    def test_cached_input_not_double_counted(self):
        self.assertEqual(e.reference('gpt-5.6-sol', 1000000, 1000000, 0)['standard_base_credit_reference'], '10')
        self.assertEqual(e.reference('gpt-5.6-luna', 1000000, 1000000, 0)['standard_base_credit_reference'], '0.5')
        self.assertEqual(e.reference('gpt-5.6-sol', 1000000, 500000, 0)['standard_base_credit_reference'], '55')

    def test_invalid_counts_fail_closed(self):
        for values in [(-1,0,0),(0,1,0),(1,-1,0),(0,0,-1),(True,0,0),(1.2,0,0)]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                e.reference('gpt-5.6-sol', *values)

    def test_unknown_model_has_no_assumed_rate(self):
        with self.assertRaises(ValueError):
            e.reference('future-model',1,0,0)

    def test_five_day_target_and_reserve(self):
        self.assertEqual(e.pace(D(100),5,D(15))['daily_percentage_point_budget'],'17.00')
        self.assertEqual(e.pace(D(60),3,D(15))['daily_percentage_point_budget'],'15.00')

    def test_exhausted_reserve_has_no_negative_spend(self):
        result = e.pace(D(10),3,D(15))
        self.assertEqual(result['daily_percentage_point_budget'],'0.00')
        self.assertEqual(result['reserve_shortfall_percentage_points'],'5')

    def test_invalid_pacing_rejected(self):
        for remaining, days, reserve in [(D('NaN'),5,D(15)),(D(101),5,D(15)),(D(-1),5,D(15)),(D(80),0,D(15)),(D(80),True,D(15)),(D(80),5,D('Infinity'))]:
            with self.subTest(values=(remaining, days, reserve)), self.assertRaises(ValueError):
                e.pace(remaining,days,reserve)

    def test_cli_does_not_need_project_or_model_calls(self):
        out=io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(e.main(['pace','--remaining-percent','100','--workdays-left','5']),0)
        self.assertEqual(json.loads(out.getvalue())['daily_percentage_point_budget'],'17.00')

    def test_cli_errors_are_not_results(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(e.main(['compare','--input-tokens','1','--cached-input-tokens','2','--output-tokens','0']),2)

    def test_diagnostics_omit_secrets_and_are_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory)
            text='model="gpt-6-astra"\nservice_tier="fast"\ndeveloper_instructions="SECRET"\napi_key="HIDDEN"\n[profiles.owner]\nmodel="gpt-5.6-sol"\n'
            (home/'config.toml').write_text(text)
            before={p.name:p.read_bytes() for p in home.iterdir()}
            result=e.settings(home)
            self.assertNotIn('SECRET',json.dumps(result))
            self.assertNotIn('HIDDEN',json.dumps(result))
            self.assertEqual(result['configured_parent']['model'],'gpt-6-astra')
            self.assertTrue(result['warnings'])
            self.assertEqual(before,{p.name:p.read_bytes() for p in home.iterdir()})
            self.assertIsNone(result['workers'][0]['model'])
            self.assertFalse(result['workers'][0]['file_present'])

    def test_symlink_configuration_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory); target=home/'outside'
            target.write_text('model="keep"')
            (home/'config.toml').symlink_to(target)
            with self.assertRaises(ValueError): e.settings(home)

    def test_role_addition_does_not_downgrade_existing_roles(self):
        expected = {'routine_executor':('gpt-5.6-luna','high'),
                    'default_executor':('gpt-5.6-luna','max'),
                    'tester':('gpt-5.6-luna','xhigh'),
                    'senior_executor':('gpt-5.6-sol','medium'),
                    'archivist':('gpt-5.6-luna','medium')}
        for role, settings in expected.items():
            cfg=tomllib.loads((PACKAGE/'agents'/f'{role}.toml').read_text())
            self.assertEqual((cfg['model'],cfg['model_reasoning_effort']),settings)
        self.assertIn('routine_executor',PackageLayout.resolve(PACKAGE).worker_names)

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

    def test_global_install_and_idempotence_and_speed_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory)/'home'; home.mkdir()
            (home/'config.toml').write_text('model="gpt-6-astra"\nmodel_reasoning_effort="low"\nservice_tier="fast"\n')
            plan,before=install.prepare(PACKAGE,home)
            backup=install.apply_plan(plan,before,home)
            self.assertTrue(backup.is_dir())
            cfg=tomllib.loads((home/'config.toml').read_text())
            self.assertEqual(cfg['model'],'gpt-6-astra')
            self.assertEqual(cfg['model_reasoning_effort'],'low')
            self.assertEqual(cfg['service_tier'],'fast')
            self.assertTrue(any('Fast mode configured' in x for x in e.settings(home)['warnings']))
            self.assertTrue((home/'agents/routine_executor.toml').is_file())
            plan,_=install.prepare(PACKAGE,home)
            self.assertEqual(plan.mutations,[])

    def test_renamed_fork_is_release_source(self):
        from runtime.release import RELEASE_REPOSITORY
        self.assertEqual(RELEASE_REPOSITORY,'7Eterius/codex_smart_orchestration')


if __name__=='__main__':
    unittest.main()
