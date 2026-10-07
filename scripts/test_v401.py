"""4.0.1 boundary regressions. These test source behavior, not live agents."""
from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'codex_workflow'))
from runtime import delivery as d

BASE = '332da7c08adfce2ac4d24d8a4a9a69dae3ebe017'


def budget(**changes):
    facts = dict(quota='available', requested_workers=5, available_slots=5,
                 independent_ready=5, mandatory_gates_pending=True)
    facts.update(changes)
    return facts


def limit(**changes):
    facts = dict(unit='credits', maximum=0.3, spent=0.1, committed=0,
                 next_estimate=0.2, observation_current=True)
    facts.update(changes)
    return facts


def repair(**changes):
    facts = dict(task='T1', defect='D1', previous_owner='routine_executor',
                 failed_fixes=3, repair_rounds=3, same_defect_no_progress=False,
                 new_evidence=True, blocking=True, authority_needed=False,
                 budget_exhausted=False)
    facts.update(changes)
    return facts


def replan(**changes):
    facts = dict(task='T1', defect='D1', decision_ref='notes/T1#new-cause',
                 failed_fixes=3, repair_rounds=3, attempt_limit=1)
    facts.update(changes)
    return facts


def preparation(**changes):
    facts = dict(domain='code', kind='research', size='large', clarity='clear',
                 risk='low', behavior_change=False, testable=True,
                 isolated=True, long_running=False)
    facts.update(changes)
    return facts


class BudgetRegressions(unittest.TestCase):
    def test_exact_decimal_fit_is_not_a_false_budget_block(self):
        for values in (limit(), limit(maximum=0.6, spent=0.2, committed=0.1, next_estimate=0.3)):
            self.assertEqual(d.budget(budget(limit=values))['action'], 'proceed_bounded')

    def test_small_real_overspend_is_not_lost_to_binary_rounding(self):
        facts = budget(limit=limit(maximum=1, spent=1e-18, next_estimate=1))
        self.assertEqual(d.budget(facts)['action'], 'replan_budget')

    def test_integer_boundary_and_exhaustion_are_unchanged(self):
        facts = budget(limit=limit(unit='tokens', maximum=1000, spent=400,
                                  committed=599, next_estimate=1))
        self.assertEqual(d.budget(facts)['action'], 'proceed_bounded')
        facts['limit']['committed'] = 600
        self.assertEqual(d.budget(facts)['action'], 'checkpoint')

    def test_low_quota_does_not_add_to_an_existing_worker(self):
        result = d.budget(budget(quota='low', open_workers=1))
        self.assertEqual(result['max_new_workers'], 0)
        self.assertEqual(result['limit_scope'], 'total_open_workers')
        self.assertTrue(result['mandatory_gates_pending'])

    def test_unknown_quota_accounts_for_existing_workers(self):
        self.assertEqual(d.budget(budget(quota='unknown', open_workers=1))['max_new_workers'], 1)

    def test_five_open_workers_never_get_another_batch(self):
        self.assertEqual(d.budget(budget(open_workers=5))['max_new_workers'], 0)
        self.assertEqual(d.budget(budget(open_workers=4))['max_new_workers'], 1)

    def test_legacy_input_explicitly_reports_batch_only_scope(self):
        result = d.budget(budget())
        self.assertEqual(result['max_new_workers'], 5)
        self.assertEqual(result['limit_scope'], 'new_batch_only')
        self.assertIsNone(result['open_workers'])

    def test_explicit_unknown_open_count_requests_inspection(self):
        result = d.budget(budget(open_workers=None))
        self.assertEqual((result['action'], result['max_new_workers']), ('inspect_capacity', 0))

    def test_invalid_open_counts_fail_even_when_quota_exhausted(self):
        for value in (True, -1, 129, 1.5, '1'):
            with self.subTest(value=value), self.assertRaises(d.DeliveryError):
                d.budget(budget(quota='exhausted', open_workers=value))

    def test_combined_old_and_new_workers_obey_quota_ceiling(self):
        for quota, ceiling in (('available', 5), ('unknown', 2), ('low', 1)):
            for opened, slots, ready in itertools.product(range(7), range(6), range(6)):
                result = d.budget(budget(quota=quota, open_workers=opened,
                                         available_slots=slots, independent_ready=ready))
                self.assertLessEqual(result['max_new_workers'], min(slots, ready, max(0, ceiling-opened)))
                self.assertFalse(result['authorizes_writes'])


