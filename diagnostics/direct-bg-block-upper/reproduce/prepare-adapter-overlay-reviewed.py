"""Exclusive Task2 ordinary overlay from the accepted Task1 stage, no Julia."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[3];C=Path(__file__).resolve().parent
E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCK-ADAPTER-PREPARATION'
P=E.parent/'DIRECT-BG-BLOCK-U-PREPARATION/overlay-reviewed.json'
O=R/'.superpowers/sdd/2026-10-16-direct-bg-block-upper/task2-stage-reviewed'
def need(c,m):
 if not c:raise RuntimeError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads(P.read_text());source=Path(d['path']);baseline=d['sha256']
need(len(baseline)==78,'Task1 membership')
need({str(p.relative_to(source)) for p in source.rglob('*') if p.is_file()}==set(baseline),'Task1 exact files')
need(all(sha(source/n)==h for n,h in baseline.items()),'Task1 frozen hashes')
need(not any(p.is_symlink() for p in source.rglob('*')),'No source symlinks')
root=(source/'src/JSimplex.jl').read_bytes();anchor=b'include("block-upper.jl")\n';addition=b'include("block-bg.jl")\n'
need(root.count(anchor)==1 and addition not in root,'Root anchor')
modified=root.replace(anchor,anchor+addition)
need(modified.replace(addition,b'')==root,'Root inverse')
need(not O.exists(),'Exclusive stage');O.mkdir(parents=True)
for n in sorted(baseline):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(modified if n=='src/JSimplex.jl' else (source/n).read_bytes())
extras={'src/block-bg.jl':'block-bg.jl','test/block-bg-tests.jl':'block-bg-tests.jl','test/fixtures.jl':'fixtures.jl'}
for dst,src in extras.items():
 with (O/dst).open('xb') as f:f.write((C/src).read_bytes())
paths=sorted(p for p in O.rglob('*') if p.is_file());need(len(paths)==81,'Exact81files')
need(all((O/n).read_bytes()==modified if n=='src/JSimplex.jl' else sha(O/n)==h for n,h in baseline.items()),'Byte copies')
record=dict(scope='UNEXECUTED Task2 ordinary overlay. No Julia/driver/admission.',path=str(O),source=str(source),master=d['master'],baseline=baseline,root_addition=addition.decode(),root_before_sha256=sha(source/'src/JSimplex.jl'),sha256={str(p.relative_to(O)):sha(p) for p in paths},inputs={str(P):sha(P),str(Path(__file__).resolve()):sha(Path(__file__))})
for p in (E/'overlay-reviewed.json',C/'adapter-source-bindings-reviewed.json'):
 with p.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print('PASS78Task1 originals/81Task2 files/rootinverse')
