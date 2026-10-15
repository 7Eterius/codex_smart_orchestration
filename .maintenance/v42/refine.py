"""Resolve integration findings on the prepared candidate, before full validation."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def change(path,old,new):
    p=ROOT/path;s=p.read_text()
    assert s.count(old)==1,(path,s.count(old),old[:80])
    p.write_text(s.replace(old,new))

def main():
    change('codex_workflow/smart_orchestration.md',
           'Use domain-appropriate evidence for non-code work.',
           'For non-code work use domain-appropriate evidence, not invented code tests.')
    for role,guide in [('tester','testing.md'),('reviewer','verification.md'),('senior_reviewer','verification.md')]:
        change(f'codex_workflow/agents/{role}.toml',
               '(default ~/.codex/codex_workflow)',f'(default ~/.codex/codex_workflow/{guide})')
    change('codex_workflow/runtime/work_contracts.py',
           "'requirement_ref','evidence_refs','pending_gates','failed_fixes','repair_rounds'})",
           "'requirement_ref','evidence_refs','pending_gates','failed_fixes','repair_rounds'},\n         {'review_baseline_ref'})")
    change('codex_workflow/runtime/work_contracts.py',
           "    for k in ('failed_fixes','repair_rounds'): count(facts[k])\n    payload =",
           "    for k in ('failed_fixes','repair_rounds'): count(facts[k])\n    if 'review_baseline_ref' in facts:\n        text(facts['review_baseline_ref'])\n        if (facts['purpose']!='semantic_review' or facts['from_role'] not in REVIEWERS\n                or facts['from_role']!=facts['to_role'] or facts['from_owner']!=facts['to_owner']):\n            raise ContractError('Review baseline is only for the same retained reviewer')\n    payload =")
    change('codex_workflow/runtime/work_contracts.py',
           "    if same and facts['purpose']=='semantic_review':\n        return result('independent_reviewer_required', **payload)",
           "    if same and facts['purpose']=='semantic_review':\n        if 'review_baseline_ref' not in facts:\n            return result('independent_reviewer_required', **payload)\n        payload['review_baseline_ref']=facts['review_baseline_ref']\n        if not facts['candidate_held']:\n            return result('hold_candidate_before_review', **payload)")
    change('codex_workflow/runtime/review_rules.py',
           "if verdict=='violation' and target['expected']=='compliant':",
           "if verdict=='violation' and target['expected'] in {'compliant','not_applicable'}:")
    change('codex_workflow/runtime/review_rules.py',
           "if verdict=='compliant' and target['expected']=='violation':",
           "if verdict in {'compliant','not_applicable'} and target['expected']=='violation':")
    change('scripts/test_v42_contracts.py',"if __name__=='__main__':unittest.main()",'''class CorrectionRegressions(unittest.TestCase):
    def test_same_qualified_reviewer_reuses_recorded_held_baseline(self):
        data=transfer(from_role='reviewer',to_role='reviewer',to_owner='one',
                      purpose='semantic_review',candidate_held=True,review_baseline_ref='review/C1')
        out=w.transition(data)
        self.assertEqual(out['action'],'reuse_bounded_context')
        self.assertEqual(out['review_baseline_ref'],'review/C1')
        self.assertFalse(out['accepted'])

    def test_review_baseline_does_not_waive_hold(self):
        out=w.transition(transfer(from_role='reviewer',to_role='reviewer',to_owner='one',
                                 purpose='semantic_review',review_baseline_ref='review/C1'))
        self.assertEqual(out['action'],'hold_candidate_before_review')

    def test_review_baseline_cannot_retag_writer_or_change_reviewer(self):
        for overrides in ({'from_role':'routine_executor'}, {'to_owner':'new'}, {'purpose':'implementation'}):
            data=transfer(from_role='reviewer',to_role='reviewer',to_owner='one',
                          purpose='semantic_review',candidate_held=True,review_baseline_ref='review/C1')
            data.update(overrides)
            with self.assertRaises(ValueError):w.transition(data)

    def test_not_applicable_can_be_a_miss_or_false_alarm(self):
        cat=catalog();pred=predictions(cat)
        pred['results'][0]['verdict']='not_applicable'
        pred['results'][4]['verdict']='violation'
        out=r.score(cat,pred)
        self.assertEqual(out['counts']['missed_violations'],1)
        self.assertEqual(out['counts']['false_alarms'],1)
        self.assertLess(out['accuracy_on_supplied_predictions'],1)

if __name__=='__main__':unittest.main()''')
    path=ROOT/'docs/v4.2.md'
    path.write_text(path.read_text()+'''\n### Correction-review continuity\n\nThe transfer adviser accepts optional review_baseline_ref only for a retained same-role reviewer\nchecking a held candidate. It preserves that reference without treating it as authenticated\nindependence or acceptance. A missing baseline, changed reviewer/role or released hold cannot\nuse this shortcut; the existing allocator and review contract remain binding. Fixture scoring\ncounts an incorrect not_applicable response to a true violation as a miss, and a violation\nreported for a labelled exception as a false alarm. Abstentions remain separate.\n''')

if __name__=='__main__':main()
