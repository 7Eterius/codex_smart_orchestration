"""Executable decision scenarios, not tests of native model compliance or savings."""
from __future__ import annotations
import copy
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PACKAGE = Path(__file__).resolve().parents[1] / 'codex_workflow'
sys.path.insert(0, str(PACKAGE))
from runtime import delivery as d


def task(**kw):
    result = dict(domain='code', kind='feature', size='medium', clarity='clear', risk='low',
                  behavior_change=True, testable=True, isolated=False, long_running=False)
    result.update(kw)
    return result


def spend(**kw):
    result = dict(quota='available', requested_workers=5, available_slots=5,
                  independent_ready=5, mandatory_gates_pending=True)
    result.update(kw)
    return result


def repair(**kw):
    result = dict(task='T1', defect='D1', previous_owner='routine_executor', failed_fixes=1,
                  repair_rounds=1, same_defect_no_progress=False, new_evidence=True,
                  blocking=True, authority_needed=False, budget_exhausted=False)
    result.update(kw)
    return result


class PracticeDecisions(unittest.TestCase):
    def test_clear_small_copy_change_is_direct_without_brainstorm_or_tdd(self):
        result = d.practices(task(kind='mechanical', size='small', behavior_change=False))
        self.assertEqual((result['brainstorm'], result['plan'], result['tdd']),
                         ('none', 'direct', 'alternative'))
        self.assertEqual(result['workspace'], 'in_place')

    def test_clear_new_feature_does_not_require_another_brainstorm(self):
        self.assertEqual(d.practices(task())['brainstorm'], 'none')

    def test_genuinely_ambiguous_work_gets_targeted_brainstorm(self):
        result = d.practices(task(clarity='ambiguous'))
        self.assertEqual(result['brainstorm'], 'targeted')
        self.assertEqual(result['action'], 'resolve_requirements')

    def test_proportionate_plans(self):
        for size, expected in [('small', 'direct'), ('medium', 'lean'), ('large', 'durable')]:
            self.assertEqual(d.practices(task(size=size))['plan'], expected)

    def test_small_high_risk_change_does_not_skip_plan(self):
        for risk in ('material', 'critical'):
            self.assertEqual(d.practices(task(size='small', risk=risk))['plan'], 'lean')

    def test_long_task_uses_durable_checkpoint_not_new_database(self):
        self.assertEqual(d.practices(task(size='small', long_running=True))['plan'], 'durable')

    def test_reproducible_behavior_bug_uses_debugging_and_red_green(self):
        result = d.practices(task(kind='bug', size='small'))
        self.assertEqual(result['tdd'], 'red_green')
        self.assertIn('debugging.md', result['guides'])

    def test_mechanical_label_cannot_bypass_behavior_test(self):
        self.assertEqual(d.practices(task(kind='mechanical'))['tdd'], 'red_green')

    def test_pure_refactor_characterizes_existing_behavior(self):
        self.assertEqual(d.practices(task(kind='refactor', behavior_change=False))['tdd'],
                         'characterize')

    def test_untestable_change_gets_alternative_evidence_not_fake_red(self):
        result = d.practices(task(testable=False))
        self.assertEqual(result['tdd'], 'alternative')
        self.assertIn('testing.md', result['guides'])

    def test_explicit_tdd_gate_cannot_be_waived(self):
        result = d.practices(task(testable=False, tdd_required=True))
        self.assertEqual((result['action'], result['tdd']), ('resolve_test_strategy', 'blocked'))

    def test_explicit_tdd_is_honored_for_testable_code(self):
        self.assertEqual(d.practices(task(behavior_change=False, tdd_required=True))['tdd'],
                         'red_green')

    def test_noncode_has_domain_evidence_not_code_tests(self):
        for kind in ('research', 'writing', 'operations'):
            result = d.practices(task(domain='noncode', kind=kind, behavior_change=False))
            self.assertEqual(result['tdd'], 'not_applicable')
            self.assertNotIn('testing.md', result['guides'])
            self.assertEqual(result['workspace'], 'none')

    def test_noncode_explicit_tdd_conflict_is_not_silently_waived(self):
        result = d.practices(task(domain='noncode', kind='writing', behavior_change=False,
                                 tdd_required=True))
        self.assertEqual(result['action'], 'resolve_test_strategy')

    def test_existing_isolation_is_reused(self):
        self.assertEqual(d.practices(task(size='large', isolated=True))['workspace'], 'reuse')

    def test_large_features_consider_isolation_without_authorizing_creation(self):
        result = d.practices(task(size='large'))
        self.assertEqual(result['workspace'], 'consider_isolation')
        self.assertIn('branches.md', result['guides'])
        self.assertIs(result['authorizes_writes'], False)

    def test_all_decisions_are_nonmutating_deterministic_and_bounded(self):
        for size, clarity, risk in itertools.product(('small', 'medium', 'large'),
                                                     ('clear', 'ambiguous'),
                                                     ('low', 'material', 'critical')):
            facts = task(size=size, clarity=clarity, risk=risk)
            before = copy.deepcopy(facts)
            result = d.practices(facts)
            self.assertEqual(result, d.practices(facts))
            self.assertEqual(facts, before)
            self.assertEqual(len(result['guides']), len(set(result['guides'])))

    def test_invalid_task_fields_types_and_missing_keys_fail_closed(self):
        for override in ({'domain':'maybe'}, {'kind':'unknown'}, {'size':[]}, {'clarity':True},
                         {'risk':'cheap'}, {'testable':1}, {'isolated':'yes'},
                         {'long_running':None}, {'tdd_required':0}, {'extra':True}):
            with self.subTest(override=override), self.assertRaises(d.DeliveryError):
                d.practices(task(**override))
        facts = task(); del facts['risk']
        with self.assertRaises(d.DeliveryError): d.practices(facts)


