"""Exclusive Task1 text-only overlay preparation. No Julia or old script execution."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[3];C=Path(__file__).resolve().parent
E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCK-U-PREPARATION'
P=E.parent/'DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION/stages.json'
O=R/'.superpowers/sdd/2026-10-16-direct-bg-block-upper/task1-stage'
def need(c,m):
    if not c:raise RuntimeError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads(P.read_text())['cost'];source=Path(old['path']);baseline=old['sha256']
need(len(baseline)==75,'Accepted source membership')
need({str(p.relative_to(source)) for p in source.rglob('*') if p.is_file()}==set(baseline),'Source membership drift')
need(not any(p.is_symlink() for p in source.rglob('*')),'Source symlink')
need(all(sha(source/n)==h for n,h in baseline.items()),'Source content drift')
root=(source/'src/JSimplex.jl').read_bytes();ending=b'\nend\n';addition=b'include("block-upper.jl")\n'
need(root.endswith(ending) and addition not in root,'Root insertion')
modified=root[:-len(ending)]+b'\n'+addition+ending
need(modified.replace(b'\n'+addition+ending,ending)==root,'Exact inverse')
need(not O.exists(),'Exclusive stage exists');O.mkdir(parents=True)
for n in sorted(baseline):
    p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(modified if n=='src/JSimplex.jl' else (source/n).read_bytes())
extra={'src/block-upper.jl':'block-upper.jl','test/block-oracles.jl':'block-oracles.jl','test/block-upper-tests.jl':'block-upper-tests.jl'}
for dst,src in extra.items():
    p=O/dst;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write((C/src).read_bytes())
paths=sorted(p for p in O.rglob('*') if p.is_file())
need(len(paths)==78,'Stage exact78')
for n,h in baseline.items():need((O/n).read_bytes()==modified if n=='src/JSimplex.jl' else sha(O/n)==h,'Stage copy '+n)
record=dict(scope='UNEXECUTED Task1 ordinary stage;75original files one inverse root include and3new texts; not launcher/admission',path=str(O),source=str(source),master=old['master'],baseline=baseline,root_addition=addition.decode(),root_before_sha256=sha(source/'src/JSimplex.jl'),sha256={str(p.relative_to(O)):sha(p) for p in paths},inputs={str(P):sha(P),str(Path(__file__).resolve()):sha(Path(__file__))})
for name in ['overlay.json']:
    with (E/name).open('x') as f:json.dump(record,f,indent=2);f.write('\n')
with (C/'source-bindings.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print('PASS75originals/78stagefiles/rootinverse; no Julia')
