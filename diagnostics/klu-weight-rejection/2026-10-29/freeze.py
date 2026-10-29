from pathlib import Path
import json,subprocess,sys
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/klu-weight-rejection/2026-10-29';J=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu')
name=sys.argv[1];files=[p for p in D.rglob('*') if p.is_file() and p.suffix not in ('.pyc',) and 'diagnosis-' not in str(p) and p.name not in ('results-1.toml',)]
files+= [Path(p) for p in json.loads((D/'vendor-provenance.json').read_text())['installed_libraries']]
files += [Path('/bin/bash').resolve(),J/'bin/julia',J/'lib/julia/sys.so',J/'lib/libjulia.so.1.13',J/'lib/julia/libjulia-internal.so.1.13',J/'share/julia/stdlib/v1.13/SparseArrays/src/solvers/umfpack.jl',J/'share/julia/stdlib/v1.13/SuiteSparse_jll/Project.toml',J/'share/julia/stdlib/v1.13/SuiteSparse_jll/src/SuiteSparse_jll.jl',Path('/home/jspitz/JSimplex.jl/Project.toml'),Path('/home/jspitz/JSimplex.jl/Manifest.toml'),Path('/home/jspitz/JSimplex.jl/LocalPreferences.toml'),Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'),Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/basis-chain-cost/julia.sh')]
files += list(Path('/home/jspitz/JSimplex.jl/src').rglob('*.jl'))
files += [Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/Profile/src/Allocs.jl')]
for p in Path('/home/jspitz/JSimplex.jl/src').rglob('*.jl'):
 q=W/'src'/p.relative_to('/home/jspitz/JSimplex.jl/src')
 if p.read_bytes()!=q.read_bytes():raise RuntimeError('production source differs '+str(q))
import tomllib
inputs=[e['path'] for e in tomllib.loads((D/'inputs.toml').read_text())['cases'] if not e['structural_only']]
cmd=[sys.executable,'-B',str(D/'guard/guard_reviewed.py'),'freeze',str(D/name)]
for p in sorted(set(p.resolve() for p in files)):
 if not p.is_file():raise FileNotFoundError(p)
 cmd+=['--file',str(p)]
for p in inputs:cmd+=['--input',p]
subprocess.run(cmd,check=True)
pins=json.loads((D/name).read_text());print(json.dumps(dict(manifest=name,bindings=len(pins['inventory']))))
