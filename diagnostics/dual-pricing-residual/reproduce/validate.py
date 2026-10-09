"""Run guarded validation sequentially; preserve every result, including failures."""
from pathlib import Path
import subprocess,json,time
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'.superpowers/dual-pricing-residual'
runner=Path(__file__).with_name('run.py')
jobs=[('budget-after',300,['-O2','diagnostics/dual-pricing-residual/reproduce/finite-check-budget.jl']),
 ('targeted',300,['-O2','-e','using JSimplex,Test; include("test/dual_weight_validation_tests.jl")']),
 ('weights-bench',300,['-O2','diagnostics/dual-pricing-residual/reproduce/weights-bench.jl',str(OUT/'weights-bench/results.toml')]),
 ('semantic',600,['--compile=min','diagnostics/primal-row-memory/reproduce/semantic.jl']),
 ('capture-after',1800,['-O2','diagnostics/dual-pricing-residual/reproduce/capture.jl',str(OUT/'capture-after')]),
 ('project-suite',300,['-O2','test/runtests.jl'])]
records=[]
for name,seconds,args in jobs:
 (OUT/'validation-current.json').write_text(json.dumps(dict(job=name,started=time.time()))+'\n')
 p=subprocess.run(['python3',str(runner),str(OUT/name),str(seconds),*args],cwd=ROOT,capture_output=True,text=True)
 records.append(dict(job=name,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
 (OUT/'validation.json').write_text(json.dumps(records,indent=2)+'\n')
 print(name,p.returncode,flush=True)
 if p.returncode and name!='project-suite':break
(OUT/'validation-current.json').write_text(json.dumps(dict(stopped=True,ended=time.time()))+'\n')
