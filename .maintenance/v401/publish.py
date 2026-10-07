"""Publish tested source only to this isolated preparation branch."""
import json
import os
from pathlib import Path
import subprocess
REPO='7Eterius/codex_smart_orchestration'
BRANCH='maintenance/prepare-v4.0.1'
assert os.environ['GITHUB_REPOSITORY']==REPO
assert os.environ['GITHUB_REF']=='refs/heads/'+BRANCH
parent=os.environ['GITHUB_SHA']
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
def api(path,payload=None,method=None):
    args=['gh','api']
    if method:args+=['--method',method]
    args+=['repos/'+REPO+'/'+path]
    if payload is not None:args+=['--input','-']
    ran=subprocess.run(args,input=None if payload is None else json.dumps(payload),text=True,capture_output=True,check=True)
    return json.loads(ran.stdout)
assert git('rev-parse','HEAD')==parent
assert api('git/ref/heads/'+BRANCH)['object']['sha']==parent,'Concurrent branch change'
subprocess.run(['git','add','-u','--','README.md','codex_workflow','docs','scripts'],check=True)
paths=subprocess.check_output(['git','diff','--cached','--name-only','-z']).decode().split('\0')
entries=[]
for name in filter(None,paths):
    p=Path(name)
    assert p.parts[0] in {'README.md','codex_workflow','docs','scripts'}
    assert p.is_file() and not p.is_symlink()
    assert p.suffix in {'.md','.py','.toml','.txt'} or p.name=='VERSION'
    entries.append(dict(path=name,mode='100755' if p.stat().st_mode&0o111 else '100644',type='blob',content=p.read_text()))
assert entries and Path('codex_workflow/operate/VERSION').read_text().strip()=='4.0.1'
# Model and permission presets are deliberately unchanged.
subprocess.run(['git','diff','--exit-code','332da7c08adfce2ac4d24d8a4a9a69dae3ebe017','--','codex_workflow/agents','codex_workflow/runtime/allocation.py','codex_workflow/runtime/agent_defaults.py'],check=True)
tree=api('git/trees',dict(base_tree=git('rev-parse','HEAD^{tree}'),tree=entries),'POST')['sha']
commit=api('git/commits',dict(message='Smart 4.0.1: validated budget and recovery bugfixes',tree=tree,parents=[parent]),'POST')['sha']
assert api('git/ref/heads/'+BRANCH)['object']['sha']==parent,'Concurrent branch change'
api('git/refs/heads/'+BRANCH,dict(sha=commit,force=False),'PATCH')
print(json.dumps(dict(source_commit=commit,tree=tree,changed_files=len(entries)),indent=2))
