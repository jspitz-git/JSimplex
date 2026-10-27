from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-ratio-monitor/2026-10-27');sys.path.insert(0,str(D));import common as c
O=D.parents[1]/'generic-interval-stagnation-devex/2026-10-27'
old=json.loads((O/'contract.json').read_text());command=old['command'][:];command[command.index(str(O/'driver.jl'))]=str(D/'driver.jl');command[-1]=str(D/'output/results.toml')
c.put('contract.json',dict(command=command,attempts=1,contexts=19,cases=1225,measured_windows=22050,expected_exit=0,shared_limit_seconds=600,guard_limit_seconds=592,baseline=c.TARGET,ordinary_Test=True))
shutil.copyfile(__file__,D/'seal.py')
paths={n for n in json.loads((O/'MASTER-run/pins.json').read_text())['inventory'] if not Path(n).is_relative_to(c.R/'diagnostics')}
for root in (c.M/'src',c.M/'test',D/'baseline'):
 paths.update(str(p) for p in root.rglob('*') if p.is_file())
paths.update(str(c.M/n) for n in ('Project.toml','Manifest.toml','LocalPreferences.toml'))
paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths.add(str(c.R/'diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json'))
c.put('pins.json',dict(files=sorted(paths),trees=[str(c.M/'src'),str(c.M/'test'),str(D/'baseline')],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
c.unchanged();c.put('author-host.json',c.host());print('sealed',len(paths),'pins; noJulia')
