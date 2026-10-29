from pathlib import Path
import json,sys,subprocess
D=Path(__file__).resolve().parent;W=D.parents[2];M=Path('/home/jspitz/JSimplex.jl');J=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu')
files=[p for p in D.rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts and 'verification-' not in str(p) and p.name!='results-1.toml']
files+=list((M/'src').rglob('*.jl'))
for p in (M/'src').rglob('*.jl'):
 if p.read_bytes()!=(W/p.relative_to(M)).read_bytes():raise RuntimeError('production sources differ')
files += [Path('/bin/bash').resolve(),J/'bin/julia',J/'lib/julia/sys.so',J/'lib/libjulia.so.1.13',J/'lib/julia/libjulia-internal.so.1.13',M/'Project.toml',M/'Manifest.toml',M/'LocalPreferences.toml',Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'),Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/basis-chain-cost/julia.sh')]
inputs=json.loads((D/'inputs.json').read_text());files += [Path(inputs['previous_results']['path'])]
cmd=[sys.executable,'-B',str(D/'guard/guard_reviewed.py'),'freeze',str(D/sys.argv[1])]
for p in sorted(set(p.resolve() for p in files)):cmd+=['--file',str(p)]
for k in ['tape','witness']:cmd+=['--input',inputs[k]['path']]
subprocess.run(cmd,check=True)
print(json.dumps({'manifest':sys.argv[1],'bindings':len(json.loads((D/sys.argv[1]).read_text())['inventory'])}))