class BudgetDecisions(unittest.TestCase):
    def test_five_is_ceiling_not_target(self):
        self.assertEqual(d.budget(spend(independent_ready=2))['max_new_workers'], 2)

    def test_available_capacity_remains_binding(self):
        self.assertEqual(d.budget(spend(available_slots=1))['max_new_workers'], 1)

    def test_unknown_capacity_does_not_invent_slots(self):
        result = d.budget(spend(available_slots=None))
        self.assertEqual((result['action'], result['max_new_workers']), ('inspect_capacity', 0))

    def test_low_quota_serializes_without_waiving_gates(self):
        result = d.budget(spend(quota='low'))
        self.assertEqual(result['max_new_workers'], 1)
        self.assertTrue(result['mandatory_gates_pending'])

    def test_unknown_quota_does_not_require_a_usage_audit(self):
        result = d.budget(spend(quota='unknown'))
        self.assertEqual(result['action'], 'proceed_bounded')
        self.assertEqual(result['max_new_workers'], 2)

    def test_exhausted_quota_checkpoints_instead_of_downgrading_quality(self):
        result = d.budget(spend(quota='exhausted'))
        self.assertEqual((result['action'], result['max_new_workers']), ('checkpoint', 0))
        self.assertTrue(result['mandatory_gates_pending'])

    def test_explicit_envelope_accounts_for_committed_work(self):
        limit = dict(unit='tokens', maximum=1000, spent=400, committed=600,
                     next_estimate=1, observation_current=True)
        self.assertEqual(d.budget(spend(limit=limit))['action'], 'checkpoint')

    def test_next_batch_must_fit_remaining_budget(self):
        limit = dict(unit='credits', maximum=10, spent=5, committed=2,
                     next_estimate=4, observation_current=True)
        self.assertEqual(d.budget(spend(limit=limit))['action'], 'replan_budget')
        limit['next_estimate'] = 3
        self.assertEqual(d.budget(spend(limit=limit))['action'], 'proceed_bounded')

    def test_unknown_estimate_does_not_certify_explicit_budget(self):
        limit = dict(unit='seconds', maximum=100, spent=10, committed=0,
                     next_estimate=None, observation_current=True)
        self.assertEqual(d.budget(spend(limit=limit))['action'], 'inspect_budget')

    def test_stale_explicit_budget_observation_is_not_spend_permission(self):
        limit = dict(unit='requests', maximum=10, spent=1, committed=0,
                     next_estimate=1, observation_current=False)
        self.assertEqual(d.budget(spend(limit=limit))['action'], 'inspect_budget')

    def test_absent_budget_does_not_imply_zero_cost(self):
        self.assertFalse(d.budget(spend())['cost_verified'])

    def test_no_work_or_no_request_never_spawns_workers(self):
        for override in ({'requested_workers':0}, {'independent_ready':0}, {'available_slots':0}):
            self.assertEqual(d.budget(spend(**override))['max_new_workers'], 0)

    def test_quota_and_capacity_combinations_never_exceed_supplied_bounds(self):
        for quota, requested, slots, ready in itertools.product(
                ('available','unknown','low','exhausted'), range(6), range(7), range(7)):
            result = d.budget(spend(quota=quota, requested_workers=requested,
                                   available_slots=slots, independent_ready=ready))
            self.assertLessEqual(result['max_new_workers'], min(requested, slots, ready, 5))
            self.assertFalse(result['authorizes_writes'])
            self.assertTrue(result['mandatory_gates_pending'])

    def test_invalid_limits_are_validated_even_when_quota_exhausted(self):
        for value in (True, -1, math.nan, math.inf, '5'):
            limit = dict(unit='tokens', maximum=100, spent=value, committed=0,
                         next_estimate=1, observation_current=True)
            with self.subTest(value=value), self.assertRaises(d.DeliveryError):
                d.budget(spend(quota='exhausted', limit=limit))

    def test_no_implicit_unit_conversion(self):
        limit = dict(unit='subscription_percent_from_api_tokens', maximum=100, spent=1,
                     committed=0, next_estimate=1, observation_current=True)
        with self.assertRaises(d.DeliveryError): d.budget(spend(limit=limit))

    def test_worker_counts_are_strict_and_bounded(self):
        for override in ({'requested_workers':6}, {'requested_workers':True},
                         {'available_slots':-1}, {'independent_ready':'2'},
                         {'quota':'unlimited'}, {'mandatory_gates_pending':1}):
            with self.subTest(override=override), self.assertRaises(d.DeliveryError):
                d.budget(spend(**override))


