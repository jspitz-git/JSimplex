from pathlib import Path
import json,subprocess,hashlib,os
W=Path('/home/jspitz/.codex/worktrees/dual-step-experiment/JSimplex.jl');D=W/'diagnostics/dual-step-experiment/task5';cache={}
def git(*a,input=None):return subprocess.check_output(['git','-C',str(W),*a],input=input)
def require(v,m):
 if not v:raise ValueError(m)
def digest(n):
 n=str(n)
 if n not in cache:
  with open(n,'rb') as f:cache[n]=hashlib.file_digest(f,'sha256').hexdigest()
 return cache[n]
require(not git('diff','--cached','--name-only').strip(),'index must be empty')
c=json.loads((D/'closure.json').read_text());require(c['accepted'] is True and all(x['passed'] for x in c['checks']),'PASS closure')
for n,h in c['bindings'].items():require(digest(n)==h,'closure bytes changed '+n)
for n,target in c['aliases'].items():require(Path(n).is_symlink() and os.readlink(n)==target and Path(n).resolve(strict=True)==W/'src','source alias changed')
p=json.loads((D/'public-green-pins.json').read_text());require(len(p['files'])==590 and set(p['files'])==set(p['inventory']),'exact590pin inventory')
for n,v in p['inventory'].items():require(str(Path(n).resolve(strict=True))==v['resolved'] and digest(n)==v['sha256'],'launch binding changed '+n)
required={str(x.relative_to(W)) for x in D.rglob('*') if x.is_file() or x.is_symlink()}
required|={x.decode() for x in git('ls-files','--modified','-z','--','experimental/dual_engine','src/solver.jl','src/dual_simplex.jl','diagnostics/dual-step-experiment/README.md').split(b'\0') if x}
# Only new experimental Julia files plus existing modified ones belong in this Task5 commit.
required|={x.decode() for x in git('ls-files','--others','--exclude-standard','-z','--','experimental/dual_engine').split(b'\0') if x}
selfname=str((D/'publication.json').relative_to(W));require(selfname not in required,'publication already exists')
def blob(n):
 path=W/n
 return git('hash-object','--stdin',input=os.fsencode(os.readlink(path))).decode().strip() if path.is_symlink() else git('hash-object','--',n).decode().strip()
def mode(n):return '120000' if (W/n).is_symlink() else ('100755' if os.stat(W/n).st_mode&0o111 else '100644')
record=dict(scope='exact local Task5 branch commit only; no master/push/Task6',names=sorted(required|{selfname}),blobs_excluding_self={n:blob(n) for n in sorted(required)},modes_excluding_self={n:mode(n) for n in sorted(required)},closure_sha256=digest(D/'closure.json'))
with (D/'publication.json').open('x') as f:json.dump(record,f,indent=2)
git('add','--',*record['names'])
actual=git('diff','--cached','--name-only','-z').decode().strip('\0').split('\0');require(actual==record['names'],'exact stage names')
entries={}
for row in git('ls-files','--stage','-z','--',*actual).split(b'\0'):
 if row:
  header,name=row.decode().split('\t',1);m,b,stage=header.split();require(stage=='0','index stage');entries[name]=dict(blob=b,mode=m)
require(set(entries)==set(actual),'exact index membership')
for n,b in record['blobs_excluding_self'].items():require(entries[n]['blob']==b and entries[n]['mode']==record['modes_excluding_self'][n],'staged bytes/mode '+n)
# The helper is an exact original definitions-only prefix; retain its final separator.
verbatim='diagnostics/dual-step-experiment/task5/recording-logger-helpers.jl'
require(digest(W/verbatim)==p['inventory'][str(W/verbatim)]['sha256'],'verbatim helper changed')
subprocess.run(['git','-C',str(W),'diff','--cached','--check','--','.',':!'+verbatim],check=True)
warning=subprocess.run(['git','-C',str(W),'diff','--cached','--check','--',verbatim],capture_output=True,text=True)
require(warning.returncode==2 and warning.stdout==verbatim+':26: new blank line at EOF.\n' and not warning.stderr,'only exact original helper EOF separator warning allowed')
with Path('/tmp/task5-exact-staged.json').open('x') as f:json.dump(dict(names=actual,entries=entries),f,indent=2)
print(json.dumps(dict(accepted=True,exact_staged_names_blobs_modes=len(actual),publication_blob=entries[selfname]['blob'])))
