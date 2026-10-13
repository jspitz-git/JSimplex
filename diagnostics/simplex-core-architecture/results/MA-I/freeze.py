from pathlib import Path
import json,hashlib,time
D=Path(__file__).resolve().parent;R=D.parents[3];E=D.parent/'MA-E';H=D.parent/'MA-H';F=D.parent/'MA-F-repair'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(n,x):
 with (D/n).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
old=json.loads((E/'admission-pins-reviewed.json').read_text())
# Fresh hashes; reuse external path inventory only, never pretend historical pins.
paths={p for p in old['inventory'] if not p.startswith(str(R)+'/')}
paths.update(str(p) for p in D.rglob('*') if p.is_file())
paths.update(str(H/n) for n in ['candidate-markowitz.jl','candidate-JSimplex.jl','candidate-Project.toml','candidate-tests.jl','route-tests.jl','reference-forward.jl','test-contract.md','review.json','review.md','closure.json','publication.json'])
paths.update(str(F/n) for n in ['driver.jl','kernels.jl','tests-instrumented.jl','test-counts.json'])
paths.update(str(E/n) for n in ['test-instrumentation.json','ledger-final.md','admission-reviewed.md'])
paths.update(str(R/n) for n in ['docs/superpowers/plans/2026-10-14-ma-routing-qualification-admission.md','src/markowitz_factorization.jl','src/JSimplex.jl','Project.toml','Manifest.toml','LocalPreferences.toml'])
base='/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/'
paths.update(base+n for n in ['stdlib/v1.13/Test/src/Test.jl','base/scopedvalues.jl'])
required={p:sha(p) for p in sorted(paths)};save('required-paths-reviewed.json',required);paths.add(str(D/'required-paths-reviewed.json'))
inv={p:dict(resolved=str(Path(p).resolve()),sha256=sha(p)) for p in sorted(paths)}
save('admission-pins-reviewed.json',dict(files=sorted(paths),trees=[],inputs=[],inventory=inv,created=time.time()))
print('pins',len(inv),'required',len(required),'manifest',sha(D/'admission-pins-reviewed.json'))
