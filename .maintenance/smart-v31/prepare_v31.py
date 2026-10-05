#!/usr/bin/env python3
"""One-shot base-checked source authoring; not a user installer or native agent scheduler."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import tomllib
BASE='a7e4c9ac715ad7098d2ddd78f2e24eb08adc1e2a'
ROOT=Path(__file__).resolve().parents[2]
changes={}
def current(path):
    return changes[path] if path in changes else (ROOT/path).read_text()
def replace(path,old,new,count=1):
    text=current(path);found=text.count(old)
    if found==0 or (count is not None and found!=count):
        raise RuntimeError(f'{path}: expected {count}, found {found}: {old[:100]!r}')
    changes[path]=text.replace(old,new)
def section(path,start,end,text):
    original=current(path)
    if original.count(start)!=1 or original.count(end)!=1:raise RuntimeError('Ambiguous section: '+path)
    a,b=original.index(start),original.index(end)
    if a>=b:raise RuntimeError('Reversed section')
    changes[path]=original[:a]+text.rstrip()+'\n\n\n'+original[b:]
def main():
    assert (ROOT/'codex_workflow/operate/VERSION').read_text().strip()=='3.0.1'
    subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=ROOT,check=True)
    subprocess.run(['git','diff','--exit-code',BASE,'--','codex_workflow','docs','scripts','README.md'],cwd=ROOT,check=True)
    for source in sorted(Path(__file__).parent.glob('files-*.json')):
        supplied=json.loads(source.read_text())
        for path,text in supplied.items():
            p=Path(path)
            assert not p.is_absolute() and '..' not in p.parts
            assert p.parts[0] in {'README.md','codex_workflow','docs','scripts'}
            assert isinstance(text,str) and text.endswith('\n')
            assert path not in changes,'Duplicate payload path'
            changes[path]=text
    assert 'codex_workflow/smart_orchestration.md' in changes
    replace('codex_workflow/runtime/layout.py','"senior_executor", "tester", "archivist", "companion", "investigator",','"senior_executor", "deep_executor", "tester", "reviewer", "senior_reviewer",\n    "archivist", "companion", "investigator",')
    replace('codex_workflow/runtime/layout.py','"smart_orchestration.md", "execution.md", "verification.md", "browser.md",','"smart_orchestration.md", "execution.md", "verification.md", "testing.md", "browser.md",')
    p='codex_workflow/runtime/agent_defaults.py'
    replace(p,"'max_concurrent_threads_per_session': 4","'max_concurrent_threads_per_session': 5")
    replace(p,"'default_subagent_model': 'gpt-6.1-sol'","'default_subagent_model': 'gpt-6-luna'")
    replace(p,"'default_subagent_reasoning_effort': 'medium'","'default_subagent_reasoning_effort': 'max'")
    replace(p,'cap < 4','cap < 5');replace(p,'cap > 4','cap > 5')
    replace(p,'at most four owned open threads','at most five owned open threads')
    replace(p,'Smart 3 balanced default','Smart 3.1 balanced default')
    p='codex_workflow/runtime/config_assessment.py'
    replace(p,'cap < 4','cap < 5');replace(p,'cap > 4','cap > 5')
    replace(p,'at most four owned open threads','at most five owned open threads')
    replace(p,'balanced Sol fallback','balanced Luna Max fallback')
    replace(p,"'recommended_parallel_cap': 4","'recommended_parallel_cap': 5")
    bootstrap='''def bootstrap(home: Path) -> str:
    policy = str(home / 'codex_workflow' / 'smart_orchestration.md')
    return f\'''Smart Orchestration 3.1: Main reads {json.dumps(policy, ensure_ascii=False)} once for substantive work. Named workers follow role/task.
Optimize accepted quality, elapsed time and total model work, not cheap tokens alone. Main owns product/architecture/design judgment and acceptance. Main may implement small understood fixes or context-heavy critical-path work directly; do not delegate every typo or pre-solve whole worker patches.
Routine/Luna Max handles ordinary implementation and bounded unknown bugs; Investigator/Luna Max handles causal discovery; Simple/Luna Max handles known recipes. Default/Sol Low handles moderate work and adaptive tools, Deep/Sol Medium deep work, Senior/Sol High serious/critical work. Start at appropriate depth, not a mandatory ladder. One same-defect evidence-based correction without progress triggers Sol/Main diagnosis with original evidence.
Tester/Luna Medium runs approved tests and reports receipts; it is not semantic sign-off or coverage authority. Reviewer/Luna Max independently reviews ordinary changes; Senior Reviewer/Sol High handles deep/critical risk. Focused checks during edits, required complete suites on stable integrated candidates. Reuse applicable verified runs instead of duplicating suites across agents; mandatory fresh/full gates win. Zero tests, missing shards, incomplete runs and unresolved flaky failures are not valid passes.
Dispatch useful independent work before waiting. Start with two branches; at most five Smart-owned open threads within actual owner/client capacity, excluding Main. Main may work on a disjoint critical path. Declare read/write scopes, prerequisites and mutable resources; whole-tree tests cannot race writers. Reserve semantic-review capacity; Tester cannot replace it. Budget test processes/CPU/RAM separately. Completion is not native closure.
Read only relevant sources and guides. No manager or mandatory ledger. Preserve candidate holds, original logs, independent gates and actual visuals. Main-authored fixes need required independent review. Release holds before repair and refresh affected proof. Missing evidence is UNVERIFIED; affected drift STALE. Workers own command waits; timeout alone causes no progress SEND, duplicate suite or unfinished-diff scan. Honor real user interruptions.
No invented tools, silent model/effort downgrade, automatic Fast/Astra, permission expansion, cap increase, ungranted Git/production writes or restart. Preserve explicit owner/profile/speed settings. Owner/project, approval, no-agent and read-only rules bind. Disk consistency is not live activation or measured savings.\'''
'''
    section('codex_workflow/runtime/smart_config.py','def bootstrap(home: Path) -> str:','def _statements(text: str):',bootstrap)
    p='codex_workflow/runtime/allocation.py'
    replace(p,"'senior_executor', 'tester', 'companion', 'investigator', 'archivist'})","'senior_executor', 'deep_executor', 'tester', 'reviewer', 'senior_reviewer',\n                   'companion', 'investigator', 'archivist'})")
    replace(p,"WRITERS = frozenset({'simple_executor', 'routine_executor', 'default_executor', 'senior_executor'})","WRITERS = frozenset({'simple_executor', 'routine_executor', 'default_executor', 'deep_executor', 'senior_executor'})\nREVIEWERS = frozenset({'reviewer', 'senior_reviewer'})\nVERIFIERS = REVIEWERS | frozenset({'tester'})")
    replace(p,'SMART_OPEN_LIMIT = 4','SMART_OPEN_LIMIT = 5')
    classifier='''def classify(task: dict) -> dict:
    """Recommend fixed presets from supplied facts; no native model selection.

    verification remains semantic; testing is procedural. Difficulty cannot weaken deep/critical.
    """
    _keys(task, {'kind', 'risk', 'settled', 'tiny', 'deep', 'independent_required'},
          {'mechanical', 'in_context', 'on_critical_path', 'stalled', 'difficulty'})
    kind = _text(task['kind'])
    if kind not in {'answer', 'judgment', 'operation', 'implementation', 'verification', 'testing', 'discovery', 'memory'}:
        raise AllocationError('Unrecognized assignment kind')
    risk = _text(task['risk'])
    if risk not in {'low', 'material', 'critical'}:
        raise AllocationError('Unrecognized risk')
    for key in ('settled', 'tiny', 'deep', 'independent_required', 'mechanical',
                'in_context', 'on_critical_path', 'stalled'):
        if key in task:
            _bool(task[key])
    if task['tiny'] and task['deep']:
        raise AllocationError('Tiny and deep are contradictory')
    levels = ('ordinary', 'moderate', 'deep', 'serious')
    difficulty = _text(task.get('difficulty', 'ordinary'))
    if difficulty not in levels:
        raise AllocationError('Unrecognized difficulty')
    depth = max(levels.index(difficulty), 2 if task['deep'] else 0)
    if kind == 'testing' and depth > 0:
        raise AllocationError('Testing is approved procedural execution; use discovery or verification for test strategy/diagnosis')
    if risk == 'critical':
        depth = 3
    stalled = task.get('stalled', False)
    if stalled and kind not in {'testing', 'memory'}:
        depth = max(depth, 1)
    mechanical = task.get('mechanical', False)
    review = task['independent_required'] or risk != 'low' or depth >= 2
    semantic = 'senior_reviewer' if depth >= 2 or (kind == 'verification' and stalled) else 'reviewer'
    sol = {1: 'default_executor', 2: 'deep_executor', 3: 'senior_executor'}
    if kind == 'answer':
        role, reason = 'main', 'answer_without_team'
    elif kind == 'judgment' or not task['settled']:
        role, reason = 'main', 'resolve_judgment_or_contract'
    elif kind == 'testing':
        role, reason = 'tester', 'approved_test_execution_not_semantic_signoff'
    elif kind == 'verification':
        role, reason = semantic, 'independent_semantic_review'
    elif kind == 'memory':
        role, reason = 'archivist', 'authorized_checkpoint_only'
    elif stalled:
        role, reason = sol[depth], 'appropriate_sol_after_stalled_correction'
    elif kind == 'discovery':
        if depth:
            role, reason = sol[depth], 'higher_depth_causal_investigation'
        else:
            role, reason = ('companion', 'exact_lookup') if mechanical else ('investigator', 'bounded_causal_investigation')
    elif ((task['tiny'] and task.get('in_context', True))
          or (task.get('in_context', False) and task.get('on_critical_path', False))):
        role, reason = 'main', 'direct_bounded_finish_avoids_handoff'
    elif depth:
        role, reason = sol[depth], 'sol_depth_selected_directly'
    elif kind == 'operation' and not mechanical:
        role, reason = 'default_executor', 'adaptive_tool_use_sol_low'
    elif mechanical and (kind == 'operation' or task['tiny']):
        role, reason = 'simple_executor', 'known_batched_recipe'
    else:
        role, reason = 'routine_executor', 'ordinary_luna_max_implementation'
    reviewer = semantic if review and kind in {'implementation', 'operation'} else None
    return {'owner': role, 'reviewer': reviewer, 'reason': reason, 'limitation': LIMITATION}
'''
    section(p,'def classify(task: dict) -> dict:','def _paths(value, *, absolute=False):',classifier)
    replace(p,"or role != 'tester'",'or role not in VERIFIERS')
    replace(p,"(role == 'tester' and (scope",'(role in VERIFIERS and (scope')
    replace(p,"(role == 'tester' and same_unit",'(role in VERIFIERS and same_unit')
    replace(p,"t['role'] == 'tester' and stopped","t['role'] in VERIFIERS and stopped")
    replace(p,"t['role'] == 'tester'\n","t['role'] in REVIEWERS\n")
    replace(p,"serving_queue = role == 'tester'",'serving_queue = role in REVIEWERS')
    replace(p,'A retained unrelated Tester','A retained unrelated semantic reviewer')
    replace(p,"raise AllocationError('New review work requires an active same-unit owner with explicit review authority')","raise AllocationError('New verification work requires an active same-unit owner with explicit review authority')\n        if any(t['owned'] and t['parent'] == obs['caller'] and t['role'] in VERIFIERS\n               and t['id'] != request['reuse_id'] for t in opened.values()):\n            return {**result, 'action': 'wait', 'reason': 'nested_verifier_already_open'}")
    replace(p,"return {**result, 'action': 'wait', 'reason': 'review_requires_candidate_hold'}\n    if scope is not None:","return {**result, 'action': 'wait', 'reason': 'review_requires_candidate_hold'}\n    if role in VERIFIERS and scope is not None and _conflict(\n            scope, {**scope, 'writes': [], 'resource_reads': [], 'resource_writes': []}):\n        return {**result, 'action': 'blocked', 'reason': 'verifier_writes_input_scope'}\n    if scope is not None:")
    p='scripts/test_current.py'
    replace(p,"VERSION = '3.0.1'","VERSION = '3.1.0'")
    section(p,'EXPECTED = {','class PackageContracts(unittest.TestCase):','''EXPECTED = {
    'simple_executor': ('gpt-6-luna', 'max'),
    'routine_executor': ('gpt-6-luna', 'max'),
    'default_executor': ('gpt-6.1-sol', 'low'),
    'deep_executor': ('gpt-6.1-sol', 'medium'),
    'senior_executor': ('gpt-6.1-sol', 'high'),
    'tester': ('gpt-6-luna', 'medium'),
    'reviewer': ('gpt-6-luna', 'max'),
    'senior_reviewer': ('gpt-6.1-sol', 'high'),
    'investigator': ('gpt-6-luna', 'max'),
    'companion': ('gpt-6-luna', 'max'),
    'archivist': ('gpt-6-luna', 'max'),
}
''')
    replace(p,"'Luna Max is an optional'","'Luna Max is the ordinary delegated baseline'")
    replace(p,"'# Smart Orchestration 3.0'","'# Smart Orchestration 3.1'")
    replace(p,"DEFAULTS['default_subagent_model'], 'gpt-6.1-sol'","DEFAULTS['default_subagent_model'], 'gpt-6-luna'")
    replace(p,"DEFAULTS['max_concurrent_threads_per_session'], 4","DEFAULTS['max_concurrent_threads_per_session'], 5")
    replace(p,"result['recommended_parallel_cap'], 4","result['recommended_parallel_cap'], 5")
    replace(p,'for cap in (1, 2, 3):','for cap in (1, 2, 3, 4):')
    replace(p,"'verification.md':700, 'browser.md':650","'verification.md':700, 'testing.md':650, 'browser.md':650")
    p='scripts/test_allocation.py'
    replace(p,"'tester'","'reviewer'",None)
    replace(p,"def test_normal_feature_uses_sol_owner(self):\n        self.assertEqual(a.classify(task())['owner'],'default_executor')","def test_normal_feature_uses_luna_max_owner(self):\n        self.assertEqual(a.classify(task())['owner'],'routine_executor')")
    replace(p,'def test_material_recipe_is_not_cheap_by_default(self):','def test_material_recipe_retains_independent_review(self):')
    replace(p,"('default_executor','reviewer')","('routine_executor','reviewer')",2)
    replace(p,"r=a.classify(task(deep=True)); self.assertEqual((r['owner'],r['reviewer']),('routine_executor','reviewer'))","r=a.classify(task(deep=True)); self.assertEqual((r['owner'],r['reviewer']),('deep_executor','senior_reviewer'))")
    replace(p,'def test_deep_requires_review_not_forced_luna_max(self):','def test_deep_starts_sol_medium_with_senior_review(self):')
    replace(p,"self.assertEqual((r['owner'],r['reviewer']),('reviewer',None))","self.assertEqual((r['owner'],r['reviewer']),('senior_reviewer',None))")
    replace(p,'def test_four_scoped_threads_not_five(self):','def test_preserved_four_thread_owner_cap_blocks_fifth(self):')
    p='scripts/test_v301.py'
    replace(p,"'tester'","'reviewer'",None)
    replace(p,'def test_four_thread_ceiling_and_owner_cap_are_not_raised(self):','def test_five_thread_policy_ceiling_is_not_a_fanout_target(self):')
    replace(p,"thread(x) for x in ('a', 'b', 'c', 'd')","thread(x) for x in ('a', 'b', 'c', 'd', 'e')")
    replace(p,"a.next_action(obs, request('e'))['reason'], 'smart_open_thread_budget'","a.next_action(obs, request('f'))['reason'], 'smart_open_thread_budget'")
    replace(p,'self.assertEqual(a.SMART_OPEN_LIMIT, 4)','self.assertEqual(a.SMART_OPEN_LIMIT, 5)')
    replace(p,"self.assertIn(old.next_action(obs, req)['action'], ('spawn', 'reuse'))",'''# Historical 3.0 called its semantic reviewer 'tester'. Rename only role
                # labels for the unchanged source; scopes, caps and evidence stay identical.
                legacy_obs, legacy_req = copy.deepcopy((obs, req))
                for t in legacy_obs['threads']:
                    if t['role'] == 'reviewer':
                        t['role'] = 'tester'
                if legacy_req['role'] == 'reviewer':
                    legacy_req['role'] = 'tester'
                self.assertIn(old.next_action(legacy_obs, legacy_req)['action'], ('spawn', 'reuse'))''')
    replace('scripts/test_migration.py',"'474326b0892e473bcde5638bccf81eb8944aac50')","'474326b0892e473bcde5638bccf81eb8944aac50',\n           'a7e4c9ac715ad7098d2ddd78f2e24eb08adc1e2a')")
    p='codex_workflow/browser.md'
    replace(p,'Simple Luna Low','Simple Luna Max')
    replace(p,'Do not reflexively increase Luna to Max.','Select Sol Low/Medium/High by demonstrated complexity, not a ritual ladder.')
    replace(p,'independent Sol coding','independent implementation')
    for path,text in list(changes.items()):
        if path.endswith('.py'):compile(text,path,'exec')
        elif path.endswith('.toml'):tomllib.loads(text)
        p=ROOT/path
        for ancestor in (p,*p.parents):
            if ancestor==ROOT.parent:break
            if ancestor.is_symlink():raise RuntimeError('Symlink: '+path)
    for path,text in sorted(changes.items()):
        p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    print(json.dumps({'version':'3.1.0','base':BASE,'changed_paths':sorted(changes)},indent=2))
if __name__=='__main__':main()