class RecoveryDecisions(unittest.TestCase):
    def test_three_failed_fixes_trip_breaker_even_with_new_model_and_evidence(self):
        for owner in ('routine_executor','default_executor','deep_executor','senior_executor'):
            result = d.recovery(repair(previous_owner=owner, failed_fixes=3))
            self.assertEqual(result['action'], 'replan')
            self.assertFalse(result['may_patch'])
            self.assertTrue(result['blocking_unresolved'])

    def test_three_repair_rounds_trip_breaker_even_if_each_has_some_progress(self):
        self.assertEqual(d.recovery(repair(repair_rounds=3))['action'], 'replan')

    def test_same_defect_no_progress_escalates_earlier_than_round_cap(self):
        result = d.recovery(repair(same_defect_no_progress=True))
        self.assertEqual(result['action'], 'escalate')
        self.assertFalse(result['may_patch'])

    def test_senior_stall_requires_replanning(self):
        result = d.recovery(repair(previous_owner='senior_executor', same_defect_no_progress=True))
        self.assertEqual(result['action'], 'replan')

    def test_no_new_evidence_requires_investigation_not_speculative_fix(self):
        self.assertEqual(d.recovery(repair(new_evidence=False))['action'], 'investigate')

    def test_new_evidence_under_budget_allows_one_bounded_fix(self):
        result = d.recovery(repair())
        self.assertEqual(result['action'], 'bounded_fix')
        self.assertTrue(result['may_patch'])
        self.assertTrue(result['blocking_unresolved'])
        self.assertFalse(result['accepted'])

    def test_optional_taste_does_not_enter_fix_loop(self):
        result = d.recovery(repair(blocking=False))
        self.assertEqual(result['action'], 'record_nonblocking')
        self.assertFalse(result['may_patch'])

    def test_budget_exhaustion_never_parks_blocker_as_success(self):
        result = d.recovery(repair(budget_exhausted=True))
        self.assertEqual(result['action'], 'checkpoint')
        self.assertTrue(result['blocking_unresolved'])
        self.assertFalse(result['accepted'])

    def test_authority_boundary_precedes_another_patch(self):
        self.assertEqual(d.recovery(repair(authority_needed=True))['action'], 'decision_needed')

    def test_identity_and_counts_are_returned_for_carryover(self):
        result = d.recovery(repair(task='work-2', defect='hydrate-flash', repair_rounds=2))
        self.assertEqual((result['task'], result['defect'], result['repair_rounds']),
                         ('work-2','hydrate-flash',2))

    def test_worker_switch_cannot_reset_counts_inside_decision(self):
        for owner in ('routine_executor','default_executor','deep_executor'):
            result = d.recovery(repair(previous_owner=owner, failed_fixes=3, repair_rounds=3))
            self.assertFalse(result['may_patch'])
            self.assertEqual(result['failed_fixes'], 3)

    def test_invalid_recovery_facts_fail_before_short_circuit(self):
        for override in ({'task':''}, {'defect':'D\n1'}, {'previous_owner':'cheapest'},
                         {'failed_fixes':True}, {'repair_rounds':-1}, {'blocking':'no'}):
            facts = repair(budget_exhausted=True, **override)
            with self.subTest(override=override), self.assertRaises(d.DeliveryError):
                d.recovery(facts)

    def test_nonmutation(self):
        for fn, facts in ((d.practices,task()), (d.budget,spend()), (d.recovery,repair())):
            before = copy.deepcopy(facts); fn(facts)
            self.assertEqual(facts,before)


