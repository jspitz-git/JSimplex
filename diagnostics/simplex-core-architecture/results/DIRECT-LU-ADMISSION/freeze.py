"""One-shot read-time admission inventory; does not call any old script or Julia."""
from control import *
import guard

def main():
    previous=rd(R/'diagnostics/simplex-core-architecture/results/PRESOLVE-ZERO-COEFFICIENT/green2-pins.json')
    # Discovery only: no old hash is called a new pin. Exclude old experiments/MPS.
    external=[Path(n) for n in previous['inventory'] if not n.startswith(str(R)+'/') and ('/.julia/' in n or '/depot/' in n or n in ('/bin/bash','/usr/bin/python3','/usr/bin/python3.14') or n.endswith('/diagnostics/basis-memory/reproduce/julia.sh') or n.endswith('/.superpowers/basis-chain-cost/julia.sh'))]
    julia=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu')
    for name in ['share/julia/stdlib/v1.13/Test/src/Test.jl','share/julia/stdlib/v1.13/SparseArrays/src/linalg.jl','share/julia/stdlib/v1.13/LinearAlgebra/src/triangular.jl']:
        external.append(julia/name)
    baseline=rd(R/'diagnostics/simplex-core-architecture/results/DIRECT-LU-PREPARATION/baseline.json')
    req(all(sha(R/n)==h for n,h in baseline['sha256'].items()),'Production baseline changed')
    old=R/'diagnostics/simplex-core-architecture/results/DIRECT-LU-PREPARATION'
    dependencies=[old/n for n in ['review-final.md','review-final-bindings.json','review-oracle-supplement.md','review-oracle-supplement.json','closure.json','publication.json','baseline.json']]
    dependencies += [R/n for n in ['docs/superpowers/plans/2026-10-14-direct-lu-markowitz.md','docs/superpowers/specs/2026-10-14-direct-lu-markowitz.md']]
    dependencies += [p for p in (R/'diagnostics/direct-lu-markowitz/reproduce').iterdir() if p.is_file()]
    authored=[p for p in D.rglob('*') if p.is_file()]
    required=sorted(str(p) for p in [*authored,*dependencies])
    save(D/'required.json',required)
    files=sorted(set(str(p) for p in [*external,*authored,*dependencies,D/'required.json'])|{str(R/n) for n in baseline['sha256']})
    W=Path(rd(D/'staging.json')['root']);trees=[str(W/'reference'),str(W/'candidate')]
    pins=dict(files=files,trees=trees,inventory=guard.inventory(files,trees),inputs=[],created=time.time(),scope='Read-time offline preparation pins; not launch admission')
    save(D/'preparation-pins.json',pins)
    print(json.dumps({'pins':len(pins['inventory']),'required_review_files':len(required),'inputs':0}))
if __name__=='__main__':main()
