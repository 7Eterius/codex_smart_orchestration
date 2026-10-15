"""Final review refinements: preserve prompt budgets and supervise startup failures."""
from pathlib import Path
import json
import subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='e96ad3bd5cbd368141f58d1940466b80fd27f578'
def change(path,old,new):
    p=ROOT/path;s=p.read_text();assert s.count(old)==1,(path,old[:90],s.count(old));p.write_text(s.replace(old,new))
def main():
    change('codex_workflow/smart_orchestration.md',
        'Optimize accepted quality, elapsed time and total model work, including context, failed attempts,\nverification and handoffs. One adaptive loop: understand, assign, execute, verify, accept. Replace\nrepetitive bookkeeping with existing tools, not a second orchestrator or mandatory ceremony.',
        'Optimize accepted quality, elapsed time and total work, including repairs and verification.\nUnderstand, assign, execute, verify, accept. Use existing tools, not another orchestrator.')
    change('codex_workflow/smart_orchestration.md',
        'Small, clear, low-risk work stays direct when Main has the context. A coherent implementation\nusually needs one owner, focused writer checks and only the independent gates actually required.\nDo not create Investigator, Tester and Reviewer merely to fill a pipeline. Optional helpers replace\nmanual work; native/CI receipts may already suffice. Plans name deliverables, not every click.',
        'Clear low-risk work stays direct when Main has context. Otherwise use one coherent owner,\nfocused checks and required independent gates, not an obligatory agent pipeline. Native/CI receipts\nmay replace optional helpers. Plans name deliverables, not clicks.')
    change('codex_workflow/smart_orchestration.md',
        'For long work keep one compact identity-bound checkpoint with accepted units, evidence, unresolved\nfindings, live process/resource owners and next action. Reconcile actual state after context loss;\ndo not redispatch accepted work, restart live suites or reset repair history. No mandatory ledger.',
        'Long-task checkpoints preserve identity, accepted work/evidence, findings, live owners and next\naction. Reconcile actual state after context loss; never redispatch accepted work, restart live\nsuites or reset repair history. No mandatory ledger.')
    change('codex_workflow/smart_orchestration.md',
        'Historical role tags and token volume do not prove actual duty. Read handoffs.md at material transfers.',
        'Role tags and token volume do not prove duty. Use handoffs.md at material transfers.')
    change('codex_workflow/standards.md',
        'For explicit reviewer evaluations, fixture-inputs --compact emits schema 2: one complete rule\nper batch and label-free cases referencing it. Legacy expanded inputs remain the default. Scope,\nreferences and exceptions travel with the rule. Predictions may specify split=development or\nsplit=holdout; completeness then concerns that split, not omitted intentional non-target cases.\nOmitting split still scores all cases. run_ref is retained; no result runs or qualifies a model.\nCatalog and prediction CLI reads are bounded at 4 MiB; smaller handoff inputs remain 64 KiB.',
        'Evaluation fixture-inputs --compact emits schema 2: complete rules once, label-free cases by\nreference. Expanded inputs remain default. Optional prediction split=development or split=holdout\nlimits completeness to that split; omission scores all cases. Results retain run_ref, not model\nqualification. Catalog/prediction CLI reads allow 4 MiB; handoffs stay at 64 KiB.')
    change('codex_workflow/runtime/verification_run.py',
        '        selector=selectors.DefaultSelector()\n        selector.register(process.stdout,selectors.EVENT_READ)\n        try:\n            while True:',
        '        selector=None\n        try:\n            selector=selectors.DefaultSelector()\n            selector.register(process.stdout,selectors.EVENT_READ)\n            while True:')
    change('codex_workflow/runtime/verification_run.py',
        '            selector.close(); process.stdout.close()',
        '            if selector is not None: selector.close()\n            process.stdout.close()')
    change('scripts/test_v421.py',"class CandidateReads(Fixture):",'''class StartupCleanup(Fixture):
    def test_selector_creation_failure_stops_started_child(self):
        with mock.patch.object(v.selectors,'DefaultSelector',side_effect=OSError('injected selector failure')):
            with mock.patch.object(v,'_stop',wraps=v._stop) as stop:
                with self.assertRaises(OSError):v.run(self.plan,self.evidence,True)
                stop.assert_called_once()
                self.assertIsNotNone(stop.call_args.args[0].returncode)

    def test_selector_registration_failure_stops_child_and_closes_selector(self):
        selector=mock.Mock();selector.register.side_effect=OSError('injected registration failure')
        with mock.patch.object(v.selectors,'DefaultSelector',return_value=selector):
            with mock.patch.object(v,'_stop',wraps=v._stop) as stop:
                with self.assertRaises(OSError):v.run(self.plan,self.evidence,True)
                stop.assert_called_once()
                self.assertIsNotNone(stop.call_args.args[0].returncode)
        selector.close.assert_called_once()

class CandidateReads(Fixture):''')
    change('docs/v4.2.1.md',
        '- Each completed command now gets a create-only private `.result.json` before a later command can',
        '- Selector initialization/registration errors now stop the already-created owned child instead\n  of leaving it unsupervised. Each completed command gets a create-only private `.result.json` before a later command can')
    paths=['codex_workflow/operate/user_AGENTS.md','codex_workflow/smart_orchestration.md','codex_workflow/standards.md']
    counts={p:dict(before=len(subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT).decode().split()),
                   after=len((ROOT/p).read_text().split())) for p in paths}
    print(json.dumps(dict(word_counts=counts),indent=2))
    assert counts[paths[1]]['after']<1200
    assert counts[paths[2]]['after']<600
if __name__=='__main__':main()
