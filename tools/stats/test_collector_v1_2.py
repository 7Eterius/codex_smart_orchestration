"""Targeted audit regressions, using invented inputs rather than private logs."""
import json
from datetime import timedelta
import smart_weekly_stats as a
from test_smart_weekly_stats import Fixture,START,meta,record,event,call,output,context,token,vec

class AuditRegressions(Fixture):
    def test_inspection_with_quoted_test_words_is_not_test_launch(self):
        cmd="ps -axo pid,ppid,command | rg 'npm-cli.js run test|vitest|content/(build|verify)'"
        self.assertFalse(a.is_test_command(cmd))
        self.write([meta(),call(cmd=cmd),output()]); _,r=self.collect()
        self.assertEqual(r['tests']['recognized_test_command_runs'],0)

    def test_quoted_separator_is_not_operator(self):
        for cmd in ("echo '|' vitest", "printf '%s' 'npm test; vitest'", "rg 'vitest' file", "cat report-test.json"):
            self.assertFalse(a.is_test_command(cmd),cmd)

    def test_real_compound_and_direct_commands_are_recognized(self):
        for cmd in ('cd repo && npm test', 'pnpm exec vitest run', 'env CI=1 npm run test:unit',
                    'bash -lc "npm test"', 'python3 -B -m unittest discover', 'uv run pytest -q'):
            self.assertTrue(a.is_test_command(cmd),cmd)

    def test_unknown_shell_constructs_are_not_executed_or_guessed(self):
        for cmd in ("cat <<'EOF'\nnpm test\nEOF", 'echo $(npm test)', 'echo `vitest`', "npm test 'unterminated"):
            self.assertFalse(a.is_test_command(cmd),cmd)

    def test_copied_parent_turn_after_creation_is_excluded_by_payload_time(self):
        self.write([meta('child','absent-parent',created=100),
                    event('task_started',seconds=110,turn_id='old',started_at=a.iso(START)),
                    event('task_complete',seconds=111,turn_id='old',completed_at=a.iso(START+timedelta(seconds=9)))])
        c,r=self.collect()
        self.assertEqual(r['turns']['peak_distinct_workers_with_closed_turn_overlap_per_root'],0)
        self.assertEqual(c.diag['copied_precreation_payload_turns_excluded'],1)

    def test_ancestor_identity_resolves_replay_independently_of_read_order(self):
        self.write([meta('root'),event('task_started',turn_id='shared',seconds=100),
                    event('task_complete',turn_id='shared',seconds=120)],'z.jsonl')
        self.write([meta('child','root',created=10),event('task_started',turn_id='shared',seconds=100),
                    event('task_complete',turn_id='shared',seconds=120)],'a.jsonl')
        c,r=self.collect()
        self.assertEqual(r['turns']['peak_distinct_workers_with_closed_turn_overlap_per_root'],0)
        self.assertEqual(c.diag['copied_ancestor_turn_ids_excluded'],1)

    def test_fourteen_replays_do_not_hide_five_real_children(self):
        self.write([meta('root'),event('task_started',seconds=0,turn_id='root-initial'),
                    event('task_complete',seconds=9,turn_id='root-initial')],'root.jsonl')
        for i in range(14):
            rows=[meta(f'child{i}','root',created=100),
                  event('task_started',seconds=110,turn_id='root-initial',started_at=a.iso(START)),
                  event('task_complete',seconds=111,turn_id='root-initial',completed_at=a.iso(START+timedelta(seconds=9)))]
            if i<5: rows += [event('task_started',seconds=200,turn_id=f'own{i}'),event('task_complete',seconds=300,turn_id=f'own{i}')]
            self.write(rows,f'child{i}.jsonl')
        _,r=self.collect()
        self.assertEqual(r['turns']['peak_distinct_workers_with_closed_turn_overlap_per_root'],5)
        self.assertIn('UNRESOLVED',r['turns']['open_thread_policy_compliance'])

    def test_second_precision_does_not_reject_same_second_child_birth(self):
        m=meta('child','root',created=100)
        m['payload']['timestamp']=a.iso(START+timedelta(seconds=100,microseconds=700000))
        self.write([m,event('task_started',seconds=101,turn_id='own',started_at=a.iso(START+timedelta(seconds=100))),
                    event('task_complete',seconds=120,turn_id='own')])
        _,r=self.collect();self.assertEqual(r['turns']['peak_distinct_workers_with_closed_turn_overlap_per_root'],1)

    def test_unknown_creation_does_not_certify_worker_overlap(self):
        m=meta('child','root');m['payload'].pop('timestamp')
        self.write([m,event('task_started',turn_id='own'),event('task_complete',seconds=50,turn_id='own')])
        c,r=self.collect();self.assertEqual(r['turns']['peak_distinct_workers_with_closed_turn_overlap_per_root'],0)
        self.assertEqual(c.diag['worker_turns_without_birth_or_start_evidence'],1)

    def test_wrapper_zero_with_embedded_failure_is_visible(self):
        self.write([meta(),call(),output(text='Process exited with code 0\nexit_status=1\n7 failed')])
        _,r=self.collect()
        self.assertEqual(r['tests']['exits']['exit_zero'],1)
        self.assertEqual(r['tests']['outcome_evidence']['wrapper_zero_conflicts_with_embedded_nonzero'],1)

    def test_wrapper_zero_is_never_promoted_to_test_pass(self):
        self.write([meta(),call(),output()]);_,r=self.collect()
        self.assertEqual(r['tests']['outcome_evidence']['process_zero_test_verdict_unverified'],1)

    def test_red_green_counts_keep_both_original_exits(self):
        self.write([meta(),call(),output(text='Process exited with code 1'),call(cid='c2',seconds=8),output(cid='c2',seconds=10)])
        _,r=self.collect();self.assertEqual(r['tests']['exits'],{'nonzero':1,'exit_zero':1})
        pair=r['tests']['examples'][0]
        self.assertFalse(pair['same_candidate_established']);self.assertIn('previous_line',pair)

    def test_usage_not_deleted_when_replayed_turn_is_removed(self):
        self.write([meta('child','root',created=100),
                    event('task_started',seconds=101,turn_id='old',started_at=a.iso(START)),
                    event('task_complete',seconds=102,turn_id='old',completed_at=a.iso(START+timedelta(seconds=9))),
                    context(seconds=110),token(vec(),seconds=120)])
        _,r=self.collect();self.assertEqual(r['observed_token_usage']['total_tokens'],130)

    def test_typed_command_wrapper_marker_parses_aggregated_output(self):
        item=dict(type='CommandExecution',id='c',command=['npm','test'],cwd='/test',status='completed',
                  exit_code=0,duration={'secs':1,'nanos':0},aggregated_output='exit_status=1\n')
        self.write([meta(),event('item_completed',item=item,seconds=5)])
        _,r=self.collect();self.assertEqual(r['tests']['outcome_evidence']['wrapper_zero_conflicts_with_embedded_nonzero'],1)

    def test_config_snapshot_is_not_effective_native_capacity(self):
        self.write([meta(),context(),token(vec())]);c,r=self.collect()
        self.assertIn('not historical',c.snapshot()['note'])
        self.assertIn('UNRESOLVED',r['turns']['open_thread_policy_compliance'])
