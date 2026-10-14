"""Offline fixed command and schedule construction; no launcher invocation."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent;W=R/'.superpowers/direct-lu-markowitz-admission'
wrapper='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
groups=[('exports',100),('rejections',66),('orientation',12),('normalization',200),('lifecycles',18272),('fallback',288),('markowitz-sparse.jl',62),('markowitz-fill.jl',8),('markowitz-triangular.jl',144),('prepared.jl',195),('lifecycle.jl',96),('stability.jl',84)]
phases={}
for phase,side,limit,exitcode in [('red','reference',30,1),('green','candidate',90,0)]:
 project=str(W/side);output=str(D/(phase+'-run'))
 command=['/bin/bash',wrapper,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+project,str(D/'driver.jl'),phase,output,project]
 phases[phase]=dict(seconds=limit,expected_exit=exitcode,project=project,output=output,command=command,groups=[dict(name='reference-contract',counts=[0,3,0,0])] if phase=='red' else [dict(name=n,counts=[c,0,0,0]) for n,c in groups])
with (D/'config.json').open('x') as f:json.dump(dict(phases=phases,scope='UNEXECUTED short correctness admission; never a cost run'),f,indent=2);f.write('\n')
print({'prospective_green_assertions':sum(c for n,c in groups),'green_groups':len(groups),'red_expected_failures':3})
