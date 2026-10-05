"""Publish tested product files to an isolated preparation branch, never main or releases."""
import json,os,subprocess
from pathlib import Path
REPO='7Eterius/codex_smart_orchestration'
BRANCH='maintenance/prepare-v3.1.1'
assert os.environ['GITHUB_REPOSITORY']==REPO
assert os.environ['GITHUB_REF']=='refs/heads/'+BRANCH
PARENT=os.environ['GITHUB_SHA']
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
def api(path,payload=None,method=None):
    args=['gh','api']+(['--method',method] if method else [])+['repos/'+REPO+'/'+path]
    if payload is not None:args+=['--input','-']
    result=subprocess.run(args,input=json.dumps(payload) if payload is not None else None,capture_output=True,text=True,check=True)
    return json.loads(result.stdout)
assert git('rev-parse','HEAD')==PARENT
assert api('git/ref/heads/'+BRANCH)['object']['sha']==PARENT,'Concurrent edit; stop'
subprocess.run(['git','add','-u','--','codex_workflow','scripts','docs','README.md'],check=True)
subprocess.run(['git','add','--','scripts/test_v311.py','docs/v3.1.1.md'],check=True)
paths=subprocess.check_output(['git','diff','--cached','--name-only','-z']).decode().split('\0')
entries=[]
for path in filter(None,paths):
    p=Path(path)
    assert p.parts[0] in {'codex_workflow','scripts','docs','README.md'}
    assert p.is_file() and not p.is_symlink() and (p.suffix in {'.py','.md','.toml'} or p.name=='VERSION')
    entries.append({'path':path,'mode':'100755' if p.stat().st_mode & 0o111 else '100644','type':'blob','content':p.read_text()})
assert entries and Path('codex_workflow/operate/VERSION').read_text()=='3.1.1\n'
tree=api('git/trees',{'base_tree':git('rev-parse','HEAD^{tree}'),'tree':entries},'POST')['sha']
commit=api('git/commits',{'tree':tree,'parents':[PARENT],'message':'Validated Smart 3.1.1 maintenance source; final workflow pending connector publication'},'POST')['sha']
assert api('git/ref/heads/'+BRANCH)['object']['sha']==PARENT,'Concurrent edit; stop'
api('git/refs/heads/'+BRANCH,{'sha':commit,'force':False},'PATCH')
print(json.dumps({'source_commit':commit,'tree':tree,'files':len(entries),
'validated_workflow_blob':git('hash-object','.github/workflows/validate.yml')},indent=2))
