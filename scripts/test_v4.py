"""4.0 package integration: methods do not replace model, scope or evidence gates."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'codex_workflow'
sys.path.insert(0,str(PACKAGE))
from runtime import allocation as a, delivery as d, boundary as b, smart_install as install
from runtime.layout import PackageLayout, BUILTIN_WORKERS
from runtime.smart_config import bootstrap
from test_allocation import task, scope, thread, observation, request
from test_delivery import task as practice_task, spend, repair

class V4Integration(unittest.TestCase):
    def test_method_choice_does_not_upgrade_ordinary_model(self):
        self.assertEqual(a.classify(task())['owner'],'routine_executor')
        self.assertEqual(d.practices(practice_task())['tdd'],'red_green')
        self.assertEqual(len(BUILTIN_WORKERS),11)
        self.assertEqual(d.OWNERS,a.ROLES|{'main'})

    def test_budget_advice_cannot_bypass_scope_conflict(self):
        self.assertEqual(d.budget(spend())['max_new_workers'],5)
        result=a.next_action(observation(thread()),request(scope=scope('src/a')))
        self.assertEqual(result['reason'],'scope_or_resource_conflict')

    def test_worktree_advice_is_not_shared_resource_isolation(self):
        self.assertEqual(d.practices(practice_task(size='large',isolated=True))['workspace'],'reuse')
        obs=observation(thread(scope=scope(resource_writes=['database/shared'])))
        req=request(scope=scope('src/b',workspace='/other',resource_writes=['database/shared']))
        self.assertEqual(a.next_action(obs,req)['reason'],'scope_or_resource_conflict')

    def test_exhausted_repair_budget_cannot_satisfy_independent_gate(self):
        self.assertFalse(d.recovery(repair(budget_exhausted=True))['accepted'])
        record=dict(schema=1,unit='U',attempt='A',contract='R',candidate='C',target='T',
                    primary='main',writer='main',reviewer='independent',hold='held',
                    gates={'semantic':True})
        verdict={key:record[key] for key in ('unit','attempt','contract','candidate','target','reviewer')}
        verdict.update(artifact='review/report',gates={'semantic':{'status':'unverified','evidence':'review/pending'}})
        self.assertFalse(b.check(record,'accept','main',verdict)['allowed'])

    def test_new_guides_and_helper_are_installed_and_integrity_checked(self):
        extras={'planning.md','debugging.md','branches.md','economics.md','runtime/delivery.py',
                'third_party/Superpowers-LICENSE.txt'}
        package=PackageLayout.resolve(PACKAGE)
        self.assertEqual(package.version,'4.0.1')
        self.assertTrue(extras <= {p.relative_to(PACKAGE).as_posix() for p in package.files})
        with tempfile.TemporaryDirectory() as temp:
            home=Path(temp).resolve()
            (home/'config.toml').write_text('model="gpt-6-luna"\nmodel_reasoning_effort="max"\n[agents]\nmax_threads=5\n')
            plan,before=install.prepare(PACKAGE,home); install.apply_plan(plan,before,home)
            self.assertTrue(install.status(home)['disk_ok'])
            for rel in extras:self.assertEqual((home/'codex_workflow'/rel).read_bytes(),(PACKAGE/rel).read_bytes())
            target=home/'codex_workflow/debugging.md';target.write_text(target.read_text()+'\nlocal change\n')
            self.assertFalse(install.status(home)['disk_ok'])

    def test_short_bootstrap_and_lazy_guide_budgets(self):
        self.assertLess(len(bootstrap(Path('/example')).split()),200)
        for name in ('planning.md','debugging.md','branches.md','economics.md'):
            self.assertLess(len((PACKAGE/name).read_text().split()),650,name)
        text=(PACKAGE/'smart_orchestration.md').read_text()
        for name in ('planning.md','debugging.md','branches.md','economics.md','testing.md'):
            self.assertIn(name,text)
        self.assertIn('only when relevant',text)

    def test_installed_runtime_helpers_stay_non_network_and_non_scheduler(self):
        import ast
        tree=ast.parse((PACKAGE/'runtime/delivery.py').read_text())
        imported={node.names[0].name for node in ast.walk(tree) if isinstance(node,ast.Import)}
        self.assertTrue(imported <= {'argparse','json','math','sys','os','stat'},imported)
        self.assertFalse(d.budget(spend())['authorizes_writes'])

    def test_license_and_pinned_source_provenance_are_present(self):
        self.assertIn('Copyright (c) 2025 Jesse Vincent',
                      (PACKAGE/'third_party/Superpowers-LICENSE.txt').read_text())
        text=(ROOT/'docs/v4.0.md').read_text()
        self.assertIn('5fd93af4cd0c623e020d0cc7e9ce178b4ac1f70f',text)
        self.assertIn('not native agent compliance',text)

    def test_source_links_are_resolvable(self):
        for p in (ROOT/'README.md',ROOT/'docs/v4.0.md'):
            for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
                if not target.startswith(('http:','https:','#')):
                    self.assertTrue((p.parent/target.split('#')[0]).is_file(),(p,target))

    def test_huge_integer_is_normalized_as_validation_error(self):
        limit=dict(unit='tokens',maximum=10,spent=10**1000,committed=0,next_estimate=1,observation_current=True)
        with self.assertRaises(d.DeliveryError):d.budget(spend(limit=limit))

    def test_limits_cannot_be_hidden_by_unknown_capacity(self):
        limit=dict(unit='credits',maximum=1,spent=1,committed=0,next_estimate=1,observation_current=True)
        self.assertEqual(d.budget(spend(available_slots=None,limit=limit))['action'],'checkpoint')

    def test_required_tdd_stays_blocked_after_ambiguous_work(self):
        result=d.practices(practice_task(clarity='ambiguous',testable=False,tdd_required=True))
        self.assertEqual(result['tdd'],'blocked')
        self.assertEqual(result['brainstorm'],'targeted')
        self.assertFalse(result['authorizes_writes'])

if __name__=='__main__':unittest.main()
