from pathlib import Path
import subprocess,json,time
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'.superpowers/simplex-shared-work'
RUNNER=ROOT/'diagnostics/simplex-shared-work/reproduce/run.py'
jobs=[('predicate-final',240,['-O1','test/primal_feasibility_predicate_tests.jl']),
 ('production-kernel',300,['-O1','diagnostics/simplex-shared-work/reproduce/feasibility-probe.jl',str(OUT/'production-kernel.toml'),'production']),
 ('semantic',600,['--compile=min','diagnostics/primal-row-memory/reproduce/semantic.jl']),
 ('external',1800,['-O1','diagnostics/native-certificate-recovery/reproduce/external.jl','diagnostics/basis-selective-preparation/reproduce/external-inputs.toml',str(OUT/'external.toml')])]
for case in ('fast','medium','runtime'):
 for arm in ('baseline','candidate'):
  args=['-O1']
  if arm=='baseline':args+=['--project=/home/jspitz/JSimplex.jl']
  args+=['diagnostics/simplex-shared-work/reproduce/paired.jl',case,str(OUT/(case+'-'+arm+'.toml'))]
  jobs.append((case+'-'+arm,1500,args))
records=[]
for name,limit,args in jobs:
 (OUT/'validation-current.json').write_text(json.dumps(dict(job=name,started=time.time()))+'\n')
 p=subprocess.run(['python3',str(RUNNER),str(OUT/name),str(limit),*args],cwd=ROOT,capture_output=True,text=True)
 records.append(dict(job=name,returncode=p.returncode,output=p.stdout,stderr=p.stderr))
 (OUT/'validation.json').write_text(json.dumps(records,indent=2)+'\n')
 print(name,p.returncode,flush=True)
 if p.returncode:raise SystemExit(p.stdout+'\n'+p.stderr)
(OUT/'validation-current.json').write_text(json.dumps(dict(completed=True,ended=time.time()))+'\n')
