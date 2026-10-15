#!/usr/bin/env python3
"""Assemble only the reviewed 4.2 payload on an exact isolated source baseline."""
import base64
import bz2
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tomllib

BASE='e725c152dea3a8794df0eb2d418831905382ca8c'
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent

def replace(path,old,new,expected=1):
    p=ROOT/path;s=p.read_text()
    if s.count(old)!=expected: raise RuntimeError(f'{path}: expected {expected}, got {s.count(old)}: {old[:80]}')
    p.write_text(s.replace(old,new))

def append(path,text):
    p=ROOT/path;p.write_text(p.read_text().rstrip()+'\n\n'+text.strip()+'\n')

def main():
    subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=ROOT,check=True)
    subprocess.run(['git','diff','--exit-code',BASE,'--','README.md','codex_workflow','docs','scripts','tools','examples','.github/workflows/validate.yml'],cwd=ROOT,check=True)
    assert (ROOT/'codex_workflow/operate/VERSION').read_text().strip()=='4.0.1'
    # Repair two checksum-identified transport-copy insertions, not source content.
    part=HERE/'payload.part04';raw=part.read_bytes()
    def blob_sha(value):return hashlib.sha1(b'blob '+str(len(value)).encode()+b'\0'+value).hexdigest()
    if blob_sha(raw)=='4bb008552e12986a7526120a026979721564f94c':
        raw=raw.replace(b'pyKKCCoo',b'pyKCCoo').replace(b'RleWe0',b'RleW0')
        assert blob_sha(raw)=='56311b4ad97632a849b2094adb9df14dd2cdb96b'
        part.write_bytes(raw)
    encoded=''.join(p.read_text().strip() for p in sorted(HERE.glob('payload.part*')))
    compressed=base64.b64decode(encoded,validate=True)
    assert hashlib.sha256(compressed).hexdigest()==(HERE/'payload.sha256').read_text().strip()
    payload=json.loads(bz2.decompress(compressed))
    roles=payload.pop('roles')
    files=payload['files']
    for path,text in files.items():
        p=Path(path)
        assert not p.is_absolute() and '..' not in p.parts and '.git' not in p.parts
        assert p.parts[0] in {'codex_workflow','scripts','tools','examples','docs'}
        assert text.endswith('\n')
        dst=ROOT/p
        assert not any(q.is_symlink() for q in (dst,*dst.parents))
        dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(text)
    before_roles={}
    for name,body in roles.items():
        path=ROOT/f'codex_workflow/agents/{name}.toml'
        s=path.read_text();before=tomllib.loads(s);before_roles[name]=before.copy()
        assert len(body.split())<200
        s,n=re.subn(r'developer_instructions = """\n.*?\n"""',lambda _: 'developer_instructions = """\n'+body.strip()+'\n"""',s,flags=re.S)
        assert n==1,name
        after=tomllib.loads(s);before.pop('developer_instructions');after.pop('developer_instructions')
        assert before==after,'Non-instruction preset change'
        path.write_text(s)
    replace('codex_workflow/operate/VERSION','4.0.1\n','4.2.0\n')
    p=ROOT/'codex_workflow/operate/user_AGENTS.md';s=p.read_text()
    s=s.replace('codex-workflow-version: 4.0.1','codex-workflow-version: 4.2.0')
    s=s.replace('No second orchestration layer, telemetry or mandatory ledger.',
                'Use handoffs.md for duty transfers and native lifecycle; receipts.md for substantial verification; standards.md for scoped rules. No second orchestration layer, telemetry or mandatory ledger.')
    p.write_text(s)
    replace('codex_workflow/runtime/layout.py','_REQUIRED = (\n',
            '_REQUIRED = (\n    "handoffs.md", "receipts.md", "standards.md",\n    "runtime/work_contracts.py", "runtime/verification_run.py", "runtime/review_rules.py",\n')
    p=ROOT/'codex_workflow/runtime/smart_config.py';s=p.read_text()
    a=s.index('def bootstrap(home: Path) -> str:');b=s.index('def _statements(text: str):')
    body='''def bootstrap(home: Path) -> str:
    policy = str(home / 'codex_workflow' / 'smart_orchestration.md')
    return f\'''Smart Orchestration 4.2.0: Main reads {json.dumps(policy, ensure_ascii=False)} once for substantive work. Named workers follow their role and bounded assignment.
Main owns judgment and acceptance. Main may implement small understood or disjoint critical-path work. Delegate coherent outcomes, not pre-solved patches. Preserve named Luna/Sol routing and separate procedural testing from independent review.
Use relevant guides only. Reuse related context; substantive duty/risk/scope changes require explicit suitable ownership, evidence, repair history and pending gates. Native roles cannot be changed by prose. Suppress no-change acknowledgements, not decisions or blockers.
Run useful independent work in parallel, at most five owned open workers within verified native capacity. Completion is not closure; copied parent turns are not worker activity. Preserve scopes, candidate holds and independent gates.
Use original subprocess results, unique failed evidence and scoped project standards. Reuse applicable checks; required fresh/full gates bind. Main inspects actual visuals. Budget exhaustion never implies acceptance. No new daemon, mandatory ledger, automatic hooks, permission expansion, model downgrade or restart. Owner/project rules bind; disk checks are not live qualification.\'''


'''
    p.write_text(s[:a]+body+s[b:])
    # Cross-links replace repeated method prose, rather than adding a second orchestrator.
    p=ROOT/'codex_workflow/execution.md';s=p.read_text();marker='## Method is not another orchestration layer'
    assert marker in s
    s=s[:s.index(marker)]+'''## Material transfers and native lifecycle

Read handoffs.md at substantive duty/scope/risk changes. Preserve useful context, requirement,
source/resource ownership, authority, original evidence, cumulative repairs and pending gates.
A retained Investigator is not automatically an implementation owner. Tester runs selected
procedures; new check authoring and diagnosis need appropriate ownership even in ignored artifacts.
No prose retag changes native model/role. Capacity facts must identify the effective native domain,
primary inclusion and actual retained/open/closed states, not copied turns or disk keys alone.
Optional work_contracts.py advice cannot replace allocation scope/reservation checks. No duplicate
review seats, status acknowledgements or mandatory per-command ledger.
'''
    p.write_text(s)
    append('codex_workflow/testing.md','''Read receipts.md when existing commands lack reliable execution receipts. Wrapper zero is not a
nested test pass. Keep failed/intermediate artifacts under unique names. Tester cannot author new
verification logic merely because its files are ignored; hand that scope to appropriate ownership.''')
    p=ROOT/'codex_workflow/verification.md';s=p.read_text();marker='## Completion claims and integrated review';assert marker in s
    p.write_text(s[:s.index(marker)]+'''## Scoped standards and completion

Read standards.md for applicable project criteria and optional labelled reviewer evaluation. Keep
mechanical checks first and one independent spec/quality pass. Rules supplement requirements;
changed or missing evidence stays visible. Writers cannot weaken standards to approve their patch.
Bind completion to actual candidate and decisive evidence. Inspect wrapper/nested-exit conflicts;
process success is not coverage, deployment or live activation. Preserve unique failed artifacts.
Large features need integrated contract review, not duplicate suites. A circuit breaker never
accepts unresolved required findings. Main retains actual visual judgment and final acceptance.
''')
    append('codex_workflow/planning.md','''At material assignment changes use handoffs.md: carry source/resource scope, native owner/preset,
purpose/risk, evidence, cumulative attempts and pending gates. Use one compact existing record.
Do not infer duplicated investigation from old role tags or encrypted followup counts.''')
    append('codex_workflow/browser.md','''Before fixing repeated locator failures, inspect the actual accessible role/name, visibility and
container scope. A new journey/probe or diagnostic helper needs check-design ownership, not an
unannounced expansion of procedural Tester. Preserve failed traces under distinct attempt names.''')
    append('codex_workflow/runtime_check.md','''For 4.2, distinguish the actual backend's effective capacity from every on-disk cap namespace.
A completed turn is not closure and persistent history is not continuous residency. Use existing
native evidence when necessary; no cap-probe fan-out or automatic namespace edits. Use handoffs.md.
Optional receipts/standards helpers do not prove native enforcement or model quality. No automatic
hooks, external deciders, background collectors or repeat full-suite qualification is introduced.''')
    append('codex_workflow/operate/smart_install.md','''## 4.2 boundaries

The declared package adds handoff/receipt/standard guides and three optional helpers. Models,
efforts, permissions and explicit caps remain. Collector and example/evaluation corpora stay
source-only and are not installed as telemetry or project rules. No hooks or decider services are
automatically activated. Preserve known V2 settings without inventing precedence; actual native
admission still needs runtime evidence. Complete preview/apply/check and restart manually once.''')
    append('docs/evaluation.md','''For 4.2, exclude copied parent turns before worker-overlap analysis; distinguish logical turns,
command envelopes, native residency and inference. Recognize executed commands rather than test
words in status filters, and preserve native wrapper versus embedded outcome evidence. Segment
real duties at material handoffs instead of treating lifetime role tags as cost labels. Repeated
commands after changed inputs or RED/GREEN are not automatically waste. Evaluate scoped review
rules on separately labelled development/holdout cases; synthetic plumbing tests do not qualify
a model. No target Luna percentage, weekly waste estimate or savings claim follows from the
purposive audit. Keep private provenance local.''')
    append('docs/smart_orchestration.md','''Smart 4.2 retains routing and allocator behavior while adding explicit assignment/native-domain
advice, create-only original-exit verification receipts, scoped reviewer criteria/evaluation,
and source-only collector attribution regressions. No native admission enforcement or model
quality is implied by helper tests. See [4.2 design and limits](v4.2.md).''')
    p=ROOT/'README.md';s=p.read_text();assert s.startswith('# Smart Orchestration 4.0.1')
    s=s.replace('# Smart Orchestration 4.0.1','# Smart Orchestration 4.2.0',1)
    insertion='''## New in 4.2: evidence-led efficiency

The targeted 4.0.1 audit corrected the apparent fourteen-worker peak to copied parent history;
genuine own closed turns in that episode peaked at five. Historical open-thread occupancy remains
unresolved. Sampled repeats included status checks, changed inputs and real RED/GREEN. Sampled
Deep/Senior assignments were justified, so **all eleven model/effort presets remain unchanged**.

4.2 improves concrete mechanisms instead: explicit duty/ownership/risk transitions with useful
context reuse; actual native capacity-domain distinctions; procedural Tester boundaries; original
subprocess exits and uniquely preserved evidence; scoped, example-backed standards in the existing
review; and omission of repeated no-change acknowledgements. No extra manager, compulsory workflow
ledger, automatic hook, external decider, project mutation or quota-driven model downgrade.

Optional Python helpers replace repetitive bookkeeping only where needed. Small tasks stay direct.
The offline collector now handles copied ancestor turns, test words inside status inspections and
zero wrappers with conflicting nested status. It remains source-only, not installed telemetry.
No real-project speed, quality or allowance saving is claimed from synthetic tests.

[4.2 design, protocols and audit lessons](docs/v4.2.md) |
[Handoffs and native lifecycle](codex_workflow/handoffs.md) |
[Verification receipts](codex_workflow/receipts.md) |
[Scoped standards](codex_workflow/standards.md) |
[Offline collector](tools/stats/README.md)

## Retained 4.0 engineering foundations'''
    assert '## What is new in 4.0' in s
    s=s.replace('## What is new in 4.0',insertion,1)
    p.write_text(s)
    # Change active package assertions only, not historical fixture references.
    for p in (ROOT/'scripts').glob('test_*.py'):
        if p.name.startswith('test_v42'): continue
        s=p.read_text();lines=s.splitlines(True)
        for i,line in enumerate(lines):
            if p.name=='test_current.py' and line.startswith("VERSION = '4.0.1'"):
                lines[i]=line.replace('4.0.1','4.2.0')
            elif 'self.assert' in line and ('.version' in line or '# Smart Orchestration' in line):
                lines[i]=line.replace('4.0.1','4.2.0').replace('# Smart Orchestration 4.0','# Smart Orchestration 4.2')
        p.write_text(''.join(lines))
    replace('scripts/test_migration.py',"'332da7c08adfce2ac4d24d8a4a9a69dae3ebe017')", "'332da7c08adfce2ac4d24d8a4a9a69dae3ebe017',\n           '776e0fc58e388996faa3471edb5b80286052bf5c',\n           'e725c152dea3a8794df0eb2d418831905382ca8c')")
    replace('.github/workflows/validate.yml',
            "      - name: Syntax and changed-commit whitespace checks\n", "      - name: Offline collector regression suite\n        run: python -B -m unittest discover -s tools/stats -p 'test_*.py' -v\n      - name: Syntax and changed-commit whitespace checks\n")
    # No protected routing, permissions, installer transaction or allocation logic changes.
    subprocess.run(['git','diff','--exit-code',BASE,'--','codex_workflow/runtime/allocation.py','codex_workflow/runtime/delivery.py',
                    'codex_workflow/runtime/agent_defaults.py','codex_workflow/runtime/config_assessment.py',
                    'codex_workflow/runtime/transaction.py','codex_workflow/runtime/smart_install.py'],cwd=ROOT,check=True)
    for p in list((ROOT/'codex_workflow').rglob('*.py'))+list((ROOT/'scripts').glob('*.py')):
        compile(p.read_text(),str(p),'exec')
    sys_path=__import__('sys').path;sys_path.insert(0,str(ROOT/'codex_workflow'))
    from runtime.smart_config import bootstrap
    words=len(bootstrap(Path('/example')).split());assert words<=174,words
    budgets={'smart_orchestration.md':1200,'execution.md':1000,'verification.md':700,'testing.md':650,
             'browser.md':650,'design.md':600,'handoffs.md':600,'receipts.md':600,'standards.md':600}
    counts={name:len((ROOT/'codex_workflow'/name).read_text().split()) for name in budgets}
    assert all(counts[k]<v for k,v in budgets.items()),counts
    print(json.dumps(dict(version='4.2.0',base=BASE,bootstrap_words=words,guide_words=counts),indent=2))

if __name__=='__main__':main()
