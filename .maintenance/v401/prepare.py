"""One-shot base-checked release assembly; no installed setup service."""
from pathlib import Path
import hashlib
import json
import subprocess

BASE='332da7c08adfce2ac4d24d8a4a9a69dae3ebe017'
ROOT=Path(__file__).resolve().parents[2]
changes={}
def source(path):
    if path in changes:return changes[path]
    p=ROOT/path
    assert not p.is_symlink()
    text=p.read_text()
    old=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT).decode()
    assert text==old,'Base source changed: '+path
    return text

def replace(path,old,new):
    text=source(path)
    assert text.count(old)==1,(path,old,text.count(old))
    changes[path]=text.replace(old,new)

def append(path,text):
    changes[path]=source(path).rstrip()+'\n\n'+text.strip()+'\n'

subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=ROOT,check=True)
changed=set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines())
assert changed=={'.maintenance/v401/patch_delivery.py','.maintenance/v401/prepare.py',
                 '.maintenance/v401/publish.py','.github/workflows/prepare-smart-v401.yml',
                 'scripts/test_v401.py','docs/v4.0.1.md'},changed
b=(ROOT/'scripts/test_v401.py').read_bytes()
assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()=='a2e97abdcdb0914964c788282dd8c6f1e7517ba5'
replace('codex_workflow/operate/VERSION','4.0.0\n','4.0.1\n')
replace('codex_workflow/operate/user_AGENTS.md','<!-- codex-workflow-version: 4.0.0 -->','<!-- codex-workflow-version: 4.0.1 -->')
replace('scripts/test_current.py',"VERSION = '4.0.0'","VERSION = '4.0.1'")
replace('scripts/test_v31.py',"self.assertEqual(package.version,'4.0.0')","self.assertEqual(package.version,'4.0.1')")
replace('scripts/test_v311.py',"startswith('# Smart Orchestration 4.0.0')","startswith('# Smart Orchestration 4.0.1')")
replace('scripts/test_v4.py',"self.assertEqual(package.version,'4.0.0')","self.assertEqual(package.version,'4.0.1')")
replace('scripts/test_v4.py',"imported <= {'argparse','json','math','sys'}","imported <= {'argparse','json','math','sys','os','stat'}")
replace('scripts/test_migration.py',"'a6ad69249cf264c969c106e44b15bda1f4bf9ef3')","'a6ad69249cf264c969c106e44b15bda1f4bf9ef3',\n           '332da7c08adfce2ac4d24d8a4a9a69dae3ebe017')")
replace('README.md','# Smart Orchestration 4.0.0','# Smart Orchestration 4.0.1')
replace('README.md','## What is new in 4.0','''## Bugfix 4.0.1

The model map and five-worker ceiling are unchanged. The delivery adviser now compares decimal
budgets without binary-rounding errors, accounts for already-open workers when supplied, and
supports a recorded bounded replan without resetting cumulative repair history. Tester/reviewer
recovery requires implementation handoff. Read-only code research/docs avoid irrelevant test or
worktree setup. Descriptor-based input checks reject final-component symlink/special-file races
on supported POSIX hosts; programming defects are not disguised as bad input.

Existing required fields remain supported. New optional fields are described in the installed
debugging/economics guides and [4.0.1 bugfix notes](docs/v4.0.1.md). These are advisory source fixes,
not measured native-agent speed or allowance improvements. Use the complete pinned release source
and the existing preview/apply/check update procedure. No extra plugin or service is required.

## What is new in 4.0''')
append('codex_workflow/debugging.md','''## Bounded resume after replanning

With delivery.py, Main records optional `replan`: task, defect, decision_ref, current cumulative
failed_fixes and repair_rounds, and attempt_limit (1-3). Identity must match. Lifetime counters
never decrease; the new window consumes their deltas and reports remaining_attempts. New evidence,
quota, authority and implementation ownership still bind. Only the exact new baseline acknowledges
a prior stall; later failures can stop again. Changing workers alone is not a replan.''')
append('codex_workflow/economics.md','''## Budget observation precision

For delivery.py, supply optional open_workers from existing observations, counting owned open
threads until native closure. Quota ceilings then cover existing plus new workers. Omission keeps
legacy next-batch-only advice, explicitly labeled new_batch_only; explicit null requests inspection.
No worker is closed automatically. Decimal budget comparisons preserve the supplied values without
binary subtraction drift, but estimates and observations remain unverified. Required allocator
scope/capacity/review reservations still apply; no extra quota audit is needed.''')
for path,text in changes.items():
    if path.endswith('.py'):compile(text,path,'exec')
    if path in ('codex_workflow/debugging.md','codex_workflow/economics.md'):
        assert len(text.split())<650,(path,len(text.split()))
    (ROOT/path).write_text(text)
subprocess.run(['python','-B','.maintenance/v401/patch_delivery.py'],cwd=ROOT,check=True)
print(json.dumps({'version':'4.0.1','base':BASE,'changed':sorted(changes),
                  'delivery_blob':'b79ce1249f5eed6eb5410e381a31f81fee3cb093'},indent=2))
