"""One-shot exact diagnostic staging after separately passed closure."""
from pathlib import Path
import json,hashlib,subprocess
Q=Path(__file__).resolve().parent;R=Q.parents[3];RUNS=Q.parent/'NATIVE-PIVOT-MASTER-READINESS/runs'
def need(v,m):
 if not v:raise RuntimeError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
def save(p,o):
 with p.open('x') as f:json.dump(o,f,indent=2);f.write('\n')
def run(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
closure=rd(Q/'closure.json');need(closure['all_passed'],'Closure')
for p,h in closure['sha256'].items():need(sha(R/p)==h,'Closure changed '+p)
need(not run('diff','--cached','--name-only'),'Index not empty')
extra=['diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
names=sorted([str(p.relative_to(R)) for root in [Q,RUNS] for p in root.rglob('*') if p.is_file()]+extra+[str((Q/'publication-names.json').relative_to(R)),str((Q/'publication.json').relative_to(R))])
need(len(names)==len(set(names)),'Duplicate names');need(not any('__pycache__' in p or Path(p).is_absolute() for p in names),'Unexpected artifact')
save(Q/'publication-names.json',names)
existing=[n for n in names if n!=str((Q/'publication.json').relative_to(R))]
subprocess.run(['git','add','--',*existing],cwd=R,check=True)
need(run('diff','--cached','--name-only').splitlines()==sorted(existing),'Stage membership')
raw=[];authored=[]
for n in existing:
 if '/payload/' in n or n.endswith(('production.patch','STATUS.md.before-master-validation','roadmap.md.before-master-validation')):raw.append(n)
 else:authored.append(n)
a=subprocess.run(['git','diff','--cached','--check','--',*authored],cwd=R,capture_output=True,text=True);need(a.returncode==0,'Authored whitespace: '+a.stdout+a.stderr)
w=subprocess.run(['git','diff','--cached','--check','--',*raw],cwd=R,capture_output=True,text=True)
need(w.returncode in (0,2) and not w.stderr,'Raw diff command failed')
# Raw whitespace belongs to exact qualified payload / exact preserved history.
blobs={n:run('rev-parse',':'+n) for n in existing};hashes={n:sha(R/n) for n in existing}
for n in existing:need(run('hash-object','--',n)==blobs[n],'Blob mismatch')
save(Q/'publication.json',dict(all_passed=True,staged_names=names,git_blobs=blobs,sha256=hashes,authored_diff_check=a.returncode,raw_diff_check=dict(returncode=w.returncode,stdout=w.stdout,stderr=w.stderr),self_binding='publication.json itself verified by exact staged-versus-working blob and after commit; no recursive self-hash'))
subprocess.run(['git','add','--',str((Q/'publication.json').relative_to(R))],cwd=R,check=True)
need(run('diff','--cached','--name-only').splitlines()==names,'Final stage membership')
for n in names:need(run('rev-parse',':'+n)==run('hash-object','--',n),'Final staged bytes')
need(not run('diff','--name-only'),'Unstaged tracked changes')
print('Publication PASS exact',len(names),'names/blobs,',len(hashes),'listed SHA bindings')
