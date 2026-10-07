#!/usr/bin/env python3
"""Assemble a pinned 4.0 source upgrade in an isolated preparation branch only."""
from __future__ import annotations
import json
from pathlib import Path
import re
import subprocess
import tomllib

ROOT=Path(__file__).resolve().parents[2]
BASE='2862add2a19a0cb3c5450ef6ebe5db0c87c07034'
PAYLOAD={'codex_workflow/runtime/delivery.py','scripts/test_delivery.py','scripts/test_v4.py',
         'codex_workflow/planning.md','codex_workflow/debugging.md','codex_workflow/branches.md',
         'codex_workflow/economics.md','codex_workflow/testing.md','codex_workflow/smart_orchestration.md',
         'codex_workflow/third_party/Superpowers-LICENSE.txt','docs/v4.0.md'}
changes={}

def load(path):
    if path in changes:return changes[path]
    actual=(ROOT/path).read_text()
    if path not in PAYLOAD:
        expected=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT).decode()
        if actual!=expected:raise RuntimeError('Base source changed: '+path)
    return actual

def replace(path,old,new,count=1):
    text=load(path)
    if text.count(old)!=count:raise RuntimeError(f'{path}: expected {count} occurrences of {old[:90]!r}, got {text.count(old)}')
    changes[path]=text.replace(old,new)

def append(path,text):changes[path]=load(path).rstrip()+'\n\n'+text.strip()+'\n'

def role(name,instructions):
    path=f'codex_workflow/agents/{name}.toml'
    text=load(path);old=tomllib.loads(text)
    body=instructions.strip()
    if len(body.split())>=200:raise RuntimeError(f'Role too large: {name}')
    updated,n=re.subn(r'developer_instructions = """\n.*?\n"""',lambda _: 'developer_instructions = """\n'+body+'\n"""',text,flags=re.S)
    if n!=1:raise RuntimeError('Ambiguous role body: '+name)
    cfg=tomllib.loads(updated)
    old.pop('developer_instructions');cfg.pop('developer_instructions')
    if old!=cfg:raise RuntimeError('Non-instruction role settings changed: '+name)
    changes[path]=updated


