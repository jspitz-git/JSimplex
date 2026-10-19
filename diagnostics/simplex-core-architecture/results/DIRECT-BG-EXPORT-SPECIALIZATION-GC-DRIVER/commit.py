"""Fail-fast publication of exact reviewed diagnostics only."""
from pathlib import Path
import subprocess,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
expected='ff248544e8f89cc05aecff64806bf60d8b2bd9cf';master='26e2291745999f485a74f643298ca997d65c7205'
v=json.loads(Path('/tmp/bgxs-gc-driver-exact-staged.json').read_text());blobs=v['staged_blobs'];names=set(blobs)
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
def require(v,msg):
 if not v:raise RuntimeError(msg)
require(v['all_passed'] and v['files']==len(names),'Publication record')
require(git('rev-parse','HEAD')==expected and git('rev-parse','master')==master,'Refs changed')
require(git('branch','--show-current')=='codex/simplex-core-architecture','Wrong branch')
require(set(git('diff','--cached','--name-only').splitlines())==names,'Exact staged names')
require(all(n.startswith('diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER/') for n in names),'Narrow planning scope')
require(all(git('rev-parse',':'+n)==b==git('hash-object',n) for n,b in blobs.items()),'Exact staged/worktree blobs')
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
subprocess.run(['git','commit','-m','diagnostics: prepare separate GC RED GREEN admission and auditor'],cwd=R,check=True)
head=git('rev-parse','HEAD')
require(set(git('diff-tree','--no-commit-id','--name-only','-r',head).splitlines())==names,'Committed exact names')
require(all(git('rev-parse',head+':'+n)==b for n,b in blobs.items()),'Committed exact blobs')
require(git('rev-parse','master')==master and not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Master/working tree changed')
subprocess.run(['git','push','origin','HEAD:refs/heads/codex/simplex-core-architecture'],cwd=R,check=True)
remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
require(head+'\trefs/heads/codex/simplex-core-architecture' in remote and master+'\trefs/heads/master' in remote,'Remote refs mismatch')
print(json.dumps(dict(committed=head,files=len(names),all_committed_blobs_verified=True,remote_verified=True,master_unchanged=master)))