class RecoveryRegressions(unittest.TestCase):
    def test_breaker_without_new_plan_remains_closed(self):
        self.assertEqual(d.recovery(repair())['action'], 'replan')

    def test_recorded_replan_resumes_without_resetting_cumulative_counts(self):
        result = d.recovery(repair(replan=replan()))
        self.assertEqual(result['action'], 'bounded_fix')
        self.assertEqual((result['failed_fixes'], result['repair_rounds']), (3, 3))
        self.assertEqual(result['remaining_attempts'], 1)
        self.assertEqual(result['replan_ref'], 'notes/T1#new-cause')
        self.assertTrue(result['blocking_unresolved'])
        self.assertFalse(result['accepted'])
        self.assertFalse(result['authorizes_writes'])

    def test_one_new_attempt_exhausts_one_attempt_replan(self):
        for counters in ({'failed_fixes':4}, {'repair_rounds':4}):
            self.assertEqual(d.recovery(repair(replan=replan(), **counters))['action'], 'replan')

    def test_model_switch_does_not_renew_replan_budget(self):
        for owner in ('routine_executor', 'default_executor', 'deep_executor', 'senior_executor'):
            result = d.recovery(repair(replan=replan(), repair_rounds=4, previous_owner=owner))
            self.assertEqual(result['action'], 'replan')
            self.assertEqual(result['remaining_attempts'], 0)

    def test_new_replan_acknowledges_stall_only_at_its_recorded_baseline(self):
        result = d.recovery(repair(same_defect_no_progress=True, replan=replan(attempt_limit=2)))
        self.assertEqual(result['action'], 'bounded_fix')
        result = d.recovery(repair(same_defect_no_progress=True, repair_rounds=4,
                                   replan=replan(attempt_limit=2)))
        self.assertEqual(result['action'], 'escalate')

    def test_new_replan_still_requires_new_evidence(self):
        result = d.recovery(repair(new_evidence=False, same_defect_no_progress=True, replan=replan()))
        self.assertEqual(result['action'], 'investigate')

    def test_replan_cannot_waive_authority_quota_or_blocking_status(self):
        for change, expected in (({'authority_needed':True}, 'decision_needed'),
                                 ({'budget_exhausted':True}, 'checkpoint')):
            result = d.recovery(repair(replan=replan(), **change))
            self.assertEqual(result['action'], expected)
            self.assertFalse(result['may_patch'])
            self.assertFalse(result['accepted'])
            self.assertTrue(result['blocking_unresolved'])

    def test_replan_cannot_be_reused_for_another_task_or_defect(self):
        for values in ({'task':'T2'}, {'defect':'D2'}):
            with self.subTest(values=values), self.assertRaises(d.DeliveryError):
                d.recovery(repair(replan=replan(**values)))

    def test_future_replan_counter_baseline_is_rejected(self):
        for values in ({'failed_fixes':4}, {'repair_rounds':4}):
            with self.subTest(values=values), self.assertRaises(d.DeliveryError):
                d.recovery(repair(replan=replan(**values)))

    def test_replan_limit_is_small_positive_and_strict(self):
        for value in (0, 4, -1, True, 1.5):
            with self.subTest(value=value), self.assertRaises(d.DeliveryError):
                d.recovery(repair(replan=replan(attempt_limit=value)))

    def test_replan_record_is_validated_before_any_short_circuit(self):
        for changes in ({'decision_ref':''}, {'decision_ref':'bad\nref'},
                        {'extra':'ignored'}, {'failed_fixes':True}):
            with self.subTest(changes=changes), self.assertRaises(d.DeliveryError):
                d.recovery(repair(budget_exhausted=True, replan=replan(**changes)))

    def test_testers_and_reviewers_need_implementation_handoff(self):
        for owner in ('tester', 'reviewer', 'senior_reviewer', 'investigator', 'companion', 'archivist'):
            result = d.recovery(repair(previous_owner=owner, failed_fixes=0, repair_rounds=0))
            self.assertEqual(result['action'], 'assign_implementation')
            self.assertFalse(result['may_patch'])

    def test_none_of_the_new_records_is_mutated(self):
        for function, facts in ((d.budget, budget(limit=limit(), open_workers=1)),
                                (d.recovery, repair(replan=replan()))):
            original = copy.deepcopy(facts)
            self.assertEqual(function(facts), function(facts))
            self.assertEqual(original, facts)


