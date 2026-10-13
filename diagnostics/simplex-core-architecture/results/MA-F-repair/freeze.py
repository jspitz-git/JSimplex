"""Freeze exact replacement inputs before independent numerical admission."""
from pathlib import Path
import hashlib,json,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-F-repair';E=D.parent/'MA-E';F=D.parent/'MA-F'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
old=json.loads((E/'admission-pins-reviewed.json').read_text())
if not all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in old['inventory'].items()):raise SystemExit('historical pin mismatch')
paths=set(old['inventory']);paths.update(str(p) for p in D.rglob('*') if p.is_file());paths.update(str(F/n) for n in ['closure.json','publication.json','review.json','review.md','postcheck.json','attempt-1/red/raw.toml','attempt-1/red/process.json','attempt-1/invocation.json'])
paths.update(['/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/Test/src/Test.jl','/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base/scopedvalues.jl',str(D.parent/'S4-AD-green-bounded/driver.jl'),str(E/'execution-seal.json'),str(E/'attempt-reserved.json')])
required={p:sha(p) for p in sorted(paths)};save(D/'required-paths-reviewed.json',required);paths.add(str(D/'required-paths-reviewed.json'))
inv={p:dict(resolved=str(Path(p).resolve()),sha256=sha(p)) for p in sorted(paths)}
save(D/'admission-pins-reviewed.json',dict(files=sorted(paths),trees=[],inputs=[],inventory=inv,created=time.time()))
print('pins',len(inv),'required',len(required),'manifest',sha(D/'admission-pins-reviewed.json'))
