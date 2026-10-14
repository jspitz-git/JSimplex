# Separate green2 fixture path and strict cost-gate preparation.
from control import *
import guard,sys,ast
phase=sys.argv[1];driver=sys.argv[2];expected=int(sys.argv[3]);project=sys.argv[4]
old=rd(D.with_name('PRESOLVE-LARGE-PROFILE')/'pins.json');prior=rd(D.with_name('PRESOLVE-EXACT-CACHE')/'host.json')
req(all(sha(p)==v for p,v in prior['protected'].items()),'protected files')
for p in D.glob('*.py'):ast.parse(p.read_text())
command=['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+project,str(D/driver),str(D/(phase+'-run'))]
required=sorted(str(p) for p in D.iterdir() if p.is_file() and not p.name.endswith(('-pins.json','-launch-pins.json')))
config=D/(phase+'-config.json');save(config,dict(command=command,required=required,expected_returncode=expected,project=project))
files=[p for p in old['files'] if not p.startswith(str(R))]+list(prior['protected'])+[str(R/p) for p in prior['master_identity']]+required+[str(config)]
trees=[p for p in old['trees'] if not p.startswith(str(R))]+[str(R/'src'),project]
files=sorted(set(files));save(D/(phase+'-pins.json'),dict(files=files,trees=trees,inputs=[],created=time.time(),inventory=guard.inventory(files,trees)))
print('Frozen',phase,len(rd(D/(phase+'-pins.json'))['inventory']))
