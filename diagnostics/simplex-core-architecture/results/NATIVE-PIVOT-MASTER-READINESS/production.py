from pathlib import Path
import json,hashlib,subprocess
Q=Path(__file__).resolve().parent;R=Q.parents[3];P=Q.parent/'NATIVE-PIVOT-PRODUCTION-INTEGRATION-PREPARATION';W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl');BASE='6f68e24e8ddac42b948da8fcc2d636c010751194'
def git(*a,cwd=W):return subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
def need(v,m):
 if not v:raise RuntimeError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,j):
 with (Q/n).open('x') as f:json.dump(j,f,indent=2);f.write('\n')
review=json.loads((P/'review-final.json').read_text());need(review['accepted'] and not review['findings'],'Review');need(git('rev-parse','HEAD')==BASE and not git('status','--porcelain'),'Clean base');need(git('rev-parse','master')==BASE,'Master')
manifest=json.loads((P/'payload-manifest.json').read_text());need(manifest['master']==BASE and len(manifest['files'])==10,'Manifest')
for x in manifest['files']:
 p=W/x['destination'];need(sha(R/x['payload'])==x['sha256'],'Payload');need((not p.exists()) if x['original_sha256'] is None else sha(p)==x['original_sha256'],'Original')
 need(x['original_git_blob'] is None or git('rev-parse',BASE+':'+x['destination'])==x['original_git_blob'],'Original blob')
# Native worktree tool supplies detached checkout; give it the accepted branch.
subprocess.run(['git','switch','-c','codex/native-pivot-production-integration'],cwd=W,check=True)
for x in manifest['files']:
 p=W/x['destination'];p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes((R/x['payload']).read_bytes())
names=sorted(x['destination'] for x in manifest['files']);subprocess.run(['git','add','--',*names],cwd=W,check=True)
need(git('diff','--cached','--name-only').splitlines()==names,'Exact staged names')
for x in manifest['files']:need(git('show',':'+x['destination'])==(R/x['payload']).read_text().rstrip('\n'),'Staged content')
subprocess.run(['git','diff','--cached','--check'],cwd=W,check=True)
subprocess.run(['git','commit','-m','Add optional threshold-one policy for managed native basis factors'],cwd=W,check=True)
commit=git('rev-parse','HEAD');need(git('rev-parse','HEAD^')==BASE,'Parent');need(git('diff-tree','--no-commit-id','--name-only','-r',commit).splitlines()==names,'Exact commit')
for x in manifest['files']:need(sha(W/x['destination'])==x['sha256'] and git('hash-object',x['destination'])==git('rev-parse',commit+':'+x['destination']),'Commit bytes')
need(not git('status','--porcelain') and git('rev-parse','master')==BASE,'Clean isolated commit/master')
save('production-commit.json',dict(base=BASE,commit=commit,worktree=str(W),branch=git('branch','--show-current'),names=names,blobs={n:git('rev-parse',commit+':'+n) for n in names},sha256={x['destination']:x['sha256'] for x in manifest['files']},review_sha256=sha(P/'review-final.json'),script_sha256=sha(Path(__file__)),pushed=False))
print('Local production commit',commit,'exact10files; master unchanged')
