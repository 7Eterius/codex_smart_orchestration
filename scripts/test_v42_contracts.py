"""4.2 fact boundaries and scoped-review protocol; no live model invocation."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'codex_workflow'))
from runtime import work_contracts as w, review_rules as r


def transfer(**kw):
    value=dict(task='T',assignment='A2',from_owner='one',to_owner='two',from_role='investigator',
               to_role='routine_executor',purpose='implementation',risk='low',previous_work_stopped=True,
               candidate_held=False,authority_ref='owner/task',scope_ref='scope/v2',requirement_ref='requirements/v1',
               evidence_refs=['failure/first'],pending_gates=['independent-review'],failed_fixes=2,repair_rounds=1)
    return value|kw


def cap(**kw):
    return dict(domain='root-A/V2',evidence_ref='native/snapshot',observation_current=True,
                effective_limit_verified=True,native_limit=6,primary_included=True,
                owned_open_workers=2,other_occupants=0)|kw


def catalog():
    return dict(schema=1,rules=[dict(id='failure-masking',scopes=['src'],mistake='Failure is replaced with success.',
        fix='Preserve original failure.',references=['src/runner.py'],exceptions=['Explicit expected RED.'],
        severity='blocking',check='semantic',cases=[
            dict(id='bad',expected='violation',split='development',state='Returns zero after a failed check.'),
            dict(id='good',expected='compliant',split='development',state='Returns the original nonzero status.'),
            dict(id='neighbor',expected='compliant',split='holdout',state='Only renames a local variable.'),
            dict(id='missing',expected='unverified',split='holdout',state='No execution evidence available.'),
            dict(id='exception',expected='not_applicable',split='holdout',state='An isolated negative control intentionally expects failure.')])])


def predictions(cat):
    return dict(schema=1,catalog_digest=r.fingerprint(cat),model='test-fixture-not-model',effort='unknown',run_ref='unit-test',
                results=[dict(rule_id=rule['id'],case_id=c['id'],verdict=c['expected'],evidence='Synthetic answer-key fixture only')
                         for rule in cat['rules'] for c in rule['cases']])


class Transfers(unittest.TestCase):
    def test_investigator_source_implementation_needs_writer(self):
        self.assertEqual(w.transition(transfer(to_role='investigator'))['action'],'select_suitable_role')

    def test_tester_cannot_design_checks_even_in_artifact_directory(self):
        self.assertEqual(w.transition(transfer(to_role='tester',purpose='check_design'))['action'],'select_suitable_role')

    def test_tester_can_execute_approved_procedure(self):
        self.assertEqual(w.transition(transfer(to_role='tester',purpose='test_execution'))['action'],'transfer_ready_for_allocator')

    def test_same_native_owner_cannot_be_relabelled_in_prose(self):
        self.assertEqual(w.transition(transfer(to_owner='one'))['action'],'dispatch_named_role')

    def test_related_writer_context_reuse_remains_possible(self):
        out=w.transition(transfer(from_role='routine_executor',to_owner='one'))
        self.assertEqual(out['action'],'reuse_bounded_context')
        self.assertFalse(out['authorizes_writes'])

    def test_active_prior_owner_blocks_transfer(self):
        self.assertEqual(w.transition(transfer(previous_work_stopped=False))['action'],'wait_for_handover')

    def test_no_authority_is_not_an_automatic_grant(self):
        self.assertEqual(w.transition(transfer(authority_ref=None))['action'],'decision_needed')

    def test_hold_is_released_before_new_writes(self):
        self.assertEqual(w.transition(transfer(candidate_held=True))['action'],'release_hold_before_writes')

    def test_risk_reclassification_does_not_keep_luna_on_critical_guard(self):
        self.assertEqual(w.transition(transfer(risk='critical'))['action'],'select_suitable_role')
        self.assertEqual(w.transition(transfer(risk='critical',to_role='senior_executor'))['action'],'transfer_ready_for_allocator')

    def test_counters_evidence_and_pending_gates_survive(self):
        out=w.transition(transfer())
        self.assertEqual(out['failed_fixes'],2);self.assertEqual(out['repair_rounds'],1)
        self.assertEqual(out['pending_gates'],['independent-review']);self.assertFalse(out['accepted'])

    def test_same_reviewer_must_not_self_certify_new_independent_transfer(self):
        out=w.transition(transfer(from_role='reviewer',to_role='reviewer',to_owner='one',purpose='semantic_review'))
        self.assertEqual(out['action'],'independent_reviewer_required')

    def test_bad_fields_are_not_hidden_by_stopped_false(self):
        with self.assertRaises(ValueError):w.transition(transfer(previous_work_stopped=False,failed_fixes=True))

    def test_nonmutation(self):
        data=transfer(); before=copy.deepcopy(data); w.transition(data);self.assertEqual(data,before)

class Capacity(unittest.TestCase):
    def test_six_including_main_means_five_workers_not_six(self):
        self.assertEqual(w.capacity(cap())['max_new_workers'],3)

    def test_five_excluding_main_is_same_domain_capacity(self):
        self.assertEqual(w.capacity(cap(native_limit=5,primary_included=False))['max_new_workers'],3)

    def test_lower_native_cap_and_other_occupants_bind(self):
        self.assertEqual(w.capacity(cap(native_limit=4,other_occupants=1))['max_new_workers'],0)

    def test_smart_ceiling_stays_five_under_larger_native_limit(self):
        self.assertEqual(w.capacity(cap(native_limit=100,owned_open_workers=4))['max_new_workers'],1)

    def test_unknown_primary_inclusion_never_guessed(self):
        self.assertEqual(w.capacity(cap(primary_included=None))['action'],'inspect_native_capacity')

    def test_disk_cap_without_effective_backend_confirmation_is_insufficient(self):
        self.assertEqual(w.capacity(cap(effective_limit_verified=False))['max_new_workers'],0)

    def test_stale_snapshot_and_missing_occupancy_are_insufficient(self):
        for change in ({'observation_current':False},{'owned_open_workers':None},{'evidence_ref':None}):
            self.assertEqual(w.capacity(cap(**change))['action'],'inspect_native_capacity')

    def test_completion_alone_never_subtracts_open_count(self):
        self.assertEqual(w.capacity(cap(owned_open_workers=5))['max_new_workers'],0)

    def test_normalization_does_not_claim_authenticated_capacity(self):
        out=w.capacity(cap());self.assertFalse(out['native_capacity_verified']);self.assertFalse(out['authorizes_writes'])

class Rules(unittest.TestCase):
    def test_changed_and_impacted_consumers_both_select(self):
        self.assertEqual(len(r.select(catalog(),['docs/x'],['src/a.py'],True)['rules']),1)

    def test_known_unrelated_scope_avoids_context(self):
        self.assertEqual(r.select(catalog(),['docs/x'],[],True)['rules'],[])

    def test_unknown_impact_does_not_silently_omit_rules(self):
        self.assertEqual(len(r.select(catalog(),['docs/x'])['rules']),1)

    def test_scope_prefix_does_not_match_neighbor(self):
        self.assertEqual(r.select(catalog(),['src-other/a.py'],[],True)['rules'],[])

    def test_fixtures_not_loaded_into_normal_brief(self):
        self.assertNotIn('cases',r.select(catalog(),['src/a.py'],[],True)['rules'][0])

    def test_fixture_input_separates_expected_labels(self):
        cases=r.fixture_inputs(catalog(),'holdout')['cases']
        self.assertEqual(len(cases),3);self.assertTrue(all('expected' not in c for c in cases))

    def test_score_reports_holdout_missing_and_no_model_execution(self):
        cat=catalog();pred=predictions(cat);pred['results']=pred['results'][:2]
        out=r.score(cat,pred);self.assertEqual(out['missing'],3);self.assertFalse(out['complete'])
        self.assertFalse(out['model_executed']);self.assertFalse(out['accepted'])

    def test_changed_rule_or_case_invalidates_predictions(self):
        cat=catalog();pred=predictions(cat);cat['rules'][0]['fix']='Use explicit status.'
        with self.assertRaises(ValueError):r.score(cat,pred)

    def test_miss_and_false_alarm_are_distinct(self):
        cat=catalog();pred=predictions(cat)
        pred['results'][0]['verdict']='compliant';pred['results'][1]['verdict']='violation'
        out=r.score(cat,pred);self.assertEqual(out['counts']['missed_violations'],1)
        self.assertEqual(out['counts']['false_alarms'],1)

    def test_good_fixture_result_does_not_claim_model_qualification(self):
        cat=catalog();out=r.score(cat,predictions(cat))
        self.assertEqual(out['accuracy_on_supplied_predictions'],1);self.assertFalse(out['model_executed'])

    def test_duplicate_unknown_results_and_empty_evidence_fail(self):
        for change in ('duplicate','unknown','no-evidence'):
            cat=catalog();pred=predictions(cat)
            if change=='duplicate': pred['results'][1]=pred['results'][0]
            elif change=='unknown': pred['results'][0]['case_id']='invented'
            else: pred['results'][0]['evidence']=''
            with self.assertRaises(ValueError):r.score(cat,pred)

    def test_path_escape_and_boolean_schema_fail(self):
        with self.assertRaises(ValueError):r.select(catalog(),['../other'])
        cat=catalog();cat['schema']=True
        with self.assertRaises(ValueError):r.validate(cat)

    def test_single_outcome_examples_are_insufficient(self):
        cat=catalog();cat['rules'][0]['cases'][0]['expected']='compliant'
        with self.assertRaises(ValueError):r.validate(cat)

    def test_empty_predictions_not_zero_error_claim(self):
        cat=catalog();pred=predictions(cat);pred['results']=[]
        out=r.score(cat,pred);self.assertIsNone(out['accuracy_on_supplied_predictions']);self.assertEqual(out['missing'],5)

    def test_new_modules_cli_has_bounded_json_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'in.json';p.write_text('{"operation":"capacity","operation":"transition"}')
            self.assertEqual(w.main(['--input',str(p)]),2)

class CorrectionRegressions(unittest.TestCase):
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

if __name__=='__main__':unittest.main()
