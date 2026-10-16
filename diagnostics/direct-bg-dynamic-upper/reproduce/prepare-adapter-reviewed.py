"""One-shot Task2 overlay; reads frozen Task1, writes only a new directory. No Julia."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[3];C=Path(__file__).resolve().parent
E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-DYNAMIC-ADAPTER-PREPARATION'
P=E.parent/'DIRECT-BG-DYNAMIC-U-PREPARATION'
O=R/'.superpowers/sdd/2026-10-16-direct-bg-dynamic-upper/task2-reviewed-stage'
def need(v,m):
 if not v:raise RuntimeError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
a=rd(P/'overlay-reviewed.json');source=Path(a['path']);baseline=a['sha256']
need(len(baseline)==77,'Task1 membership')
need(set(baseline)=={str(p.relative_to(source)) for p in source.rglob('*') if p.is_file()},'Source names')
need(not source.is_symlink() and not any(p.is_symlink() for p in source.rglob('*')),'Source symlink')
for n,h in baseline.items():need(sha(source/n)==h,'Source drift '+n)
root=(source/'src/JSimplex.jl').read_bytes();ending=b'\nend\n';addition=b'include("dynamic-bg.jl")\n'
need(root.endswith(ending) and addition not in root,'Insertion anchor')
modified=root[:-len(ending)]+b'\n'+addition+ending
need(modified.replace(b'\n'+addition+ending,ending)==root,'Root inverse')
need(not O.exists(),'Exclusive new overlay');O.mkdir(parents=True)
for n in sorted(baseline):
 dst=O/n;dst.parent.mkdir(parents=True,exist_ok=True)
 with dst.open('xb') as f:f.write(modified if n=='src/JSimplex.jl' else (source/n).read_bytes())
new={'dynamic-bg-reviewed.jl':'src/dynamic-bg.jl','dynamic-bg-tests-reviewed.jl':'test/dynamic-bg-tests.jl',
     'fixtures.jl':'test/fixtures.jl','slot-oracles.jl':'test/slot-oracles.jl'}
for n,d in new.items():
 dst=O/d;dst.parent.mkdir(parents=True,exist_ok=True)
 with dst.open('xb') as f:f.write((C/n).read_bytes())
paths=sorted(p for p in O.rglob('*') if p.is_file());need(len(paths)==81,'81 members')
for n,h in baseline.items():need((O/n).read_bytes()==modified if n=='src/JSimplex.jl' else sha(O/n)==h,'Copy inverse '+n)
save(E/'overlay-reviewed.json',dict(scope='UNEXECUTED Task2; not runtime admission',path=str(O),source=str(source),baseline=baseline,new_files=new,root_addition=addition.decode(),root_before_sha256=hashlib.sha256(root).hexdigest(),sha256={str(p.relative_to(O)):sha(p) for p in paths}))
save(E/'preparation-pins-reviewed.json',dict(sha256={str(p):sha(p) for p in [Path(__file__).resolve(),P/'overlay-reviewed.json',*[C/n for n in new]]}))
print('Task2 overlay: 77 unchanged baseline files except one root include, four additions =81; no Julia')
