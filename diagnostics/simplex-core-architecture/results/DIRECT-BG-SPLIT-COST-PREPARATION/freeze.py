"""One-shot offline preparation binding, no phase seal or Julia."""
from control import *
require(not (D/'runs').exists(),'No phase activity')
for n in ['source-check.json','offline-tests.json','prefix-tests.json','negative-supplement.json','split-tests.json']:require(rd(D/n)['all_passed'] is True,'Author checks '+n)
require(bindings(rd(D/'source-check.json')),'Source-checked bytes')
files=[p for p in D.iterdir() if p.is_file()]
files += [p for p in C.rglob('*') if p.is_file()]
files += [Path(n) for n in rd(D/'lineage.json')['sha256']]
files += [Path(v['source']) for v in rd(D/'reused-files.json').values()]
files += [Path(n) for n in rd(D/'runtime-inputs-complete.json')['inventory']]
files += [Path(s['path'])/n for s in rd(D/'stages.json').values() for n in s['sha256']]
files += [root/n for label,root in [('diagnostic',R),('production',W)] for n in rd(D/'baseline.json')[label]]
files += [R/'docs/superpowers/plans/2026-10-18-direct-bg-split-free-blocks.md',R/'docs/superpowers/specs/2026-10-18-direct-bg-split-free-blocks.md',R/'AGENTS.md']
base=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base')
files += [base/n for n in ['array.jl','boot.jl','summarysize.jl']]
files=sorted(set(files+[D/'required-paths.json']))
save(D/'required-paths.json',dict(paths=[str(p) for p in files],scope='Exact offline preparation; reviewer/closure/publication and future run evidence bound separately'))
save(D/'preparation-pins.json',dict(sha256={str(p):sha(p) for p in files},scope='Offline read-time bindings; no numerical launch admission'))
print('Preparation pins:',len(files))
