"""Sequential validation; never launch a second numerical Julia process."""
from pathlib import Path
import subprocess,json,time
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'.superpowers/dual-residual-work'
runner=ROOT/'diagnostics/dual-residual-work/reproduce/run.py'
jobs=[
 ('targeted-v2',600,['-O2','diagnostics/dual-residual-work/reproduce/targeted.jl']),
 ('paired-final',600,['-O2','diagnostics/dual-residual-work/reproduce/paired.jl',str(OUT/'paired-final/results.toml')]),
 ('semantic',600,['--compile=min','diagnostics/primal-row-memory/reproduce/semantic.jl']),
 ('external',1800,['-O2','diagnostics/simplex-data-movement/reproduce/external.jl','diagnostics/basis-selective-preparation/reproduce/external-inputs.toml',str(OUT/'external/results.toml')]),
]
for name,project in [('runtime-baseline-1','/home/jspitz/JSimplex.jl'),('runtime-candidate-1',str(ROOT)),('runtime-candidate-2',str(ROOT)),('runtime-baseline-2','/home/jspitz/JSimplex.jl')]:
 jobs.append((name,900,['--project='+project,'-O2','diagnostics/dual-residual-work/reproduce/runtime.jl',str(OUT/name/'results.toml')]))
jobs.append(('project-suite',300,['-O2','test/runtests.jl']))
records=[]
for name,seconds,args in jobs:
 (OUT/'validation-current.json').write_text(json.dumps(dict(job=name,started=time.time()))+'\n')
 p=subprocess.run(['python3',str(runner),str(OUT/name),str(seconds),*args],cwd=ROOT,capture_output=True,text=True)
 records.append(dict(job=name,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
 (OUT/'validation.json').write_text(json.dumps(records,indent=2)+'\n');print(name,p.returncode,flush=True)
 if p.returncode and name!='project-suite':break
(OUT/'validation-current.json').write_text(json.dumps(dict(stopped=True,ended=time.time()))+'\n')
