from pathlib import Path
import json,shutil,sys
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-local/2026-10-27');R=D.parents[2];M=Path('/home/jspitz/JSimplex.jl');O=R/'diagnostics/generic-quality-devex/2026-10-27'
for a,b in [('quality-local-fixtures.jl','fixtures.jl'),('quality-local-driver.jl','driver.jl')]:shutil.copyfile('/tmp/'+a,D/b)
shutil.copytree(O/'guard',D/'guard',ignore=shutil.ignore_patterns('__pycache__'));shutil.copyfile(O/'launch.py',D/'launch.py')
cmd=[v.replace(str(O),str(D)) for v in json.loads((O/'contract.json').read_text())['command']]
cases=15*136+2*34+2*32
(D/'contract.json').write_text(json.dumps(dict(command=cmd,expected_exit=0,attempts=1,shared_limit_seconds=600,guard_limit_seconds=592,cases=cases,measured_windows=18*cases,contexts=19),indent=2)+'\n')
sys.path.insert(0,str(D));import common as c
paths={n for n in json.loads((O/'pins.json').read_text())['inventory'] if not Path(n).is_relative_to(R/'diagnostics')}
paths.update(str(p) for root in [M/'src',M/'test',D/'baseline'] for p in root.rglob('*') if p.is_file());paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
shutil.copyfile(__file__,D/'seal.py');paths.add(str(D/'seal.py'))
c.put('pins.json',dict(files=sorted(paths),trees=[str(M/'src'),str(M/'test'),str(D/'baseline')],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}));c.unchanged();c.put('author-host.json',c.host());print('Prepared',cases,'cells',18*cases,'windows',len(paths),'pins/noJulia')
