"""Exact Task2 publication only; executes after separate reviewed closure."""
from pathlib import Path
import json,hashlib,subprocess
E=Path(__file__).resolve().parent;R=E.parents[3];C=R/'diagnostics/direct-bg-dynamic-upper/reproduce'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
def need(v,m):
 if not v:raise RuntimeError(m)
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def g(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
c=rd(E/'closure.json');need(c['all_passed'],'Closure')
for n,h in c['sha256'].items():need(sha(R/n)==h,'Closure drift '+n)
need(not g('diff','--cached','--name-only'),'Index dirty')
extras=['diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
newfiles=rd(E/'canonical.json')['new_candidate_files']
# Membership is fixed by canonical list+closure, never all old files in C.
actual=[str(p.relative_to(R)) for p in E.rglob('*') if p.is_file()]+[str((C/n).relative_to(R)) for n in newfiles]+extras
expected=set(c['sha256'])|{str((E/'closure.json').relative_to(R))}
need(len(actual)==len(set(actual)) and set(actual)==expected,'Unbound/missing prepublication file')
# Every untracked file in C must be one of these11; accepted tracked Task1 stays out.
untracked=g('ls-files','--others','--exclude-standard','--',str(C.relative_to(R))).splitlines()
need(set(untracked)=={str((C/n).relative_to(R)) for n in newfiles},'Unexpected candidate file')
names=sorted(actual+[str((E/n).relative_to(R)) for n in ['publication-names.json','publication.json']])
need(len(names)==len(set(names)) and not any('__pycache__' in n for n in names),'Unexpected names')
save(E/'publication-names.json',names);existing=[n for n in names if n!=str((E/'publication.json').relative_to(R))]
subprocess.run(['git','add','--',*existing],cwd=R,check=True)
need(g('diff','--cached','--name-only').splitlines()==existing,'Stage membership')
rawnames=['STATUS.md.before-Task2','roadmap.md.before-Task2','reference-excerpts.jl','reference-excerpts-reviewed.jl','actual-dispatch-excerpts.jl','reference-to-candidate.patch','reference-to-candidate-reviewed.patch']
raw=[str((E/n).relative_to(R)) for n in rawnames];authored=[n for n in existing if n not in raw]
a=subprocess.run(['git','diff','--cached','--check','--',*authored],cwd=R,capture_output=True,text=True);need(a.returncode==0,'Authored whitespace '+a.stdout+a.stderr)
w=subprocess.run(['git','diff','--cached','--check','--',*raw],cwd=R,capture_output=True,text=True);need(w.returncode in (0,2) and not w.stderr,'Raw command')
save(E/'publication.json',dict(all_passed=True,staged_names=names,git_blobs={n:g('rev-parse',':'+n) for n in existing},sha256={n:sha(R/n) for n in existing},raw_diff_check=dict(returncode=w.returncode,stdout=w.stdout),self_binding='Exact staged/working and later committed blob; no recursive selfhash'))
subprocess.run(['git','add','--',str((E/'publication.json').relative_to(R))],cwd=R,check=True)
need(g('diff','--cached','--name-only').splitlines()==names,'Final names')
for n in names:need(g('rev-parse',':'+n)==g('hash-object','--',n),'Final blobs '+n)
need(not g('diff','--name-only'),'Unstaged tracked changes')
print('Task2 publication PASS',len(names),'exact names/blobs')
