"""One-shot base-checked patch preparation; excluded from the shipped source."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import tomllib
ROOT=Path(__file__).resolve().parents[2]
BASE='2e28dba69fb16dd8e14aa97a33862450d36a5d77'
CHANGES={}
def read(path):
    return CHANGES[path] if path in CHANGES else (ROOT/path).read_text()
def replace(path,old,new,count=1):
    text=read(path)
    if text.count(old)!=count:
        raise RuntimeError(f'{path}: expected {count} occurrences, found {text.count(old)}: {old[:90]!r}')
    CHANGES[path]=text.replace(old,new)
def append(path,text):
    CHANGES[path]=read(path).rstrip()+'\n\n'+text.strip()+'\n'
def main():
    subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=ROOT,check=True)
    subprocess.run(['git','diff','--exit-code',BASE,'--','codex_workflow','scripts','docs','README.md','.github/workflows/validate.yml'],cwd=ROOT,check=True)
    assert read('codex_workflow/operate/VERSION')=='3.1.0\n'
    CHANGES['codex_workflow/operate/VERSION']='3.1.1\n'
    replace('codex_workflow/operate/user_AGENTS.md','codex-workflow-version: 3.1.0','codex-workflow-version: 3.1.1')
    p='codex_workflow/runtime/allocation.py'
    replace(p,"'stalled', 'difficulty'})","'stalled', 'difficulty', 'previous_owner'})")
    replace(p,"    depth = max(levels.index(difficulty), 2 if task['deep'] else 0)","""    if task['tiny'] and difficulty in {'deep', 'serious'}:
        raise AllocationError('Tiny and deep/serious difficulty are contradictory')
    previous = _text(task['previous_owner']) if 'previous_owner' in task else None
    if previous is not None and previous not in ROLES | {'main'}:
        raise AllocationError('Unrecognized previous owner')
    depth = max(levels.index(difficulty), 2 if task['deep'] else 0)""")
    replace(p,"    if stalled and kind not in {'testing', 'memory'}:\n        depth = max(depth, 1)","""    if stalled and kind != 'memory':
        # Do not route an already-stalled Sol owner straight back to the same preset.
        floor = {'default_executor': 2, 'deep_executor': 3}.get(previous, 1)
        depth = max(depth, floor)""")
    replace(p,"    elif kind == 'testing':\n        role, reason = 'tester', 'approved_test_execution_not_semantic_signoff'", """    elif (stalled and kind != 'memory'
          and previous in {'main', 'senior_executor', 'senior_reviewer'}):
        role, reason = 'main', 'replan_after_senior_stall_not_another_retry'
    elif kind == 'testing':
        role, reason = ((sol[depth], 'stalled_testing_needs_diagnosis') if stalled
                        else ('tester', 'approved_test_execution_not_semantic_signoff'))""")
    replace(p,'    if caller is not None:\n        if (caller[\'state\']',"    if caller is not None and intent == 'work':\n        if (caller['state']")
    replace(p,"    if (role in VERIFIERS and (scope is not None or 'candidate_held' in request)\n            and request.get('candidate_held') is not True):", "    if role in VERIFIERS and request.get('candidate_held') is not True:")
    replace(p,"        return {**result, 'action': 'wait', 'reason': 'review_requires_candidate_hold'}\n    if role in VERIFIERS and scope is not None", """        return {**result, 'action': 'wait', 'reason': 'review_requires_candidate_hold'}
    # Legacy unscoped work never establishes safe verification or repair access.
    if scope is None and (role in VERIFIERS or any(t['role'] in VERIFIERS for t in peers)):
        return {**result, 'action': 'inspect', 'reason': 'verification_scope_required'}
    if role in VERIFIERS and scope is not None""")
    replace(p,'verification remains semantic; testing is procedural. Difficulty cannot weaken deep/critical.', 'verification remains semantic; testing is procedural. Difficulty cannot weaken deep/critical.\n    Optional previous_owner makes stalled recovery progress beyond a known attempted preset.')
    # Leave every model/effort untouched; inherit the actual parent sandbox instead of overriding it.
    for file in sorted((ROOT/'codex_workflow/agents').glob('*.toml')):
        path=file.relative_to(ROOT).as_posix()
        replace(path,'sandbox_mode = "workspace-write"\n','')
        if file.stem=='tester':
            replace(path,'Read testing.md','Read the installed CODEX_HOME/codex_workflow/testing.md (default ~/.codex/codex_workflow/testing.md)')
        elif file.stem in {'reviewer','senior_reviewer'}:
            replace(path,'Read verification.md,','Read the installed CODEX_HOME/codex_workflow/verification.md (default ~/.codex/codex_workflow/verification.md),')
    p='codex_workflow/runtime/smart_config.py'
    old=read(p)
    begin,end=old.index('def bootstrap(home: Path) -> str:'),old.index('def _statements(text: str):')
    bootstrap='''def bootstrap(home: Path) -> str:
    policy = str(home / 'codex_workflow' / 'smart_orchestration.md')
    return f\'''Smart Orchestration 3.1.1. For substantive work Main reads {json.dumps(policy, ensure_ascii=False)} once; named workers follow their role/task and relevant project rules, not the full Main policy.
Optimize accepted quality, elapsed time and total work. Main owns product/architecture/design judgment and acceptance. Main may implement tiny understood fixes or context-heavy critical-path work. Delegate coherent work without pre-solving the patch.
Luna Max handles ordinary work; Sol Low/Medium/High handles moderate/deep/serious work. Tester/Luna Medium executes approved tests, never semantic sign-off. Independent Reviewer handles required semantic gates. Follow the installed policy for exact presets and evidence-based recovery; no silent downgrade or repeated stalled attempt.
Run useful independent work in parallel within actual capacity, at most five owned open workers excluding Main. Declare scopes/resources, freeze verification inputs, preserve review capacity and observe native closure. Main may work on a disjoint path.
Reuse applicable evidence, never waive mandatory fresh/full gates. Missing proof is UNVERIFIED; drift STALE. Main inspects actual visuals. No duplicate suites or status polling on timeout.
Preserve owner/project, approval, no-agent, read-only, sandbox and speed settings. No ungranted writes or automatic restart. Disk checks are not live proof. Do not audit or retune the workflow during ordinary tasks.\'''


'''
    CHANGES[p]=old[:begin]+bootstrap+old[end:]
    p='codex_workflow/smart_orchestration.md'
    replace(p,'# Smart Orchestration 3.1\n','# Smart Orchestration 3.1.1\n')
    replace(p,'original failure, attempts and remaining hypotheses. Do not', 'original failure, attempted owner/preset, attempts and remaining hypotheses. Do not') if 'original failure, attempts and remaining hypotheses. Do not' in read(p) else None
    replace(p,'Routine compile errors with progress do not require a new model.', 'Routine compile errors with progress do not require a new model. A stalled Sol Low attempt\nneeds Medium or appropriate higher depth, not Low again; a stalled Senior needs Main to replan,\nnot self-certify acceptance. Supply previous_owner to the optional router when known.')
    append(p,"""## Stable everyday use