class PracticeRegressions(unittest.TestCase):
    def test_reading_code_does_not_request_test_or_worktree_setup(self):
        result = d.practices(preparation())
        self.assertEqual(result['tdd'], 'not_applicable')
        self.assertEqual(result['workspace'], 'none')
        self.assertNotIn('testing.md', result['guides'])
        self.assertNotIn('branches.md', result['guides'])

    def test_writing_docs_without_behavior_change_avoids_code_test_ceremony(self):
        result = d.practices(preparation(kind='writing'))
        self.assertEqual(result['tdd'], 'not_applicable')

    def test_research_label_cannot_hide_actual_behavior_change(self):
        self.assertEqual(d.practices(preparation(behavior_change=True))['tdd'], 'red_green')

    def test_explicit_tdd_conflict_is_not_silently_overridden(self):
        result = d.practices(preparation(tdd_required=True, testable=False))
        self.assertEqual(result['action'], 'resolve_test_strategy')
        self.assertEqual(result['tdd'], 'blocked')
        result = d.practices(preparation(tdd_required=True))
        self.assertEqual(result['tdd'], 'red_green')
        self.assertIn('testing.md', result['guides'])


class InputRegressions(unittest.TestCase):
    def test_symlink_swap_between_check_and_open_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            path, target = root/'input.json', root/'other.json'
            value = json.dumps(dict(operation='budget', facts=budget()))
            path.write_text(value); target.write_text(value)
            original = Path.is_file
            def swap(p):
                result = original(p)
                if p == path:
                    p.unlink(); p.symlink_to(target)
                return result
            with mock.patch.object(Path, 'is_file', swap), contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(d.main(['--input', str(path)]), 2)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'POSIX special file')
    def test_file_replaced_by_fifo_is_rejected_without_blocking(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); path = root/'input.json'; path.write_text('{}')
            original = Path.is_file
            def swap(p):
                result = original(p)
                if p == path:
                    p.unlink(); os.mkfifo(p)
                return result
            with mock.patch.object(Path, 'is_file', swap), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(d.main(['--input', str(path)]), 2)

    def test_programming_typeerror_is_not_disguised_as_invalid_user_json(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'input.json'
            path.write_text(json.dumps(dict(operation='budget', facts=budget())))
            with mock.patch.object(d, 'budget', side_effect=TypeError('programming defect')), \
                    contextlib.redirect_stderr(io.StringIO()), self.assertRaises(TypeError):
                d.main(['--input', str(path)])

    def test_descriptor_is_closed_after_read_failure(self):
        if not hasattr(d, '_read_input'):
            self.fail('descriptor-safe input reader missing')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'input.json'; path.write_text('{}')
            with mock.patch.object(d.os, 'fstat', side_effect=OSError('read failed')), \
                    mock.patch.object(d.os, 'close', wraps=os.close) as close:
                with self.assertRaises(OSError): d._read_input(path)
                close.assert_called_once()


class ArchivedRegressions(unittest.TestCase):
    def test_exact_400_source_reproduces_precision_and_recovery_gaps(self):
        process = subprocess.run(['git', 'show', BASE+':codex_workflow/runtime/delivery.py'],
                                 cwd=ROOT, capture_output=True, text=True, timeout=10)
        if process.returncode:
            if os.environ.get('CI'):
                self.fail('Required 4.0.0 Git history missing: '+process.stderr)
            self.skipTest('Exact Git history required in CI; local extracted source has none')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'old.py'; path.write_text(process.stdout)
            spec = importlib.util.spec_from_file_location('delivery400_regression', path)
            old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
            self.assertEqual(old.budget(budget(limit=limit()))['action'], 'replan_budget')
            self.assertEqual(d.budget(budget(limit=limit()))['action'], 'proceed_bounded')
            self.assertEqual(old.budget(budget(limit=limit(maximum=1, spent=1e-18, next_estimate=1)))['action'], 'proceed_bounded')
            self.assertEqual(old.recovery(repair())['action'], 'replan')
            with self.assertRaises(old.DeliveryError): old.recovery(repair(replan=replan()))
            self.assertEqual(d.recovery(repair(replan=replan()))['action'], 'bounded_fix')
            self.assertTrue(old.recovery(repair(previous_owner='tester', failed_fixes=0, repair_rounds=0))['may_patch'])
            self.assertFalse(d.recovery(repair(previous_owner='tester', failed_fixes=0, repair_rounds=0))['may_patch'])


if __name__ == '__main__':
    unittest.main()
