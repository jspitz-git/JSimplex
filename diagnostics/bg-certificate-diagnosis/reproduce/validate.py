"""Run the BG terminal-recovery checks sequentially under the existing guard."""
from pathlib import Path
import json,subprocess,sys
ROOT=Path(__file__).resolve().parents[3]
P='diagnostics/bg-certificate-diagnosis/reproduce/'
OUT=Path('.superpowers/bg-certificate-diagnosis')
snapshot=str(OUT/'capture1/3-internal.bin')
helpers=[P+'restore.jl',P+'native_cleanup_recovery.jl.baseline']
jobs=[
 ('targeted',300,[P+'targeted.jl']),
 ('cost-baseline',120,[P+'cost.jl','baseline',snapshot,str(OUT/'cost-baseline/result.toml'),*helpers]),
 ('cost-production',120,[P+'cost.jl','production',snapshot,str(OUT/'cost-production/result.toml'),*helpers]),
 ('semantic',300,['--compile=min','diagnostics/primal-row-memory/reproduce/semantic.jl']),
 ('external',1200,['diagnostics/simplex-data-movement/reproduce/external.jl','diagnostics/basis-selective-preparation/reproduce/external-inputs.toml',str(OUT/'external/result.toml')]),
 ('project-suite',600,['test/runtests.jl']),
 ('runtime',1800,['diagnostics/basis-kernel-savings/reproduce/runtime.jl','production','bartels_golub',str(OUT/'runtime/result.toml')]),
]
results=[]
for name,seconds,args in jobs:
 (OUT/'validation-current.json').write_text(json.dumps(dict(job=name,args=args),indent=2)+'\n')
 print('START',name,flush=True)
 r=subprocess.run([sys.executable,'diagnostics/basis-kernel-savings/reproduce/run.py',str(OUT/name),str(seconds),*args],cwd=ROOT)
 results.append(dict(job=name,returncode=r.returncode))
 (OUT/'validation-results.json').write_text(json.dumps(results,indent=2)+'\n')
 print('DONE',name,r.returncode,flush=True)
 if r.returncode and name!='project-suite':sys.exit(r.returncode)
