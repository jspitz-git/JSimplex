"""S5-G: explicit freeze and single guarded run; never retry an existing output."""
from pathlib import Path
import hashlib,json,subprocess,sys,tomllib
ROOT=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
HERE=Path(__file__).resolve().parent
F=HERE.parent/'S5-F'
BASE=ROOT/'.superpowers/simplex-core-architecture/S5-G'
PINS=BASE/'qualification-1-pins.json'
OUT=BASE/'qualification-1'
GUARD=ROOT/'diagnostics/simplex-core-architecture/reproduce/guarded_run.py'
WRAPPER=Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh')
RUNTIME=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu')
COMMAND=['/bin/bash',str(WRAPPER),'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(ROOT),str(F/'driver-reviewed.jl'),str(OUT/'raw')]
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def main():
    mode=sys.argv[1]
    if mode=='freeze':
        BASE.mkdir(parents=True,exist_ok=True)
        manifest=tomllib.loads((F/'source-pins-reviewed.toml').read_text())['sha256']
        assert all(sha(p)==h for p,h in manifest.items())
        files=set(map(Path,manifest))|set(F.glob('*'))|set(HERE.glob('*'))
        files|={GUARD,WRAPPER,WRAPPER.parents[3]/'.superpowers/basis-chain-cost/julia.sh',RUNTIME/'bin/julia',RUNTIME/'share/julia/base/loading.jl',RUNTIME/'share/doc/julia/html/en/manual/command-line-interface.html',ROOT/'docs/superpowers/plans/2026-10-13-precision-journal-launcher-admission.md'}
        files|={ROOT/'diagnostics/simplex-core-architecture/S5-PRECISION-JOURNAL-INTERRUPTION-DRIVER-REVIEW.md'}
        # Pin runtime libraries, including GMP/MPFR and libjulia, without loading them.
        files|={p for p in (RUNTIME/'lib').rglob('*') if p.is_file()}
        cmd=[sys.executable,str(GUARD),'freeze',str(PINS),'--tree',str(ROOT/'src'),'--tree',str(ROOT/'test')]
        for f in sorted(files):
            if f.is_file():cmd+=['--file',str(f)]
        for name in ('big.mps','largo.mps','AnyMOD.mps'):cmd+=['--forbidden','/home/jspitz/mps/'+name]
        subprocess.run(cmd,check=True)
    elif mode=='run':
        # Concrete review is required before even invoking the general guard.
        review=json.loads((HERE/'prelaunch-acceptance.json').read_text())
        assert review['accepted'] is True and review['unresolved_findings']==[]
        assert all(sha(p)==h for p,h in review['reviewed_sha256'].items())
        raise SystemExit(subprocess.call([sys.executable,str(GUARD),'run',str(PINS),str(OUT),'--seconds','120','--',*COMMAND]))
    else:raise ValueError(mode)
if __name__=='__main__':main()
