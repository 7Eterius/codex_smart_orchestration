"""Publish tested source to one isolated branch; no main/tag/release or permission changes."""
import json
import os
from pathlib import Path
import subprocess
REPO='7Eterius/codex_smart_orchestration'
BRANCH='smart/v3.1-balanced-routing'
assert os.environ['GITHUB_REPOSITORY']==REPO
assert os.environ['GITHUB_REF']=='refs/heads/'+BRANCH
parent=os.environ['GITHUB_SHA']
def git(*args):
    return subprocess.check_output(['git',*args],text=True).strip()
def api(path,payload=None,method=None):
    args=['gh','api']
    if method:args += ['--method',method]
    args += ['repos/'+REPO+'/'+path]
    if payload is not None:args += ['--input','-']
    result=subprocess.run(args,input=None if payload is None else json.dumps(payload),capture_output=True,text=True,check=True)
    return json.loads(result.stdout)
assert git('rev-parse','HEAD')==parent
assert api('git/ref/heads/'+BRANCH)['object']['sha']==parent,'Branch changed; stop, never overwrite'
subprocess.run(['git','add','-u','--','codex_workflow','docs','scripts','README.md'],check=True)
subprocess.run(['git','add','--','codex_workflow/agents/deep_executor.toml','codex_workflow/agents/reviewer.toml','codex_workflow/agents/senior_reviewer.toml','codex_workflow/testing.md','docs/v3.1.md','scripts/test_v31.py'],check=True)
paths=subprocess.check_output(['git','diff','--cached','--name-only','-z']).decode().split('\0')
entries=[]
for path in filter(None,paths):
    p=Path(path)
    assert p.parts[0] in {'codex_workflow','docs','scripts','README.md'}
    assert not p.is_symlink() and p.is_file()
    assert p.suffix in {'.md','.py','.toml'} or p.name=='VERSION'
    entries.append({'path':path,'mode':'100755' if p.stat().st_mode & 0o111 else '100644','type':'blob','content':p.read_text()})
assert entries,'No source changes'
assert Path('codex_workflow/operate/VERSION').read_text().strip()=='3.1.0'
tree=api('git/trees',{'base_tree':git('rev-parse','HEAD^{tree}'),'tree':entries},'POST')['sha']
commit=api('git/commits',{'message':'Smart 3.1: Luna Max routing, Sol depth presets and separate procedural testing','tree':tree,'parents':[parent]},'POST')['sha']
assert api('git/ref/heads/'+BRANCH)['object']['sha']==parent,'Concurrent branch change; stop'
api('git/refs/heads/'+BRANCH,{'sha':commit,'force':False},'PATCH')
print(json.dumps({'validated_source_commit':commit,'tree':tree,'branch':BRANCH,'files':len(entries)},indent=2))
