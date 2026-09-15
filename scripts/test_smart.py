"""Smart Orchestration contracts and isolated global-install regression tests.

No network, live Codex runtime, repository scans or model calls. Model choice
assertions validate configuration, not a claim of observed runtime behavior.
"""
from __future__ import annotations
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'codex_workflow'
CURRENT_VERSION=(PACKAGE/'operate/VERSION').read_text().strip()
sys.path.insert(0,str(PACKAGE))
from runtime import smart_install as install
from runtime.smart_config import patch_config, SMART
from runtime._toml import tomllib
from runtime.errors import ValidationError,TransactionError
from runtime.layout import PackageLayout,RuntimePaths,ProjectPaths
from runtime.lifecycle import plan_bootstrap
from runtime.markers import USER_MANAGED,extract,replace
from runtime.plan import OperationPlan
from runtime import transaction


def snapshot(root):
    return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}


class ConfigTests(unittest.TestCase):
    def test_empty_round_trip_and_idempotence(self):
        home=Path('/tmp/example codex')
        result=patch_config('',home)
        self.assertIn('Smart Orchestration',tomllib.loads(result)['developer_instructions'])
        self.assertEqual(patch_config(result,home),result)

    def test_existing_instruction_prefix_is_preserved(self):
        result=patch_config('developer_instructions = "Preserve my rule."\nmodel="owner-model"\n',Path('/x'))
        data=tomllib.loads(result)
        self.assertTrue(data['developer_instructions'].startswith('Preserve my rule.\n\n'))
        self.assertEqual(data['model'],'owner-model')

    def test_every_unrelated_setting_remains_exactly_equal(self):
        text='''model="owner-model"
model_reasoning_effort="low"
service_tier="fast"
[agents]
max_concurrent_threads_per_session=2
enabled=true
[mcp_servers.custom]
command="keep"
[profiles.mine]
model="other"
'''
        data=tomllib.loads(patch_config(text,Path('/x')))
        data.pop('developer_instructions')
        self.assertEqual(data,tomllib.loads(text))

    def test_multiline_basic_instruction_and_fake_header(self):
        text='''developer_instructions = """Keep this.
[not_a_table]
Escaped quote: \\" inside.
"""
model="keep"
[agents]
enabled=true
'''
        result=patch_config(text,Path('/x'))
        data=tomllib.loads(result)
        self.assertTrue(data['developer_instructions'].startswith(tomllib.loads(text)['developer_instructions']))
        self.assertEqual(data['agents'],{'enabled':True})

    def test_multiline_literal_with_apostrophe(self):
        text="developer_instructions = '''Keep user's rules.\n[still text]\n'''\nmodel='keep'\n"
        result=patch_config(text,Path('/x'))
        self.assertIn("Keep user's rules",tomllib.loads(result)['developer_instructions'])
        self.assertEqual(tomllib.loads(result)['model'],'keep')

    def test_multiline_value_before_instruction_not_misread(self):
        text='''extra=["a", # comment
"b", "[fake]"]
developer_instructions="mine" # old owned-field comment
[agents]
enabled=true
'''
        after=tomllib.loads(patch_config(text,Path('/x')))
        self.assertEqual(after['extra'],['a','b','[fake]'])
        self.assertTrue(after['developer_instructions'].startswith('mine'))

    def test_quoted_root_key(self):
        for key in ('"developer_instructions"',"'developer_instructions'"):
            with self.subTest(key=key):
                after=tomllib.loads(patch_config(key+'="mine"',Path('/x')))
                self.assertTrue(after['developer_instructions'].startswith('mine'))

    def test_comments_before_key_preserved(self):
        text='# header\n# second\ndeveloper_instructions="mine"\n# tail\n'
        after=patch_config(text,Path('/x'))
        self.assertIn('# header\n# second\n',after)
        self.assertIn('# tail',after)

    def test_no_final_newline(self):
        self.assertEqual(tomllib.loads(patch_config('model="keep"',Path('/x')))['model'],'keep')

    def test_windows_and_unicode_path(self):
        result=patch_config('',Path('C:/Users/Илья/My Codex'))
        self.assertIn('Илья',tomllib.loads(result)['developer_instructions'])

    def test_reserved_marker_partial_rejected(self):
        for bad in (SMART.start,SMART.end,SMART.end+'\n'+SMART.start,SMART.start*2+SMART.end):
            with self.subTest(bad=bad),self.assertRaises(ValidationError):
                patch_config('developer_instructions='+json.dumps(bad),Path('/x'))

    def test_invalid_toml_rejected(self):
        for bad in ('x=','x=1\nx=2','developer_instructions=4'):
            with self.subTest(bad=bad),self.assertRaises(ValidationError):
                patch_config(bad,Path('/x'))

    def test_existing_block_updates_without_duplicate(self):
        first=patch_config('',Path('/first'))
        second=patch_config(first,Path('/second'))
        instructions=tomllib.loads(second)['developer_instructions']
        self.assertEqual(instructions.count(SMART.start),1)
        self.assertNotIn('/first',instructions)
        self.assertIn('/second',instructions)

    def test_table_string_is_not_a_root_key(self):
        text='[profiles.special]\ndeveloper_instructions="Owner profile"\n'
        result=tomllib.loads(patch_config(text,Path('/x')))
        self.assertEqual(result['profiles']['special']['developer_instructions'],'Owner profile')
        self.assertIn('Smart Orchestration',result['developer_instructions'])


class GlobalInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.home=self.root/'codex-home'
        self.project=self.root/'source-project'
        self.project.mkdir()
        (self.project/'AGENTS.md').write_text('Owner rules.\n')
        (self.project/'live.bin').write_bytes(b'private')
        (self.project/'source.swift').write_text('untouched')
        self.before_project=snapshot(self.project)

    def prepare(self):
        return install.prepare(PACKAGE,self.home)

    def apply(self):
        plan,before=self.prepare()
        backup=install.apply_plan(plan,before,self.home)
        return plan,backup

    def test_preview_never_touches_home_or_project(self):
        before=snapshot(self.root)
        plan,_=self.prepare()
        self.assertTrue(plan.mutations)
        self.assertEqual(snapshot(self.root),before)
        self.assertEqual(plan.agent_actions,[])
        self.assertEqual(plan.details['project_mutations'],0)

    def test_apply_installs_global_without_project_paths(self):
        _,backup=self.apply()
        self.assertTrue(backup.is_dir())
        self.assertEqual(snapshot(self.project),self.before_project)
        status=install.status(self.home)
        self.assertTrue(status['global_bootstrap_present'])
        self.assertTrue(status['policy_present'])
        self.assertEqual(status['version'],CURRENT_VERSION)
        self.assertTrue((self.home/'agents/simple_executor.toml').is_file())

    def test_second_install_is_idempotent(self):
        self.apply()
        before=snapshot(self.home)
        plan,original=self.prepare()
        self.assertEqual(plan.mutations,[])
        self.assertIsNone(install.apply_plan(plan,original,self.home))
        self.assertEqual(snapshot(self.home),before)

    def test_preserves_owner_global_rules_and_parent_configuration(self):
        self.home.mkdir()
        original='model="sol-owner"\nservice_tier="fast"\n[agents]\nmax_threads=3\n'
        (self.home/'config.toml').write_text(original)
        (self.home/'AGENTS.md').write_text('Owner header\n'+USER_MANAGED.start+'\nOld global patch\n'+USER_MANAGED.end+'\nOwner footer\n')
        self.apply()
        data=tomllib.loads((self.home/'config.toml').read_text())
        data.pop('developer_instructions')
        self.assertEqual(data,tomllib.loads(original))
        user=(self.home/'AGENTS.md').read_text()
        self.assertIn('Owner header',user)
        self.assertIn('Owner footer',user)
        self.assertNotIn('Old global patch',user)

    def test_nondefault_home_is_in_global_bootstrap(self):
        self.apply()
        instructions=tomllib.loads((self.home/'config.toml').read_text())['developer_instructions']
        self.assertIn(str(self.home/'codex_workflow/smart_orchestration.md'),instructions)
        self.assertIn(str(self.home),(self.home/'AGENTS.md').read_text())

    def test_backups_preserve_exact_old_bytes_privately(self):
        self.home.mkdir()
        (self.home/'config.toml').write_text('model="old"\n')
        _,backup=self.apply()
        self.assertEqual((backup/'files/config.toml').read_text(),'model="old"\n')
        self.assertEqual(backup.stat().st_mode & 0o777,0o700)
        self.assertEqual((backup/'files/config.toml').stat().st_mode & 0o777,0o600)
        records=json.loads((backup/'manifest.json').read_text())['files']
        self.assertTrue(any(r['path']=='config.toml' and r['existed'] for r in records))

    def test_stale_preparation_refuses_owner_change(self):
        plan,before=self.prepare()
        self.home.mkdir()
        (self.home/'AGENTS.md').write_text('New owner edit')
        with self.assertRaisesRegex(ValidationError,'changed during preparation'):
            install.apply_plan(plan,before,self.home)
        self.assertEqual((self.home/'AGENTS.md').read_text(),'New owner edit')
        self.assertFalse((self.home/'codex_workflow').exists())

    def test_custom_unowned_worker_collision_is_not_overwritten(self):
        target=self.home/'agents/simple_executor.toml'
        target.parent.mkdir(parents=True)
        target.write_text('name="my-own-role"\n')
        before=snapshot(self.root)
        with self.assertRaisesRegex(ValidationError,'Custom/unowned worker'):
            self.prepare()
        self.assertEqual(snapshot(self.root),before)

    def test_user_worker_tuning_requires_review(self):
        self.apply()
        target=self.home/'agents/archivist.toml'
        target.write_text(target.read_text()+'\n# custom owner tuning\n')
        with self.assertRaisesRegex(ValidationError,'Custom/unowned worker'):
            self.prepare()

    def test_symlink_home_or_ancestor_is_refused(self):
        actual=self.root/'actual'
        actual.mkdir()
        self.home.symlink_to(actual,target_is_directory=True)
        with self.assertRaisesRegex(ValidationError,'symlink'):
            self.prepare()
        self.assertEqual(list(actual.iterdir()),[])

    def test_symlink_config_is_refused(self):
        self.home.mkdir()
        external=self.root/'outside.toml'
        external.write_text('model="outside"')
        (self.home/'config.toml').symlink_to(external)
        with self.assertRaisesRegex(ValidationError,'symlink'):
            self.prepare()
        self.assertEqual(external.read_text(),'model="outside"')

    def test_symlink_in_worker_directory_is_refused(self):
        (self.home/'agents').mkdir(parents=True)
        (self.home/'agents/link').symlink_to(self.project,target_is_directory=True)
        with self.assertRaisesRegex(ValidationError,'Symlink'):
            self.prepare()

    def test_symlink_backup_parent_is_refused(self):
        self.home.mkdir()
        (self.home/'.smart-orchestration-backups').symlink_to(self.project,target_is_directory=True)
        plan,before=self.prepare()
        with self.assertRaisesRegex(ValidationError,'symlink'):
            install.apply_plan(plan,before,self.home)
        self.assertEqual(snapshot(self.project),self.before_project)

    def test_malformed_global_region_fails_before_writes(self):
        self.home.mkdir()
        (self.home/'AGENTS.md').write_text(USER_MANAGED.start)
        before=snapshot(self.root)
        with self.assertRaises(ValidationError):
            self.prepare()
        self.assertEqual(snapshot(self.root),before)

    def test_profile_override_is_explicit_warning(self):
        self.home.mkdir()
        (self.home/'config.toml').write_text('[profiles.special]\ndeveloper_instructions="mine"\n')
        plan,_=self.prepare()
        self.assertTrue(any('special' in w for w in plan.warnings))

    def test_explicit_disabled_agents_not_overridden(self):
        self.home.mkdir()
        (self.home/'config.toml').write_text('[agents]\nenabled=false\n')
        with self.assertRaisesRegex(ValidationError,'explicitly disabled'):
            self.prepare()

    def test_newer_version_refused(self):
        version=self.home/'codex_workflow/operate/VERSION'
        version.parent.mkdir(parents=True)
        version.write_text('9.0.0\n')
        with self.assertRaisesRegex(ValidationError,'downgrade'):
            self.prepare()

    def test_lock_rejects_concurrent_installer(self):
        plan,before=self.prepare()
        (self.home/'.smart-orchestration-install.lock').mkdir(parents=True)
        with self.assertRaisesRegex(ValidationError,'lock'):
            install.apply_plan(plan,before,self.home)

    def test_transaction_failure_restores_live_files(self):
        self.home.mkdir()
        (self.home/'config.toml').write_text('model="old"\n')
        (self.home/'AGENTS.md').write_text('Owner rule')
        plan,before=self.prepare()
        original=transaction._atomic_write
        failed=[False]
        def fail_once(path,content,mode):
            if path==self.home/'config.toml' and not failed[0]:
                failed[0]=True
                raise OSError('injected write failure')
            return original(path,content,mode)
        with mock.patch.object(transaction,'_atomic_write',side_effect=fail_once):
            with self.assertRaises(TransactionError):
                install.apply_plan(plan,before,self.home)
        self.assertEqual((self.home/'config.toml').read_text(),'model="old"\n')
        self.assertEqual((self.home/'AGENTS.md').read_text(),'Owner rule')
        self.assertEqual(snapshot(self.project),self.before_project)
        self.assertFalse((self.home/'.smart-orchestration-install.lock').exists())

    def test_cli_apply_and_check_without_project_argument(self):
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(install.main(['--codex-home',str(self.home),'--apply']),0)
        self.assertTrue(json.loads(output.getvalue())['applied'])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(install.main(['--codex-home',str(self.home),'--check']),0)

    def test_real_v12_takeover_preserves_project_and_global_patch(self):
        import subprocess,tarfile
        baseline=Path(os.environ.get('SMART_BASELINE_PATH','/nonexistent'))
        if not (baseline/'codex_workflow/runtime/workflow.py').is_file():
            baseline=self.root/'baseline'
            result=subprocess.run(['git','archive','3d610ebae50055a0fd41fa49977b0131797c8e7c','codex_workflow'],
                                  cwd=ROOT,check=True,capture_output=True)
            with tarfile.open(fileobj=io.BytesIO(result.stdout)) as archive:
                for item in archive.getmembers():
                    relative=Path(item.name)
                    if relative.is_absolute() or '..' in relative.parts or relative.parts[0]!='codex_workflow':
                        raise ValueError('Unsafe baseline archive member')
                    if item.isfile():
                        path=baseline/relative; path.parent.mkdir(parents=True,exist_ok=True)
                        path.write_bytes(archive.extractfile(item).read())
                    elif not item.isdir():
                        raise ValueError('Unexpected baseline member type')
        result=subprocess.run([sys.executable,'-B',str(baseline/'codex_workflow/runtime/workflow.py'),
                               'bootstrap','--project',str(self.project),'--codex-home',str(self.home),'--json'],
                              capture_output=True,text=True,check=True)
        old_project=snapshot(self.project)
        old_backup=self.home/'codex_workflow/.source_backup/1.2.0'
        old_source=snapshot(old_backup)
        global_entry=self.home/'AGENTS.md'
        global_entry.write_text(replace(global_entry.read_text(),USER_MANAGED,'Local Quality Economy global patch'))
        self.apply()
        self.assertEqual(snapshot(self.project),old_project)
        self.assertEqual(snapshot(old_backup),old_source)
        self.assertNotIn('Local Quality Economy global patch',global_entry.read_text())
        self.assertTrue(install.status(self.home)['global_bootstrap_present'])
        self.assertEqual((self.home/'codex_workflow/operate/VERSION').read_text().strip(),CURRENT_VERSION)

    def test_cli_cannot_scan_repositories(self):
        with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
            install.main(['--project',str(self.project)])


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy=(PACKAGE/'smart_orchestration.md').read_text()

    def test_single_name_and_legacy_redirects(self):
        for name in ('heavy_route.md','medium_route.md'):
            content=(PACKAGE/name).read_text()
            self.assertIn('Smart Orchestration',content)
            self.assertLess(len(content.split()),90)
        self.assertIn('Never call it a Heavy/Medium route',self.policy)

    def test_main_retains_serious_audit(self):
        for phrase in ('main model owns the plan','serious audit','must not rubber-stamp',
                       'directly examines decisive diffs/contracts'):
            self.assertIn(phrase,self.policy)

    def test_conditional_team_and_context(self):
        self.assertIn('context/research roles are\nconditional',self.policy)
        self.assertIn('Questions or trivial complete edits need no team',self.policy)
        self.assertIn('only the\ncontracts and source needed',self.policy)
        self.assertIn('widen discovery when dependencies are unclear',self.policy)

    def test_no_mandatory_low_tier_failure(self):
        self.assertIn('known hard task',self.policy)
        self.assertIn('Escalate immediately',self.policy)
        self.assertIn('missing context -> supply that context',self.policy)
        self.assertIn('unavailable environment/authority -> report the blocker',self.policy)

    def test_advice_or_ownership_transfer(self):
        for phrase in ('read-only advice','Stop the old\nwriter','new configured role','not a pretend'):
            self.assertIn(phrase,self.policy)

    def test_memory_not_dropped(self):
        for phrase in ('one Archivist','append-only dated meaningful deltas',
                       'Read current state next session, not the entire changelog',
                       'No secrets','Read-only/no-write requests forbid memory writes',
                       'must not invent a resolution or mark pending work done'):
            self.assertIn(phrase,self.policy)

    def test_risk_and_acceptance_not_lowered(self):
        for phrase in ('independent Tester','Never weaken a required gate','unknown freshness requires a check',
                       'final requested screenshots','deferred gates remain OPEN'):
            self.assertIn(phrase,self.policy)

    def test_role_tiers_are_actual_configs(self):
        expected={'simple_executor':('gpt-5.6-luna','medium'),
                  'default_executor':('gpt-5.6-luna','max'),
                  'senior_executor':('gpt-5.6-sol','medium'),
                  'tester':('gpt-5.6-luna','xhigh'),
                  'companion':('gpt-5.6-luna','medium'),
                  'investigator':('gpt-5.6-luna','high'),
                  'archivist':('gpt-5.6-luna','medium')}
        for name,(model,effort) in expected.items():
            with self.subTest(name=name):
                cfg=tomllib.loads((PACKAGE/'agents'/f'{name}.toml').read_text())
                self.assertEqual((cfg['model'],cfg['model_reasoning_effort']),(model,effort))
                self.assertIn('not the main orchestrator',cfg['developer_instructions'])
                self.assertIn('Task ID',cfg['developer_instructions'])
                self.assertNotIn('danger-full-access',cfg.get('sandbox_mode',''))

    def test_preserves_six_column_reporting_and_marker(self):
        skill=(PACKAGE/'skills/deployment-token-report/SKILL.md').read_text()
        self.assertIn('| Agent | Quantity | Rollouts | Cached input | Input | Output |',skill)
        self.assertIn('codex-workflow-deployment-start:',self.policy)
        self.assertIn('Cached input is a subset of Input',self.policy)

    def test_instruction_lengths_stay_bounded(self):
        self.assertLess(len(self.policy.split()),1500)
        for role in (PACKAGE/'agents').glob('*.toml'):
            cfg=tomllib.loads(role.read_text())
            self.assertLess(len(cfg['developer_instructions'].split()),300,role.name)
        self.assertLess(len((PACKAGE/'operate/user_AGENTS.md').read_text().split()),160)

    def test_package_validates_and_version_matches(self):
        package=PackageLayout.resolve(PACKAGE)
        self.assertEqual(package.version,CURRENT_VERSION)
        self.assertIn('simple_executor',package.worker_names)


if __name__=='__main__':
    unittest.main()
