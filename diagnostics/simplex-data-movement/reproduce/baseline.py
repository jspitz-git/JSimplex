from pathlib import Path
import subprocess,json,time
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'.superpowers/simplex-data-movement';runner=Path(__file__).with_name('run.py')
jobs=[('prepared-probe',300,['-O2','diagnostics/simplex-data-movement/reproduce/prepared-probe.jl',str(OUT/'prepared-probe/results.toml')],0),('certificate-red',300,['-O2','diagnostics/simplex-data-movement/reproduce/certificate-scratch-tests.jl'],1),('medium-baseline',1800,['-O2','diagnostics/simplex-data-movement/reproduce/inventory.jl','batch',str(OUT/'medium-baseline')],0),('late-hh-kernels',900,['-O2','diagnostics/simplex-data-movement/reproduce/late-hh-kernels.jl','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/medium-hh-main',str(OUT/'late-hh-kernels/results.toml')],0)]
records=[]
for name,seconds,args,expected in jobs:
 (OUT/'baseline-current.json').write_text(json.dumps(dict(job=name,started=time.time()))+'\n')
 p=subprocess.run(['python3',str(runner),str(OUT/name),str(seconds),*args],cwd=ROOT,capture_output=True,text=True)
 records.append(dict(job=name,returncode=p.returncode,expected=expected,stdout=p.stdout,stderr=p.stderr));(OUT/'baseline.json').write_text(json.dumps(records,indent=2)+'\n');print(name,p.returncode,flush=True)
 if p.returncode!=expected:break
(OUT/'baseline-current.json').write_text(json.dumps(dict(stopped=True,ended=time.time()))+'\n')
