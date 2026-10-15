"""Installed integration and source budgets. No native model benchmark."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest
ROOT=Path(__file__).resolve().parents[1];PACKAGE=ROOT/'codex_workflow'
sys.path.insert(0,str(PACKAGE))
from runtime import smart_install as install
from runtime.layout import PackageLayout,BUILTIN_WORKERS
from runtime.smart_config import bootstrap
from runtime import work_contracts as w

class Package42(unittest.TestCase):
    def test_current_version_and_eleven_roles(self):
        self.assertEqual(PackageLayout.resolve(PACKAGE).version,'4.2.1')
        self.assertEqual(len(BUILTIN_WORKERS),11)
        self.assertEqual(w.ROLES,BUILTIN_WORKERS|{'main'})

    def test_new_runtime_files_are_declared_but_collector_is_not_installed(self):
        names={str(p.relative_to(PACKAGE)) for p in PackageLayout.resolve(PACKAGE).files}
        for rel in ('runtime/work_contracts.py','runtime/verification_run.py','runtime/review_rules.py','handoffs.md','receipts.md','standards.md'):
            self.assertIn(rel,names)
        self.assertFalse(any('stats' in n for n in names))

    def test_guide_and_bootstrap_budgets(self):
        self.assertLessEqual(len(bootstrap(Path('/example')).split()),174)
        for name in ('handoffs.md','receipts.md','standards.md'):
            self.assertLess(len((PACKAGE/name).read_text().split()),600,name)
        main=(PACKAGE/'smart_orchestration.md').read_text()
        for name in ('handoffs.md','receipts.md','standards.md'):self.assertIn(name,main)

    def test_install_preserves_main_and_cap_no_auto_hooks_or_project_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp).resolve();config='model="owner"\nmodel_reasoning_effort="low"\n[agents]\nmax_threads=3\n'
            (home/'config.toml').write_text(config)
            plan,before=install.prepare(PACKAGE,home);install.apply_plan(plan,before,home)
            after=tomllib.loads((home/'config.toml').read_text())
            self.assertEqual(after['model'],'owner');self.assertEqual(after['agents']['max_threads'],3)
            self.assertNotIn('hooks',after)
            self.assertTrue(install.status(home)['disk_ok'])
            self.assertEqual(install.prepare(PACKAGE,home)[0].mutations,[])
            self.assertFalse((home/'tools/stats').exists())
            self.assertTrue((home/'codex_workflow/runtime/verification_run.py').is_file())

    def test_no_private_audit_corpus_is_published(self):
        for path in [PACKAGE/'smart_orchestration.md',ROOT/'docs/v4.2.md',ROOT/'examples/review/rules.json']:
            text=path.read_text()
            self.assertNotIn('/Users/ilyamilashchenko',text)
            self.assertNotIn('session-968709e19b96a5',text)
        self.assertFalse((ROOT/'findings.PRIVATE.md').exists())

    def test_cli_examples_catalog_and_packet_parse_without_network(self):
        cmd=[sys.executable,'-B',str(PACKAGE/'runtime/review_rules.py'),'--catalog',str(ROOT/'examples/review/rules.json'),
             'select','--changed','src/check.py','--impact-known']
        ran=subprocess.run(cmd,capture_output=True,text=True,timeout=10)
        self.assertEqual(ran.returncode,0,ran.stderr);self.assertEqual(len(json.loads(ran.stdout)['rules']),1)

    def test_standalone_collector_version_and_cli(self):
        module=ROOT/'tools/stats/smart_weekly_stats.py'
        self.assertIn("VERSION = '1.2.1'",module.read_text())
        ran=subprocess.run([sys.executable,'-B',str(module),'--help'],capture_output=True,text=True,timeout=10)
        self.assertEqual(ran.returncode,0,ran.stderr)

if __name__=='__main__':unittest.main()
