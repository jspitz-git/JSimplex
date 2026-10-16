"""One-shot OFFLINE Task1 overlay preparation; never invokes Julia or old scripts."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[3]
C=Path(__file__).resolve().parent
E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-DYNAMIC-U-PREPARATION'
D=E.parent/'DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION'
P=E.parent/'DIRECT-BG-DYNAMIC-U-PLAN'
O=R/'.superpowers/sdd/2026-10-16-direct-bg-dynamic-upper/task1-reviewed-stage'
def need(v,m):
 if not v:raise RuntimeError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
old=rd(D/'stages.json')['cost'];source=Path(old['path']);baseline=old['sha256']
need(len(baseline)==75,'Expected accepted overlay membership')
need({str(p.relative_to(source)) for p in source.rglob('*') if p.is_file()}==set(baseline),'Source membership drift')
need(not source.is_symlink() and not any(p.is_symlink() for p in source.rglob('*')),'Source symlink')
for n,h in baseline.items():need(sha(source/n)==h,'Source hash drift '+n)
for n,h in rd(P/'source-pins.json')['sha256'].items():need(sha(Path(n))==h,'Relevant source drift '+n)
root=(source/'src/JSimplex.jl').read_bytes();ending=b'\nend\n';addition=b'include("slot-upper.jl")\n'
need(root.endswith(ending) and addition not in root,'Root insertion anchor')
modified=root[:-len(ending)]+b'\n'+addition+ending
need(modified.replace(b'\n'+addition+ending,ending)==root,'Root inverse')
need(not O.exists(),'Exclusive overlay already exists')
O.mkdir(parents=True)
for n in sorted(baseline):
 dst=O/n;dst.parent.mkdir(parents=True,exist_ok=True)
 with dst.open('xb') as f:f.write(modified if n=='src/JSimplex.jl' else (source/n).read_bytes())
for src,dst in [(C/'slot-upper-reviewed.jl',O/'src/slot-upper.jl'),(C/'slot-upper-tests-reviewed.jl',O/'test/slot-upper-tests.jl')]:
 dst.parent.mkdir(parents=True,exist_ok=True)
 with dst.open('xb') as f:f.write(src.read_bytes())
paths=sorted(p for p in O.rglob('*') if p.is_file())
need(len(paths)==77,'New overlay membership')
for n,h in baseline.items():
 need((O/n).read_bytes()==modified if n=='src/JSimplex.jl' else sha(O/n)==h,'Copy/inverse '+n)
save(E/'overlay-reviewed.json',dict(scope='UNEXECUTED, ordinary accepted-stage copy plus one candidate include and test text',path=str(O),source=str(source),master=old['master'],baseline=baseline,root_addition=addition.decode(),root_before_sha256=hashlib.sha256(root).hexdigest(),sha256={str(p.relative_to(O)):sha(p) for p in paths}))
inputs=[C/'slot-upper-reviewed.jl',C/'slot-upper-tests-reviewed.jl',Path(__file__).resolve(),D/'stages.json',P/'source-pins.json',P/'review.json',R/'docs/superpowers/specs/2026-10-16-direct-bg-dynamic-upper.md',R/'docs/superpowers/plans/2026-10-16-direct-bg-dynamic-upper.md']
save(E/'preparation-pins-reviewed.json',dict(scope='Task1 offline source pins; not launch admission',sha256={str(p):sha(p) for p in inputs}))
print('Overlay PASS: 75 originals, one root insertion, 2 added texts = 77 files; no Julia')
