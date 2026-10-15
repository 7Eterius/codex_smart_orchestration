"""Publish validated text to the preparation branch only, never main/tags/workflows."""
import json
import os
from pathlib import Path
import subprocess
REPO='7Eterius/codex_smart_orchestration';BRANCH='maintenance/prepare-v4.2.1'
assert os.environ['GITHUB_REPOSITORY']==REPO
assert os.environ['GITHUB_REF']=='refs/heads/'+BRANCH
parent=os.environ['GITHUB_SHA']
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
def api(path,value=None,method=None):
    args=['gh','api']
    if method:args+=['--method',method]
    args+=['repos/'+REPO+'/'+path]
    if value is not None:args+=['--input','-']
    ran=subprocess.run(args,input=None if value is None else json.dumps(value),text=True,capture_output=True)
    if ran.returncode:raise RuntimeError(path+': '+ran.stderr[-2000:])
    return json.loads(ran.stdout)
assert git('rev-parse','HEAD')==parent
assert api('git/ref/heads/'+BRANCH)['object']['sha']==parent
subprocess.run(['git','add','-u','--','README.md','codex_workflow','docs','scripts','tools'],check=True)
subprocess.run(['git','add','--','scripts/test_v421.py','tools/stats/test_stats_v121.py','docs/v4.2.1.md'],check=True)
paths=subprocess.check_output(['git','diff','--cached','--name-only','-z']).decode().split('\0')
entries=[]
for name in filter(None,paths):
    p=Path(name)
    assert p.parts[0] in {'README.md','codex_workflow','docs','scripts','tools'}
    assert p.is_file() and not p.is_symlink()
    assert p.suffix in {'.py','.md','.txt'} or p.name=='VERSION'
    entries.append(dict(path=name,mode='100755' if p.stat().st_mode&0o111 else '100644',type='blob',content=p.read_text()))
assert 1<=len(entries)<=35
assert Path('codex_workflow/operate/VERSION').read_text().strip()=='4.2.1'
tree=api('git/trees',dict(base_tree=git('rev-parse','HEAD^{tree}'),tree=entries),'POST')['sha']
commit=api('git/commits',dict(message='Smart 4.2.1: validated targeted efficiency and reliability patch',tree=tree,parents=[parent]),'POST')['sha']
assert api('git/ref/heads/'+BRANCH)['object']['sha']==parent
api('git/refs/heads/'+BRANCH,dict(sha=commit,force=False),'PATCH')
print(json.dumps(dict(source_commit=commit,tree=tree,changed_files=len(entries)),indent=2))
