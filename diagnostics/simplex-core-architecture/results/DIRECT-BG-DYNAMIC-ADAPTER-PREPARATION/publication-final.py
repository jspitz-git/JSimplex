"""Separate exact Task2 publication after original whitespace refusal. No source edits."""
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
c=rd(E/'closure-supplement.json');need(c['all_passed'],'Supplement closure')
for n,h in c['sha256'].items():need(sha(R/n)==h,'Closure supplement drift '+n)
p=rd(E/'publication-failure.json');need(g('diff','--cached','--name-only').splitlines()==p['staged_names'],'Original stage membership')
for n,b in p['git_blobs'].items():need(g('rev-parse',':'+n)==g('hash-object','--',n)==b,'Original stage blob')
extras=['diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'];newfiles=rd(E/'canonical.json')['new_candidate_files']
actual=[str(q.relative_to(R)) for q in E.rglob('*') if q.is_file()]+[str((C/n).relative_to(R)) for n in newfiles]+extras
expected=set(c['sha256'])|{str((E/'closure-supplement.json').relative_to(R))}
need(len(actual)==len(set(actual)) and set(actual)==expected,'Unbound/missing prepublication file')
need(not g('ls-files','--others','--exclude-standard','--',str(C.relative_to(R))),'Unexpected untracked candidate file')
need((C/'slot-oracles.jl').read_text()==(C/'slot-upper-tests-reviewed.jl').read_text().split('_bg_test_matrix() =',1)[0].replace('::BGSlotUpper','::J.BGSlotUpper'),'Verbatim oracle prefix')
names=sorted(actual+[str((E/n).relative_to(R)) for n in ['publication-final-names.json','publication-final.json']])
need(len(names)==len(set(names)) and not any('__pycache__' in n for n in names),'Unexpected names')
save(E/'publication-final-names.json',names);existing=[n for n in names if n!=str((E/'publication-final.json').relative_to(R))]
subprocess.run(['git','add','--',*existing],cwd=R,check=True)
need(g('diff','--cached','--name-only').splitlines()==existing,'Final stage membership')
rawnames=['STATUS.md.before-Task2','roadmap.md.before-Task2','reference-excerpts.jl','reference-excerpts-reviewed.jl','actual-dispatch-excerpts.jl','reference-to-candidate.patch','reference-to-candidate-reviewed.patch']
raw=[str((E/n).relative_to(R)) for n in rawnames]+[str((C/'slot-oracles.jl').relative_to(R))];authored=[n for n in existing if n not in raw]
a=subprocess.run(['git','diff','--cached','--check','--',*authored],cwd=R,capture_output=True,text=True);need(a.returncode==0,'Authored whitespace '+a.stdout+a.stderr)
w=subprocess.run(['git','diff','--cached','--check','--',*raw],cwd=R,capture_output=True,text=True);need(w.returncode in (0,2) and not w.stderr,'Raw command')
save(E/'publication-final.json',dict(all_passed=True,staged_names=names,git_blobs={n:g('rev-parse',':'+n) for n in existing},sha256={n:sha(R/n) for n in existing},raw_diff_check=dict(returncode=w.returncode,stdout=w.stdout),self_binding='Exact staged/working and later committed blob; no recursive selfhash'))
subprocess.run(['git','add','--',str((E/'publication-final.json').relative_to(R))],cwd=R,check=True)
need(g('diff','--cached','--name-only').splitlines()==names,'Final names')
for n in names:need(g('rev-parse',':'+n)==g('hash-object','--',n),'Final blobs '+n)
need(not g('diff','--name-only'),'Unstaged tracked changes')
print('Task2 publication FINAL PASS',len(names),'exact names/blobs')