def main():
    subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=ROOT,check=True)
    if load('codex_workflow/operate/VERSION').strip()!='3.1.1':raise RuntimeError('Wrong base version')
    changes['codex_workflow/operate/VERSION']='4.0.0\n'
    load('codex_workflow/operate/user_AGENTS.md')
    changes['codex_workflow/operate/user_AGENTS.md']='<!-- codex-workflow-user-id: viettran-edgeAI/codex_workflow -->\n<!-- codex-workflow-version: 4.0.0 -->\n<!-- codex-workflow-user-managed-start -->\n# Smart Orchestration\n\nFor substantive work Main reads installed `codex_workflow/smart_orchestration.md` under\nactual CODEX_HOME (default `~/.codex`) once. Named workers follow their role and bounded task.\nMain owns product, architecture, design and acceptance; small understood work can stay direct.\nPreserve the Luna Max / Sol Low-Medium-High routing and separate Luna Medium Tester.\n\nUse planning/debugging/testing/branch practices only when relevant. Clear authorized work\nneeds no brainstorming ritual. Delegate coherent outcomes, not pre-solved patches. Preserve\noriginal evidence, candidate holds and required independent gates. Cumulative repair limits\nand accepted-work checkpoints survive worker/model/context handoffs. Budget exhaustion does\nnot permit false completion. No second orchestration layer, telemetry or mandatory ledger.\n\nUp to five owned open workers fit only within actual owner/client limits and disjoint scopes\nand resources. Main may work on a disjoint critical path. Observe native closure. Preserve\nexplicit models, parent/profile/speed/sandbox settings, permissions and lower capacity unless\nan owner authorizes a change. Install via `operate/smart_install.md`, restart manually and\nuse a fresh conversation. Disk integrity is not live activation or measured savings.\n<!-- codex-workflow-user-managed-end -->\n'
    replace('codex_workflow/runtime/layout.py','_REQUIRED = (\n','_REQUIRED = (\n    "planning.md", "debugging.md", "branches.md", "economics.md",\n    "runtime/delivery.py", "third_party/Superpowers-LICENSE.txt",\n')
    path='codex_workflow/runtime/smart_config.py'
    text=load(path);start=text.index('def bootstrap(home: Path) -> str:');end=text.index('def _statements(text: str):')
    new_boot='''def bootstrap(home: Path) -> str:
    policy = str(home / 'codex_workflow' / 'smart_orchestration.md')
    return f\'''Smart Orchestration 4.0: Main reads {json.dumps(policy, ensure_ascii=False)} once for substantive work. Named workers follow their role and bounded task.
Main owns product/architecture/design and acceptance. Main may implement small understood or disjoint critical-path work. Delegate coherent outcomes, not pre-solved patches. Preserve Luna Max ordinary work, Sol Low/Medium/High depth, Luna Medium procedural Tester and separate independent semantic review.
Read only relevant planning, debugging, testing, branches and economics guides. Brainstorm only real ambiguity; plan deliverables, not microsteps. Use meaningful RED/GREEN where appropriate, not deletion rituals. Carry original evidence and cumulative repair counts across handoffs; exhausted loops or quota checkpoint blockers, never certify them.
Run useful independent work in parallel, at most five owned open workers within actual capacity and owner limits. Keep read/write/resource scopes, candidate holds, review capacity and observed native closure. Reuse valid test evidence; required fresh/full gates bind. Main inspects actual visuals.
Use domain-appropriate evidence. No second orchestration bootstrap, mandatory per-command ledger, recurring audit, silent model downgrade, permission expansion or automatic restart. Owner/project instructions and approval boundaries bind. Disk checks are not live activation or savings.\'''


'''
    if len(new_boot.split())>230:raise RuntimeError('Bootstrap unexpectedly large')
    changes[path]=text[:start]+new_boot+text[end:]
    replace('codex_workflow/smart_orchestration.md','actual visual\nevidence','actual visual evidence')
    replace('codex_workflow/smart_orchestration.md','without recurring\ninstaller checks','without recurring installer checks')

    for name,body in json.loads((Path(__file__).parent/'roles.json').read_text()).items():
        role(name,body)

    append('codex_workflow/execution.md', '''## Method is not another orchestration layer

Use planning.md for unclear outcomes or long-task checkpoints, debugging.md for causal repair and
cumulative circuit breakers, economics.md for bounded batches, and branches.md for large-feature
isolation/integration. Keep one review owner for spec and quality; do not duplicate worker-spawned
review. Carry accepted-unit evidence and repair counts across model/context changes. New methods
never weaken the existing ownership, hold, scope, capacity or acceptance constraints above.''')
    append('codex_workflow/verification.md', '''## Completion claims and integrated review

Report spec compliance and technical quality in one independent pass. Bind every completion claim
to the actual candidate, fulfilled requirements and decisive evidence; a test pass is not deployment
or live installation proof. Large features need integrated contract review, not duplicate suites.
The debugging.md circuit breaker stops repair dispatch, never accepts unresolved required findings.
Keep material new blockers visible even outside a correction diff.''')
    append('codex_workflow/design.md', '''Use planning.md only for genuine unresolved outcomes or consequential choices; clear authorized
visual work needs no repeat approval ritual. testing.md permits rendered evidence for visual
changes rather than fake RED/GREEN, without replacing required behavioral or accessibility checks.''')
    append('codex_workflow/runtime_check.md', '''For 4.0, qualify only the methods needed by the next real task: relevant guide resolution,
original-failure diagnosis, meaningful RED/GREEN where suitable, stable evidence reuse and
checkpoint recovery without redispatch. delivery.py decisions do not prove native compliance or
quota enforcement. Report a conflicting second orchestration bootstrap; never disable/remove an
existing plugin without authorization. Do not install Superpowers as a dependency of Smart.''')
    append('codex_workflow/operate/smart_install.md', '''## 4.0 method upgrade

The complete package adds planning/debugging/branch/economics guides, the optional delivery
adviser, and an upstream license notice. The model/effort map is unchanged. Main remains selected
by the owner, not silently changed to a recommendation. No additional Superpowers installation,
server, hook or telemetry is required. Report conflicting orchestration bootstraps without
removing plugins automatically. The README's explicit backed-up five-worker cap opt-in remains
available in the same installation session; existing lower caps are otherwise preserved.''')
    replace('scripts/test_current.py',"VERSION = '3.1.1'","VERSION = '4.0.0'")
    replace('scripts/test_current.py',"'# Smart Orchestration 3.1'","'# Smart Orchestration 4.0'")
    replace('scripts/test_v31.py',"self.assertEqual(package.version,'3.1.1')","self.assertEqual(package.version,'4.0.0')")
    replace('scripts/test_v311.py',"'# Smart Orchestration 3.1.1'","'# Smart Orchestration 4.0.0'")
    replace('scripts/test_v311.py',"3.1.1={after}","current={after}")
    replace('scripts/test_migration.py',"'2e28dba69fb16dd8e14aa97a33862450d36a5d77')","'2e28dba69fb16dd8e14aa97a33862450d36a5d77',\n           'a6ad69249cf264c969c106e44b15bda1f4bf9ef3')")
    replace('docs/smart_orchestration.md','Smart 3.1 uses','Smart 4.0 uses')
    append('docs/smart_orchestration.md', '''4.0 adds conditionally loaded planning/debugging/branches/economics methods and an optional
stateless delivery adviser. The adviser recommends practice depth, bounds the next batch from
supplied quota/budget facts, and trips cumulative repair breakers without accepting work. It does
not replace allocation, evidence or native permissions. See [4.0 adaptation and validation](v4.0.md).''')
    append('docs/evaluation.md', '''For 4.0 evaluate the method, not only the model: clear copy edit without ceremony, ambiguous
feature with targeted decisions, reproducible behavior bug with honest RED/GREEN, pure refactor
with characterization, lost-context recovery without redispatch, low-quota required review, and
large-feature integration with complete candidate evidence. Keep matched requirements, baselines
and quality gates. Record repeated suites, unproductive repair waves and stale-evidence acceptance
as failures. Deterministic helper tests do not prove native LLM behavior or future cost savings.''')
    replace('README.md','# Smart Orchestration 3.1.1','# Smart Orchestration 4.0.0')
    replace('README.md','**Luna Max for useful work. Sol for depth. Testing without duplicate suites.**',
            '**Smart model routing. Disciplined engineering. Evidence without unnecessary ceremony.**')
    intro='''## What is new in 4.0

Smart keeps its Codex-specific model routing and quota discipline, with selected Superpowers
engineering practices adapted to the task rather than a second orchestrator.

```text
Main judgment + Smart routing + bounded quota-aware work
  |-- Systematic debugging: evidence, cause, one discriminating hypothesis
  |-- Targeted brainstorming only for genuinely unclear outcomes
  |-- Lean deliverable/decision/interface plans and long-task checkpoints
  |-- Real RED/GREEN for testable behavior; characterization or alternatives otherwise
  |-- Cumulative repair circuit breaker, never a shortcut to false completion
  |-- Evidence bound to the candidate, without duplicate valid test runs
  `-- Native-first branch/worktree workflow for large features and safe integration
```

Clear authorized work needs no repeat brainstorming gate. Plans describe contracts and coherent
outcomes, not full Main-authored code for a cheaper typist. Small tasks stay direct when useful.
Three failed causal fixes or three task repair/re-review waves triggers Main replanning; changing
workers does not reset counts. Budget exhaustion preserves blockers instead of waiving them.

Use a compact durable checkpoint for long/handoff work, not a ledger for every command. Reconcile
actual candidate/process state after context loss before repeating accepted work. Review spec and
technical quality together; keep independent review and actual visual acceptance where required.
Reuse appropriate test receipts, while all mandated fresh/full gates still run.

All eleven named presets and the five-worker ceiling remain unchanged. Main remains owner-selected;
Sol Medium is a recommendation, not an installer override. Observed low quota narrows concurrency,
and unknown usage does not trigger an expensive routine audit. Optional delivery.py advice is not
native quota metering, scheduling, enforcement or acceptance.

No Superpowers installation is needed. Do not activate two orchestration bootstraps for the same
work; report existing conflicts rather than automatically remove plugins. No telemetry, daemon,
new manager or standing agent team is added. Upstream methodology is credited and its MIT notice
is included in the package.

[4.0 source review, design and protocol](docs/v4.0.md) |
[Planning](codex_workflow/planning.md) | [Debugging](codex_workflow/debugging.md) |
[Economics](codex_workflow/economics.md) | [Branches](codex_workflow/branches.md)

## Retained 3.1.1 reliability foundations'''
    replace('README.md','## Maintenance patch 3.1.1',intro)
    replace('README.md','## What changes in 3.1','## Preserved model routing from 3.1')
    replace('README.md','An already verified 3.1.1 installation needs only this step;',
            'An already verified current installation needs only this cap step;')
    replace('README.md','[3.1.1 maintenance audit](docs/v3.1.1.md) |',
            '[4.0 adaptation and validation](docs/v4.0.md) | [3.1.1 maintenance audit](docs/v3.1.1.md) |')

    budgets={'smart_orchestration.md':1200,'execution.md':1000,'verification.md':700,
             'testing.md':650,'browser.md':650,'design.md':600,
             'planning.md':650,'debugging.md':650,'branches.md':650,'economics.md':650}
    for name,limit in budgets.items():
        words=len(load('codex_workflow/'+name).split())
        if words>=limit:raise RuntimeError(f'Guide budget {name}: {words} >= {limit}')
    for path,text in changes.items():
        if not text.endswith('\n'):raise RuntimeError('Missing newline: '+path)
        if path.endswith('.py'):compile(text,path,'exec')
        if path.endswith('.toml'):tomllib.loads(text)
        for ancestor in (ROOT/path,*(ROOT/path).parents):
            if ancestor==ROOT.parent:break
            if ancestor.is_symlink():raise RuntimeError('Symlink path: '+path)
    for path,text in changes.items():(ROOT/path).write_text(text)
    print(json.dumps({'base':BASE,'version':'4.0.0','changed_paths':sorted(changes),
                      'guide_words':{n:len(load('codex_workflow/'+n).split()) for n in budgets}},indent=2))

if __name__=='__main__':main()
