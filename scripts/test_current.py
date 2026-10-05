"""Smart 3 active package, model and lossless-configuration contracts."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import re
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'codex_workflow'
sys.path.insert(0, str(PACKAGE))
from runtime import smart_install as install
from runtime.agent_defaults import configure, DEFAULTS
from runtime.config_assessment import assess_configuration
from runtime.errors import ValidationError
from runtime.layout import PackageLayout, BUILTIN_WORKERS
from runtime.smart_config import patch_config, bootstrap
from runtime.smart_restore import prepare_restore

VERSION = '3.0.1'
EXPECTED = {
    'simple_executor': ('gpt-6-luna', 'low'),
    'routine_executor': ('gpt-6-luna', 'high'),
    'default_executor': ('gpt-6.1-sol', 'medium'),
    'senior_executor': ('gpt-6.1-sol', 'xhigh'),
    'tester': ('gpt-6.1-sol', 'medium'),
    'investigator': ('gpt-6.1-sol', 'medium'),
    'companion': ('gpt-6-luna', 'medium'),
    'archivist': ('gpt-6-luna', 'medium'),
}

class PackageContracts(unittest.TestCase):
    def test_version_inventory_models_and_role_budgets(self):
        package = PackageLayout.resolve(PACKAGE)
        self.assertEqual(package.version, VERSION)
        self.assertEqual(package.worker_names, BUILTIN_WORKERS)
        self.assertEqual(set(EXPECTED), BUILTIN_WORKERS)
        for role, model in EXPECTED.items():
            cfg = tomllib.loads((PACKAGE/'agents'/f'{role}.toml').read_text())
            self.assertEqual((cfg['model'], cfg['model_reasoning_effort']), model, role)
            self.assertIs(cfg['agents']['enabled'], role in {'routine_executor', 'default_executor'})
            self.assertLess(len(cfg['developer_instructions'].split()), 200, role)
            self.assertEqual(set(cfg), {'name','description','model','model_reasoning_effort',
                                      'sandbox_mode','developer_instructions','agents'})

    def test_prompt_budgets(self):
        for name, limit in {'smart_orchestration.md':1200, 'execution.md':1000,
                            'verification.md':700, 'browser.md':650, 'design.md':600}.items():
            self.assertLess(len((PACKAGE/name).read_text().split()), limit, name)
        self.assertLess(len(bootstrap(Path('/example')).split()), 400)

    def test_bootstrap_removes_mandatory_small_task_delegation(self):
        text = bootstrap(Path('/example'))
        self.assertIn('Main may implement', text)
        self.assertIn('Sol', text)
        self.assertIn('parallel', text.lower())
        for retired in ('Delegation is the execution default, including small edits',
                        'At most two Smart-owned', 'Do not self-patch'):
            self.assertNotIn(retired, text)

    def test_safety_and_quality_survive_architecture_change(self):
        text = (PACKAGE/'smart_orchestration.md').read_text()
        for phrase in ('Main owns product meaning', 'Required independent review',
                       'No acknowledgement messages', 'DECISION_NEEDED',
                       'only after observed state change', 'no-agent'):
            self.assertIn(phrase, text)
        self.assertIn('actual visual evidence', text)
        self.assertIn('Luna Max is an optional', text)

    def test_links_and_install_contract(self):
        for path in [ROOT/'README.md', ROOT/'docs/v3.0.md', ROOT/'docs/smart_orchestration.md']:
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if not target.startswith(('http:', 'https:', '#')):
                    self.assertTrue((path.parent/target.split('#')[0]).is_file(), (path,target))
        readme = (ROOT/'README.md').read_text()
        self.assertTrue(readme.startswith('# Smart Orchestration 3.0'))
        for text in ('current HEAD commit SHA of main', 'without --apply first',
                     'Do not use GitHub Releases', 'restart Codex manually'):
            self.assertIn(text, readme)
        self.assertNotIn('workflow.py validate', readme)

class ConfigurationTests(unittest.TestCase):
    def test_only_absent_balanced_defaults_are_inserted(self):
        text, warnings, added = configure('model="owner"\n')
        self.assertEqual(tomllib.loads(text)['agents'], DEFAULTS)
        self.assertEqual(DEFAULTS['default_subagent_model'], 'gpt-6.1-sol')
        self.assertEqual(DEFAULTS['max_concurrent_threads_per_session'], 4)
        self.assertEqual(configure(text)[0], text)
        self.assertEqual(configure(text)[2], {})

    def test_existing_parent_child_cap_profile_and_permission_are_unchanged(self):
        original = ('model="owner-sol"\nmodel_reasoning_effort="high"\n'
            'plan_mode_reasoning_effort="xhigh"\nservice_tier="standard"\n'
            'approval_policy="on-request"\n[agents]\nmax_threads=2\n'
            'default_subagent_model="owner-luna"\ndefault_subagent_reasoning_effort="low"\n'
            '[profiles.custom]\nmodel="custom"\n[mcp_servers.mine]\ncommand="keep"\n')
        value, warnings, added = configure(patch_config(original, Path('/example')))
        before, after = tomllib.loads(original), tomllib.loads(value)
        after.pop('developer_instructions')
        self.assertEqual(before, after)
        self.assertEqual(added, {})
        self.assertTrue(warnings)
        self.assertEqual(patch_config(value, Path('/example')), value)

    def test_inline_and_dotted_settings_not_lossily_rewritten(self):
        for text in ('agents={enabled=true,max_threads=2}\n', 'agents.max_threads=2\n'):
            result, warnings, added = configure(text)
            self.assertEqual(result, text)
            self.assertEqual(added, {})
            self.assertTrue(warnings)

    def test_low_cap_is_visible_but_not_changed(self):
        for cap in (1, 2, 3):
            cfg = {'agents': {'max_threads': cap}}
            before = copy.deepcopy(cfg)
            result = assess_configuration(cfg)
            self.assertEqual(cfg, before)
            self.assertTrue(result['ok'])
            self.assertEqual(result['effective_configured_cap'], cap)
            self.assertEqual(result['recommended_parallel_cap'], 4)
            self.assertTrue(any('lower cap' in x for x in result['warnings']))

    def test_invalid_or_disabled_configuration_fails_without_repair(self):
        for cfg in ({'agents': {'enabled':False}}, {'agents':{'max_threads':True}},
                    {'agents':{'max_threads':2,'max_concurrent_threads_per_session':4}},
                    {'agents':[]}, {'model':'gpt-6.1-sol','model_reasoning_effort':'none'}):
            self.assertFalse(assess_configuration(cfg)['ok'], cfg)

    def test_model_contract_is_specific_not_a_global_guess(self):
        for effort in ('low','medium','high','xhigh','max'):
            self.assertTrue(assess_configuration({'model':'gpt-6.1-sol','model_reasoning_effort':effort})['ok'])
        self.assertTrue(assess_configuration({'model':'owner','model_reasoning_effort':'none'})['ok'])

    def test_owner_instruction_region_is_preserved(self):
        original = 'developer_instructions="Owner rules remain."\nmodel="owner"\n'
        text = patch_config(original, Path('/example'))
        self.assertIn('Owner rules remain.', tomllib.loads(text)['developer_instructions'])
        self.assertEqual(patch_config(text, Path('/example')), text)

class InstallerTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root=Path(temp.name).resolve(); self.home=self.root/'home'; self.home.mkdir()
        self.original='model="owner"\nmodel_reasoning_effort="high"\n[agents]\nmax_threads=2\n'
        (self.home/'config.toml').write_text(self.original)
        self.project=self.root/'project'; self.project.mkdir()
        (self.project/'data').write_text('Owner data')

    def apply(self):
        plan, before = install.prepare(PACKAGE,self.home)
        return install.apply_plan(plan,before,self.home)

    def test_install_check_noop_and_project_preservation(self):
        self.apply()
        state=install.status(self.home)
        self.assertTrue(state['disk_ok'])
        self.assertEqual(state['version'], VERSION)
        self.assertEqual((self.project/'data').read_text(),'Owner data')
        self.assertEqual(tomllib.loads((self.home/'config.toml').read_text())['agents']['max_threads'],2)
        self.assertEqual(install.prepare(PACKAGE,self.home)[0].mutations,[])
        for role in EXPECTED:
            self.assertEqual((self.home/'agents'/f'{role}.toml').read_bytes(),
                             (PACKAGE/'agents'/f'{role}.toml').read_bytes())

    def test_exact_fresh_rollback(self):
        backup=self.apply(); plan,before=prepare_restore(self.home,backup)
        install.apply_plan(plan,before,self.home)
        self.assertEqual((self.home/'config.toml').read_text(),self.original)
        self.assertFalse((self.home/'codex_workflow').exists())
        self.assertFalse((self.home/'agents').exists())

    def test_conflict_between_preview_and_apply_stops(self):
        plan,before=install.prepare(PACKAGE,self.home)
        (self.home/'config.toml').write_text(self.original+'# changed\n')
        with self.assertRaises(ValidationError): install.apply_plan(plan,before,self.home)
        self.assertFalse((self.home/'codex_workflow').exists())

    def test_custom_worker_and_runtime_edits_are_not_overwritten(self):
        self.apply()
        for relative in ('agents/default_executor.toml','codex_workflow/execution.md'):
            path=self.home/relative; original=path.read_bytes(); path.write_bytes(original+b'\n# Owner\n')
            self.assertFalse(install.status(self.home)['disk_ok'])
            with self.assertRaises(ValidationError): install.prepare(PACKAGE,self.home)
            self.assertTrue(path.read_bytes().endswith(b'# Owner\n')); path.write_bytes(original)

    def test_rollback_refuses_later_edits(self):
        backup=self.apply(); (self.home/'config.toml').write_text('# later owner\n')
        with self.assertRaises(ValidationError): prepare_restore(self.home,backup)

if __name__=='__main__': unittest.main()
