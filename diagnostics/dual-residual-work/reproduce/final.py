"""Final frozen-source verification after prototype performance refinement."""
from pathlib import Path
import subprocess,json,time
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'.superpowers/dual-residual-work/final';OUT.mkdir(exist_ok=False)
runner=ROOT/'diagnostics/dual-residual-work/reproduce/run.py'
jobs=[('paired',600,['-O2','diagnostics/dual-residual-work/reproduce/paired.jl',str(OUT/'paired/results.toml')])]
for name,project in [('runtime-baseline-1','/home/jspitz/JSimplex.jl'),('runtime-candidate-1',str(ROOT)),('runtime-candidate-2',str(ROOT)),('runtime-baseline-2','/home/jspitz/JSimplex.jl')]:
 jobs.append((name,900,['--project='+project,'-O2','diagnostics/dual-residual-work/reproduce/runtime.jl',str(OUT/name/'results.toml')]))
jobs += [
 ('targeted-external',2400,['-O2','-e','include(joinpath(pwd(),"diagnostics/dual-residual-work/reproduce/targeted.jl")); include(joinpath(pwd(),"diagnostics/simplex-data-movement/reproduce/external.jl"))','diagnostics/basis-selective-preparation/reproduce/external-inputs.toml',str(OUT/'targeted-external/results.toml')]),
 ('semantic',600,['--compile=min','diagnostics/primal-row-memory/reproduce/semantic.jl']),
 ('project-suite',300,['-O2','test/runtests.jl'])]
records=[]
for name,seconds,args in jobs:
 (OUT/'current.json').write_text(json.dumps(dict(job=name,started=time.time()))+'\n')
 p=subprocess.run(['python3',str(runner),str(OUT/name),str(seconds),*args],cwd=ROOT,capture_output=True,text=True)
 records.append(dict(job=name,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
 (OUT/'jobs.json').write_text(json.dumps(records,indent=2)+'\n');print(name,p.returncode,flush=True)
 if p.returncode and name!='project-suite':break
(OUT/'current.json').write_text(json.dumps(dict(stopped=True,ended=time.time()))+'\n')
