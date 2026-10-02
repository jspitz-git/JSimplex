"""Run the repair checks serially under the existing owned-process memory guard."""
import json
from pathlib import Path
import subprocess
import sys
import tomllib

root=Path(__file__).resolve().parents[3]
results=root/'diagnostics/adaptive-degeneracy/results/runtime-failure-repair'
local=root/'.superpowers/adaptive-degeneracy/runtime-failure-repair'
wrapper=Path('/home/jspitz/JSimplex.jl/.worktrees/primal-direction-prices/.superpowers/primal-prices')
repro='diagnostics/adaptive-degeneracy/reproduce/'
prefixes=[str(local/("final-"+case)) for case in ("native-dual","jump-dual","jump-primal")]
prefixes.append(str(root/".superpowers/adaptive-degeneracy/runtime-reader-full/native-primal"))
stages=[
 ('exact-verification',300,['--project=.',repro+'runtime_reader_verify.jl',*prefixes,str(results/'exact-verification.toml')]),
 ('compiled',240,['--project=.','-e','using JSimplex,Test; include("test/native_phase_coupled_tests.jl"); include("test/native_dual_tableau_tests.jl")']),
 ('semantics',600,['--project=.','--compile=min',repro+'runtime_failure_semantics.jl',
    str(root/'.superpowers/adaptive-degeneracy/native-prices/direction-price-removal-boundary'),
    str(results/'semantic-replay.toml')]),
 ('models',1800,['--project=.superpowers/adaptive-degeneracy/broad-validation/env',
    repro+'broad_corpus.jl','diagnostics/adaptive-degeneracy/results/broad-validation/inputs.toml',
    'diagnostics/adaptive-degeneracy/results/broad-validation/references.toml',
    'diagnostics/adaptive-degeneracy/results/presolve-tolerance/jobs.toml',str(local/'models')]),
 ('full-suite',300,['--project=.','test/runtests.jl']),
]
record_path=results/'validation-processes.json'
records=json.loads(record_path.read_text()) if record_path.exists() else []
for name,seconds,args in stages:
    if len(sys.argv)>1 and name not in sys.argv[1:]:continue
    path=results/(name+'.log')
    if path.exists():raise RuntimeError(f'Refusing to overwrite {path}')
    if name=='exact-verification':
        assert all(tomllib.loads(Path(p+'.toml').read_text())['status']=='OPTIMAL' for p in prefixes)
    print('START',name,flush=True)
    command=['python3',str(wrapper/'guard.py'),'--seconds',str(seconds),str(wrapper/'julia.sh'),*args]
    with path.open('w') as out:
        process=subprocess.run(command,cwd=root,stdout=out,stderr=subprocess.STDOUT)
    records.append({'stage':name,'exit_code':process.returncode,'outer_seconds':seconds,'command':command})
    (results/'validation-processes.json').write_text(json.dumps(records,indent=2)+'\n')
    print('DONE',name,'exit',process.returncode,flush=True)
    if process.returncode and name!='full-suite':raise SystemExit(process.returncode)
    if name=='exact-verification':
        assert len(tomllib.loads((results/'exact-verification.toml').read_text())['records'])==len(prefixes)