class CliContract(unittest.TestCase):
    def run_cli(self, raw):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'input.json'; path.write_text(raw)
            before = path.read_bytes()
            ran = subprocess.run([sys.executable,'-B',d.__file__,'--input',str(path)],
                                 text=True,capture_output=True,timeout=10)
            self.assertEqual(path.read_bytes(),before)
            return ran

    def test_real_cli_prepare(self):
        ran = self.run_cli(json.dumps({'operation':'prepare','facts':task()}))
        self.assertEqual(ran.returncode,0,ran.stderr)
        self.assertEqual(json.loads(ran.stdout)['tdd'],'red_green')

    def test_real_cli_stop_is_nonzero_and_keeps_blocker(self):
        ran = self.run_cli(json.dumps({'operation':'recover','facts':repair(failed_fixes=3)}))
        self.assertEqual(ran.returncode,1,ran.stderr)
        self.assertTrue(json.loads(ran.stdout)['blocking_unresolved'])

    def test_unknown_operation_duplicate_keys_and_nonfinite_are_errors(self):
        for raw in ('{"operation":"deploy","facts":{}}',
                    '{"operation":"budget","operation":"recover","facts":{}}',
                    '{"operation":"budget","facts":{"spent":NaN}}'):
            ran = self.run_cli(raw)
            self.assertEqual(ran.returncode,2)
            self.assertIn('error',json.loads(ran.stderr))

    def test_oversized_and_deep_input_is_bounded_error(self):
        for raw in (' '*65537,'['*2000+'0'+']'*2000):
            self.assertEqual(self.run_cli(raw).returncode,2)

    def test_symlink_input_is_not_read(self):
        with tempfile.TemporaryDirectory() as temp:
            real = Path(temp)/'real.json'; real.write_text('{}')
            alias = Path(temp)/'alias.json'; alias.symlink_to(real)
            ran = subprocess.run([sys.executable,'-B',d.__file__,'--input',str(alias)],
                                 capture_output=True,text=True,timeout=10)
            self.assertEqual(ran.returncode,2)


if __name__ == '__main__': unittest.main()
