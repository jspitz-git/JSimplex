from pathlib import Path
import json,hashlib,subprocess,os
W=Path('/home/jspitz/.codex/worktrees/dual-step-experiment/JSimplex.jl');D=W/'diagnostics/dual-step-experiment/measurement';cache={}
def git(*a,input=None):return subprocess.check_output(['git','-C',str(W),*a],input=input)
def require(v,m):
 if not v:raise ValueError(m)
def digest(n):
 n=str(n)
 if n not in cache:
  with open(n,'rb') as f:cache[n]=hashlib.file_digest(f,'sha256').hexdigest()
 return cache[n]
require(not git('diff','--cached','--name-only').strip(),'index empty')
c=json.loads((D/'closure.json').read_text());require(c['accepted'] is True and all(x['passed'] for x in c['checks']),'PASS closure')
for n,h in c['bindings'].items():require(digest(n)==h,'closure bytes changed '+n)
for n,target in c['aliases'].items():require(Path(n).is_symlink() and os.readlink(n)==target and Path(n).resolve(strict=True)==W/'src','source alias unchanged')
for mode,count in [('qualify',622),('compare',642)]:
 p=json.loads((D/(mode+'-pins.json')).read_text());require(len(p['files'])==count and set(p['files'])==set(p['inventory']),'exact inventory '+mode)
 for n,v in p['inventory'].items():require(str(Path(n).resolve(strict=True))==v['resolved'] and digest(n)==v['sha256'],'launch binding changed '+n)
required={str(x.relative_to(W)) for x in D.rglob('*') if x.is_file() or x.is_symlink()}|{'diagnostics/dual-step-experiment/README.md'}
selfname=str((D/'publication.json').relative_to(W));require(selfname not in required,'publication exists')
def blob(n):
 p=W/n
 return git('hash-object','--stdin',input=os.fsencode(os.readlink(p))).decode().strip() if p.is_symlink() else git('hash-object','--',n).decode().strip()
def mode(n):return '120000' if (W/n).is_symlink() else ('100755' if os.stat(W/n).st_mode&0o111 else '100644')
r=dict(scope='exact Task6 localcommit, userauthorized eventual experimentbranch push; no master/CI change',names=sorted(required|{selfname}),blobs_excluding_self={n:blob(n) for n in sorted(required)},modes_excluding_self={n:mode(n) for n in sorted(required)},closure_sha256=digest(D/'closure.json'))
with (D/'publication.json').open('x') as f:json.dump(r,f,indent=2)
git('add','--',*r['names']);names=git('diff','--cached','--name-only','-z').decode().strip('\0').split('\0');require(names==r['names'],'exact staged names')
entries={}
for row in git('ls-files','--stage','-z','--',*names).split(b'\0'):
 if row:
  header,name=row.decode().split('\t',1);m,b,s=header.split();require(s=='0','index stage');entries[name]=dict(blob=b,mode=m)
require(set(entries)==set(names),'exact index membership')
for n,b in r['blobs_excluding_self'].items():require(entries[n]==dict(blob=b,mode=r['modes_excluding_self'][n]),'exact staged blob/mode '+n)
subprocess.run(['git','-C',str(W),'diff','--cached','--check'],check=True)
with Path('/tmp/task6-exact-staged.json').open('x') as f:json.dump(dict(names=names,entries=entries),f,indent=2)
print(json.dumps(dict(accepted=True,exact_staged_names_blobs_modes=len(names),publication_blob=entries[selfname]['blob'])))
