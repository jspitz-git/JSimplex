from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-unit-perturb-residual/2026-10-28');O=D.parents[1]/'generic-residual-pivot-crash/2026-10-28';sys.path.insert(0,str(D));import common as c
cmd=c.read(str(O/'contract-final.json'))['command'];cmd[-2:]=[str(D/'driver.jl'),str(D/'output/results.toml')]
grid=c.read('expected-cases.json')
c.put('contract.json',dict(command=cmd,attempts=1,contexts=19,cases=len(grid),measured_windows=len(grid)*18,expected_exit=0,shared_limit_seconds=900,guard_limit_seconds=892,baseline=c.TARGET,ordinary_Test=True))
shutil.copyfile(__file__,D/'seal.py')
# Installed runtime/dependencies retained; no old diagnostic scripts or raw as launch inputs.
paths={n for n in c.read(str(O/'MASTER-run/pins.json'))['inventory'] if not Path(n).is_relative_to(c.R/'diagnostics')}
for root in [c.M/'src',c.M/'test',D/'baseline']:paths.update(str(p) for p in root.rglob('*') if p.is_file())
paths.update(str(c.M/n) for n in ['Project.toml','Manifest.toml','LocalPreferences.toml']);paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths.add(str(c.R/'diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json'))
c.put('pins.json',dict(files=sorted(paths),trees=[str(c.M/'src'),str(c.M/'test'),str(D/'baseline')],inputs=[str(D/'grid.toml')],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
c.unchanged();c.put('author-host.json',c.host());print(json.dumps(dict(pins=len(paths),cells=len(grid),windows=len(grid)*18,noJulia=True)))
