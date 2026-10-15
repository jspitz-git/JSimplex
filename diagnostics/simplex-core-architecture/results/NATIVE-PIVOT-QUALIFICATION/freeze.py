"""Offline final package pinning, not a stage seal or numerical admission."""
from common import *
files={p for p in Q.iterdir() if p.is_file()}|{p for p in PREV.rglob('*') if p.is_file()}|{Path(n) for n in rd(Q/'runtime-pins.json')['sha256']}
files|={R/'docs/superpowers/plans/2026-10-15-native-pivot-policy.md',R/'docs/superpowers/specs/2026-10-15-native-pivot-policy-design.md'}
files|={R/s['source'] for s in rd(Q/'neighbor-slices.json')}
files|={Path(z['path']) for v in rd(Q/'saved-C.json').values() for z in v}
files|=set(Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/Test/src').glob('*.jl'))
files|=set(Path('/home/jspitz/.julia/packages/PrecompileTools/QUxvR/src').glob('*.jl'))
require(not (Q/'runs').exists(),'Unexpected stage')
save(Q/'preparation-pins.json',dict(sha256={str(p):sha(p) for p in sorted(files)},scope='Offline package only. Not a sealed stage, not numerical admission.'))
print({'pins':len(files),'julia_executed':False})
