"""Sequential regression and paired validation; preserve every process failure."""
from pathlib import Path
import subprocess,json,time
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'.superpowers/native-kernel-speedups'
runner=ROOT/'diagnostics/native-kernel-speedups/reproduce/run.py'
paired=ROOT/'diagnostics/native-kernel-speedups/reproduce/paired.jl'
jobs=[('semantic',600,['--compile=min','diagnostics/primal-row-memory/reproduce/semantic.jl']),
 ('external',1800,['-O1','diagnostics/native-certificate-recovery/reproduce/external.jl','diagnostics/basis-selective-preparation/reproduce/external-inputs.toml',str(OUT/'external.toml')])]
for case in ('runtime','medium','cleanup'):
 for arm in ('baseline','candidate'):
  args=['-O1']
  if arm=='baseline':args+=['--project=/home/jspitz/JSimplex.jl']
  args+=[str(paired),case,str(OUT/(case+'-'+arm+'.toml'))]
  jobs.append((case+'-'+arm,1500 if case=='runtime' else 900,args))
jobs.append(('project-suite',600,['-O1','test/runtests.jl']))
records=[]
for name,limit,args in jobs:
 (OUT/'validation-current.json').write_text(json.dumps(dict(job=name,started=time.time()))+'\n')
 p=subprocess.run(['python3',str(runner),str(OUT/name),str(limit),*args],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 print(name,p.returncode,flush=True)
 records.append(dict(job=name,returncode=p.returncode,runner_output=p.stdout))
 (OUT/'validation.json').write_text(json.dumps(records,indent=2)+'\n')
 if p.returncode and name!='project-suite':raise SystemExit(p.stdout)
(OUT/'validation-current.json').write_text(json.dumps(dict(completed=True,ended=time.time()))+'\n')
