"""Run fresh verification solves serially without changing their production source."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tomllib

root=Path(__file__).resolve().parents[3]
results=root/'diagnostics/adaptive-degeneracy/results/runtime-failure-repair'
local=root/'.superpowers/adaptive-degeneracy/runtime-failure-repair'
wrapper=Path('/home/jspitz/JSimplex.jl/.worktrees/primal-direction-prices/.superpowers/primal-prices')
def digest():
    h=hashlib.sha256()
    for p in sorted([Path('Project.toml'),*Path('src').rglob('*.jl')],key=str):
        h.update((str(p)+'\0').encode());h.update(p.read_bytes())
    return h.hexdigest()
os.chdir(root)
source=digest()
for case in sys.argv[1:]:
    reader,method=case.split('-')
    assert reader in ('native','jump') and method in ('primal','dual')
    assert digest()==source
    prefix=local/('final-'+case)
    log=results/('final-'+case+'.log')
    assert not log.exists() and not Path(str(prefix)+'.toml').exists()
    env=dict(os.environ,JSIMPLEX_EXPECTED_SOURCE=source)
    command=['python3',str(wrapper/'guard.py'),'--seconds','7500',str(wrapper/'julia.sh'),
        '--project=.superpowers/adaptive-degeneracy/broad-validation/env',
        'diagnostics/adaptive-degeneracy/reproduce/runtime_reader_full.jl',reader,method,'7200',str(prefix)]
    print('START',case,source,flush=True)
    with log.open('w') as out:
        run=subprocess.run(command,cwd=root,env=env,stdout=out,stderr=subprocess.STDOUT)
    assert run.returncode==0,run.returncode
    report=Path(str(prefix)+'.toml').read_text()
    (results/('final-'+case+'.toml')).write_text(report)
    data=tomllib.loads(report)
    print('DONE',case,data['status'],data['iterations'],data['seconds'],flush=True)
    assert digest()==source
    if not data['passed']:raise SystemExit(1)
