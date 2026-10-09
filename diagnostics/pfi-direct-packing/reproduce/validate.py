"""Sequential guarded validation; every attempt gets its own directory."""
from pathlib import Path
import subprocess,json,time
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'.superpowers/pfi-direct-packing'
RUNNER=Path(__file__).with_name('run.py')
jobs=[('targeted',300,['-O1','-e','using JSimplex, Test; include("test/pfi_packing_tests.jl"); include("test/factorization_allocation_tests.jl"); include("test/pfi_history_reuse_allocation_tests.jl"); include("test/factorization_tests.jl")']),
 ('production-kernel',300,['-O1','diagnostics/pfi-direct-packing/reproduce/bench.jl',str(OUT/'production-kernel/results.toml'),'production']),
 ('semantic',600,['--compile=min','diagnostics/primal-row-memory/reproduce/semantic.jl'])]
for case in ('fast','medium','runtime'):
 for arm in ('baseline','candidate'):
  args=['-O1']
  if arm=='baseline':args+=['--project=/home/jspitz/JSimplex.jl']
  args+=['diagnostics/pfi-direct-packing/reproduce/paired.jl',case,str(OUT/(case+'-'+arm)/'results.toml')]
  jobs.append((case+'-'+arm,1800,args))
records=[]
for name,limit,args in jobs:
 (OUT/'validation-current.json').write_text(json.dumps(dict(job=name,started=time.time()))+'\n')
 p=subprocess.run(['python3',str(RUNNER),str(OUT/name),str(limit),*args],cwd=ROOT,capture_output=True,text=True)
 records.append(dict(job=name,returncode=p.returncode,output=p.stdout,stderr=p.stderr))
 (OUT/'validation.json').write_text(json.dumps(records,indent=2)+'\n')
 print(name,p.returncode,flush=True)
 if p.returncode:raise SystemExit(p.stdout+'\n'+p.stderr)
(OUT/'validation-current.json').write_text(json.dumps(dict(completed=True,ended=time.time()))+'\n')