For research, writing, planning, files and administrative tasks, apply these ownership principles
with domain-appropriate evidence, not invented code tests or mandatory code-review teams.
Load only guides the task needs. Use the installed version without recurring installer checks,
model research, workflow retuning or new tracking systems. Revisit it only for an observed problem,
an incompatible client change or an explicit request. Complete the user's work, not the workflow.""")
    p='codex_workflow/execution.md'
    replace(p,'on_critical_path, stalled and optional difficulty (ordinary/moderate/deep/serious).', 'on_critical_path, stalled, previous_owner and optional difficulty (ordinary/moderate/deep/serious).')
    replace(p,'kind=verification remains semantic review; kind=testing means approved procedural test execution.', 'kind=verification remains semantic review; kind=testing means approved procedural test execution.\nStalled testing routes to diagnosis. Known previous_owner prevents retrying the same stalled Sol\npreset; Senior exhaustion goes to Main for replanning, never independent self-approval.')
    replace(p,'Scoped testing/review requires candidate_held=true.', 'All testing/review requires explicit scope and candidate_held=true, including legacy requests.')
    replace(p,'A one-slot client can release a writer\nand run Tester then Reviewer serially.', 'At low capacity, preserve the repair capsule and release the stopped writer, then run Tester\nand Reviewer serially, observing closure between them. Do not wait indefinitely on a reservation\nor waive semantic review; Main retains the required gate after closing its writer record.')
    p='codex_workflow/testing.md'
    replace(p,'A command against a mutable whole tree conflicts with all relevant active writers.', 'A command against a mutable whole tree conflicts with all relevant active writers.')
    append(p,"""At low capacity save the writer's repair capsule and observe its closure before starting tests;
close Tester after preserving the receipt to free capacity for required semantic review. Main
keeps that gate pending even after the allocator's writer record closes. Reuse a valid session
and environment, not an idle worker slot. A stalled test investigation is not another procedural run.""")
    p='codex_workflow/operate/smart_install.md'
    append(p,"""## Stable 3.1.1 configuration

The model mix and five-worker ceiling are unchanged. Role files omit sandbox_mode so the parent
sandbox is inherited instead of unnecessarily overridden. Project and live owner restrictions
still bind. Existing customized role files still require conflict review, not forced replacement.
Worker guides resolve under actual CODEX_HOME/codex_workflow, not a same-named project document.
Do not run installation checks on every ordinary task. Use the installed policy until an observed
problem, relevant client change or explicit update request. Patch releases carry version-specific notes.""")
    p='README.md'
    replace(p,'# Smart Orchestration 3.1\n','# Smart Orchestration 3.1.1\n')
    replace(p,'After v3.1 is merged to main, send Codex:', 'For the current published version, send Codex:')
    replace(p,'Before merge, use the exact reviewed branch commit instead of\nclaiming main contains 3.1.', 'Pin the inspected source commit; do not assume a branch or archive has the requested version.')
    replace(p,'[3.1 release notes and research](docs/v3.1.md)', '[3.1.1 maintenance audit](docs/v3.1.1.md) | [3.1 design and research](docs/v3.1.md)')
    insert='''## Maintenance patch 3.1.1

The model mix stays unchanged. This patch closes the legacy unscoped verification bypass,
prevents known stalled Sol owners from being routed back to the same preset, separates nested
readback from new scheduling authority, inherits parent sandbox settings, resolves worker guides
from the installed location, and shortens the duplicated global bootstrap. Low-capacity testing
and review have an explicit serial handoff. Patch-specific release notes and pinned CI actions
keep maintenance predictable. See [audit details and validation](docs/v3.1.1.md).

Use it for the work itself. Research, writing, planning and administrative tasks need relevant
evidence, not invented software tests. No routine workflow audits, model research, reinstallations
or retuning are required. Revisit the workflow for observed problems or explicit update requests.

'''
    replace(p,'## What changes in 3.1\n',insert+'## What changes in 3.1\n')
    p='scripts/test_current.py'
    replace(p,"VERSION = '3.1.0'","VERSION = '3.1.1'")
    replace(p,"'sandbox_mode','developer_instructions','agents'","'developer_instructions','agents'")
    p='scripts/test_hardening.py'
    replace(p,"        result = a.next_action(observation(thread(), caller='writer'), request(role='tester'))\n        self.assertEqual(result['action'], 'spawn')", """        sc = dict(workspace='/repo', reads=['src'], writes=[], resource_reads=[], resource_writes=[])
        owner = thread(scope={**sc, 'writes':['src']})
        result = a.next_action(observation(owner, caller='writer', main_scope=None),
                               request(role='tester', scope=sc, candidate_held=True))
        self.assertEqual(result['action'], 'spawn')""")
    p='scripts/test_v31.py'
    replace(p,"self.assertEqual(package.version,'3.1.0')", "self.assertEqual(package.version,'3.1.1')")
    p='scripts/test_migration.py'
    replace(p,"'a7e4c9ac715ad7098d2ddd78f2e24eb08adc1e2a')", "'a7e4c9ac715ad7098d2ddd78f2e24eb08adc1e2a',\n           '2e28dba69fb16dd8e14aa97a33862450d36a5d77')")
    # Validate the actual release shell, but publish this workflow through the connector, not a bot token.
    p='.github/workflows/validate.yml'
    replace(p,'actions/checkout@v4','actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1',count=2)
    replace(p,'actions/setup-python@v5','actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0')
    replace(p,'    strategy:\n',"    concurrency:\n      group: smart-validate-${{ github.event.pull_request.number || github.run_id }}-${{ matrix.os }}-${{ matrix.python-version }}\n      cancel-in-progress: ${{ github.event_name == 'pull_request' }}\n    strategy:\n")
    replace(p,'          notes="docs/v${version%.*}.md"', '''          notes="docs/v$version.md"
          if [[ "$version" == *.0 && ! -s "$notes" ]]; then
            notes="docs/v${version%.*}.md"
          fi''')
    CHANGES['scripts/test_v311.py']=(Path(__file__).parent/'tests.py').read_text()
    CHANGES['docs/v3.1.1.md']=(Path(__file__).parent/'notes.md').read_text()
    for path,text in CHANGES.items():
        if path.endswith('.py'):compile(text,path,'exec')
        if path.endswith('.toml'):tomllib.loads(text)
        target=ROOT/path
        assert not target.is_symlink()
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(text)
    print(json.dumps({'base':BASE,'version':'3.1.1','changed_paths':sorted(CHANGES),
        'guide_words':{n:len(read('codex_workflow/'+n).split()) for n in ('smart_orchestration.md','execution.md','testing.md')},
        'workflow_blob':subprocess.check_output(['git','hash-object',p],cwd=ROOT,text=True).strip()},indent=2))
if __name__=='__main__':main()
