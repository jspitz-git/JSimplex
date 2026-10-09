"""Sequential validation; never start a second Julia or overwrite an attempt."""
from pathlib import Path
import json,subprocess,sys,tomllib
ROOT=Path(__file__).resolve().parents[3]
P='diagnostics/basis-kernel-savings/reproduce/'
OUT=Path('.superpowers/basis-kernel-savings')
jobs=[
 ('pfi-production2',300,[P+'pfi-production.jl']),
 ('upper-production1',300,[P+'upper-production.jl']),
 ('upper-production2',300,[P+'upper-production.jl']),
 ('hh-compact2',300,[P+'hh-compact-probe.jl']),
 ('compiled-final',300,[P+'compiled.jl']),
 ('semantic',300,['--compile=min','diagnostics/primal-row-memory/reproduce/semantic.jl']),
 ('external',1200,['diagnostics/simplex-data-movement/reproduce/external.jl','diagnostics/basis-selective-preparation/reproduce/external-inputs.toml']),
]
for manager in ('pfi','bartels_golub'):
 for mode in ('baseline','production'):
  jobs.append((manager+'-'+mode,1500,[P+'runtime.jl',mode,manager]))
for name,seconds,args in jobs:
 out=OUT/name
 if name not in ('compiled-final','semantic'):args=[*args,str(out/'result.toml')]
 (OUT/'validation-current.json').write_text(json.dumps(dict(job=name,args=args),indent=2)+'\n')
 print('START',name,flush=True)
 subprocess.run([sys.executable,P+'run.py',str(out),str(seconds),*args],cwd=ROOT,check=True)
 print('DONE',name,flush=True)
for manager in ('pfi','bartels_golub'):
 a,b=[tomllib.loads((OUT/(manager+'-'+mode)/'result.toml').read_text()) for mode in ('baseline','production')]
 for key in ('events_hash','states_hash','iterations','refactorizations','objective','events'):
  assert a[key]==b[key],(manager,key,a[key],b[key])
print('All jobs and runtime trajectory comparisons passed.',flush=True)
(OUT/'validation-complete.json').write_text(json.dumps({'completed':[j[0] for j in jobs]})+'\n')
